"""
tests/unit/domains/combat_engagement/test_phase4_combat_engagement_events.py

Phase 4 — Observability and event trace mapping unit tests.
Verifies selected event triggers and telemetry updates when combat postures are determined.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent, PersonalityComponent, AuthoritativeState
from src.domains.combat_engagement.service import CombatEngagementDecisionService
from src.domains.combat_engagement.schema import CombatPosture


def _entity(e_id):
    b = V2EntityBuilder(e_id)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p)
    return b.build()


def _state(entities) -> AuthoritativeState:
    ent_map = {e.id: e for e in entities}
    return AuthoritativeState(
        tick=1, seed=1, world_time=100, entities=ent_map,
        groups={}, regions={}, resource_nodes={}, buildings={},
        chests={}, ground_items={}, corpses={}, camps={},
        local_scars={}, global_resources={}, town_tiles=(),
        building_tiles=(), terrain=(), home_storage={},
        town_center=(0, 0), periodic_due_ticks={}, work_debt={},
        movement_count=0, maturity=0, last_calamity_tick=0,
        blocked_tiles=(), town_entity_ids=(),
    )


def test_combat_engagement_decision_result_contains_detailed_trace():
    actor = _entity(1)
    target = _entity(2)
    state = _state([actor, target])

    # Run evaluation
    result = CombatEngagementDecisionService.evaluate(actor, target, state)

    # Verify decision includes required diagnostic telemetry
    assert result.actor_id == 1
    assert result.target_id == 2
    assert result.posture is not None
    assert result.trace is not None
    assert "posture" in result.trace
    assert "win_confidence" in result.trace
    assert "death_risk" in result.trace
    assert result.reason is not None
