"""Built-in GoalScorer implementations.

Refactored for AOA Stabilization:
- Explicit aspect access (spatial, combat, mind, progression).
- Nested mind-state access (decision, emotion, perception).
- Removed legacy property shims and getattr hacks.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from src.ai.goals.base import GoalScorer
from src.core.models.enums import AIState, GoalType, Faction
from src.core.entities.traits import aggregate_trait_stats, aggregate_trait_utility

if TYPE_CHECKING:
    from src.ai.states import AIContext

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _trait_utility(ctx: AIContext):
    return aggregate_trait_utility(ctx.actor.identity.traits)

def _is_hero(ctx: AIContext) -> bool:
    return ctx.actor.identity.faction == Faction.HERO_GUILD

# ---------------------------------------------------------------------------
# Combat — seek and fight enemies
# ---------------------------------------------------------------------------

class CombatGoal(GoalScorer):
    @property
    def name(self) -> GoalType: return GoalType.COMBAT
    @property
    def target_state(self) -> AIState: return AIState.HUNT
    def score(self, ctx: AIContext) -> float:
        actor = ctx.actor
        hp_ratio = actor.combat.hp_ratio
        base = 0.3
        enemy = ctx.nearest_enemy()
        if enemy:
            dist = actor.spatial.pos.manhattan(enemy.spatial.pos)
            base += 0.5 * max(0, 1.0 - dist / 10.0)
        return base + _trait_utility(ctx).combat

# ---------------------------------------------------------------------------
# Flee — retreat to safety
# ---------------------------------------------------------------------------

class FleeGoal(GoalScorer):
    @property
    def name(self) -> GoalType: return GoalType.FLEE
    @property
    def target_state(self) -> AIState: return AIState.FLEE
    def score(self, ctx: AIContext) -> float:
        if ctx.actor.combat.hp_ratio < 0.25: return 2.0
        return 0.0

# ---------------------------------------------------------------------------
# Explore — discover unknown territory
# ---------------------------------------------------------------------------

class ExploreGoal(GoalScorer):
    @property
    def name(self) -> GoalType: return GoalType.EXPLORE
    @property
    def target_state(self) -> AIState: return AIState.WANDER
    def score(self, ctx: AIContext) -> float:
        return 0.2 + _trait_utility(ctx).explore

# ---------------------------------------------------------------------------
# Loot — pick up items
# ---------------------------------------------------------------------------

class LootGoal(GoalScorer):
    @property
    def name(self) -> GoalType: return GoalType.LOOT
    @property
    def target_state(self) -> AIState: return AIState.LOOTING
    def score(self, ctx: AIContext) -> float:
        return 0.1 + _trait_utility(ctx).loot

# ---------------------------------------------------------------------------
# Bio-Needs — Sleep & Eat [PHASE 3]
# ---------------------------------------------------------------------------

class SleepScorer(GoalScorer):
    """Utility based on exhaustion and time of day."""
    @property
    def name(self) -> GoalType: return GoalType.SLEEP
    @property
    def target_state(self) -> AIState: return AIState.SLEEPING
    def score(self, ctx: AIContext) -> float:
        debt = ctx.actor.mind.routine.sleep_debt
        hour = (ctx.snapshot.tick % 240) // 10
        utility = debt * 1.5
        if hour >= 22 or hour <= 6: utility += 1.0
        return utility

class EatScorer(GoalScorer):
    """Utility based on hunger level."""
    @property
    def name(self) -> GoalType: return GoalType.EAT
    @property
    def target_state(self) -> AIState: return AIState.EATING
    def score(self, ctx: AIContext) -> float:
        return ctx.actor.mind.routine.hunger_level * 1.0

# ---------------------------------------------------------------------------
# Legacy Stubs for other goals
# ---------------------------------------------------------------------------
class TradeGoal(GoalScorer):
    @property
    def name(self) -> GoalType: return GoalType.TRADE
    @property
    def target_state(self) -> AIState: return AIState.VISIT_SHOP
    def score(self, ctx: AIContext) -> float: return 0.05
class RestGoal(GoalScorer):
    @property
    def name(self) -> GoalType: return GoalType.REST
    @property
    def target_state(self) -> AIState: return AIState.RESTING_IN_TOWN
    def score(self, ctx: AIContext) -> float: return 0.0
class CraftGoal(GoalScorer):
    @property
    def name(self) -> GoalType: return GoalType.CRAFT
    @property
    def target_state(self) -> AIState: return AIState.VISIT_BLACKSMITH
    def score(self, ctx: AIContext) -> float: return 0.05
class SocialGoal(GoalScorer):
    @property
    def name(self) -> GoalType: return GoalType.SOCIAL
    @property
    def target_state(self) -> AIState: return AIState.VISIT_GUILD
    def score(self, ctx: AIContext) -> float: return 0.05
class GuardGoal(GoalScorer):
    @property
    def name(self) -> GoalType: return GoalType.GUARD
    @property
    def target_state(self) -> AIState: return AIState.GUARD_CAMP
    def score(self, ctx: AIContext) -> float: return 0.0
class CorpseScorer(GoalScorer):
    @property
    def name(self) -> GoalType: return GoalType.CORPSE_RUN
    @property
    def target_state(self) -> AIState: return AIState.RECOVER_CORPSE
    def score(self, ctx: AIContext) -> float: return 0.0
