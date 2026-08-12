from src.core.strategic import GoalKind
from src.ai.goals.base import GoalRegistry
from src.ai.goals.adventure_scorer import AdventureGoalScorer
from src.ai.goals.social_contract_scorer import SocialContractGoalScorer
from src.ai.goals.region_stabilization_scorer import RegionStabilizationGoalScorer
from src.ai.goals.scorers import (
    HarvestScorer, SleepScorer, EatScorer, SocialScorer, TownScorer,
    CombatEngageScorer, CombatRetreatScorer, RecoverScorer, ResolveBlockerScorer,
    GuildNeedScorer
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
GoalRegistry.register(GoalKind.GUILD, GuildNeedScorer())
GoalRegistry.register(GoalKind.ADVENTURE_ROUTE, AdventureGoalScorer())
GoalRegistry.register(GoalKind.SOCIAL_CONTRACT, SocialContractGoalScorer())
GoalRegistry.register(GoalKind.REGION_STABILIZATION, RegionStabilizationGoalScorer())

