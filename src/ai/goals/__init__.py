from src.core.strategic import GoalKind
from src.ai.goals.base import GoalRegistry
from src.ai.goals.scorers import (
    HarvestScorer, SleepScorer, EatScorer, SocialScorer, TownScorer,
    CombatEngageScorer, CombatRetreatScorer, RecoverScorer, ResolveBlockerScorer
)

# Register built-in scorers
GoalRegistry.register(GoalKind.HARVESTING, HarvestScorer())
GoalRegistry.register(GoalKind.FATIGUE, SleepScorer())
GoalRegistry.register(GoalKind.HUNGER, EatScorer())
GoalRegistry.register(GoalKind.SOCIAL, SocialScorer())
GoalRegistry.register(GoalKind.TOWN_RETURN, TownScorer())
GoalRegistry.register(GoalKind.COMBAT_ENGAGE, CombatEngageScorer())
GoalRegistry.register(GoalKind.COMBAT_RETREAT, CombatRetreatScorer())
GoalRegistry.register(GoalKind.RECOVER, RecoverScorer())
GoalRegistry.register(GoalKind.RESOLVE_BLOCKER, ResolveBlockerScorer())

