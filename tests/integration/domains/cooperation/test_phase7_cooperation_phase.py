"""
tests/integration/domains/cooperation/test_phase7_cooperation_phase.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 Integration Tests for orchestrating CooperationPhase.
"""

import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, GroupRecord
from src.core.builder import V2EntityBuilder
from src.core.strategic import RiskLevel, ProjectState, ProjectKind, ObjectiveState, ObjectiveKind
from src.core.updates import StateUpdate
from src.domains.cooperation.phase import CooperationPhase
from src.domains.cooperation.postures import CooperationPosture
from src.domains.combat_engagement.phase import build_combat_risk_belief
from src.systems.social_systems.contracts import ContractService, COOPERATION_OFFER_COOLDOWN_TICKS


def test_phase_skips_entity_without_help_need():
    # If no objective / no help needs exists and not in group, no evaluations are done
    req = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).lifecycle(active=True).build())
    state = AuthoritativeState(entities={1: req}, tick=1, seed=123)
    
    update = StateUpdate()
    refined = CooperationPhase.execute(state, update)
    
    # cooperation_evaluations metric remains 0
    assert refined.metric_counters.get("cooperation_evaluations", 0) == 0


def test_phase_runs_when_help_need_exists():
    req = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).combat(hp=20, max_hp=100).lifecycle(active=True).build())
    # low HP creates healer/protection need
    object.__setattr__(req.strategic, "current_objective_id", "obj_1")
    
    state = AuthoritativeState(entities={1: req}, tick=1, seed=123)
    
    update = StateUpdate()
    refined = CooperationPhase.execute(state, update)
    
    assert refined.metric_counters.get("cooperation_evaluations", 0) == 1
    assert 1 in refined.entity_updates
    ent_up = refined.entity_updates[1]
    assert "last_cooperation_decision" in ent_up.property_updates


def test_cooperation_phase_no_immediate_reoffer_after_expiry_tick():
    # Tick T: entity A has a RECRUITMENT offer to trusted ally B that has just expired.
    a = (V2EntityBuilder(1)
         .kind("HERO")
         .location(0.0, 0.0)
         .combat(hp=100, max_hp=100, tactical_role="SUPPORT")
         .lifecycle(active=True)
         .build())

    b = (V2EntityBuilder(2)
         .kind("HERO")
         .location(1.0, 1.0)
         .combat(hp=100, max_hp=100, tactical_role="VANGUARD")
         .lifecycle(active=True)
         .build())

    obj = ObjectiveState(id="obj_wolf", kind=ObjectiveKind.DEFEAT_ENEMY)
    proj = ProjectState(id="proj_wolf", kind=ProjectKind.COMBAT, objectives=[obj], active_objective_id="obj_wolf")

    # TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN: real BeliefEntry (death_risk 0.6 -> HIGH)
    a.strategic.beliefs["combat_risk"] = build_combat_risk_belief(death_risk=0.6, current_tick=1)
    a.strategic.projects["proj_wolf"] = proj
    object.__setattr__(a.strategic, "current_project_id", "proj_wolf")
    object.__setattr__(a.strategic, "current_objective_id", "obj_wolf")

    a.social.trust_history[2] = 0.8

    expired_offer = ContractService.create_recruitment_contract(
        "cnt_recruit_1_2_90",
        source_id=1,
        target_id=2,
        tick=90,
    )
    assert expired_offer.expiry_tick == 100

    a = replace(
        a,
        strategic=replace(a.strategic, contracts={expired_offer.id: expired_offer}),
    )

    current_tick = 100
    state_t = AuthoritativeState(entities={1: a, 2: b}, tick=current_tick, seed=123)

    reap_update = ContractService.reap_expired_offers(state_t, StateUpdate())
    a_reap_up = reap_update.entity_updates[1]
    assert expired_offer.id in a_reap_up.strategic.contracts_remove
    ready_tick = a_reap_up.identity.cooldown_updates["cooperation_offer_retry"]
    assert ready_tick == current_tick + COOPERATION_OFFER_COOLDOWN_TICKS

    # Tick T+1: apply the authoritative effects of the reap (contract removed,
    # cooldown set) to build entity A's post-tick state, then re-run the
    # cooperation phase with the same eligible partner still available.
    a_next = replace(
        a,
        strategic=replace(a.strategic, contracts={}),
        identity=replace(a.identity, cooldowns={"cooperation_offer_retry": ready_tick}),
    )

    state_t1 = AuthoritativeState(entities={1: a_next, 2: b}, tick=current_tick + 1, seed=123)
    refined = CooperationPhase.execute(state_t1, StateUpdate())

    assert 1 in refined.entity_updates
    a_up_t1 = refined.entity_updates[1]
    decision_posture = a_up_t1.property_updates["last_cooperation_decision"]
    assert decision_posture != CooperationPosture.REQUEST_HELP.value
    assert decision_posture != CooperationPosture.HIRE_SUPPORT.value
    if a_up_t1.strategic is not None:
        assert not any(
            c.kind.name == "RECRUITMENT"
            for c in a_up_t1.strategic.contracts_add_or_update
        )


def test_phase_respects_feature_flag():
    req = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).combat(hp=20, max_hp=100).lifecycle(active=True).build())
    object.__setattr__(req.strategic, "current_objective_id", "obj_1")
    
    state = AuthoritativeState(entities={1: req}, tick=1, seed=123)
    state.periodic_due_ticks["social_cooperation_disabled"] = 1
    
    update = StateUpdate()
    refined = CooperationPhase.execute(state, update)
    
    assert 1 not in refined.entity_updates
    assert refined.metric_counters == {}
