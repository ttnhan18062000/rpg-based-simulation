"""
tests/unit/domains/cooperation/test_phase7_party_objective_alignment.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 unit tests for PartyObjectiveAlignmentService.
"""

import pytest
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.domains.cooperation.services import PartyObjectiveAlignmentService


def test_member_aligns_with_trusted_leader_objective():
    lead = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).build())
    member = (V2EntityBuilder(2).kind("HERO").location(1.0, 1.0).build())
    
    # Trusted leader
    member.social.trust_history[1] = 0.8
    
    # Active objective on leader
    object.__setattr__(lead.strategic, "current_objective_id", "obj_hunt_wolf")
    
    state = AuthoritativeState(entities={1: lead, 2: member}, tick=1, seed=123)
    
    report = PartyObjectiveAlignmentService.evaluate(lead, (member,), state)
    
    assert 2 in report.aligned_member_ids
    assert len(report.drifting_member_ids) == 0


def test_member_survival_need_overrides_leader_objective():
    lead = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).build())
    # Low HP member
    member = (V2EntityBuilder(2).kind("HERO").location(1.0, 1.0).combat(hp=20, max_hp=100).build())
    
    member.social.trust_history[1] = 0.8
    object.__setattr__(lead.strategic, "current_objective_id", "obj_hunt_wolf")
    
    state = AuthoritativeState(entities={1: lead, 2: member}, tick=1, seed=123)
    
    report = PartyObjectiveAlignmentService.evaluate(lead, (member,), state)
    
    assert 2 in report.blocked_member_ids
    assert 2 not in report.aligned_member_ids
    assert "survival override" in report.reasons[2].lower()
