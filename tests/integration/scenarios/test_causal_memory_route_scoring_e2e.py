"""
tests/integration/scenarios/test_causal_memory_route_scoring_e2e.py

TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING: end-to-end proof that causal memory now flows through
the live pipeline rather than only via hand-constructed test dicts. A real ATTACK routed through
AuthoritativeApplyPipeline.refine()/ApplyPath.apply_generation() emits a COMBAT_LOSS WorldEvent;
one tick later (the inherent recent_world_events lag, matching the faction_awareness precedent)
MemoryUpdatePhase consumes it and entity.cognition.memory.causal.entries becomes non-empty; and
AdventureRouteScorer.score() -- untouched by this ticket -- then produces the documented -1.0
memory_adjustment for a HUNT_WEAK_ENEMY route.

The defender is deliberately healthy (high def_stat keeps damage minimal, default stamina/weapon
durability) so hp_pct stays above 0.3 and CausalAttributionService.attribute()'s combat_loss
branch falls through to the "strong_enemy"/"avoid_enemy" fallback rather than low_health/
low_stamina/damaged_weapon -- the only path AdventureRouteScorer currently maps to a nonzero
adjustment (see plan.md Step 5 / Scope Guards).
"""
from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate, StateUpdate, TaskUpdate
from src.domains.adventure.schema import AdventureRouteOption, RouteFamily
from src.domains.adventure.scoring import AdventureRouteScorer
from src.domains.optimization.feature_flags import FeatureMode
from src.engine.apply import ApplyPath
from src.engine.pipeline import AuthoritativeApplyPipeline


def _attacker_entity(entity_id: int) -> object:
    return (
        V2EntityBuilder(entity_id)
        .kind("monster")
        .location(10.0, 10.0)
        .combat(hp=100, max_hp=100, atk=10, alive=True, readiness=100.0, attack_range=10)
        .lifecycle(active=True)
        .identity(faction=Faction.HERO_GUILD)
        .build()
    )


def _defender_entity(entity_id: int) -> object:
    return (
        V2EntityBuilder(entity_id)
        .kind("monster")
        .location(10.0, 11.0)
        .combat(hp=100, max_hp=100, def_stat=50, alive=True)
        .lifecycle(active=True)
        .identity(faction=Faction.MONSTER_HORDE)
        .navigation(region_id="wolf_den")
        .build()
    )


def _attack_update(attacker_id: int, target_id: int) -> StateUpdate:
    return StateUpdate(entity_updates={
        attacker_id: EntityUpdate(
            entity_id=attacker_id,
            task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "ATTACK", "target_id": target_id}),
        )
    })


def test_combat_loss_end_to_end_produces_nonzero_memory_adjustment_next_tick():
    attacker = _attacker_entity(1)
    defender = _defender_entity(2)

    state1 = AuthoritativeState(
        tick=1, seed=42, entities={1: attacker, 2: defender},
        feature_flags={"ENABLE_MEMORY_UPDATE": FeatureMode.ON},
    )

    # Tick 1: the attack resolves via action_routing and the defender survives, damaged but
    # healthy (hp_pct stays well above 0.3).
    refined1 = AuthoritativeApplyPipeline.refine(state1, _attack_update(1, 2))
    state2 = ApplyPath.apply_generation(state1, refined1, next_tick=2)

    defender_after_tick1 = state2.entities[2]
    assert 0 < defender_after_tick1.combat.hp < 100
    assert defender_after_tick1.combat.alive is True
    # One-tick lag: MemoryUpdatePhase runs before action_routing in the same tick, so the
    # combat_loss trigger this attack produced is not yet consumable -- causal memory is still
    # empty immediately after tick 1.
    assert len(defender_after_tick1.cognition.memory.causal.entries) == 0

    # Tick 2: recent_world_events now carries the prior tick's COMBAT_LOSS event.
    refined2 = AuthoritativeApplyPipeline.refine(state2, StateUpdate())
    state3 = ApplyPath.apply_generation(state2, refined2, next_tick=3)

    defender_after_tick2 = state3.entities[2]
    causal_entries = defender_after_tick2.cognition.memory.causal.entries
    assert len(causal_entries) == 1
    assert causal_entries[0].event_kind == "combat_loss"
    assert "avoid_enemy" in causal_entries[0].future_advice

    route = AdventureRouteOption(
        family=RouteFamily.HUNT_WEAK_ENEMY,
        score=0.0,
        confidence=0.8,
        expected_benefit=0.5,
        expected_risk=0.1,
    )
    scored = AdventureRouteScorer.score(defender_after_tick2, route)
    assert scored.memory_adjustment == -1.0
