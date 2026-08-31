"""TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING: ActionRoutingPhase.route() must emit a
WorldEventCategory.COMBAT_LOSS WorldEvent whenever a defender survives an ATTACK and takes
damage -- the real, live trigger_event producer for MemoryUpdatePhase (previously fed only by
hand-constructed test dicts). Deliberately independent of NearDeathHardeningPhase's
hp_pct<=10% threshold: coupling to that threshold would guarantee hp_pct<0.3 on every firing and
starve CausalAttributionService's avoid_enemy fallback branch.

No event may be emitted when the attack lands no damage (rejected/out-of-range) or when the
defender dies -- a dead entity has no future to receive a memory update.
"""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate, StateUpdate, TaskUpdate
from src.domains.world_emergence.schema import WorldEventCategory
from src.engine.pipeline_phases.actions import ActionRoutingPhase


def _attacker_entity(entity_id: int, atk: int = 10, readiness: float = 100.0, attack_range: int = 10, pos=(10.0, 10.0)):
    return (
        V2EntityBuilder(entity_id)
        .kind("monster")
        .location(*pos)
        .combat(hp=100, max_hp=100, atk=atk, alive=True, readiness=readiness, attack_range=attack_range)
        .lifecycle(active=True)
        .identity(faction=Faction.HERO_GUILD)
        .build()
    )


def _target_entity(entity_id: int, hp: int = 100, def_stat: int = 50, pos=(10.0, 11.0), region_id=None):
    b = (
        V2EntityBuilder(entity_id)
        .kind("monster")
        .location(*pos)
        .combat(hp=hp, max_hp=100, def_stat=def_stat, alive=True)
        .lifecycle(active=True)
        .identity(faction=Faction.MONSTER_HORDE)
    )
    if region_id is not None:
        b = b.navigation(region_id=region_id)
    return b.build()


def _attack_update(entity_id: int, target_id: int) -> StateUpdate:
    return StateUpdate(entity_updates={
        entity_id: EntityUpdate(
            entity_id=entity_id,
            task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "ATTACK", "target_id": target_id}),
        )
    })


def test_combat_loss_world_event_emitted_when_defender_survives_and_takes_damage():
    attacker = _attacker_entity(1, atk=10)
    defender = _target_entity(2, hp=100, def_stat=50, region_id="wolf_den")
    state = AuthoritativeState(tick=7, seed=42, entities={1: attacker, 2: defender})

    refined = ActionRoutingPhase.route(state, _attack_update(1, 2))

    combat_loss_events = [e for e in refined.world_events_add if e.category == WorldEventCategory.COMBAT_LOSS]
    assert len(combat_loss_events) == 1
    event = combat_loss_events[0]
    assert event.subject == "2"
    assert event.tick == 7
    assert event.region_id == "wolf_den"


def test_combat_loss_world_event_not_emitted_when_attack_is_out_of_range():
    attacker = _attacker_entity(1, attack_range=1, pos=(0.0, 0.0))
    defender = _target_entity(2, pos=(50.0, 50.0))
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: defender})

    refined = ActionRoutingPhase.route(state, _attack_update(1, 2))

    assert not any(e.category == WorldEventCategory.COMBAT_LOSS for e in refined.world_events_add)


def test_combat_loss_world_event_not_emitted_when_defender_dies():
    attacker = _attacker_entity(1, atk=1000)
    defender = _target_entity(2, hp=10, def_stat=1)
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: defender})

    refined = ActionRoutingPhase.route(state, _attack_update(1, 2))

    combat_ref = refined.entity_updates[2].combat
    assert combat_ref.alive_set is False
    assert not any(e.category == WorldEventCategory.COMBAT_LOSS for e in refined.world_events_add)


def test_combat_loss_world_event_preserves_earlier_same_tick_writers():
    """Confirms accumulation onto update.world_events_add rather than overwrite -- see plan.md
    Step 4's shared-resource analysis of diplomatic_transitions/military_conflict as earlier
    same-tick writers of this same field."""
    from src.domains.world_emergence.schema import WorldEvent

    attacker = _attacker_entity(1, atk=10)
    defender = _target_entity(2, hp=100, def_stat=50)
    state = AuthoritativeState(tick=3, seed=42, entities={1: attacker, 2: defender})

    prior_event = WorldEvent(category=WorldEventCategory.FACTION_WAR_DECLARED, tick=3, subject="99")
    incoming_update = _attack_update(1, 2)
    incoming_update = StateUpdate(
        entity_updates=incoming_update.entity_updates,
        world_events_add=[prior_event],
    )

    refined = ActionRoutingPhase.route(state, incoming_update)

    assert prior_event in refined.world_events_add
    assert any(e.category == WorldEventCategory.COMBAT_LOSS for e in refined.world_events_add)
