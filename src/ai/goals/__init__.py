from src.ai.goals.base import GoalRegistry
from src.ai.goals.scorers import HarvestScorer, SleepScorer, EatScorer, SocialScorer, TownScorer

# Register built-in scorers
GoalRegistry.register("harvesting", HarvestScorer())
GoalRegistry.register("fatigue", SleepScorer())
GoalRegistry.register("hunger", EatScorer())
GoalRegistry.register("social", SocialScorer())
GoalRegistry.register("town_return", TownScorer())
