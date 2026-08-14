"""
Integration tests for the tier-5 SOCIAL_CONTRACT materialization branch
(TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER, plan.md Step 5/Step 7).

Covers AC3 (arbitration clears with no current project), AC4/AC6 (materialization uses
metadata["raw_score"], never best_candidate.utility, and a real ProjectKind member), AC5
(high-lock current project retains against a low-urgency contract), AC6 (a high-urgency
contract interrupts a locked current project), Design Decision #2 (shared score scale with
ADVENTURE_ROUTE), Design Decision #8 (target_pos is tactically resolvable, not a stall), and
Design Decision #11 (the resume/dedup lookup stays inert for SOCIAL_CONTRACT winners).
"""
from __future__ import annotations

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.strategic import (
    ContractState, ContractKind, ContractStatus, GoalKind, ProjectKind, ObjectiveKind,
    ProjectState, ProjectStatus,
)
from src.engine.tactical import TacticalDecisionSystem
from src.systems.strategic import StrategicIntelligenceSystem
from src.systems.strategic_systems.intelligence import _score_scale_max, _ADVENTURE_ROUTE_SCORE_MAX


def _entity(eid=1, pos=(0.0, 0.0), trust_history=None, contracts=None,
            projects=None, current_project_id=None, hp=None, max_hp=None):
    builder = V2EntityBuilder(eid).kind("hero").location(*pos)
    if trust_history is not None:
        builder = builder.social(trust_history=trust_history)
    if contracts is not None or projects is not None or current_project_id is not None:
        builder = builder.strategic(
            contracts=contracts or {},
            projects=projects or {},
            current_project_id=current_project_id,
        )
    if hp is not None or max_hp is not None:
        builder = builder.combat(hp=hp, max_hp=max_hp)
    return builder.build()


def _state(entities=None, tick=0):
    return AuthoritativeState(tick=tick, seed=42, entities=entities or {})


# The RECRUITMENT contract used across several tests below: trust=0.8 (trust_history), expiry_tick=50,
# duration=100 -> urgency=0.5; daily_pay=20, evolution_level=1 -> expected_pay=10 -> value=1.0;
# risk_level=NORMAL -> risk_weight=0.5. raw = 0.8+0.5+0.9-0.15 = 2.05.
_RECRUIT_CONTRACT = ContractState(
    id="c1", kind=ContractKind.RECRUITMENT, source_id=2, target_id=1,
    terms={"daily_pay": 20, "duration": 100, "risk_level": "NORMAL"},
    status=ContractStatus.ACTIVE, expiry_tick=50,
)


def test_active_contract_wins_arbitration_with_no_current_project():
    entity = _entity(trust_history={2: 0.8}, contracts={"c1": _RECRUIT_CONTRACT})
    state = _state(entities={1: entity}, tick=0)

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    assert result is not None
    assert result.current_project_id_set == "proj_contract_c1_t0"
    assert len(result.projects_add_or_update) == 1
    assert result.projects_add_or_update[0].id == "proj_contract_c1_t0"


def test_social_contract_winner_materializes_with_raw_score_not_utility():
    """AC4/AC6: ProjectState.score must equal the RAW score (2.05), never the normalized
    utility ((2.05/2.9)*100 ~= 70.6897) -- a regression here silently reproduces
    TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG's defect class."""
    entity = _entity(trust_history={2: 0.8}, contracts={"c1": _RECRUIT_CONTRACT})
    state = _state(entities={1: entity}, tick=0)

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    assert result is not None
    project = result.projects_add_or_update[0]
    expected_utility = (2.05 / 2.9) * 100.0

    assert project.score == pytest.approx(2.05)
    assert project.score != expected_utility
    assert project.kind == ProjectKind.COMBAT
    assert project.kind != GoalKind.SOCIAL_CONTRACT


