"""
tests/unit/domains/cooperation/test_phase7_partner_candidate_provider.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 unit tests for PartnerCandidateProvider.
"""

import pytest
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.domains.cooperation.providers import PartnerCandidateProvider, CandidateBudget
from src.domains.cooperation.evaluators import HelpNeed


def test_provider_excludes_dead_entities():
    # Requester
    req = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).lifecycle(active=True).build())
    # Dead candidate
    dead_cand = (V2EntityBuilder(2).kind("HERO").location(1.0, 1.0).combat(hp=0, alive=False).lifecycle(active=True).build())
    
    state = AuthoritativeState(entities={1: req, 2: dead_cand}, tick=1, seed=123)
    help_need = HelpNeed("combat_support_needed", 0.8, "Test need")
    
    budget = CandidateBudget(max_candidates=5, spatial_radius=10.0)
    candidates = PartnerCandidateProvider.get_candidates(req, state, (help_need,), budget)
    
    assert len(candidates) == 0


def test_provider_prefers_trusted_nearby_candidate():
    req = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).lifecycle(active=True).build())
    
    # Highly trusted candidate (A) at distance 5
    cand_a = (V2EntityBuilder(2).kind("HERO").location(3.0, 4.0).lifecycle(active=True).build())
    # Low trust candidate (B) at distance 2
    cand_b = (V2EntityBuilder(3).kind("HERO").location(1.0, 1.0).lifecycle(active=True).build())
    
    # Set relationship values
    req.social.trust_history[2] = 0.9 # Trusted
    req.social.trust_history[3] = 0.2 # Untrusted
    
    state = AuthoritativeState(entities={1: req, 2: cand_a, 3: cand_b}, tick=1, seed=123)
    help_need = HelpNeed("combat_support_needed", 0.8, "Test need")
    
    budget = CandidateBudget(max_candidates=5, spatial_radius=10.0)
    candidates = PartnerCandidateProvider.get_candidates(req, state, (help_need,), budget)
    
    assert len(candidates) == 2
    assert candidates[0].entity_id == 2 # Candidate A preferred due to high trust scoring
