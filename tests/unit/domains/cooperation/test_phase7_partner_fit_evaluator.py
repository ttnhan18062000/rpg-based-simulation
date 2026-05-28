"""
tests/unit/domains/cooperation/test_phase7_partner_fit_evaluator.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 unit tests for PartnerFitEvaluator.
"""

import pytest
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.domains.cooperation.evaluators import PartnerFitEvaluator, HelpNeed


def test_high_trust_increases_partner_fit():
    req = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).lifecycle(active=True).build())
    cand = (V2EntityBuilder(2).kind("HERO").location(0.0, 0.0).lifecycle(active=True).build())
    
    # Establish high trust
    req.social.trust_history[2] = 0.95
    
    state = AuthoritativeState(entities={1: req, 2: cand}, tick=1, seed=123)
    need = HelpNeed("combat_support_needed", 0.8, "Need combat support")
    
    report = PartnerFitEvaluator.evaluate(req, cand, (need,), state)
    
    assert report.trust_score == 0.95
    assert report.fit_score >= 0.7


def test_private_betrayal_decreases_partner_fit():
    req = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).lifecycle(active=True).build())
    cand = (V2EntityBuilder(2).kind("HERO").location(0.0, 0.0).lifecycle(active=True).build())
    
    # Establish base trust but add a severe grudge (abandonment/betrayal history)
    req.social.trust_history[2] = 0.5
    req.social.grudge_history[2] = 0.4
    
    state = AuthoritativeState(entities={1: req, 2: cand}, tick=1, seed=123)
    need = HelpNeed("combat_support_needed", 0.8, "Need combat support")
    
    report = PartnerFitEvaluator.evaluate(req, cand, (need,), state)
    
    # Grudge penalizes effective trust score down to 0.1
    assert report.trust_score == pytest.approx(0.1)
    assert report.fit_score < 0.4
