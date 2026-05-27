"""
tests/unit/domains/combat_engagement/test_phase4_posture_selector.py

Phase 4 — CombatPostureSelector unit tests.
Verifies risk-to-posture mappings, retreats, and vengeance options.
"""

import pytest
from src.domains.combat_engagement.schema import (
    CombatPosture,
    PerceivedOpponentEstimate,
    SelfCombatEstimate,
    EngagementRiskEvaluation,
)
from src.domains.combat_engagement.selector import CombatPostureSelector


def test_weaker_enemy_selects_engage():
    opp = PerceivedOpponentEstimate(target_id=2, estimated_power=20.0, uncertainty=0.1, confidence=0.9)
    self_est = SelfCombatEstimate(actor_id=1, estimated_power=50.0, confidence=0.9)
    
    risk = EngagementRiskEvaluation(
        win_confidence=0.8, death_risk=0.1, uncertainty_penalty=0.0,
        objective_value=0.0, personality_bias=0.0, emotional_bias=0.0,
        risk_score=0.1, value_score=0.8, acceptable=True, reasons=()
    )
    
    res = CombatPostureSelector.select(1, 2, opp, self_est, risk)
    assert res.posture == CombatPosture.ENGAGE


def test_unknown_equal_enemy_selects_probe():
    opp = PerceivedOpponentEstimate(target_id=2, estimated_power=30.0, uncertainty=0.4, confidence=0.6)
    self_est = SelfCombatEstimate(actor_id=1, estimated_power=30.0, confidence=0.8)
    
    risk = EngagementRiskEvaluation(
        win_confidence=0.5, death_risk=0.4, uncertainty_penalty=0.1,
        objective_value=0.0, personality_bias=0.0, emotional_bias=0.0,
        risk_score=0.4, value_score=0.5, acceptable=True, reasons=()
    )
    
    res = CombatPostureSelector.select(1, 2, opp, self_est, risk)
    assert res.posture == CombatPosture.PROBE


def test_stronger_enemy_without_objective_selects_avoid():
    opp = PerceivedOpponentEstimate(target_id=2, estimated_power=80.0, uncertainty=0.1, confidence=0.9)
    self_est = SelfCombatEstimate(actor_id=1, estimated_power=30.0, confidence=0.8)
    
    risk = EngagementRiskEvaluation(
        win_confidence=0.2, death_risk=0.8, uncertainty_penalty=0.0,
        objective_value=0.0, personality_bias=0.0, emotional_bias=0.0,
        risk_score=0.8, value_score=0.2, acceptable=False, reasons=()
    )
    
    res = CombatPostureSelector.select(1, 2, opp, self_est, risk)
    assert res.posture == CombatPosture.AVOID


def test_low_hp_selects_retreat():
    opp = PerceivedOpponentEstimate(target_id=2, estimated_power=30.0, uncertainty=0.1, confidence=0.9)
    # Actor has near_death constraint
    self_est = SelfCombatEstimate(actor_id=1, estimated_power=10.0, confidence=0.2, constraints=("near_death",))
    
    risk = EngagementRiskEvaluation(
        win_confidence=0.1, death_risk=0.9, uncertainty_penalty=0.0,
        objective_value=0.0, personality_bias=0.0, emotional_bias=0.0,
        risk_score=0.9, value_score=0.1, acceptable=False, reasons=()
    )
    
    res = CombatPostureSelector.select(1, 2, opp, self_est, risk)
    assert res.posture == CombatPosture.RETREAT


def test_grudge_selects_vengeance_engage():
    opp = PerceivedOpponentEstimate(target_id=2, estimated_power=50.0, uncertainty=0.1, confidence=0.9)
    self_est = SelfCombatEstimate(actor_id=1, estimated_power=30.0, confidence=0.8)
    
    risk = EngagementRiskEvaluation(
        win_confidence=0.3, death_risk=0.6, uncertainty_penalty=0.0,
        objective_value=0.0, personality_bias=-0.2, emotional_bias=0.8,
        risk_score=0.6, value_score=0.9, acceptable=True, reasons=("grudge_vengeance",)
    )
    
    res = CombatPostureSelector.select(1, 2, opp, self_est, risk)
    assert res.posture == CombatPosture.VENGEANCE_ENGAGE
