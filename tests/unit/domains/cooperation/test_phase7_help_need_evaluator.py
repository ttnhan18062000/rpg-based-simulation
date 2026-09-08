"""
tests/unit/domains/cooperation/test_phase7_help_need_evaluator.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 unit tests for HelpNeedEvaluator.
"""

import pytest
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.core.strategic import RiskLevel, ProjectState, ProjectKind, ObjectiveState, ObjectiveKind
from src.domains.cooperation.evaluators import HelpNeedEvaluator, HelpNeed
from src.domains.combat_engagement.phase import build_combat_risk_belief


def test_risky_combat_creates_combat_support_need():
    # Setup entity with combat risk belief set to HIGH
    b = (V2EntityBuilder(1)
         .kind("HERO")
         .location(0.0, 0.0)
         .combat(hp=100, max_hp=100)
         .lifecycle(active=True))
    entity = b.build()
    
    # Active objective and project
    obj = ObjectiveState(id="obj_1", kind=ObjectiveKind.DEFEAT_ENEMY)
    proj = ProjectState(id="proj_1", kind=ProjectKind.COMBAT, objectives=[obj], active_objective_id="obj_1")
    
    # TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN: combat_risk is now a real BeliefEntry
    # written by CombatEngagementPhase, not a bespoke {"level": ...} dict. Built via the real
    # producer helper so this test breaks if the producer's own contract drifts.
    # death_risk 0.6 maps to RiskLevel.HIGH.
    entity.strategic.beliefs["combat_risk"] = build_combat_risk_belief(
        death_risk=0.6, current_tick=1
    )
    entity.strategic.projects["proj_1"] = proj
    object.__setattr__(entity.strategic, "current_project_id", "proj_1")
    object.__setattr__(entity.strategic, "current_objective_id", "obj_1")
    
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=123)
    needs = HelpNeedEvaluator.evaluate(entity, state)
    
    assert len(needs) == 1
    assert needs[0].key == "combat_support_needed"
    assert needs[0].severity >= 0.6


def test_low_hp_creates_protection_or_healer_need():
    b = (V2EntityBuilder(1)
         .kind("HERO")
         .location(0.0, 0.0)
         .combat(hp=20, max_hp=100) # Low HP (20%)
         .lifecycle(active=True))
    entity = b.build()
    
    # Setup active objective so need is analyzed
    object.__setattr__(entity.strategic, "current_objective_id", "obj_1")
    
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=123)
    needs = HelpNeedEvaluator.evaluate(entity, state)
    
    healer_needs = [n for n in needs if n.key == "healer_needed"]
    assert len(healer_needs) == 1
    assert healer_needs[0].severity >= 0.8
