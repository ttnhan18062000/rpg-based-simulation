"""
tests/unit/domains/cooperation/test_phase7_cooperation_decision_service.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 unit tests for CooperationDecisionService.
"""

import pytest
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.domains.cooperation.evaluators import HelpNeed, PartnerFitReport
from src.domains.cooperation.providers import PartnerCandidate
from src.domains.cooperation.services import CooperationDecisionService
from src.domains.cooperation.postures import CooperationPosture


def test_easy_objective_selects_solo():
    # If no help needs are detected, decision is SOLO
    req = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).build())
    state = AuthoritativeState(entities={1: req}, tick=1, seed=123)
    
    decision = CooperationDecisionService.select(req, (), (), (), state)
    assert decision.selected_posture == CooperationPosture.SOLO


def test_risky_objective_selects_request_help_when_good_partner_exists():
    req = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).build())
    cand = (V2EntityBuilder(2).kind("HERO").location(0.0, 0.0).build())
    state = AuthoritativeState(entities={1: req, 2: cand}, tick=1, seed=123)
    
    need = HelpNeed("combat_support_needed", 0.8, "Risky target")
    candidate_record = PartnerCandidate(
        entity_id=2,
        relationship_score=0.5,
        trust_score=0.8,
        role_fit_score=0.8,
        availability_score=0.9,
        cost_gold=0
    )
    fit_rep = PartnerFitReport(
        candidate_id=2,
        fit_score=0.8,
        trust_score=0.8,
        capability_match=0.8,
        objective_alignment=0.5,
        risk=0.1,
        reasons=()
    )
    
    decision = CooperationDecisionService.select(req, (need,), (candidate_record,), (fit_rep,), state)
    assert decision.selected_posture == CooperationPosture.REQUEST_HELP
    assert decision.selected_partner_id == 2


def test_cooperation_offer_retry_blocked_within_cooldown_window():
    # Cooldown ready_tick (6) is still in the future relative to state.tick (1):
    # the good-partner branch must be gated off, falling through to the
    # existing SOLO/DEFER_NO_PARTNER fallback logic.
    req = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0)
           .identity(cooldowns={"cooperation_offer_retry": 6}).build())
    cand = (V2EntityBuilder(2).kind("HERO").location(0.0, 0.0).build())
    state = AuthoritativeState(entities={1: req, 2: cand}, tick=1, seed=123)

    need = HelpNeed("combat_support_needed", 0.8, "Risky target")
    candidate_record = PartnerCandidate(
        entity_id=2,
        relationship_score=0.5,
        trust_score=0.8,
        role_fit_score=0.8,
        availability_score=0.9,
        cost_gold=0
    )
    fit_rep = PartnerFitReport(
        candidate_id=2,
        fit_score=0.8,
        trust_score=0.8,
        capability_match=0.8,
        objective_alignment=0.5,
        risk=0.1,
        reasons=()
    )

    decision = CooperationDecisionService.select(req, (need,), (candidate_record,), (fit_rep,), state)
    assert decision.selected_posture in (CooperationPosture.SOLO, CooperationPosture.DEFER_NO_PARTNER)


def test_cooperation_offer_retry_allowed_after_cooldown_expires():
    # Cooldown ready_tick (1) is not in the future relative to state.tick (1):
    # the good-partner branch must proceed exactly as it does with no cooldown set.
    req = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0)
           .identity(cooldowns={"cooperation_offer_retry": 1}).build())
    cand = (V2EntityBuilder(2).kind("HERO").location(0.0, 0.0).build())
    state = AuthoritativeState(entities={1: req, 2: cand}, tick=1, seed=123)

    need = HelpNeed("combat_support_needed", 0.8, "Risky target")
    candidate_record = PartnerCandidate(
        entity_id=2,
        relationship_score=0.5,
        trust_score=0.8,
        role_fit_score=0.8,
        availability_score=0.9,
        cost_gold=0
    )
    fit_rep = PartnerFitReport(
        candidate_id=2,
        fit_score=0.8,
        trust_score=0.8,
        capability_match=0.8,
        objective_alignment=0.5,
        risk=0.1,
        reasons=()
    )

    decision = CooperationDecisionService.select(req, (need,), (candidate_record,), (fit_rep,), state)
    assert decision.selected_posture == CooperationPosture.REQUEST_HELP
    assert decision.selected_partner_id == 2


def test_risky_objective_selects_defer_when_no_partner_exists():
    # If objective is too risky but no partners are available/trusted, defer
    req = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).build())
    # Candidate exists but fit report shows low trust
    cand = (V2EntityBuilder(2).kind("HERO").location(0.0, 0.0).build())
    state = AuthoritativeState(entities={1: req, 2: cand}, tick=1, seed=123)
    
    need = HelpNeed("combat_support_needed", 0.9, "Extreme risk target")
    candidate_record = PartnerCandidate(
        entity_id=2,
        relationship_score=0.1,
        trust_score=0.1,
        role_fit_score=0.8,
        availability_score=0.9,
        cost_gold=0
    )
    fit_rep = PartnerFitReport(
        candidate_id=2,
        fit_score=0.2, # Poor fit score
        trust_score=0.1, # Untrusted
        capability_match=0.8,
        objective_alignment=0.5,
        risk=0.8,
        reasons=()
    )
    
    decision = CooperationDecisionService.select(req, (need,), (candidate_record,), (fit_rep,), state)
    assert decision.selected_posture == CooperationPosture.DEFER_NO_PARTNER
