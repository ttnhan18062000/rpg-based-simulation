"""
tests/unit/domains/cooperation/test_phase7_cooperation_learning.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 unit tests for CooperationOutcomeLearning.
"""

import pytest
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.domains.cooperation.services import CooperationLearningService, CooperationOutcomeEvent


def test_successful_party_increases_partner_trust_slightly():
    req = (V2EntityBuilder(1).kind("HERO").build())
    state = AuthoritativeState(entities={1: req}, tick=1, seed=123)
    
    event = CooperationOutcomeEvent(
        tick=1,
        partner_id=2,
        outcome_type="success",
        description="Completed hunt successfully"
    )
    
    result = CooperationLearningService.learn(req, event, state)
    
    assert result.trust_delta == 0.08
    assert result.future_preference_modifier > 1.0


def test_abandonment_decreases_trust():
    req = (V2EntityBuilder(1).kind("HERO").build())
    state = AuthoritativeState(entities={1: req}, tick=1, seed=123)
    
    event = CooperationOutcomeEvent(
        tick=1,
        partner_id=2,
        outcome_type="abandoned",
        description="Fled combat mid-fight"
    )
    
    result = CooperationLearningService.learn(req, event, state)
    
    assert result.trust_delta == -0.25
    assert result.grudge_delta == 0.3
    assert result.future_preference_modifier < 0.5
