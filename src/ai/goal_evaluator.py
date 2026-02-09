"""Backward-compatibility shim — re-exports from ``src.ai.goals``.

The monolithic goal evaluator has been refactored into a plugin-based
system under ``src/ai/goals/``.  This module re-exports the key symbols
so any existing imports continue to work.

Prefer importing from ``src.ai.goals`` directly in new code.
"""

from src.ai.goals.base import GoalScore, GoalEvaluator, GOAL_REGISTRY  # noqa: F401

__all__ = ["GoalScore", "GoalEvaluator", "GOAL_REGISTRY"]
