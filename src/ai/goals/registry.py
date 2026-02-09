"""Goal scorer registration.

Call ``register_all_goals()`` once at import time to populate GOAL_REGISTRY.
To add a custom goal, either append to this function or call
``register_goal()`` directly from your own module.
"""

from __future__ import annotations

from src.ai.goals.base import register_goal
from src.ai.goals.scorers import (
    CombatGoal,
    FleeGoal,
    ExploreGoal,
    LootGoal,
    TradeGoal,
    RestGoal,
    CraftGoal,
    SocialGoal,
    GuardGoal,
)

_registered = False


def register_all_goals() -> None:
    """Register all built-in goal scorers (idempotent)."""
    global _registered
    if _registered:
        return
    _registered = True

    register_goal(CombatGoal())
    register_goal(FleeGoal())
    register_goal(ExploreGoal())
    register_goal(LootGoal())
    register_goal(TradeGoal())
    register_goal(RestGoal())
    register_goal(CraftGoal())
    register_goal(SocialGoal())
    register_goal(GuardGoal())
