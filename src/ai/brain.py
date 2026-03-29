"""AIBrain — stateless decision engine with Utility AI goal selection.

Hybrid architecture:
  1. For "decision" states (IDLE, WANDER, RESTING_IN_TOWN, GUARD_CAMP),
     the GoalEvaluator scores all viable goals and picks one via weighted
     random.  The selected goal sets the AIState, then the state handler
     executes it.
  2. For "execution" states (HUNT, COMBAT, FLEE, LOOTING, VISIT_*, etc.),
     the state handler runs directly — the entity is already committed to
     an action and shouldn’t re-evaluate every tick.

Uses the STATE_HANDLERS registry from ``ai.states`` and the FactionRegistry
for faction-aware enemy/ally detection.
"""

from __future__ import annotations
from dataclasses import replace
from typing import Any, Protocol, TypeVar, runtime_checkable, TYPE_CHECKING

from src.core.models.enums import AIState, ActionType, Domain
from src.actions.base import ActionProposal
from src.ai.goals import GoalEvaluator
from src.ai.perception import Perception
from src.ai.states import AIContext, STATE_HANDLERS, IdleHandler
from src.core.gameplay.faction import FactionRegistry

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.core.entities.entity import Entity
    from src.core.models.snapshot import Snapshot
    from src.platform.rng import DeterministicRNG

_FALLBACK = IdleHandler()


