"""AI Goal scoring plugin system.

Each goal is a GoalScorer subclass registered in GOAL_REGISTRY.
The GoalEvaluator iterates all registered scorers to produce ranked goals.
"""

from src.ai.goals.base import GoalScorer, GoalScore, GoalEvaluator, GOAL_REGISTRY
from src.ai.goals.registry import register_all_goals

# Auto-register all built-in goals on import
register_all_goals()

__all__ = [
    "GoalScorer",
    "GoalScore",
    "GoalEvaluator",
    "GOAL_REGISTRY",
]
