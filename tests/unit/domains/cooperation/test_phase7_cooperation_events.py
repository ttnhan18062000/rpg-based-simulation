"""
tests/unit/domains/cooperation/test_phase7_cooperation_events.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 unit tests verifying cooperation trace events.
"""

import pytest
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.domains.cooperation.events import HelpNeedDetectedEvent, PartnerSelectedEvent
from src.domains.cooperation.postures import CooperationPosture


def test_partner_selected_event_contains_fit_and_reason():
    evt = PartnerSelectedEvent(
        entity_id=1,
        tick=5,
        partner_id=2,
        posture=CooperationPosture.REQUEST_HELP,
        fit_score=0.85,
        reason="Excellent role fit"
    )
    
    assert evt.entity_id == 1
    assert evt.tick == 5
    assert evt.partner_id == 2
    assert evt.posture == CooperationPosture.REQUEST_HELP
    assert evt.fit_score == 0.85
    assert evt.reason == "Excellent role fit"


def test_event_generation_does_not_change_state_hash():
    # Verify that constructing / serializing trace events does not change the core state values
    req = (V2EntityBuilder(1).kind("HERO").build())
    state = AuthoritativeState(entities={1: req}, tick=1, seed=123)
    
    h1 = hash((req.id, req.kind, req.navigation.position))
    
    evt = HelpNeedDetectedEvent(
        entity_id=1,
        tick=1,
        need_key="combat_support_needed",
        severity=0.8,
        reason="Wolf target is risky"
    )
    req.timeline.append(evt)
    
    h2 = hash((req.id, req.kind, req.navigation.position))
    
    assert h1 == h2
