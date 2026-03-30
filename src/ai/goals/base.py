"""Base classes for the Goal scoring plugin system.

GoalScorer   — Abstract base class; subclass and implement `score()`.
GoalScore    — A (goal_name, score, target_state) tuple for selection.
GoalEvaluator— Iterates registered scorers, filters, sorts, selects.
GOAL_REGISTRY— Module-level list where scorers are registered.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from src.core.models.enums import AIState

if TYPE_CHECKING:
    from src.ai.states import AIContext


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class GoalScore:
    """A scored goal ready for selection."""
    goal: str
    score: float
    target_state: AIState


# ---------------------------------------------------------------------------
# Abstract scorer
# ---------------------------------------------------------------------------

class GoalScorer(ABC):
    """Base class for all goal scorers.

    Subclass this and implement:
      - name:         unique goal identifier string
      - target_state: AIState the entity transitions to if this goal wins
      - score(ctx):   return a float utility score (<=0 means non-viable)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique goal identifier (e.g. 'combat', 'flee')."""

    @property
    @abstractmethod
    def target_state(self) -> AIState:
        """AIState to transition to when this goal is selected."""

    @abstractmethod
    def score(self, ctx: AIContext) -> float:
        """Score this goal for the given entity context.

        Returns a float where higher = more desirable.
        Scores <= 0.0 are filtered out as non-viable.
        """

    def evaluate(self, ctx: AIContext) -> GoalScore:
        """Convenience: score and wrap into GoalScore."""
        return GoalScore(
            goal=self.name,
            score=self.score(ctx),
            target_state=self.target_state,
        )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

GOAL_REGISTRY: list[GoalScorer] = []


def register_goal(scorer: GoalScorer) -> GoalScorer:
    """Register a GoalScorer instance in the global registry."""
    GOAL_REGISTRY.append(scorer)
    return scorer


# ---------------------------------------------------------------------------
# Modifiers (Biases)
# ---------------------------------------------------------------------------

class ScoreModifier(ABC):
    """Interface for modifying a GoalScore based on external factors."""
    @abstractmethod
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        """Apply modification to the score object in-place."""

class BoredomModifier(ScoreModifier):
    """Applies actor's boredom multipliers to current scores."""
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        multiplier = ctx.actor.mind.decision.boredom_multipliers.get(score.goal, 1.0)
        score.score *= multiplier

class LifeStageModifier(ScoreModifier):
    """Heuristic based on level brackets to differentiate progression focus."""
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        level = ctx.actor.progression.level
        goal = score.goal
        
        # Early Stage (1-10)
        if level <= 10:
            if goal in ("explore", "rest"): score.score *= 1.3
            if goal in ("trade", "combat"): score.score *= 0.8
        # Mid Stage (11-20)
        elif level <= 20:
            if goal in ("combat", "loot"): score.score *= 1.2
            if goal == "rest": score.score *= 0.9
        # Late Stage (21+)
        else:
            if goal in ("social", "trade", "craft"): score.score *= 1.4
            if goal == "explore": score.score *= 0.7

class PersonalityModifier(ScoreModifier):
    """Biases scores based on OCEAN personality traits."""
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        identity = ctx.actor.identity
        goal = score.goal
        
        if goal == "explore":
            score.score *= (0.5 + identity.openness)
        elif goal in ("rest", "craft"):
            score.score *= (0.5 + identity.conscientiousness)
        elif goal == "social":
            score.score *= (0.5 + identity.extraversion)
        elif goal == "trade":
            # Agreeableness might affect likelihood to visit shops (better deals or social interaction)
            score.score *= (0.5 + identity.agreeableness)
        elif score.goal == "flee":
            score.score *= (0.5 + identity.neuroticism)
        elif goal == "combat":
            # Anxious entities are less aggressive
            score.score *= (1.2 - identity.neuroticism)

class StuckModifier(ScoreModifier):
    """Encourages resting/idling if the entity is stuck (emotional state)."""
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        if ctx.actor.mind.emotion.emotional_state.get("stuck", 0.0) > 0:
            if score.goal in ("rest", "social"):
                score.score *= 2.0
            if score.goal in ("explore", "combat", "loot"):
                score.score *= 0.5

