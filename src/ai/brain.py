"""AIBrain — stateless decision engine with Utility AI goal selection.

Pillar-Oriented Architecture (AOA Stabilization):
1.  Read-Only Sensing: AI decision cycle does not mutate the actor state.
2.  Intent Collection: All state changes (memory, mood, pathing) are proposed as metadata.
3.  Phase Decomposition: Explicit perception, appraisal, and deliberation phases.
"""

from __future__ import annotations
import logging
from dataclasses import replace
from typing import Any, TYPE_CHECKING

from src.core.models.enums import AIState, Domain, ActionType
from src.actions.base import ActionProposal, MindUpdate
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
logger = logging.getLogger(__name__)

class AIBrain:
    """Dispatches entity AI decisions based on their current state.

    Stateless and Side-Effect Free — safe to parallelize.
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

    _DECISION_STATES = frozenset({
        AIState.IDLE, AIState.WANDER,
        AIState.HUNT, AIState.COMBAT, AIState.FLEE,
        AIState.RESTING_IN_TOWN, AIState.GUARD_CAMP,
    })

    def decide(self, actor: Entity, snapshot: Snapshot) -> tuple[AIState, ActionProposal]:
        """Run the AI Cognitive Pipeline for *actor*."""
        mind_updates: dict[str, Any] = {}
        
        # --- Phase 1: Input (Sensory & Perception) ---
        ctx = self._sensory_perception_phase(actor, snapshot, mind_updates)
        
        # --- Phase 2: Internal State (Memory & Appraisal) ---
        self._memory_appraisal_phase(ctx, mind_updates)
        
        # --- Phase 3: Deliberation (Planning) ---
        selected_state = self._deliberation_tactical_phase(ctx, mind_updates)
        
        # --- Phase 4: Output (Proposal) ---
        return self._finalization_phase(ctx, selected_state, mind_updates)

    def _sensory_perception_phase(self, actor: Entity, snapshot: Snapshot, updates: dict[str, Any]) -> AIContext:
        """Phase 1: Input. Gather raw data and apply selective attention."""
        ctx = AIContext(
            actor=actor,
            snapshot=snapshot,
            config=self._config,
            rng=self._rng,
            faction_reg=self._faction_reg,
        )
        
        # 1. Update Position History (Proposed)
        history = list(actor.mind.navigation.pos_history)
        history.append(actor.spatial.pos)
        if len(history) > 5:
            history.pop(0)
        updates["pos_history"] = history
            
        # 2. Selective Attention
        visible = ctx.visible
        def get_saliency(e):
            dist = actor.spatial.pos.manhattan(e.spatial.pos)
            is_hostile = self._faction_reg.is_hostile(actor.identity.faction, e.identity.faction)
            weight = 2.0 if is_hostile else 1.0
            tier = getattr(e.identity, 'tier', 0)
            if tier > 0:
                weight *= (1.0 + tier)
            return weight / (dist + 1)
            
        ranked = sorted(visible, key=get_saliency, reverse=True)
        attention_pool = [e.id for e in ranked[:actor.mind.perception.max_attention_slots]]
        updates["attention_pool"] = attention_pool
        
        # Filter ctx.visible for this tick's cognitive pipeline
        attention_set = set(attention_pool)
        ctx._visible = [e for e in visible if e.id in attention_set]
                
        return ctx

    def _memory_appraisal_phase(self, ctx: AIContext, updates: dict[str, Any]) -> None:
        """Phase 2: Internal State. Project-specific appraisal and Emotional influence."""
        actor = ctx.actor
        mind = actor.mind
        snapshot = ctx.snapshot
        
        # 1. Memory Management (Forgotten dead and stale entries)
        proposed_memory_updates = {}
        stale_updates = {}
        memory_remove = []
        
        # Current memory and visibility
        current_memory = mind.perception.entity_memory
        current_stale = mind.perception.memory_stale_ticks
        visible_ids = {e.id for e in ctx.visible}
        attention_set = set(mind.perception.attention_pool)
        
        # visibility: items we see now are updated in memory and reset stale ticks
        for e in ctx.visible:
            proposed_memory_updates[e.id] = e.spatial.pos
            stale_updates[e.id] = 0
            
        # identifying stale and dead entries
        from src.ai.states.base import get_dead_memory_ids
        dead_ids = get_dead_memory_ids(actor, snapshot)
        memory_remove.extend(dead_ids)
        
        # decay: entities in memory but not currently visible
        for eid in current_memory:
            if eid in visible_ids or eid in dead_ids:
                continue
                
            # If not visible, increment stale counter
            new_stale = current_stale.get(eid, 0) + 1
            
            # If too stale, forget it (Threshold: 15 ticks)
            # Higher threshold for important entities (like heroes if the actor is a boss)
            threshold = 15
            if eid in attention_set: # if it was in attention, keep it longer
                threshold = 30
                
            if new_stale >= threshold:
                memory_remove.append(eid)
            else:
                stale_updates[eid] = new_stale
        
        updates["memory_update"] = proposed_memory_updates
        updates["memory_stale_update"] = stale_updates
        updates["memory_remove"] = memory_remove

        # 2. Stuck detection
        history = updates.get("pos_history", mind.navigation.pos_history)
        if len(history) >= 5 and all(p == history[0] for p in history):
            updates["emotion_stuck"] = 1.0
        else:
            updates["emotion_stuck"] = 0.0

        # 3. Trauma Zone Dread (Sentiment influence on Panic)
        rid = actor.spatial.current_region_id
        if rid:
            sentiment = mind.narrative.memory_locations.get(rid, 0.0)
            if sentiment < -0.5:
                # Feeling dread in bad regions: +0.05 panic per tick
                current_panic = mind.emotion.emotional_state.get("panic", 0.0)
                updates["emotion_panic"] = min(1.0, current_panic + 0.05)

        # Physical Maintenance (Aging)
        updates["age_increment"] = 1


    def _deliberation_tactical_phase(self, ctx: AIContext, updates: dict[str, Any]) -> AIState:
        """Phase 3: Deliberation. Choose the next state."""
        actor = ctx.actor
        
        if actor.mind.decision.ai_state not in self._DECISION_STATES:
            return actor.mind.decision.ai_state

        # Use GoalEvaluator (which should also be read-only)
        if self._goal_evaluator.is_goal_locked(ctx):
            self._generate_tactical_hints(ctx, actor.mind.decision.ai_state)
            return actor.mind.decision.ai_state

        # 1. Decay existing boredom (Recovery)
        current_boredom = dict(actor.mind.decision.boredom_multipliers)
        boredom_updates = {}
        for gname, val in current_boredom.items():
            if val < 1.0:
                boredom_updates[gname] = min(1.0, val + 0.02)
        
        goal_scores = self._goal_evaluator.evaluate(ctx)
        if not goal_scores:
            if boredom_updates:
                updates["boredom_update"] = boredom_updates
            return actor.mind.decision.ai_state
            
        rng_val = self._rng.next_float(Domain.AI_DECISION, actor.id, ctx.snapshot.tick + 50)
        temp = 0.05 + actor.identity.openness * 0.3
        selected = self._goal_evaluator.select(goal_scores, rng_val, temperature=temp)
        
        if selected:
            # 2. Apply new boredom for selected goal
            current_val = boredom_updates.get(selected.goal, current_boredom.get(selected.goal, 1.0))
            boredom_updates[selected.goal] = max(0.1, current_val * 0.8)
            
            # Phase 5: Emit typed MindUpdate
            updates["updates"] = [MindUpdate(
                goal_scores={s.goal: s.score for s in goal_scores},
                last_goal=selected.goal,
                boredom_delta=boredom_updates,
                new_ai_state=int(selected.target_state)
            )]
            
            # Legacy fields for backward compatibility (optional but keeping for now)
            updates["boredom_update"] = boredom_updates
            updates["selected_goal"] = selected.goal
            updates["last_goal"] = selected.goal
            updates["goal_scores"] = {s.goal: s.score for s in goal_scores}
            updates["target_ai_state"] = selected.target_state
            
            self._generate_tactical_hints(ctx, selected.target_state)
            return selected.target_state
            
        if boredom_updates:
            updates["boredom_update"] = boredom_updates
        return actor.mind.decision.ai_state

    def _generate_tactical_hints(self, ctx: AIContext, state: AIState) -> None:
        """Pillar 3: Attach tactical guidance to the context."""
        actor = ctx.actor
        hints = ctx.tactical_hints
        
        from src.core.models.enums import HeroClass
        ranged_classes = (HeroClass.RANGER, HeroClass.MAGE, HeroClass.SHARPSHOOTER, HeroClass.ARCHMAGE, HeroClass.CASTER)
        if actor.progression.hero_class in ranged_classes:
            hints["skirmish"] = True
            hints["min_dist"] = 3
        
        if actor.identity.agreeableness > 0.7:
             low_hp_ally = next((a for a in ctx.visible if a.identity.faction == actor.identity.faction and a.combat.hp_ratio < 0.6), None)
             if low_hp_ally:
                 hints["support_target_id"] = low_hp_ally.id

    def _finalization_phase(self, ctx: AIContext, state: AIState, updates: dict[str, Any]) -> tuple[AIState, ActionProposal]:
        """Phase 4: Output. Proposal generation."""
        actor = ctx.actor
        handler = STATE_HANDLERS.get(state, _FALLBACK)
            
        try:
            # The handler itself must also be side-effect free (AOA Stabilization)
            new_state, proposal = handler.handle(ctx)
            
            if self._goal_evaluator.is_goal_locked(ctx):
                new_state = state 
                
            # Merge context updates into proposal metadata
            final_metadata = dict(updates)
            typed_updates = final_metadata.pop("updates", [])
            
            if proposal.intent_metadata:
                final_metadata.update(proposal.intent_metadata)
            
            # Merge typed updates
            final_typed = list(typed_updates)
            if proposal.updates:
                final_typed.extend(proposal.updates)
                
            proposal = replace(proposal, 
                               new_ai_state=final_metadata.get("target_ai_state") or int(new_state), 
                               intent_metadata=final_metadata,
                               updates=final_typed)
            return new_state, proposal
                
        except Exception as e:
            logger.error("AI: Decision error for %s (%s): %s", actor.identity.display_name, state.name, e, exc_info=True)
            return state, ActionProposal(actor_id=actor.id, verb=ActionType.REST, reason="Decision Error Fallback")
