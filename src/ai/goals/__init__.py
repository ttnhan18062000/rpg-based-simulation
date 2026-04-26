from src.ai.goals.base import GoalRegistry
from src.ai.goals.scorers import HarvestScorer, SleepScorer, EatScorer, SocialScorer

# Register built-in scorers
GoalRegistry.register(HarvestScorer())
GoalRegistry.register(SleepScorer())
GoalRegistry.register(EatScorer())
GoalRegistry.register(SocialScorer())
