"""TCK-20261007-A-WALKER-BESIDE-A-PERCEIVED-HOSTILE-KEEPS-STEPPING-AND-EATS-AN-OPPORTUNITY-ATTACK-PER-STEP:
an entity that holds an action task (ATTACK, SKILL, INTERACT, HOLD) does not walk on a navigation target left behind by an
earlier decision.

Measured (pinned, frontier_living_world seed 43): of 515 movement-phase calls for an entity holding an ATTACK task, 156 had the
live target already adjacent and still moved the attacker (71 with an opportunity-attack swing). The movement phase reads only
``navigation.target``, live-retargets it to the entity named in ``payload["target_id"]`` for ANY task, and a refused step onto the
occupied target tile falls to the sidestep ladder (``MovementSystem._find_sidestep``), which steps the attacker off adjacency.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.config.profiles import PROD_SMALL
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.movement_modes import MovementMode
from src.core.state import AuthoritativeState, TaskComponent
from src.core.updates import EntityUpdate, NavigationUpdate, TaskUpdate
from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers
from src.engine.candidate_selector import MovementCandidateSelector as MCS
from src.engine.combat import CombatResolutionSystem
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.tactical import TacticalDecisionSystem
from src.platform.rng import DeterministicRNG


@pytest.fixture(scope="module", autouse=True)
def _consumers():
    from src.content.repository import CatalogRepository

    repo = CatalogRepository("data/content")
    repo.load_all()
    configure_behavior_consumers(repo)
    yield
    reset_behavior_consumers()


def _fighter(eid, pos, faction, *, strong):
    role = EntityRole.HERO if faction == Faction.HERO_GUILD else EntityRole.MONSTER
    return (
        V2EntityBuilder(eid)
        .kind("hero" if role == EntityRole.HERO else "monster")
        .location(*pos)
        .identity(role=role, faction=faction)
        .combat(hp=300 if strong else 40, max_hp=300 if strong else 40, atk=60 if strong else 1,
                def_stat=30 if strong else 1, attack_range=1, readiness=100.0, alive=True)
        .lifecycle(active=True)
        .build()
    )


def _holder(task_kind, payload, target=(40.0, 40.0), mode=MovementMode.PURSUE):
    e = _fighter(1, (10.0, 10.0), Faction.HERO_GUILD, strong=True)
    return replace(e, navigation=replace(e.navigation, target=target, movement_mode=mode),
                   task=TaskComponent(work_kind=task_kind, payload=payload))


@pytest.mark.parametrize("kind,payload,expected", [
    ("ENTITY_ACT", {"action": "ATTACK", "target_id": 2}, True),
    ("ENTITY_ACT", {"action": "INTERACT", "target_id": 7}, True),
    ("ENTITY_ACT", {}, False),          # the idle encoding: the brain decides
    ("ENTITY_MOVE", {"target_id": 2}, False),
])
def test_holds_action_task_is_an_action_with_a_payload(kind, payload, expected):
    assert MCS.holds_action_task(_holder(kind, payload)) is expected


def test_live_tracking_follows_the_target_only_for_entity_tracking_moves():
    target = _fighter(2, (30.0, 31.0), Faction.MONSTER_HORDE, strong=False)
    entities = {2: target}
    pursuit = _holder("ENTITY_MOVE", {"target_id": 2})
    assert MCS.resolve_live_tracking_target(pursuit, entities, (40.0, 40.0)) == (30.0, 31.0)
    attack = _holder("ENTITY_ACT", {"action": "ATTACK", "target_id": 2})
    assert MCS.resolve_live_tracking_target(attack, entities, (40.0, 40.0)) == (40.0, 40.0)
    cover = _holder("ENTITY_MOVE", {"target_id": 2, "reason": "SEEK_COVER"}, mode=MovementMode.REPOSITION)
    assert MCS.resolve_live_tracking_target(cover, entities, (40.0, 40.0)) == (40.0, 40.0)


def test_the_candidate_selector_does_not_offer_an_action_holder_a_move_but_offers_an_idle_entity_one():
    target = _fighter(2, (11.0, 10.0), Faction.MONSTER_HORDE, strong=False)
    holder = _holder("ENTITY_ACT", {"action": "ATTACK", "target_id": 2})
    idle = _holder("ENTITY_ACT", {})
    for entity, offered in ((holder, False), (idle, True)):
        state = AuthoritativeState(tick=5, seed=1, entities={1: entity, 2: target})
        assert (1 in MCS.select(state, None, [1])) is offered


def test_an_action_holder_does_move_on_a_tick_that_sets_a_target():
    target = _fighter(2, (11.0, 10.0), Faction.MONSTER_HORDE, strong=False)
    holder = _holder("ENTITY_ACT", {"action": "ATTACK", "target_id": 2})
    state = AuthoritativeState(tick=5, seed=1, entities={1: holder, 2: target})
    # a decision: a target set together with an ENTITY_MOVE task update (CONFLICT-04 at the movement layer: a bare navigation update
    # beside an engaged hostile is not one)
    decision = EntityUpdate(entity_id=1, navigation=NavigationUpdate(target_set=(20.0, 20.0)),
                            task=TaskUpdate(work_kind_set="ENTITY_MOVE", payload_set={"target_position": (20.0, 20.0)}))
    fresh = type("U", (), {"entity_updates": {1: decision},
                           "dirty_set": None, "force_full_scan": False})()
    assert 1 in MCS.select(state, fresh, [1])


def test_an_attack_emission_clears_the_navigation_target_it_inherits():
    hero = _holder("ENTITY_MOVE", {"target_id": 2, "target_position": (40.0, 40.0)})
    monster = _fighter(2, (11.0, 10.0), Faction.MONSTER_HORDE, strong=False)
    state = AuthoritativeState(tick=1, seed=1, entities={1: hero, 2: monster})
    update = TacticalDecisionSystem.evaluate_entity_intent(state, hero, [monster], 0.0)
    assert update.task.payload_set["action"] == "ATTACK"
    assert update.navigation is not None and update.navigation.target_clear


def test_an_adjacent_attacker_holding_an_attack_task_stays_on_its_tile_and_takes_no_opportunity_attack(monkeypatch):
    """Kernel-level: the attacker inherits a navigation target; the target is pinned adjacent. Before the change the movement
    phase live-retargeted onto the target's tile and the sidestep ladder stepped the attacker off adjacency."""
    swings = []
    original = CombatResolutionSystem.resolve_multi_attack

    def spy(attackers, target, ctx, is_opportunity_attack=False, **kw):
        if is_opportunity_attack:
            swings.append(getattr(ctx, "tick", None))
        return original(attackers, target, ctx, is_opportunity_attack=is_opportunity_attack, **kw)

    monkeypatch.setattr(CombatResolutionSystem, "resolve_multi_attack", staticmethod(spy))
    attacker = _holder("ENTITY_ACT", {"action": "ATTACK", "target_id": 2}, target=(11.0, 10.0))
    target = _fighter(2, (11.0, 10.0), Faction.MONSTER_HORDE, strong=False)
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: target})
    kernel = Kernel(
        profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(42),
        flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor(),
    )
    positions = []
    try:
        for _ in range(6):
            kernel.tick_once()
            current = kernel._state
            positions.append(tuple(current.entities[1].navigation.position))
            pinned = replace(target, combat=replace(target.combat, hp=current.entities[2].combat.hp,
                                                    alive=current.entities[2].combat.alive))
            kernel._state = replace(current, entities={**dict(current.entities), 2: pinned})
    finally:
        kernel.shutdown()
    assert set(positions) == {(10.0, 10.0)}, positions
    assert swings == []


def test_a_navigation_only_errand_walk_still_walks_and_a_pursuit_still_live_retargets():
    """Errand walks (the WANDER objective walk sets only a navigation target, no task) and entity-tracking moves are unchanged."""
    target = _fighter(2, (30.0, 31.0), Faction.MONSTER_HORDE, strong=False)
    errand = _holder("ENTITY_ACT", {}, target=(40.0, 40.0), mode=MovementMode.WANDER)
    state = AuthoritativeState(tick=2, seed=1, entities={1: errand, 2: target})  # (tick + id) % 3 == 0 passes the WANDER cadence
    assert MCS.movement_target(errand, None, state.entities) == (40.0, 40.0)
    assert 1 in MCS.select(state, None, [1])
    pursuit = _holder("ENTITY_MOVE", {"target_id": 2})
    assert MCS.movement_target(pursuit, None, state.entities) == (30.0, 31.0)
