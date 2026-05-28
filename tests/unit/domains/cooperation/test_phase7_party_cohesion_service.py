"""
tests/unit/domains/cooperation/test_phase7_party_cohesion_service.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 unit tests for PartyCohesionService.
"""

import pytest
from src.core.state import AuthoritativeState, GroupRecord
from src.core.builder import V2EntityBuilder
from src.domains.cooperation.services import PartyCohesionService


def test_dead_leader_creates_leader_lost_issue():
    # Setup leader at hp=0
    lead = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).combat(hp=0, alive=False).lifecycle(active=True).build())
    mb = (V2EntityBuilder(2).kind("HERO").location(1.0, 1.0).lifecycle(active=True).build())
    
    group = GroupRecord(
        id=101,
        leader_id=1,
        member_ids={1, 2},
        anchor=(0.0, 0.0)
    )
    
    state = AuthoritativeState(entities={1: lead, 2: mb}, groups={101: group}, tick=1, seed=123)
    
    report = PartyCohesionService.evaluate(101, state)
    
    assert report.status == "LEADER_LOST"
    assert 1 in report.issue_member_ids


def test_far_member_creates_regroup_issue():
    lead = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).lifecycle(active=True).build())
    # Member far away at distance 20
    mb = (V2EntityBuilder(2).kind("HERO").location(20.0, 0.0).lifecycle(active=True).build())
    
    group = GroupRecord(
        id=101,
        leader_id=1,
        member_ids={1, 2},
        anchor=(0.0, 0.0)
    )
    
    state = AuthoritativeState(entities={1: lead, 2: mb}, groups={101: group}, tick=1, seed=123)
    
    report = PartyCohesionService.evaluate(101, state)
    
    assert report.status == "NEEDS_REGROUP"
    assert 2 in report.issue_member_ids
    assert "far from leader" in report.issue_reasons[0].lower()
