"""Built-in GoalScorer implementations.

Each class is a self-contained scoring unit.  To add a new goal:
  1. Create a new GoalScorer subclass here (or in a separate file).
  2. Register it in ``registry.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.ai.goals.base import GoalScorer
from src.core.enums import AIState
from src.core.faction import Faction
from src.core.traits import aggregate_trait_stats, aggregate_trait_utility

if TYPE_CHECKING:
    from src.ai.states import AIContext


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _trait_utility(ctx: AIContext):
    return aggregate_trait_utility(ctx.actor.traits)


def _trait_stats(ctx: AIContext):
    return aggregate_trait_stats(ctx.actor.traits)


def _is_hero(ctx: AIContext) -> bool:
    return ctx.actor.faction == Faction.HERO_GUILD


def _current_region_difficulty(ctx: AIContext) -> int:
    """Return difficulty tier of the region the actor is currently standing in (0 if none)."""
    rid = ctx.actor.current_region_id
    if not rid:
        return 0
    for r in ctx.snapshot.regions:
        if r.region_id == rid:
            return r.difficulty
    return 0


def _region_danger_penalty(ctx: AIContext) -> float:
    """Penalty when hero is in a region too dangerous for their level.

    Rule: region is dangerous when difficulty * 3 > hero_level + 3.
    Returns a value >= 0 (0 = no penalty, higher = more dangerous).
    """
    diff = _current_region_difficulty(ctx)
    if diff <= 0:
        return 0.0
    level = ctx.actor.stats.level
    danger_threshold = diff * 3
    comfort_ceiling = level + 3
    if danger_threshold <= comfort_ceiling:
        return 0.0
    return min((danger_threshold - comfort_ceiling) * 0.05, 0.4)


# ---------------------------------------------------------------------------
# Combat — seek and fight enemies
# ---------------------------------------------------------------------------

class CombatGoal(GoalScorer):

    @property
    def name(self) -> str:
        return "combat"

    @property
    def target_state(self) -> AIState:
        return AIState.HUNT

    def score(self, ctx: AIContext) -> float:
        actor = ctx.actor
        hp_ratio = actor.stats.hp_ratio
        base = 0.3

        enemy = ctx.nearest_enemy()
        if enemy is not None:
            dist = actor.pos.manhattan(enemy.pos)
            base += 0.5 * max(0, 1.0 - dist / 10.0)
            enemy_power = enemy.effective_atk() + enemy.effective_matk()
            my_power = actor.effective_atk() + actor.effective_matk()
            if my_power > enemy_power * 1.2:
                base += 0.2
            elif enemy_power > my_power * 1.5:
                base -= 0.3
        else:
            base -= 0.2

        if hp_ratio < 0.5:
            base -= 0.3 * (1.0 - hp_ratio)

        # Mobs are more aggressive when defending home territory
        if not _is_hero(ctx):
            from src.ai.states import is_on_home_territory
            if is_on_home_territory(ctx):
                base += 0.3  # territorial aggression bonus
            if enemy is not None:
                base += 0.15  # mobs always eager to fight intruders
        else:
            # Heroes are less eager to fight in regions above their level
            base -= _region_danger_penalty(ctx)

        base += _trait_utility(ctx).combat
        return base


# ---------------------------------------------------------------------------
# Flee — retreat to safety
# ---------------------------------------------------------------------------

class FleeGoal(GoalScorer):

    @property
    def name(self) -> str:
        return "flee"

    @property
    def target_state(self) -> AIState:
        return AIState.FLEE

    def score(self, ctx: AIContext) -> float:
        actor = ctx.actor
        hp_ratio = actor.stats.hp_ratio

        flee_threshold = ctx.config.flee_hp_threshold
        flee_threshold += _trait_stats(ctx).flee_threshold_mod
        # Heroes flee earlier in regions above their comfort zone (epic-15 F8)
        if _is_hero(ctx):
            diff = _current_region_difficulty(ctx)
            if diff > 0:
                comfort = actor.stats.level + 3
                excess = max(diff * 3 - comfort, 0)
                flee_threshold += excess * 0.03  # +3% per excess danger point
        flee_threshold = max(0.05, min(0.8, flee_threshold))

        base = 0.0
        if hp_ratio <= flee_threshold:
            base = 0.8 + (flee_threshold - hp_ratio) * 2.0
        elif hp_ratio < 0.5:
            base = 0.2 * (1.0 - hp_ratio)

        if ctx.nearest_enemy() is not None and hp_ratio < 0.6:
            base += 0.2

        # Mobs are less willing to flee on home territory
        if not _is_hero(ctx):
            from src.ai.states import is_on_home_territory
            if is_on_home_territory(ctx):
                base *= 0.5  # halve flee desire on home turf

        base += _trait_utility(ctx).flee
        return base


# ---------------------------------------------------------------------------
# Explore — discover unknown territory
# ---------------------------------------------------------------------------

class ExploreGoal(GoalScorer):

    @property
    def name(self) -> str:
        return "explore"

    @property
    def target_state(self) -> AIState:
        return AIState.WANDER

    def score(self, ctx: AIContext) -> float:
        actor = ctx.actor
        hp_ratio = actor.stats.hp_ratio
        stamina_ratio = actor.stats.stamina_ratio

        base = 0.2
        if hp_ratio > 0.7 and stamina_ratio > 0.4:
            base += 0.2
        if ctx.nearest_enemy() is None:
            base += 0.15

        # Heroes prefer exploring regions near their power level (epic-15 F8)
        if _is_hero(ctx):
            penalty = _region_danger_penalty(ctx)
            base -= penalty
            # Slight bonus for being in a region that matches hero level
            diff = _current_region_difficulty(ctx)
            if diff > 0:
                level = actor.stats.level
                if diff * 3 <= level + 3:  # comfortable
                    base += 0.1

        base += _trait_utility(ctx).explore
        return base


# ---------------------------------------------------------------------------
# Loot — pick up ground items / harvest resources
# ---------------------------------------------------------------------------

class LootGoal(GoalScorer):

    @property
    def name(self) -> str:
        return "loot"

    @property
    def target_state(self) -> AIState:
        return AIState.LOOTING

    def score(self, ctx: AIContext) -> float:
        actor = ctx.actor
        base = 0.0

        if _is_hero(ctx):
            # Don't loot if inventory is full (slots or weight)
            if actor.inventory and actor.inventory.is_effectively_full:
                return 0.0
            from src.ai.perception import Perception
            loot_pos = Perception.ground_loot_nearby(actor, ctx.snapshot, radius=5)
            if loot_pos is not None:
                base = 0.5
                if actor.pos.manhattan(loot_pos) <= 2:
                    base = 0.7
            # Reduce desire when bag is nearly full (slots or weight)
            if actor.inventory:
                free = actor.inventory.max_slots - actor.inventory.used_slots
                nearly_full = free <= 2 or actor.inventory.weight_ratio >= 0.9
                if nearly_full:
                    base *= 0.3  # strongly discourage looting with nearly-full bag
                elif free > 2:
                    base += 0.1

        base += _trait_utility(ctx).loot
        return base


# ---------------------------------------------------------------------------
# Trade — visit shops to buy/sell
# ---------------------------------------------------------------------------

class TradeGoal(GoalScorer):

    @property
    def name(self) -> str:
        return "trade"

    @property
    def target_state(self) -> AIState:
        return AIState.VISIT_SHOP

    def score(self, ctx: AIContext) -> float:
        base = 0.0
        if _is_hero(ctx):
            from src.ai.states import hero_has_sellable_items, hero_wants_to_buy
            if hero_has_sellable_items(ctx.actor):
                base += 0.4
            if hero_wants_to_buy(ctx.actor):
                base += 0.3
            # Urgently sell when bag is nearly full (slots or weight)
            inv = ctx.actor.inventory
            if inv and (inv.used_slots >= inv.max_slots - 2 or inv.weight_ratio >= 0.9):
                base += 0.4

        base += _trait_utility(ctx).trade
        return base


# ---------------------------------------------------------------------------
# Rest — heal and recover
# ---------------------------------------------------------------------------

class RestGoal(GoalScorer):

    @property
    def name(self) -> str:
        return "rest"

    @property
    def target_state(self) -> AIState:
        return AIState.RESTING_IN_TOWN

    def score(self, ctx: AIContext) -> float:
        actor = ctx.actor
        hp_ratio = actor.stats.hp_ratio
        stamina_ratio = actor.stats.stamina_ratio

        base = 0.0
        if hp_ratio < 0.8:
            base = 0.3 * (1.0 - hp_ratio)
        if stamina_ratio < 0.3:
            base += 0.3
        if _is_hero(ctx) and actor.home_pos:
            base += 0.05

        base += _trait_utility(ctx).rest
        return base


# ---------------------------------------------------------------------------
# Craft — visit blacksmith, gather materials
# ---------------------------------------------------------------------------

class CraftGoal(GoalScorer):

    @property
    def name(self) -> str:
        return "craft"

    @property
    def target_state(self) -> AIState:
        return AIState.VISIT_BLACKSMITH

    def score(self, ctx: AIContext) -> float:
        base = 0.0
        if _is_hero(ctx):
            from src.ai.states import hero_should_visit_blacksmith
            if hero_should_visit_blacksmith(ctx.actor):
                base = 0.4

        base += _trait_utility(ctx).craft
        return base


# ---------------------------------------------------------------------------
# Social — visit guild, interact with NPCs
# ---------------------------------------------------------------------------

class SocialGoal(GoalScorer):

    @property
    def name(self) -> str:
        return "social"

    @property
    def target_state(self) -> AIState:
        return AIState.VISIT_GUILD

    def score(self, ctx: AIContext) -> float:
        base = 0.0
        if _is_hero(ctx):
            from src.ai.states import hero_should_visit_guild, hero_should_visit_class_hall
            if hero_should_visit_guild(ctx.actor):
                base = 0.35
            if hero_should_visit_class_hall(ctx.actor):
                base += 0.3

        base += _trait_utility(ctx).social
        return base


# ---------------------------------------------------------------------------
# Guard — patrol and protect territory (enemies only)
# ---------------------------------------------------------------------------

class GuardGoal(GoalScorer):

    @property
    def name(self) -> str:
        return "guard"

    @property
    def target_state(self) -> AIState:
        return AIState.GUARD_CAMP

    def score(self, ctx: AIContext) -> float:
        if _is_hero(ctx):
            return 0.0

        actor = ctx.actor
        base = 0.0

        from src.ai.states import is_on_home_territory
        if is_on_home_territory(ctx):
            base = 0.4
            # Spike urgency if an enemy is visible on our turf
            if ctx.nearest_enemy() is not None:
                base = 0.8
        elif actor.home_pos:
            dist_home = actor.pos.manhattan(actor.home_pos)
            if dist_home > 5:
                base = 0.3

        return base
