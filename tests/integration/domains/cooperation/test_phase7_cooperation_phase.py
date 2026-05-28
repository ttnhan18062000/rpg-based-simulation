"""
tests/integration/domains/cooperation/test_phase7_cooperation_phase.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 Integration Tests for orchestrating CooperationPhase.
"""

import pytest
from src.core.state import AuthoritativeState, GroupRecord
from src.core.builder import V2EntityBuilder
from src.core.updates import StateUpdate
from src.domains.cooperation.phase import CooperationPhase


def test_phase_skips_entity_without_help_need():
    # If no objective / no help needs exists and not in group, no evaluations are done
    req = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).lifecycle(active=True).build())
    state = AuthoritativeState(entities={1: req}, tick=1, seed=123)
    
    update = StateUpdate()
    refined = CooperationPhase.execute(state, update)
    
    # cooperation_evaluations metric remains 0
    assert refined.metric_counters.get("cooperation_evaluations", 0) == 0


def test_phase_runs_when_help_need_exists():
    req = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).combat(hp=20, max_hp=100).lifecycle(active=True).build())
    # low HP creates healer/protection need
    object.__setattr__(req.strategic, "current_objective_id", "obj_1")
    
    state = AuthoritativeState(entities={1: req}, tick=1, seed=123)
    
    update = StateUpdate()
    refined = CooperationPhase.execute(state, update)
    
    assert refined.metric_counters.get("cooperation_evaluations", 0) == 1
    assert 1 in refined.entity_updates
    ent_up = refined.entity_updates[1]
    assert "last_cooperation_decision" in ent_up.property_updates


def test_phase_respects_feature_flag():
    req = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).combat(hp=20, max_hp=100).lifecycle(active=True).build())
    object.__setattr__(req.strategic, "current_objective_id", "obj_1")
    
    state = AuthoritativeState(entities={1: req}, tick=1, seed=123)
    state.periodic_due_ticks["social_cooperation_disabled"] = 1
    
    update = StateUpdate()
    refined = CooperationPhase.execute(state, update)
    
    assert 1 not in refined.entity_updates
    assert refined.metric_counters == {}
