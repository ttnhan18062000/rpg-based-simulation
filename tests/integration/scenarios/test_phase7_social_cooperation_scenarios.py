"""
tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 Scenario-Driven Integration Tests.
"""

import pytest
from src.core.state import AuthoritativeState, GroupRecord
from src.core.builder import V2EntityBuilder
from src.core.strategic import RiskLevel, ProjectState, ProjectKind, ObjectiveState, ObjectiveKind
from src.core.updates import StateUpdate
from src.domains.cooperation.phase import CooperationPhase
from src.domains.cooperation.postures import CooperationPosture


def test_scenario_7_1_risky_objective_creates_help_request():
    # Setup Entity A wanting a wolf hunt, capability high risk, trusted ally B nearby
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
         
    # A has wolf target objective
    obj = ObjectiveState(id="obj_wolf", kind=ObjectiveKind.DEFEAT_ENEMY)
    proj = ProjectState(id="proj_wolf", kind=ProjectKind.COMBAT, objectives=[obj], active_objective_id="obj_wolf")
    
    a.strategic.beliefs["combat_risk"] = {"level": RiskLevel.HIGH}
    a.strategic.projects["proj_wolf"] = proj
    object.__setattr__(a.strategic, "current_project_id", "proj_wolf")
    object.__setattr__(a.strategic, "current_objective_id", "obj_wolf")
    
    # A trusts B
    a.social.trust_history[2] = 0.8
    
    state = AuthoritativeState(entities={1: a, 2: b}, tick=1, seed=123)
    
    update = StateUpdate()
    refined = CooperationPhase.execute(state, update)
    
    # Assert A chose to REQUEST_HELP and proposed a contract targeting B
    assert 1 in refined.entity_updates
    a_up = refined.entity_updates[1]
    decision_posture = a_up.property_updates["last_cooperation_decision"]

    assert decision_posture == CooperationPosture.REQUEST_HELP.value
    assert "proposed_cooperation_contract" in a_up.property_updates
    contract = a_up.strategic.contracts_add_or_update[0]
    assert contract.target_id == 2

    # Verify Forbidden Behavior assertion: Entity A does NOT go solo
    assert decision_posture != CooperationPosture.SOLO.value


def test_scenario_7_2_no_good_partner_causes_defer():
    # Setup Entity A with risky objective but no trusted/available partners
    a = (V2EntityBuilder(1)
         .kind("HERO")
         .location(0.0, 0.0)
         .combat(hp=100, max_hp=100)
         .lifecycle(active=True)
         .build())
         
    # B exists but is untrusted
    b = (V2EntityBuilder(2)
         .kind("HERO")
         .location(1.0, 1.0)
         .lifecycle(active=True)
         .build())
         
    obj = ObjectiveState(id="obj_wolf", kind=ObjectiveKind.DEFEAT_ENEMY)
    proj = ProjectState(id="proj_wolf", kind=ProjectKind.COMBAT, objectives=[obj], active_objective_id="obj_wolf")
    
    a.strategic.beliefs["combat_risk"] = {"level": RiskLevel.HIGH}
    a.strategic.projects["proj_wolf"] = proj
    object.__setattr__(a.strategic, "current_project_id", "proj_wolf")
    object.__setattr__(a.strategic, "current_objective_id", "obj_wolf")
    
    # Low trust in B
    a.social.trust_history[2] = 0.1
    
    state = AuthoritativeState(entities={1: a, 2: b}, tick=1, seed=123)
    
    update = StateUpdate()
    refined = CooperationPhase.execute(state, update)
    
    assert 1 in refined.entity_updates
    a_up = refined.entity_updates[1]
    decision_posture = a_up.property_updates["last_cooperation_decision"]

    assert decision_posture == CooperationPosture.DEFER_NO_PARTNER.value
    assert "cooperation_blocker" in a_up.property_updates
