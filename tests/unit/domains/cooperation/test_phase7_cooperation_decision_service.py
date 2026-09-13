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
from src.core.strategic import ContractState, ContractKind, ContractStatus


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


def test_cooperation_offer_creation_blocked_while_pending_offer_unexpired():
    # TCK-20260830-COOPERATION-OFFER-CONCURRENT-DUPLICATE-BURST: entity already has a pending
    # (OFFERED, unexpired) RECRUITMENT contract out — creating a second simultaneous offer must
    # be gated, same as the on-cooldown branch, falling through to SOLO/DEFER_NO_PARTNER.
    pending = ContractState(
        id="cnt_recruit_1_9_0",
        kind=ContractKind.RECRUITMENT,
        source_id=1,
        target_id=9,
        status=ContractStatus.OFFERED,
        created_tick=0,
        expiry_tick=10,  # tick 1 has not reached expiry (10) yet
    )
    req = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0)
           .strategic(contracts={pending.id: pending}).build())
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


def test_cooperation_offer_creation_allowed_once_pending_offer_expired():
    # Same pending contract as above, but its expiry_tick (10) is now in the past relative to
    # state.tick (11) — the gate must not block a genuinely expired-but-not-yet-reaped offer.
    pending = ContractState(
        id="cnt_recruit_1_9_0",
        kind=ContractKind.RECRUITMENT,
        source_id=1,
        target_id=9,
        status=ContractStatus.OFFERED,
        created_tick=0,
        expiry_tick=10,
    )
    req = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0)
           .strategic(contracts={pending.id: pending}).build())
    cand = (V2EntityBuilder(2).kind("HERO").location(0.0, 0.0).build())
    state = AuthoritativeState(entities={1: req, 2: cand}, tick=11, seed=123)

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


# ---------------------------------------------------------------------------
# TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION: JOIN_PARTY accept-side wiring.
# Contracts are only ever stored on the OFFERING entity's own strategic.contracts (never
# mirrored to the target), so the receiving entity must scan state.entities for offers
# addressed to it.
# ---------------------------------------------------------------------------

def _recruitment_offer(source_id: int, target_id: int, tick: int, expiry_tick: int = 0) -> ContractState:
    return ContractState(
        id=f"cnt_recruit_{source_id}_{target_id}_{tick}",
        kind=ContractKind.RECRUITMENT,
        source_id=source_id,
        target_id=target_id,
        terms={"daily_pay": 0, "duration": 100},
        status=ContractStatus.OFFERED,
        created_tick=tick,
        expiry_tick=expiry_tick,
    )


def test_find_pending_incoming_offer_finds_real_offer_targeting_entity():
    offerer = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).build())
    target = (V2EntityBuilder(2).kind("HERO").location(1.0, 1.0).build())
    contract = _recruitment_offer(source_id=1, target_id=2, tick=5, expiry_tick=15)
    from dataclasses import replace
    offerer = replace(offerer, strategic=replace(offerer.strategic, contracts={contract.id: contract}))
    state = AuthoritativeState(entities={1: offerer, 2: target}, tick=10, seed=123)

    result = CooperationDecisionService.find_pending_incoming_offer(target, state)
    assert result == (1, contract.id)


def test_find_pending_incoming_offer_none_when_target_already_grouped():
    from dataclasses import replace
    offerer = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).build())
    target = (V2EntityBuilder(2).kind("HERO").location(1.0, 1.0).identity(group_id=99).build())
    contract = _recruitment_offer(source_id=1, target_id=2, tick=5, expiry_tick=15)
    offerer = replace(offerer, strategic=replace(offerer.strategic, contracts={contract.id: contract}))
    state = AuthoritativeState(entities={1: offerer, 2: target}, tick=10, seed=123)

    assert CooperationDecisionService.find_pending_incoming_offer(target, state) is None


def test_find_pending_incoming_offer_none_when_offer_expired():
    from dataclasses import replace
    offerer = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).build())
    target = (V2EntityBuilder(2).kind("HERO").location(1.0, 1.0).build())
    contract = _recruitment_offer(source_id=1, target_id=2, tick=5, expiry_tick=8)
    offerer = replace(offerer, strategic=replace(offerer.strategic, contracts={contract.id: contract}))
    state = AuthoritativeState(entities={1: offerer, 2: target}, tick=10, seed=123)

    assert CooperationDecisionService.find_pending_incoming_offer(target, state) is None


def test_find_pending_incoming_offer_none_when_offerer_dead():
    from dataclasses import replace
    offerer = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).combat(hp=0, max_hp=100, alive=False).build())
    target = (V2EntityBuilder(2).kind("HERO").location(1.0, 1.0).build())
    contract = _recruitment_offer(source_id=1, target_id=2, tick=5, expiry_tick=15)
    offerer = replace(offerer, strategic=replace(offerer.strategic, contracts={contract.id: contract}))
    state = AuthoritativeState(entities={1: offerer, 2: target}, tick=10, seed=123)

    assert CooperationDecisionService.find_pending_incoming_offer(target, state) is None


def test_select_returns_join_party_when_pending_offer_exists_even_with_no_help_needs():
    """A pending incoming offer takes priority over the entity's own help-needs evaluation --
    an entity with zero help needs of its own must still be able to accept."""
    from dataclasses import replace
    offerer = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).build())
    target = (V2EntityBuilder(2).kind("HERO").location(1.0, 1.0).build())
    contract = _recruitment_offer(source_id=1, target_id=2, tick=5, expiry_tick=15)
    offerer = replace(offerer, strategic=replace(offerer.strategic, contracts={contract.id: contract}))
    state = AuthoritativeState(entities={1: offerer, 2: target}, tick=10, seed=123)

    decision = CooperationDecisionService.select(target, (), (), (), state)
    assert decision.selected_posture == CooperationPosture.JOIN_PARTY
    assert decision.selected_partner_id == 1
    assert decision.trace["accepted_contract_id"] == contract.id