class AIBrain:
    """Dispatches entity AI decisions based on their current state.

    Fully stateless — safe to call from any thread.
    """

    __slots__ = ("_config", "_rng", "_faction_reg", "_goal_evaluator")

    def __init__(
        self,
        config: SimulationConfig,
        rng: DeterministicRNG,
        faction_reg: FactionRegistry | None = None,
    ) -> None:
        self._config = config
        self._rng = rng
        self._faction_reg = faction_reg or FactionRegistry.default()
        self._goal_evaluator = GoalEvaluator()

    # States where the goal evaluator runs before the handler
    _DECISION_STATES = frozenset({
        AIState.IDLE, AIState.WANDER,
        AIState.HUNT, AIState.COMBAT, AIState.FLEE,
        AIState.RESTING_IN_TOWN, AIState.GUARD_CAMP,
    })

    def decide(self, actor: Entity, snapshot: Snapshot) -> tuple[AIState, ActionProposal]:
        """Run the AI Cognitive Pipeline for *actor*."""
        # --- Phase 1: Input (Sensory & Perception) ---
        ctx = self._sensory_perception_phase(actor, snapshot) # Steps 1 & 2
        
        # --- Phase 2: Internal State (Memory & Appraisal) ---
        self._memory_appraisal_phase(ctx) # Steps 3 & 4
        
        # --- Phase 3: Deliberation (Planning) ---
        selected_state = self._deliberation_tactical_phase(ctx) # Steps 5 & 6
        
        # --- Phase 4: Output (Proposal) ---
        return self._finalization_phase(ctx, selected_state) # Step 7

    def _sensory_perception_phase(self, actor: Entity, snapshot: Snapshot) -> AIContext:
        """Phase 1: Input. Gather raw data and apply selective attention."""
        ctx = AIContext(
            actor=actor,
            snapshot=snapshot,
            config=self._config,
            rng=self._rng,
            faction_reg=self._faction_reg,
        )
        
        # Step 1: Sensory (Gather data - handled by ctx.visible)
        
        # Step 2: Selective Attention (Filter saliency)
        # 1. Update Position History (Stuck Detection)
        actor.mind.pos_history.append(actor.spatial.pos)
        if len(actor.mind.pos_history) > 5:
            actor.mind.pos_history.pop(0)
            
        # 2. Rank by saliency: (Distance, Faction, Rarity)
        visible = ctx.visible
        def get_saliency(e):
            dist = actor.spatial.pos.manhattan(e.spatial.pos)
            is_hostile = self._faction_reg.is_hostile(actor.identity.faction, e.identity.faction)
            # Hostile/Rare entities have higher weight
            weight = 2.0 if is_hostile else 1.0
            rarity = getattr(e, 'rarity', 0)
            if isinstance(rarity, (int, float)) and rarity > 0:
                weight *= 2.0 # More importance to rare targets
            return weight / (dist + 1)
            
        ranked = sorted(visible, key=get_saliency, reverse=True)
        # Pillar 1: Selective Attention slots
        actor.mind.attention_pool = [e.id for e in ranked[:actor.mind.max_attention_slots]]
        
        # Actually filter ctx.visible for the rest of this tick's cognitive pipeline
        # (Decision Scorers and State Handlers will only see these entities)
        attention_set = set(actor.mind.attention_pool)
        ctx._visible = [e for e in visible if e.id in attention_set]
                
        return ctx

    def _memory_appraisal_phase(self, ctx: AIContext) -> None:
        """Phase 2: Internal State. Retrieve context and evaluate emotions."""
        actor = ctx.actor
        snapshot = ctx.snapshot
        
        # Step 3: Memory Recall (Retrieve Context)
        # 1. Remember visible hostile entities
        for e in ctx.visible:
            if self._faction_reg.is_hostile(actor.identity.faction, e.identity.faction):
                actor.mind.memory[e.id] = e.spatial.pos
        
        # 2. Fatigue Decay (Anti-loop)
        for rid in list(actor.mind.region_fatigue.keys()):
            val = actor.mind.region_fatigue[rid]
            actor.mind.region_fatigue[rid] = max(0.0, val - 0.005) # Slow decay

        # Step 4: Appraisal (Subjective Emotions)
        # 1. Boredom recovery & Emotional decay
        for gname in list(actor.mind.boredom_multipliers.keys()):
            val = actor.mind.boredom_multipliers[gname]
            if val < 1.0:
                actor.mind.boredom_multipliers[gname] = min(1.0, val + 0.02)
        
        for eme in list(actor.mind.emotional_state.keys()):
            val = actor.mind.emotional_state[eme]
            if val > 0:
                actor.mind.emotional_state[eme] = max(0.0, val - 0.01)

        # 3. Trigger Emotions & Mood (Pillar 1: Soul)
        # Influence mood from recent memory events
        recent_memories = [m for m in actor.mind.memory_log if (snapshot.tick - m.get("tick", 0)) < 100]
        for m in recent_memories:
            impact = m.get("impact", 0.0)
            if impact > 0:
                actor.mind.mood = min(1.0, actor.mind.mood + (impact * 0.02))
            else:
                actor.mind.mood = max(0.0, actor.mind.mood + (impact * 0.05)) # Trauma hits harder
                
        # 4. Physical Maintenance (Aging)
        if hasattr(actor, 'progression'):
            actor.progression.age_ticks += 1
            if actor.progression.age_ticks >= actor.progression.longevity_limit:
                actor.stats.combat.hp = 0
                return
            
        # 5. Narrative Memory: Discovery events
        region_id = getattr(actor, 'current_region_id', None)
        if region_id:
            # First-time DISCOVERY
            if region_id not in actor.mind.memory_locations:
                actor.mind.memory_locations[region_id] = 0.0  # neutral initial sentiment
                actor.mind.memory_log.append({
                    "tick": snapshot.tick,
                    "type": "DISCOVERY",
                    "desc": f"Discovered region {region_id}",
                    "impact": 2.0,
                })

        # 6. Specific Emotion Triggers
        if actor.stats.combat.hp_ratio < 0.3:
            current_panic = actor.mind.emotional_state.get("panic", 0.0)
            actor.mind.emotional_state["panic"] = min(1.0, current_panic + 0.1)

        # 6. Environmental Dread (Sentiment)
        region_id = getattr(actor, 'current_region_id', None)
        if region_id:
            sentiment = actor.mind.memory_locations.get(region_id, 0.0)
            if sentiment < -0.1: # Threshold for dread
                current_panic = actor.mind.emotional_state.get("panic", 0.0)
                actor.mind.emotional_state["panic"] = min(1.0, current_panic + 0.05)
            
        if len(actor.mind.pos_history) >= 5 and all(p == actor.mind.pos_history[0] for p in actor.mind.pos_history):
            actor.mind.emotional_state["stuck"] = 1.0
        else:
            actor.mind.emotional_state.pop("stuck", None)

        # 7. Relationship & Familiarity (Pillar 4: Social)
        # If we see a very high-familiarity hero, mood slightly improves
        for v in ctx.visible:
            fam = actor.identity.hero_familiarity.get(v.id, 0.0)
            if fam > 0.8:
                actor.mind.mood = min(1.0, actor.mind.mood + 0.005)

        # 8. Memory Decay: prune oldest low-impact memories
        actor.mind.prune_memories(max_entries=50)

    def _deliberation_tactical_phase(self, ctx: AIContext) -> AIState:
        """Phase 3: Deliberation. Choose the next state and plan 'how' (Tactical Intent)."""
        actor = ctx.actor
        
        # Step 5: Goal Deliberation (Goal scoring)
        if actor.mind.ai_state not in self._DECISION_STATES:
            return actor.mind.ai_state

        # Layer 1: Goal Lock — skip re-evaluation if committed
        from src.core.models.enums import EntityRole
        # Heroes and Elites/Bosses have sophisticated locking
        if actor.identity.role == EntityRole.HERO or (actor.identity.role == EntityRole.MOB and actor.identity.tier >= 1):
            if self._goal_evaluator.is_goal_locked(ctx):
                # Refresh tactical hints even if locked
                self._generate_tactical_hints(ctx, actor.mind.ai_state)
                return actor.mind.ai_state

        goal_scores = self._goal_evaluator.evaluate(ctx)
        if not goal_scores:
            return actor.mind.ai_state
            
        # Step 6: Selection with Temperature (Softmax)
        rng_val = self._rng.next_float(
            Domain.AI_DECISION, actor.id, ctx.snapshot.tick + 50)
        
        # Openness drives creativity/randomness
        temp = 0.05 + actor.identity.openness * 0.3
        selected = self._goal_evaluator.select(goal_scores, rng_val, temperature=temp)
        
        if selected:
            old_goal = actor.mind.last_goal

            # Layer 2: Record switch and apply commitment
            if old_goal and old_goal != selected.goal:
                cooldown_ticks = getattr(self._config, 'goal_cooldown_ticks', 5)
                actor.mind.goal_cooldowns[old_goal] = ctx.snapshot.tick + cooldown_ticks
                actor.mind.goal_switch_count += 1
                actor.mind.goal_committed_at = ctx.snapshot.tick

            actor.mind.ai_state = selected.target_state
            actor.mind.last_goal = selected.goal

            # Apply boredom penalty
            current = actor.mind.boredom_multipliers.get(selected.goal, 1.0)
            actor.mind.boredom_multipliers[selected.goal] = max(0.1, current * 0.8)
            
            # 3. Generate Tactical Hints (The "How" - Pillar 3)
            self._generate_tactical_hints(ctx, selected.target_state)
            
        return actor.mind.ai_state

    def _generate_tactical_hints(self, ctx: AIContext, state: AIState) -> None:
        """Pillar 3: Attach tactical guidance to the context."""
        actor = ctx.actor
        hints = ctx.tactical_hints
        
        # Example 1: Kiting for Ranged
        from src.core.models.enums import HeroClass
        ranged_classes = (HeroClass.RANGER, HeroClass.MAGE, HeroClass.SHARPSHOOTER, HeroClass.ARCHMAGE, HeroClass.CASTER)
        if actor.progression.hero_class in ranged_classes:
            hints["skirmish"] = True
            hints["min_dist"] = 3
        
        # Example 2: Flanking / Backstabbing (Melee High-Agi)
        if actor.progression.hero_class in (HeroClass.ROGUE, HeroClass.ASSASSIN):
            if any(v for v in ctx.visible if v.identity.faction == actor.identity.faction):
                hints["flanking"] = True

        # Example 3: Support Logic (Generous Thinking)
        if actor.identity.agreeableness > 0.7:
             # Look for low HP allies
             low_hp_ally = next((a for a in ctx.visible if a.identity.faction == actor.identity.faction and a.stats.combat.hp_ratio < 0.6), None)
             if low_hp_ally:
                 hints["support_target_id"] = low_hp_ally.id


    def _finalization_phase(self, ctx: AIContext, state: AIState) -> tuple[AIState, ActionProposal]:
        """Phase 4: Output. Proposal generation."""
        actor = ctx.actor
        handler = STATE_HANDLERS.get(state, _FALLBACK)
            
        # Step 7: Proposal Construction
        try:
            new_state, proposal = handler.handle(ctx)
            
            # Pillar 3: Hysteresis Force (Grounded)
            # If the evaluator decided to lock, we MUST respect it even if the 
            # handler wants to deviate (unless it's a critical HP override).
            if self._goal_evaluator.is_goal_locked(ctx):
                new_state = state # force back to selected state
                
            # Finalize proposal AI state
            proposal = replace(proposal, new_ai_state=int(new_state))
                
        except Exception as e:
            from src.utils.metrics import SIM_ERRORS_TOTAL
            SIM_ERRORS_TOTAL.labels(exception_type=type(e).__name__, component=f"ai_handler_{state.name.lower()}").inc()
            new_state = AIState.IDLE
            proposal = ActionProposal(actor_id=actor.id, verb=ActionType.REST, reason=f"Handler {state.name} failed")

        # Apply Stance / Action Style
        style = getattr(actor.mind, 'action_style', 'balanced')
        if style != "balanced":
            proposal = replace(proposal, reason=f"[{style}] {proposal.reason}")
            
        # Update heuristics
        if proposal.verb == ActionType.REST:
            actor.consecutive_idle_ticks += 1
        else:
            actor.consecutive_idle_ticks = 0

        return new_state, proposal