class HysteresisModifier(ScoreModifier):
    """Provides a boost to the currently active goal to prevent jitter.
    
    Boost scales with commitment duration:
      base=1.25 + 0.05 * min(ticks_held, 10) → up to 1.75x after 10 ticks.
    """
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        mind_dec = ctx.actor.mind.decision
        if mind_dec.last_goal == score.goal:
            ticks_held = max(0, ctx.snapshot.tick - mind_dec.goal_committed_at)
            # AOA Stabilization: Cooler hysteresis (1.1 instead of 1.25)
            # to allow high-utility transitions to win after lock expires.
            boost = 1.1 + 0.05 * min(ticks_held, 10)
            score.score *= boost


class CooldownModifier(ScoreModifier):
    """Penalizes recently abandoned goals to prevent flip-flopping.
    
    If the goal is on cooldown (tick < expiry), multiply score by
    config.goal_cooldown_penalty (default 0.5).
    """
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        cooldowns = ctx.actor.mind.decision.goal_cooldowns
        expiry = cooldowns.get(score.goal)
        if expiry is not None and ctx.snapshot.tick < expiry:
            penalty = getattr(ctx.config, 'goal_cooldown_penalty', 0.5)
            score.score *= penalty


class MemoryModifier(ScoreModifier):
    """Biases scores based on accumulated narrative memories.

    - High glory  → stronger combat preference
    - High trauma → stronger flee preference
    - Discoveries → stronger explore preference
    """
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        mind = ctx.actor.mind
        goal = score.goal

        if goal == "combat":
            glory = mind.total_glory()
            if glory > 0:
                score.score *= 1.0 + glory / 100.0
            
            # Nemesis fear: discourage fighting a high-grudge rival directly (0.1x penalty)
            enemy = ctx.nearest_enemy()
            if enemy and mind.emotion.grudges.get(enemy.id, 0.0) > 30.0:
                score.score *= 0.1
        elif goal == "flee":
            trauma = mind.total_trauma()
            if trauma < 0:
                score.score *= 1.0 + abs(trauma) / 100.0
            
            # Nemesis bias: if a known nemesis is visible, EXTREME boost to flee (10.0x)
            enemy = ctx.nearest_enemy()
            if enemy and mind.emotion.grudges.get(enemy.id, 0.0) > 30.0:
                score.score *= 10.0
        elif goal == "explore":
            discoveries = sum(
                1 for e in mind.narrative.memory_log if e.get("type") == "DISCOVERY"
            )
            if discoveries > 0:
                score.score *= 1.0 + discoveries / 20.0


class EmotionalModifier(ScoreModifier):
    """Biases scores based on short-term emotional states (Panic, etc.)."""
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        emotions = ctx.actor.mind.emotion.emotional_state
        goal = score.goal
        
        panic = emotions.get("panic", 0.0)
        if panic > 0:
            if goal == "flee":
                score.score *= (1.0 + panic * 5.0)
            if goal in ("combat", "loot", "trade"):
                score.score *= max(0.0, 1.0 - panic)

class SkirmishModifier(ScoreModifier):
    """Biases ranged entities towards kiting / maintaining distance."""
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        from src.core.models.enums import HeroClass
        ranged_classes = (HeroClass.RANGER, HeroClass.MAGE, HeroClass.SHARPSHOOTER, HeroClass.ARCHMAGE, HeroClass.CASTER)
        
        if ctx.actor.progression.hero_class in ranged_classes:
            goal = score.goal
            # If a hostile is adjacent, boost flee or move_away
            if goal in ("flee", "move"):
                target_id = ctx.actor.combat.combat_target_id
                if target_id:
                    mem = ctx.actor.mind.perception.entity_memory.get(target_id)
                    if mem:
                        # Extract position from memory entry (could be a dict or object)
                        t_pos = mem.get("pos") if isinstance(mem, dict) else getattr(mem, "pos", mem)
                        if t_pos:
                            from src.core.models.vectors import Vector2
                            v_target = Vector2.from_any(t_pos)
                            dist = ctx.actor.spatial.pos.manhattan(v_target)
                            if dist <= 3:
                                score.score *= 2.0