def test_social_contract_recruitment_maps_to_combat_project_loan_maps_to_social_project():
    recruit_entity = _entity(eid=1, trust_history={2: 0.8}, contracts={"c1": _RECRUIT_CONTRACT})
    recruit_state = _state(entities={1: recruit_entity}, tick=0)
    recruit_result = StrategicIntelligenceSystem.evaluate_strategic_intent(
        recruit_state, recruit_entity, force=True
    )
    recruit_proj = recruit_result.projects_add_or_update[0]
    assert recruit_proj.kind == ProjectKind.COMBAT
    assert recruit_proj.objectives[0].kind == ObjectiveKind.REACH_LOCATION
    assert recruit_proj.objectives[0].target == "2"

    loan_contract = ContractState(
        id="c_loan", kind=ContractKind.LOAN, source_id=3, target_id=1,
        terms={"amount": 100, "duration": 200},
        status=ContractStatus.ACTIVE, expiry_tick=100,
    )
    loan_entity = _entity(eid=1, trust_history={3: 0.9}, contracts={"c_loan": loan_contract})
    loan_state = _state(entities={1: loan_entity}, tick=0)
    loan_result = StrategicIntelligenceSystem.evaluate_strategic_intent(
        loan_state, loan_entity, force=True
    )
    loan_proj = loan_result.projects_add_or_update[0]
    assert loan_proj.kind == ProjectKind.SOCIAL
    assert loan_proj.objectives[0].kind == ObjectiveKind.REACH_LOCATION
    assert loan_proj.objectives[0].target == "3"


def test_high_lock_current_project_retains_against_low_urgency_contract():
    """AC5: hp is deliberately below the 80% _threat_resolved() early-release threshold (50/100
    -> 0.5) so the locked-branch's normalized comparison actually runs instead of being
    unconditionally bypassed by evaluate_project_switch()'s threat-resolved short-circuit.

    current: kind=GoalKind.HARVESTING, score=90.0, lock_until_tick=150 (> tick=100), default
    profile (interruption_resistance=0.3, resistance_multiplier=30.0) -> retention_margin=9.0.
    current_max=_score_scale_max(GoalKind.HARVESTING)=100.0 -> current_pct=0.9;
    normalized_effective_current_pct = 0.9 + 9.0/100 = 0.99.

    Low-urgency contract (RECRUITMENT): trust=0.3, no duration/expiry set -> urgency=0.5;
    daily_pay=5, risk_level=HIGH -> expected_pay=10 -> value=0.5; risk_weight=1.0.
    raw = 0.3+0.5+0.45-0.3 = 0.95. candidate_pct = 0.95/2.9 ~= 0.3276, clears neither
    normalized_effective_current_pct (0.99) nor the 0.8 urgency floor -> blocked.
    """
    low_urgency_contract = ContractState(
        id="c_low", kind=ContractKind.RECRUITMENT, source_id=2, target_id=1,
        terms={"daily_pay": 5, "risk_level": "HIGH"},
        status=ContractStatus.ACTIVE,
    )
    current = ProjectState(
        id="current", kind=GoalKind.HARVESTING, status=ProjectStatus.ACTIVE,
        score=90.0, lock_until_tick=150,
    )
    entity = _entity(
        trust_history={2: 0.3},
        contracts={"c_low": low_urgency_contract},
        projects={"current": current},
        current_project_id="current",
        hp=50, max_hp=100,
    )
    state = _state(entities={1: entity}, tick=100)

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    # evaluate_project_switch() returns None (blocked at the lock-bypass gate), so
    # evaluate_strategic_intent() falls through to its boredom-only return -- current_project_id
    # is never touched and no project is added/suspended.
    assert result is not None
    assert result.current_project_id_set is None
    assert result.projects_add_or_update == []


