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


def test_fled_produces_a_real_weak_correction():
    """
    TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER: FLED was named in this method's own type
    comment before this fix but had no real branch -- learn(outcome="FLED", ...) silently fell
    through every if/elif with zero numeric correction. A real, disclosed defect, fixed here: a
    weak but real signal (docs/mechanics/04_strategic_cognition.md Sec 13.5a), smaller than
    WON_EASY/LOST/NEAR_DEATH's own corrections.
    """
    mem_initial = OpponentModel(
        subject_key="entity.99", estimated_power=25.0, uncertainty=0.4, confidence=0.5,
    )

    mem_updated = CombatLearning.learn(
        memory=mem_initial,
        subject_key="entity.99",
        outcome="FLED",
        observed_damage=0.0,
        observed_skills=(),
        tick=3,
    )

    # A real, but small, correction -- power estimate itself is untouched, deliberately (Sec
    # 13.5a): an entity flees because its existing estimate already reads the target as
    # dangerous, so nudging the estimate UP on FLED would confirm the very belief that caused
    # the flight, letting fear escalate purely from an entity's own avoidance with no real fight
    # ever occurring. Only confidence/uncertainty move, and by less than any resolved-outcome
    # correction.
    assert mem_updated.estimated_power == 25.0
    assert mem_updated.confidence > mem_initial.confidence
    assert mem_updated.uncertainty < mem_initial.uncertainty
    assert (mem_updated.confidence - mem_initial.confidence) < 0.1
    assert (mem_initial.uncertainty - mem_updated.uncertainty) < 0.1
    assert mem_updated.outcomes[-1] == "FLED"
