"""
tests/integration/scenarios/test_phase4_combat_engagement_scenarios.py

Phase 4 — Scenario-driven integration tests for Combat Engagement Cognition.
Verifies Scenarios 4.1 to 4.6.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent, PersonalityComponent, AuthoritativeState
from src.domains.combat_engagement.service import CombatEngagementDecisionService
from src.domains.combat_engagement.schema import CombatPosture, OpponentModel
from src.domains.combat_engagement.reassessment import CombatReassessmentService


def _entity(e_id, hp=100, evolution_level=1, bravery=0.5):
    b = V2EntityBuilder(e_id)
    b.replace_combat(CombatComponent(hp=hp, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=bravery, sociability=0.5, industry=0.5)
    b.identity(evolution_level=evolution_level, personality=p)
    return b.build()


def _state(entities, tick=10) -> AuthoritativeState:
    ent_map = {e.id: e for e in entities}
    return AuthoritativeState(
        tick=tick, seed=1, world_time=100, entities=ent_map,
        groups={}, regions={}, resource_nodes={}, buildings={},
        chests={}, ground_items={}, corpses={}, camps={},
        local_scars={}, global_resources={}, town_tiles=(),
        building_tiles=(), terrain=(), home_storage={},
        town_center=(0, 0), periodic_due_ticks={}, work_debt={},
        movement_count=0, maturity=0, last_calamity_tick=0,
        blocked_tiles=(), town_entity_ids=(),
    )



def test_scenario_4_1_unknown_equal_opponent():
    # Unknown equal target does not trigger immediate ENGAGE posture, prefers watching/probing
    actor = _entity(1, bravery=0.5)
    target = _entity(2)
    state = _state([actor, target])

    result = CombatEngagementDecisionService.evaluate(actor, target, state)

    # Shoud probe or watch rather than immediately engage due to high uncertainty
    assert result.posture in (CombatPosture.WATCH, CombatPosture.PROBE)


def test_scenario_4_2_brave_vs_cautious_divergence():
    target = _entity(2)
    state = _state([target])

    # Brave actor evaluates same target
    brave_actor = _entity(1, bravery=0.9)
    result_brave = CombatEngagementDecisionService.evaluate(brave_actor, target, state)

    # Cautious actor evaluates same target
    cautious_actor = _entity(3, bravery=0.1)
    result_cautious = CombatEngagementDecisionService.evaluate(cautious_actor, target, state)

    # Divergence check
    assert result_brave.posture in (CombatPosture.PROBE, CombatPosture.ENGAGE)
    assert result_cautious.posture in (CombatPosture.WATCH, CombatPosture.AVOID)


def test_scenario_4_3_objective_pressure_justifies_risk():
    actor = _entity(1, bravery=0.4)
    target = _entity(2, evolution_level=2)  # Risky/stronger target
    state = _state([actor, target])

    # Without quest pressure
    result_normal = CombatEngagementDecisionService.evaluate(actor, target, state, objective_pressure=0.0)

    # With quest pressure
    result_quest = CombatEngagementDecisionService.evaluate(actor, target, state, objective_pressure=1.0)

    # Objective pressure should increase risk tolerance, making quest target more acceptable/active
    assert result_quest.risk_evaluation.value_score > result_normal.risk_evaluation.value_score


def test_scenario_4_4_loss_changes_future_decision():
    actor = _entity(1)
    target = _entity(2)
    state = _state([actor, target])

    # Evaluate target initially without memory
    res_initial = CombatEngagementDecisionService.evaluate(actor, target, state)

    # Create memory after a bad loss
    memory = OpponentModel(
        subject_key="entity.2",
        estimated_power=150.0,  # Much higher than default (20.0)
        uncertainty=0.1,
        confidence=0.9,
        outcomes=("LOST",),
    )

    # Re-evaluate with memory
    res_with_memory = CombatEngagementDecisionService.evaluate(actor, target, state, memory=memory)

    # Perceived estimate should have lower uncertainty and much higher power
    assert res_with_memory.opponent_estimate.uncertainty < res_initial.opponent_estimate.uncertainty
    assert res_with_memory.opponent_estimate.estimated_power > res_initial.opponent_estimate.estimated_power
    assert res_with_memory.posture in (CombatPosture.AVOID, CombatPosture.WATCH, CombatPosture.RETREAT)


def test_scenario_4_5_hidden_skill_revealed_mid_combat():
    actor = _entity(1)
    target = _entity(2)
    state = _state([actor, target])

    # Initial decision is to watch or probe
    res_initial = CombatEngagementDecisionService.evaluate(actor, target, state)

    # Combat events reveal a skill was used by the attacker (target)
    events = [{"attacker_id": 2, "skill_id": "heavy_strike"}]

    # Reassess
    res_reassessed = CombatReassessmentService.reassess(actor, target, events, res_initial, state)

    # Since skill was observed, full evaluation was run which records reassessment trigger
    assert res_reassessed.trace.get("last_reassessed_tick") is not None


def test_scenario_4_6_monster_self_preservation():
    # Badly wounded actor retreats
    actor = _entity(1, hp=15)  # Under 20% hp
    target = _entity(2)
    state = _state([actor, target])

    result = CombatEngagementDecisionService.evaluate(actor, target, state)

    # HP is critical, selecting retreat for self-preservation
    assert result.posture == CombatPosture.RETREAT
