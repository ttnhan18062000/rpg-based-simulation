"""
tests/unit/domains/combat_engagement/test_phase4_combat_learning.py

Phase 4 — CombatLearning unit tests.
Verifies estimate updates, skill learning, and outcome logs.
"""

import pytest
from src.domains.combat_engagement.learning import CombatLearning
from src.domains.combat_engagement.schema import OpponentModel


def test_losing_to_target_increases_future_estimate():
    mem_initial = None
    
    # Lost combat
    mem_updated = CombatLearning.learn(
        memory=mem_initial,
        subject_key="enemy_type.wolf",
        outcome="LOST",
        observed_damage=50.0,
        observed_skills=("heavy_strike",),
        tick=5,
    )
    
    assert mem_updated.estimated_power > 20.0
    assert "heavy_strike" in mem_updated.known_skill_ids
    assert mem_updated.uncertainty < 0.4
    assert mem_updated.confidence > 0.5


def test_easy_win_reduces_future_risk():
    mem_initial = OpponentModel(
        subject_key="enemy_type.rat",
        estimated_power=30.0,
        uncertainty=0.3,
        confidence=0.6,
    )
    
    mem_updated = CombatLearning.learn(
        memory=mem_initial,
        subject_key="enemy_type.rat",
        outcome="WON_EASY",
        observed_damage=5.0,
        observed_skills=(),
        tick=10,
    )
    
    # Power estimate decreases (weaker than expected)
    assert mem_updated.estimated_power < 30.0
    assert mem_updated.confidence > 0.6
