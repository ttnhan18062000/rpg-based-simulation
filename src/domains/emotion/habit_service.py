"""
src/domains/emotion/habit_service.py
───────────────────────────────────────────────────────────────────────────────
HabitBiasService for Phase 16.
"""

from __future__ import annotations
from dataclasses import replace
from src.core.cognition import HabitMemory

class HabitBiasService:
    """Forms habit bias scoring modifiers based on action outcomes."""

    @staticmethod
    def record_outcome(memory: HabitMemory, pattern_id: str, success: bool) -> HabitMemory:
        patterns = dict(memory.patterns)
        
        current_bias = patterns.get(pattern_id, 0.5)
        if success:
            patterns[pattern_id] = min(1.0, current_bias + 0.1)
        else:
            patterns[pattern_id] = max(0.0, current_bias - 0.1)
            
        return replace(memory, patterns=patterns)

    @staticmethod
    def apply_habit_bias(memory: HabitMemory, tags: list[str], base_score: float) -> float:
        score = base_score
        for tag in tags:
            if tag in memory.patterns:
                # scale score based on habit bias (positive or negative deviation from neutral 0.5)
                score += (memory.patterns[tag] - 0.5) * 0.4
        return score
