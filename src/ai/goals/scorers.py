"""Built-in GoalScorer implementations.

Refactored for AOA Stabilization:
- Explicit aspect access (spatial, combat, mind, progression).
- Nested mind-state access (decision, emotion, perception).
- Removed legacy property shims and getattr hacks.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from src.ai.goals.base import GoalScorer
from src.core.models.enums import AIState, GoalType, EmotionType
from src.core.gameplay.faction import Faction
from src.core.entities.traits import aggregate_trait_stats, aggregate_trait_utility

if TYPE_CHECKING:
    from src.ai.states import AIContext

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _trait_utility(ctx: AIContext):
    return aggregate_trait_utility(ctx.actor.identity.traits)

def _trait_stats(ctx: AIContext):
    return aggregate_trait_stats(ctx.actor.identity.traits)

def _is_hero(ctx: AIContext) -> bool:
    return ctx.actor.identity.faction == Faction.HERO_GUILD

def _current_region_difficulty(ctx: AIContext) -> int:
    """Return difficulty tier of the region the actor is currently standing in (0 if none)."""
    rid = ctx.actor.spatial.current_region_id
    if not rid:
        return 0
    for r in ctx.snapshot.regions:
        if r.region_id == rid:
            return r.difficulty
    return 0

def _region_danger_penalty(ctx: AIContext) -> float:
    """Penalty when hero is in a region too dangerous for their level."""
    diff = _current_region_difficulty(ctx)
    if diff <= 0:
        return 0.0
    level = ctx.actor.progression.level
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
    def name(self) -> GoalType: return GoalType.COMBAT

    @property
    def target_state(self) -> AIState: return AIState.HUNT

    def score(self, ctx: AIContext) -> float:
        actor = ctx.actor
        combat = actor.combat
        hp_ratio = combat.hp_ratio
        base = 0.3 if _is_hero(ctx) else 0.3 # Boost hero aggression

        enemy = ctx.nearest_enemy()
        dist = 999
        if enemy is not None:
            dist = actor.spatial.pos.manhattan(enemy.spatial.pos)
            base += 0.5 * max(0, 1.0 - dist / 10.0)
            enemy_power = enemy.combat.atk + enemy.combat.matk
            my_power = combat.atk + combat.matk
            if my_power > enemy_power * 1.2:
                base += 0.2
            elif enemy_power > my_power * 1.5:
                base -= 0.3
        else:
            base -= 0.2

        if enemy is not None and enemy.identity.faction == Faction.HERO_GUILD:
            fame = enemy.progression.fame
            if fame > 100: base -= 0.6
            elif fame > 50: base -= 0.3
            elif fame > 20: base -= 0.1

        if enemy is not None and dist <= 1:
            base += 0.4 # Melee stickiness

        if hp_ratio < 0.3:
            base -= 0.6 * (1.0 - hp_ratio)
        elif hp_ratio < 0.6:
            base -= 0.2 * (1.0 - hp_ratio)

        # Brave heroes are significantly more aggressive
        bravery = actor.mind.emotion.bravery
        neuroticism = actor.identity.neuroticism
        
        from src.core.entities.traits import TraitType
        if TraitType.BRAVE in actor.identity.traits:
            base += 0.8
        
        base += (0.5 - neuroticism) * 0.6
        base += (bravery - 0.5) * 0.4

        if not _is_hero(ctx):
            from src.ai.states import is_on_home_territory
            if is_on_home_territory(ctx):
                base += 0.3
            if enemy is not None:
                base += 0.15
        else:
            base -= _region_danger_penalty(ctx)

        base += _trait_utility(ctx).combat
        if enemy is not None and dist <= 3:
            base += 1.2 # Strong engagement bias when close
        return base

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
        hp_ratio = actor.combat.hp_ratio
        mind = actor.mind

        currently_fleeing = mind.decision.ai_state == AIState.FLEE
        flee_exit = getattr(ctx.config, 'flee_exit_threshold', 0.5)

        if currently_fleeing and hp_ratio <= flee_exit:
            base = 0.8 + (flee_exit - hp_ratio) * 1.5
            return base + _trait_utility(ctx).flee

        if currently_fleeing and hp_ratio > flee_exit:
            return 0.1 + _trait_utility(ctx).flee

        enemy = ctx.nearest_enemy()
        if enemy and mind.emotion.grudges.get(enemy.id, 0.0) >= 30.0 and hp_ratio < 0.6:
            return 2.0 + _trait_utility(ctx).flee
        
        flee_threshold = ctx.config.flee_hp_threshold + _trait_stats(ctx).flee_threshold_mod
        if _is_hero(ctx):
            diff = _current_region_difficulty(ctx)
            if diff > 0:
                comfort = actor.progression.level + 3
                excess = max(diff * 3 - comfort, 0)
                flee_threshold += excess * 0.03
        
        bravery = mind.emotion.bravery
        flee_threshold = max(0.05, min(0.9, flee_threshold + (0.5 - bravery) * 0.4))

        base = 0.0
        if hp_ratio <= flee_threshold:
            base = 0.8 + (flee_threshold - hp_ratio) * 2.0
        elif hp_ratio < 0.6:
            div = (0.6 - flee_threshold)
            base = 0.4 * (0.6 - hp_ratio) / div if div > 0 else 0.1
        
        from src.core.entities.traits import TraitType
        if TraitType.BRAVE in actor.identity.traits:
            base -= 0.6
        
        base += (actor.identity.neuroticism - 0.5) * 0.8

        if enemy is not None and hp_ratio < 0.6:
            base += 0.2

        if not _is_hero(ctx):
            from src.ai.states import is_on_home_territory
            if is_on_home_territory(ctx):
                base *= 0.5

        return base + _trait_utility(ctx).flee

# ---------------------------------------------------------------------------
# Explore — discover unknown territory
# ---------------------------------------------------------------------------

class ExploreGoal(GoalScorer):
    @property
    def name(self) -> GoalType: return GoalType.EXPLORE

    @property
    def target_state(self) -> AIState: return AIState.WANDER

    def score(self, ctx: AIContext) -> float:
        actor = ctx.actor
        hp_ratio = actor.combat.hp_ratio
        stamina_ratio = actor.progression.stamina_ratio

        base = 0.2
        if hp_ratio > 0.7 and stamina_ratio > 0.4:
            base += 0.2
        if ctx.nearest_enemy() is None:
            base += 0.15

        if _is_hero(ctx):
            base -= _region_danger_penalty(ctx)
            diff = _current_region_difficulty(ctx)
            if diff > 0 and diff * 3 <= actor.progression.level + 3:
                base += 0.1

        return base + _trait_utility(ctx).explore

# ---------------------------------------------------------------------------
# Loot — pick up ground items / harvest resources
# ---------------------------------------------------------------------------

class LootGoal(GoalScorer):
    @property
    def name(self) -> GoalType: return GoalType.LOOT

    @property
    def target_state(self) -> AIState: return AIState.LOOTING

    def score(self, ctx: AIContext) -> float:
        actor = ctx.actor
        base = 0.0

        if _is_hero(ctx):
            inv = actor.inventory
            if inv and inv.is_effectively_full:
                return 0.0
            from src.ai.perception import Perception
            loot_pos = Perception.ground_loot_nearby(actor, ctx.snapshot, radius=5)
            if loot_pos is not None:
                base = 0.5
                if actor.spatial.pos.manhattan(loot_pos) <= 2:
                    base = 0.7
            if inv:
                free = inv.max_slots - inv.used_slots
                if free <= 2 or inv.weight_ratio >= 0.9:
                    base *= 0.3 
                elif free > 2:
                    base += 0.1

        return base + _trait_utility(ctx).loot

# ---------------------------------------------------------------------------
# Trade — visit shops to buy/sell
# ---------------------------------------------------------------------------

class TradeGoal(GoalScorer):
    @property
    def name(self) -> GoalType: return GoalType.TRADE

    @property
    def target_state(self) -> AIState: return AIState.VISIT_SHOP

    def score(self, ctx: AIContext) -> float:
        base = 0.05
        if _is_hero(ctx):
            from src.ai.states import hero_has_sellable_items, hero_wants_to_buy
            if hero_has_sellable_items(ctx.actor):
                base += 0.4
            if hero_wants_to_buy(ctx.actor):
                base += 0.3
            inv = ctx.actor.inventory
            if inv and (inv.used_slots >= inv.max_slots - 2 or inv.weight_ratio >= 0.9):
                base += 0.4

        if _is_hero(ctx) and ctx.nearest_enemy() is not None:
            return 0.05
        return base + _trait_utility(ctx).trade

# ---------------------------------------------------------------------------
# Rest — heal and recover
# ---------------------------------------------------------------------------

class RestGoal(GoalScorer):
    @property
    def name(self) -> GoalType: return GoalType.REST

    @property
    def target_state(self) -> AIState: return AIState.RESTING_IN_TOWN

    def score(self, ctx: AIContext) -> float:
        actor = ctx.actor
        hp_ratio = actor.combat.hp_ratio
        stamina_ratio = actor.progression.stamina_ratio

        base = 0.0
        if hp_ratio < 0.8:
            base = 0.3 * (1.0 - hp_ratio)
        if stamina_ratio < 0.3:
            base += 0.3
        if _is_hero(ctx) and actor.spatial.home_pos:
            base += 0.05

        if ctx.nearest_enemy() is not None:
            return -1.0  # HARD BLOCK
        return base + _trait_utility(ctx).rest

# ---------------------------------------------------------------------------
# Craft — visit blacksmith, gather materials
# ---------------------------------------------------------------------------

class CraftGoal(GoalScorer):
    @property
    def name(self) -> GoalType: return GoalType.CRAFT

    @property
    def target_state(self) -> AIState: return AIState.VISIT_BLACKSMITH

    def score(self, ctx: AIContext) -> float:
        base = 0.05
        if _is_hero(ctx):
            from src.ai.states import hero_should_visit_blacksmith
            if hero_should_visit_blacksmith(ctx.actor):
                base = 0.4

        if _is_hero(ctx) and ctx.nearest_enemy() is not None:
            return 0.05
        return base + _trait_utility(ctx).craft

# ---------------------------------------------------------------------------
# Social — visit guild, interact with NPCs
# ---------------------------------------------------------------------------

class SocialGoal(GoalScorer):
    @property
    def name(self) -> GoalType: return GoalType.SOCIAL

    @property
    def target_state(self) -> AIState: return AIState.VISIT_GUILD

    def score(self, ctx: AIContext) -> float:
        base = 0.05
        if _is_hero(ctx):
            from src.ai.states import hero_should_visit_guild, hero_should_visit_class_hall
            if hero_should_visit_guild(ctx.actor):
                base = 0.35
            if hero_should_visit_class_hall(ctx.actor):
                base += 0.3

        if _is_hero(ctx) and ctx.nearest_enemy() is not None:
            return 0.05
        return base + _trait_utility(ctx).social

# ---------------------------------------------------------------------------
# Guard — patrol and protect territory (enemies only)
# ---------------------------------------------------------------------------

class GuardGoal(GoalScorer):
    @property
    def name(self) -> GoalType: return GoalType.GUARD

    @property
    def target_state(self) -> AIState: return AIState.GUARD_CAMP

    def score(self, ctx: AIContext) -> float:
        if _is_hero(ctx):
            return 0.0

        actor = ctx.actor
        base = 0.0

        from src.ai.states import is_on_home_territory
        if is_on_home_territory(ctx):
            base = 0.4
            if ctx.nearest_enemy() is not None:
                base = 0.8
        elif actor.spatial.home_pos:
            dist_home = actor.spatial.pos.manhattan(actor.spatial.home_pos)
            base = 0.2 if dist_home < 10 else 0.0
        return base

# ---------------------------------------------------------------------------
# Corpse Run — recover items after death
# ---------------------------------------------------------------------------

class CorpseScorer(GoalScorer):
    @property
    def name(self) -> GoalType: return GoalType.CORPSE_RUN

    @property
    def target_state(self) -> AIState: return AIState.RECOVER_CORPSE

    def score(self, ctx: AIContext) -> float:
        if not _is_hero(ctx):
            return 0.0
            
        nodes = getattr(ctx.snapshot, "corpse_nodes", {})
        for node in nodes.values():
            if node.entity_id == ctx.actor.id:
                return 5.0
                
        return 0.0