class AmbitionModifier(ScoreModifier):
    """Biases scores based on the actor's Life Directive (Obsession)."""
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        directive = getattr(ctx.actor.identity, "life_directive", None)
        if not directive:
            return
            
        goal = score.goal
        # Pillar 6: Narrative Biases
        if directive == "DRAGON_SLAYER":
            if goal == "combat": score.score *= 1.5
            if goal == "explore": score.score *= 1.2
        elif directive == "CRAFTER":
            if goal == "craft": score.score *= 1.7
            if goal == "loot": score.score *= 1.3
        elif directive == "MERCHANT":
            if goal == "trade": score.score *= 1.6
            if goal == "social": score.score *= 1.3
        elif directive == "COLLECTOR":
            if goal == "loot": score.score *= 1.7
            if goal == "explore": score.score *= 1.2
        elif directive == "EXPLORATION":
            if goal == "explore": score.score *= 1.6
            if goal == "loot": score.score *= 1.2

class FatigueModifier(ScoreModifier):
    """Penalty for goals that stay in the same region too long (Anti-Loop)."""
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        rid = ctx.actor.spatial.current_region_id
        if not rid:
            return
            
        fatigue = ctx.actor.mind.narrative.region_fatigue.get(rid, 0.0)
        if fatigue > 0:
            # Penalize the goals that keep us in the current region
            if score.goal in ("explore", "combat", "loot"):
                score.score *= (1.0 - fatigue * 0.5)

# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

class GoalEvaluator:
    """Scores all registered goals and selects one via weighted random.

    Usage::

        evaluator = GoalEvaluator()
        scores = evaluator.evaluate(ctx)
        goal = evaluator.select(scores, rng_value)
    """

    def __init__(self, modifiers: list[ScoreModifier] | None = None) -> None:
        self.modifiers = modifiers if modifiers is not None else [
            BoredomModifier(),
            LifeStageModifier(),
            PersonalityModifier(),
            EmotionalModifier(),
            HysteresisModifier(),
            CooldownModifier(),
            MemoryModifier(),
            StuckModifier(),
            SkirmishModifier(),
            AmbitionModifier(),
            FatigueModifier(),
        ]

    def evaluate(self, ctx: AIContext) -> list[GoalScore]:
        """Score all registered goals, filter non-viable, sort descending."""
        scores = [scorer.evaluate(ctx) for scorer in GOAL_REGISTRY]
        
        # Apply modifiers (Boredom, Personality, Life-Cycle, etc.)
        for s in scores:
            for modifier in self.modifiers:
                modifier.modify(s, ctx)
        
        scores = [s for s in scores if s.score > 0.0]
        scores.sort(key=lambda g: g.score, reverse=True)
        return scores

    def is_goal_locked(self, ctx: AIContext) -> bool:
        min_ticks = getattr(ctx.config, 'min_commitment_ticks', 3)
        committed_at = ctx.actor.mind.decision.goal_committed_at
        ticks_held = ctx.snapshot.tick - committed_at

        if ticks_held < min_ticks:
            # Soul/Personality override: fear breaks the lock early
            panic = ctx.actor.mind.emotion.emotional_state.get("panic", 0.0)
            if ctx.actor.combat.hp_ratio < 0.5 and (ctx.actor.identity.neuroticism > 0.5 or panic > 0.5):
                return False
            # Critical override for all: near death breaks the lock
            if ctx.actor.combat.hp_ratio < 0.15:
                return False
            return True
        return False

    @staticmethod
    def select(
        scores: list[GoalScore],
        rng_value: float,
        top_n: int = 3,
        temperature: float = 0.2,
    ) -> GoalScore | None:
        """Select a goal via Softmax weighted random from top N candidates.

        Args:
            scores: Sorted list of GoalScore (descending).
            rng_value: Random float [0, 1) for selection.
            top_n: How many top goals to consider.
            temperature: Softmax smoothing factor (higher = more random).

        Returns:
            Selected GoalScore, or None if no viable goals.
        """
        if not scores:
            return None

        candidates = scores[:top_n]
        if len(candidates) == 1:
            return candidates[0]

        # Softmax: w_i = exp(score / temperature)
        # Shift by max_score for numerical stability
        max_score = candidates[0].score
        import math
        weights = [math.exp((c.score - max_score) / temperature) for c in candidates]
        total = sum(weights)

        # Weighted selection
        target = rng_value * total
        cumulative = 0.0
        for i, w in enumerate(weights):
            cumulative += w
            if target <= cumulative:
                return candidates[i]

        return candidates[-1]