def test_high_urgency_contract_interrupts_locked_current_project():
    """AC6: a genuinely high-urgency contract clears BOTH of evaluate_project_switch()'s gates
    (the normalized lock-bypass gate AND the raw, unnormalized effective_current_score check)
    against a low-score locked current -- mirroring
    test_score_normalization.py::test_max_adventure_route_candidate_can_exceed_low_urgency_goal_current's
    own low-interruption-resistance pattern, since a contract-originated candidate's raw score is
    capped at 2.9 (Design Decision #2's shared scale) and can never clear the final raw check
    against a current holding the DEFAULT retention_margin (9.0) -- interruption_resistance is
    deliberately set low (0.01) here so the final raw check is actually reachable, exactly as
    the adventure ticket's own equivalent test already established for its own ProjectKind-typed
    candidates.

    current: kind=GoalKind.HARVESTING, score=1.0, lock_until_tick=150 (> tick=100).
    interruption_resistance=0.01, resistance_multiplier=30.0 (default) -> retention_margin=0.3.
    current_max=_score_scale_max(GoalKind.HARVESTING)=100.0 -> current_pct=0.01;
    normalized_effective_current_pct = 0.01 + 0.3/100 = 0.013.

    LOAN contract: trust=1.0 (bond sentiment=1.0), expiry_tick=100, duration=100, current
    tick=100 -> ticks_remaining=0 -> urgency=1.0; amount=1000, evolution_level=1 ->
    expected_amount=50 -> value=min(1.0, 20.0)=1.0; risk_weight=0.0 (LOAN carries no
    risk_level). raw = 1.0+1.0+0.9-0.0 = 2.9 (the formula's own ceiling).
    candidate_pct = 2.9/2.9 = 1.0, clears both 0.013 and the 0.8 floor -> lock bypassed.
    Final raw check: effective_current_score = 1.0+0.3 = 1.3; candidate.score(2.9) > 1.3 ->
    switch succeeds.
    """
    from src.core.models.social import SocialBond

    high_urgency_contract = ContractState(
        id="c_high", kind=ContractKind.LOAN, source_id=2, target_id=1,
        terms={"amount": 1000, "duration": 100},
        status=ContractStatus.ACTIVE, expiry_tick=100,
    )
    current = ProjectState(
        id="current", kind=GoalKind.HARVESTING, status=ProjectStatus.ACTIVE,
        score=1.0, lock_until_tick=150,
    )
    entity = (
        V2EntityBuilder(1).kind("hero").location(0.0, 0.0)
        .social(bonds={2: SocialBond(target_id=2, sentiment=1.0)})
        .strategic(
            contracts={"c_high": high_urgency_contract},
            projects={"current": current},
            current_project_id="current",
        )
        .cognition(interruption_resistance=0.01)
        .combat(hp=50, max_hp=100)
        .build()
    )
    state = _state(entities={1: entity}, tick=100)

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    assert result is not None
    assert result.current_project_id_set == "proj_contract_c_high_t100"
    suspended = [p for p in result.projects_add_or_update if p.id == "current"]
    assert len(suspended) == 1
    assert suspended[0].status == ProjectStatus.SUSPENDED


def test_social_contract_target_position_is_tactically_resolvable_not_a_stall():
    entity = _entity(trust_history={2: 0.8}, contracts={"c1": _RECRUIT_CONTRACT})
    counterparty = _entity(eid=2, pos=(15.0, 20.0))
    state = _state(entities={1: entity, 2: counterparty}, tick=0)

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
    project = result.projects_add_or_update[0]
    materialized_obj = project.objectives[0]

    assert materialized_obj.target_position == counterparty.navigation.position

    resolved_pos, node_id, building_id = TacticalDecisionSystem._resolve_target_position(
        state, materialized_obj
    )
    assert resolved_pos == counterparty.navigation.position
    # int(obj.target) == 2 succeeds, but no resource_node/building with id=2 exists in this
    # fixture's state -- confirming the target_position fallback (not an accidental id
    # collision) is what resolves it.
    assert node_id is None
    assert building_id is None


def test_social_contract_and_adventure_route_share_score_scale_as_designed():
    """Design Decision #2: explicit, in-code assertion that a contract-originated ProjectKind
    lands on the SAME 2.9-ceiling constant as adventure's own ProjectKind-typed candidates --
    a deliberate, disclosed design choice (_score_scale_max() dispatches by Python enum class
    identity, not provenance)."""
    assert _score_scale_max(ProjectKind.COMBAT) == _ADVENTURE_ROUTE_SCORE_MAX
    assert _score_scale_max(ProjectKind.SOCIAL) == _ADVENTURE_ROUTE_SCORE_MAX


def test_social_contract_winner_preserves_dedup_lookup_inert_behavior():
    """Design Decision #11: a suspended contract-project is never resumed by the pre-existing
    `existing = next(...)` lookup (intelligence.py:1429) for a SOCIAL_CONTRACT winner -- it is
    re-materialized fresh under a new tick-suffixed id. Documents the accepted, shared, unfixed
    gap rather than leaving it silently unasserted."""
    suspended = ProjectState(
        id="proj_contract_old_t0", kind=ProjectKind.COMBAT, status=ProjectStatus.SUSPENDED,
        score=1.0,
    )
    entity = _entity(
        trust_history={2: 0.8},
        contracts={"c1": _RECRUIT_CONTRACT},
        projects={"proj_contract_old_t0": suspended},
    )
    state = _state(entities={1: entity}, tick=5)

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    assert result is not None
    assert result.current_project_id_set == "proj_contract_c1_t5"
    assert result.current_project_id_set != "proj_contract_old_t0"
