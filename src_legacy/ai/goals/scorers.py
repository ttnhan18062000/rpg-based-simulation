"""Built-in GoalScorer implementations.

Refactored for AOA Stabilization:
- Explicit aspect access (spatial, combat, mind, progression).
- Nested mind-state access (decision, emotion, perception).
- Removed legacy property shims and getattr hacks.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from src_legacy.ai.goals.base import GoalScorer
from src_legacy.core.models.enums import AIState, GoalType, Faction
from src_legacy.core.models.strategy import ObjectiveKind
from src_legacy.core.entities.traits import aggregate_trait_stats, aggregate_trait_utility
from src_legacy.core.models.vectors import Vector2

if TYPE_CHECKING:
    from src_legacy.ai.states import AIContext

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _trait_utility(ctx: AIContext):
    return aggregate_trait_utility(ctx.actor.identity.traits)

def _is_hero(ctx: AIContext) -> bool:
    return ctx.actor.identity.faction == Faction.HERO_GUILD

def _current_region_difficulty(ctx: AIContext) -> int:
    """Returns the difficulty tier of the current region (1-4)."""
    actor = ctx.actor
    rid = actor.spatial.current_region_id
    if not rid:
        return 0
    
    # Check current regions in snapshot
    for region in ctx.snapshot.regions:
        if region.region_id == rid:
            return region.difficulty
            
    return 0

def _region_danger_penalty(ctx: AIContext) -> float:
    """Calculates a utility penalty based on region difficulty vs actor level. [PHASE 4]"""
    difficulty = _current_region_difficulty(ctx)
    if difficulty <= 0:
        return 0.0
        
    level = ctx.actor.progression.level
    
    # Formula: excess_danger = (diff * 3) - (level + 3)
    # Each point of excess_danger adds 0.05 penalty, capped at 0.4
    excess = (difficulty * 3) - (level + 3)
    if excess <= 0:
        return 0.0
        
    penalty = excess * 0.05
    return min(0.4, penalty)

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
        base = 0.5
        enemy = ctx.nearest_enemy()
        if enemy:
            dist = actor.spatial.pos.manhattan(enemy.spatial.pos)
            base += 0.5 * max(0, 1.0 - dist / 15.0)  # [AOA STABILIZATION] Dominant utility for engagement
            
            # [Milestone 2] Target Stickiness (Hysteresis)
            from src_legacy.core.logic.combat_interaction_service import CombatInteractionService
            base += CombatInteractionService.get_stickiness_bonus(actor, enemy.id)
            
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
        actor = ctx.actor
        
        # [AOA STABILIZATION] Unify with tactical should_flee heuristic
        # This ensures ranged/melee bias and situational awareness are consistent 
        # between goal selection and action execution.
        from src_legacy.ai.states.base import should_flee
        
        # We check locally visible context and memory via should_flee
        if should_flee(actor, ctx.config, ctx.nearest_enemy()):
            return 2.0
            
        # Situational Panic: Even if HP is high, extreme local trauma might trigger a retreat
        if actor.mind.emotion.panic > 0.8:
            return 1.5 # Panic flight
                
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
        # [PHASE 4 STAGE 3] Suppress exploration in dangerous zones
        rid = ctx.actor.spatial.current_region_id
        penalty = 0.0
        if rid:
            region_metric = ctx.snapshot.region_consequence_registry.get(rid)
            if region_metric:
                penalty = region_metric.danger_level * 0.5
        
        return max(0.0, 0.3 + _trait_utility(ctx).explore - penalty)

# ---------------------------------------------------------------------------
# Loot — pick up items
# ---------------------------------------------------------------------------

class LootGoal(GoalScorer):
    @property
    def name(self) -> GoalType: return GoalType.LOOT
    @property
    def target_state(self) -> AIState: return AIState.LOOTING
    def score(self, ctx: AIContext) -> float:
        actor = ctx.actor
        if not actor.inventory: return 0.0
        
        # Abort if full or overweight
        if actor.inventory.is_full or actor.inventory.weight_ratio >= 1.0:
            return 0.0
            
        base = 0.1
        # Penalty for near-full bag
        if actor.inventory.slots_free <= 2 or actor.inventory.weight_ratio >= 0.9:
            base *= 0.2
            
        # Nearby loot bonus
        if ctx.snapshot.ground_items:
            # Simple proximity check for ground loot
            for pos_tuple in ctx.snapshot.ground_items:
                pos = Vector2(*pos_tuple)
                if actor.spatial.pos.manhattan(pos) < 10:
                    base += 0.5
                    break
                    
        return base + _trait_utility(ctx).loot

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
        utility = debt * 1.5
        if debt > 0.05:
            hour = ctx.snapshot.hour
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
    def score(self, ctx: AIContext) -> float:
        actor = ctx.actor
        if not actor.inventory: return 0.0
        
        base = 0.05
        # Urgency bonus for full/heavy bag
        if actor.inventory.is_full or actor.inventory.weight_ratio >= 0.9:
            base += 0.8
        elif actor.inventory.slots_free <= 3:
            base += 0.4
            
        return base
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

# ---------------------------------------------------------------------------
# Investigation detours [PHASE 3]
# ---------------------------------------------------------------------------

class InvestigateGoal(GoalScorer):
    """Utility based on having an active strategic lead/investigation objective."""
    @property
    def name(self) -> GoalType: return GoalType.INVESTIGATE
    @property
    def target_state(self) -> AIState: return AIState.INVESTIGATING
    def score(self, ctx: AIContext) -> float:
        obj = ctx.actor.mind.strategic.current_objective
        if obj and obj.kind == ObjectiveKind.INVESTIGATE:
            # High priority detour to resolve uncertainty
            return 2.5 
        return 0.0
