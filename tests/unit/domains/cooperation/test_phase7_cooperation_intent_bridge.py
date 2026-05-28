"""
tests/unit/domains/cooperation/test_phase7_cooperation_intent_bridge.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 unit tests for CooperationIntentBridge mapping chosen postures to Contract/Strategic Updates.
"""

import pytest
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.domains.cooperation.postures import CooperationPosture
from src.domains.cooperation.services import CooperationDecisionResult, CooperationIntentBridge


def test_defer_no_partner_creates_blocker():
    req = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).build())
    state = AuthoritativeState(entities={1: req}, tick=1, seed=123)
    
    decision = CooperationDecisionResult(
        entity_id=1,
        selected_posture=CooperationPosture.DEFER_NO_PARTNER,
        selected_partner_id=None,
        fit_score=0.0,
        rejected_partners={},
        trace={"need_severity": 0.8}
    )
    
    intent_upd = CooperationIntentBridge.map_decision(req, decision, state)
    
    assert intent_upd.strategic is not None
    assert len(intent_upd.strategic.blockers_add_or_update) == 1
    blocker = intent_upd.strategic.blockers_add_or_update[0]
    assert blocker.subject == "suitable_partner"
    assert blocker.severity == 0.8


def test_request_help_maps_to_recruitment_contract_offer():
    req = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).build())
    state = AuthoritativeState(entities={1: req}, tick=1, seed=123)
    
    decision = CooperationDecisionResult(
        entity_id=1,
        selected_posture=CooperationPosture.REQUEST_HELP,
        selected_partner_id=2,
        fit_score=0.8,
        rejected_partners={},
        trace={}
    )
    
    intent_upd = CooperationIntentBridge.map_decision(req, decision, state)
    
    assert intent_upd.strategic is not None
    assert len(intent_upd.strategic.contracts_add_or_update) == 1
    contract = intent_upd.strategic.contracts_add_or_update[0]
    assert contract.source_id == 1
    assert contract.target_id == 2
    assert contract.status.value == "OFFERED"
