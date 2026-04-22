"""
Contract tests for Narrative Memory.

Covers:
- LEG-RPG-151: Narrative memory logging
- Part 1 §Social: Turning points feed future behavior
"""
import pytest
from src_v2.systems.social import TurningPoint
from src_v2.systems.narrative import NarrativeMemory, NarrativeMemorySystem


class TestTurningPointPersistence:
    """LEG-RPG-151: Turning points persist in narrative memory."""

    def test_record_turning_point(self):
        memory = NarrativeMemory()
        tp = TurningPoint(id="tp_1", kind="betrayal", subject_id=42, salience=0.8, tick=50)
        new_memory = NarrativeMemorySystem.record_turning_point(memory, tp)
        assert len(new_memory.turning_points) == 1
        assert new_memory.turning_points[0].kind == "betrayal"

    def test_betrayal_increases_trauma(self):
        memory = NarrativeMemory(trauma_score=0.0)
        tp = TurningPoint(id="tp_1", kind="betrayal", subject_id=42, salience=0.8, tick=50)
        new_memory = NarrativeMemorySystem.record_turning_point(memory, tp)
        assert new_memory.trauma_score > 0

    def test_victory_increases_confidence(self):
        memory = NarrativeMemory(confidence=0.5)
        tp = TurningPoint(id="tp_2", kind="great_victory", salience=0.9, tick=60)
        new_memory = NarrativeMemorySystem.record_turning_point(memory, tp)
        assert new_memory.confidence > 0.5

    def test_multiple_events_accumulate(self):
        memory = NarrativeMemory()
        tp1 = TurningPoint(id="tp_1", kind="near_death", salience=0.7, tick=50)
        tp2 = TurningPoint(id="tp_2", kind="near_death", salience=0.6, tick=70)
        m1 = NarrativeMemorySystem.record_turning_point(memory, tp1)
        m2 = NarrativeMemorySystem.record_turning_point(m1, tp2)
        assert len(m2.turning_points) == 2
        assert m2.trauma_score > m1.trauma_score


class TestUtilityBiasing:
    """LEG-RPG-151: Narrative memory biases future utility scoring."""

    def test_trauma_increases_flee_bias(self):
        memory = NarrativeMemory(trauma_score=0.8)
        bias = NarrativeMemorySystem.compute_utility_bias(memory, "FLEE")
        assert bias > 1.0

    def test_trauma_decreases_explore_bias(self):
        memory = NarrativeMemory(trauma_score=0.8)
        bias = NarrativeMemorySystem.compute_utility_bias(memory, "EXPLORE")
        assert bias < 1.0

    def test_confidence_increases_attack_bias(self):
        memory = NarrativeMemory(confidence=0.9)
        bias = NarrativeMemorySystem.compute_utility_bias(memory, "ATTACK")
        assert bias > 1.0

    def test_neutral_memory_no_bias(self):
        memory = NarrativeMemory(trauma_score=0.0, confidence=0.0)
        bias = NarrativeMemorySystem.compute_utility_bias(memory, "EXPLORE")
        assert bias == pytest.approx(1.0)

    def test_bias_never_below_minimum(self):
        """Bias never goes below 0.1 to prevent division by zero."""
        memory = NarrativeMemory(trauma_score=1.0)
        bias = NarrativeMemorySystem.compute_utility_bias(memory, "EXPLORE")
        assert bias >= 0.1


class TestTraumaTracking:
    """Track trauma with specific subjects."""

    def test_has_trauma_with_betrayer(self):
        memory = NarrativeMemory(turning_points=[
            TurningPoint(id="tp_1", kind="betrayal", subject_id=42, salience=0.8, tick=50)
        ])
        assert NarrativeMemorySystem.has_trauma_with(memory, 42) is True
        assert NarrativeMemorySystem.has_trauma_with(memory, 99) is False
