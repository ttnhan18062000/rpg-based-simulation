"""AIBrain — stateless decision engine with Utility AI goal selection.

Pillar-Oriented Architecture (AOA Stabilization):
1.  Read-Only Sensing: AI decision cycle does not mutate the actor state.
2.  Intent Collection: All state changes (memory, mood, pathing) are proposed as metadata.
3.  Phase Decomposition: Explicit perception, appraisal, and deliberation phases.
"""

from __future__ import annotations
import logging
from typing import Any, TYPE_CHECKING

from src.core.models.enums import AIState, ActionType, GoalType, EmotionType
from src.actions.base import (
    ActionProposal, IntentUpdate, MindUpdate, NavigationUpdate, PerceptionUpdate
)
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
        
        from src.ai.goals.registry import register_all_goals
        register_all_goals()
        
        self._goal_evaluator = GoalEvaluator()

    _DECISION_STATES = frozenset({
        AIState.IDLE, AIState.WANDER,
        AIState.HUNT, AIState.COMBAT, AIState.FLEE,
        AIState.RESTING_IN_TOWN, AIState.GUARD_CAMP,
    })

    def decide(self, actor: Entity, snapshot: Snapshot) -> tuple[AIState, ActionProposal]:
        """Run the AI Cognitive Pipeline for *actor*."""
        typed_updates: list[IntentUpdate] = []
        
        # --- Phase 1: Input (Sensory & Perception) ---
        ctx = self._sensory_perception_phase(actor, snapshot, typed_updates)
        
        # --- Phase 2: Internal State (Memory & Appraisal) ---
        self._memory_appraisal_phase(ctx, typed_updates)
        
        # --- Phase 3: Deliberation (Planning) ---
        selected_state = self._deliberation_tactical_phase(ctx, typed_updates)
        
        # --- Phase 4: Output (Proposal) ---
        return self._finalization_phase(ctx, selected_state, typed_updates)

    def _sensory_perception_phase(self, actor: Entity, snapshot: Snapshot, updates: list[IntentUpdate]) -> AIContext:
        """Phase 1: Input. Gather raw data and apply selective attention."""
        # 1. Gather all currently visible entities (Lazy)
        all_visible = Perception.visible_entities(actor, snapshot, actor.spatial.vision_range)
        
        # 2. Selective Attention
        def get_saliency(e):
            dist = actor.spatial.pos.manhattan(e.spatial.pos)
            is_hostile = self._faction_reg.is_hostile(actor.identity.faction, e.identity.faction)
            weight = 2.0 if is_hostile else 1.0
            tier = getattr(e.identity, 'tier', 0)
            if tier > 0:
                weight *= (1.0 + tier)
            return weight / (dist + 1)
            
        ranked = sorted(all_visible, key=get_saliency, reverse=True)
        attention_pool = [e.id for e in ranked[:actor.mind.perception.max_attention_slots]]
        attention_set = set(attention_pool)
        filtered_visible = [e for e in all_visible if e.id in attention_set]
        
        # 3. Create Context with filtered visibility
        ctx = AIContext(
            actor=actor,
            snapshot=snapshot,
            config=self._config,
            rng=self._rng,
            faction_reg=self._faction_reg,
            _visible_override=filtered_visible
        )
        
        # 4. Propose Perception & Navigation Updates
        history = list(actor.mind.navigation.pos_history)
        history.append(actor.spatial.pos)
        if len(history) > 10:
            history.pop(0)
            
        updates.append(PerceptionUpdate(attention_pool=attention_pool))
        updates.append(NavigationUpdate(pos_history=history))
                
        return ctx

    def _memory_appraisal_phase(self, ctx: AIContext, updates: list[IntentUpdate]) -> None:
        """Phase 2: Internal State. Project-specific appraisal and Emotional influence."""
        from src.actions.base import (
            PerceptionUpdate, MindUpdate, NavigationUpdate, ProgressionUpdate
        )
        actor = ctx.actor
        mind = actor.mind
        snapshot = ctx.snapshot
        
        # 1. Memory Management (Forgotten dead and stale entries)
        from src.core.aspects.mind import MemoryRecord
        proposed_memory_updates: dict[int, MemoryRecord] = {}
        stale_updates: dict[int, int] = {}
        memory_remove: list[int] = []
        
        # Current memory and visibility
        current_memory = mind.perception.entity_memory
        current_stale = mind.perception.memory_stale_ticks
        visible_ids = {e.id for e in ctx.visible}
        attention_set = set(mind.perception.attention_pool)
        
        # visibility: items we see now are updated in memory and reset stale ticks
        for e in ctx.visible:
            proposed_memory_updates[e.id] = MemoryRecord(
                entity_id=e.id,
                pos=e.spatial.pos,
                kind=e.kind,
                faction=e.identity.faction.name if hasattr(e.identity.faction, "name") else str(e.identity.faction),
                last_seen_tick=snapshot.tick,
                threat_level=1.0 if self._faction_reg.is_hostile(actor.identity.faction, e.identity.faction) else 0.0
            )
            stale_updates[e.id] = 0
            
        # 2. Aging and Mortality (Genetics)
        prog = actor.progression
        updates.append(ProgressionUpdate(age_ticks_delta=1))
        if prog.age_ticks + 1 >= prog.longevity_limit:
            # Mortal coil reached. Propose immediate death.
            updates.append(ProgressionUpdate(hp_delta=-actor.combat.hp))
            
        # 3. identifying stale and dead entries
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
            threshold = 15
            if eid in attention_set:
                threshold = 30
                
            if new_stale >= threshold:
                memory_remove.append(eid)
            else:
                stale_updates[eid] = new_stale
        
        if proposed_memory_updates or stale_updates or memory_remove:
            updates.append(PerceptionUpdate(
                entity_memory=proposed_memory_updates if proposed_memory_updates else None,
                memory_stale_delta=stale_updates if stale_updates else None,
                memory_remove=memory_remove if memory_remove else None
            ))

        # 2. Stuck detection
        nav_up = next((u for u in updates if isinstance(u, NavigationUpdate)), None)
        history = nav_up.pos_history if nav_up else mind.navigation.pos_history
        
        emotion_set = {}
        if len(history) >= 5 and all(p == history[0] for p in history):
            emotion_set[EmotionType.STUCK] = 1.0
        else:
            emotion_set[EmotionType.STUCK] = 0.0

        # 3. Trauma Zone Dread (Sentiment influence on Panic)
        rid = actor.spatial.current_region_id
        if rid:
            # Discovery logic: first time in a region awards a discovery memory log
            if rid not in mind.narrative.memory_locations:
                from src.core.aspects.mind import MemoryLogEntry, DiscoveryNarrative
                discovery = MemoryLogEntry(
                    tick=snapshot.tick,
                    type="discovery",
                    impact=2.0,
                    details=DiscoveryNarrative(
                        location_id=rid,
                        location_name=rid, # Best effort mapping
                        rarity="common"
                    )
                )
                updates.append(PerceptionUpdate(
                    memory_log_add=[discovery],
                    memory_locations_set={rid: 2.0} # Sentiment boost for discovery
                ))
                
            # AOA Phase 7: Locational sentiment influence on Panic
            sentiment = mind.narrative.memory_locations.get(rid, 0.0)
            if sentiment < -0.5:
                # Additive panic for high-trauma regions
                updates.append(MindUpdate(emotion_delta={EmotionType.PANIC: 0.05}))

        # 4. HP-Based Appraisal (Panic Increment)
        from src.ai.states.base import should_flee
        if should_flee(actor, ctx.config):
            updates.append(MindUpdate(emotion_delta={EmotionType.PANIC: 0.1}))

        # 5. Memory Pruning (Heuristic management)
        # Note: we call it here to keep the context clean; ActionSystem will apply final limit.
        actor.mind.prune_memories()

        if emotion_set:
            updates.append(MindUpdate(emotion_set=emotion_set))

    def _deliberation_tactical_phase(self, ctx: AIContext, updates: list[IntentUpdate]) -> AIState:
        """Phase 3: Deliberation. Choose the next state."""
        actor = ctx.actor
        
        if actor.mind.decision.ai_state not in self._DECISION_STATES:
            return actor.mind.decision.ai_state

        # Use GoalEvaluator
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
                updates.append(MindUpdate(boredom_delta=boredom_updates))
            return actor.mind.decision.ai_state
            
        from src.core.models.enums import Domain
        rng_val = self._rng.next_float(Domain.AI_DECISION, actor.id, ctx.snapshot.tick + 50)
        temp = 0.05 + actor.identity.openness * 0.3
        selected = self._goal_evaluator.select(goal_scores, rng_val, temperature=temp)
        
        if selected:
            # 2. Apply new boredom for selected goal
            current_val = boredom_updates.get(selected.goal, current_boredom.get(selected.goal, 1.0))
            boredom_updates[selected.goal] = max(0.1, current_val * 0.8)
            
            updates.append(MindUpdate(
                goal_scores={s.goal: s.score for s in goal_scores},
                last_goal=selected.goal,
                goal_committed_at=ctx.snapshot.tick if selected.goal != actor.mind.decision.last_goal else None,
                boredom_delta=boredom_updates,
                new_ai_state=int(selected.target_state)
            ))
            
            # Generate hints for the final destination
            hints = self._generate_tactical_hints(ctx, selected.target_state)
            ctx.tactical_hints.update(hints) # Still minor mutation, but isolated to Brain finalization
            return selected.target_state
            
        if boredom_updates:
            updates.append(MindUpdate(boredom_delta=boredom_updates))
        return actor.mind.decision.ai_state

    def _generate_tactical_hints(self, ctx: AIContext, state: AIState) -> dict[str, Any]:
        """Pillar 3: Produce tactical guidance for the selected state."""
        actor = ctx.actor
        hints = {}
        
        from src.core.models.enums import HeroClass
        ranged_classes = (HeroClass.RANGER, HeroClass.MAGE, HeroClass.SHARPSHOOTER, HeroClass.ARCHMAGE, HeroClass.CASTER)
        if actor.progression.hero_class in ranged_classes:
            hints["skirmish"] = True
            hints["min_dist"] = 3
        
        if actor.identity.agreeableness > 0.7:
             low_hp_ally = next((a for a in ctx.visible if a.identity.faction == actor.identity.faction and a.combat.hp_ratio < 0.6), None)
             if low_hp_ally:
                 hints["support_target_id"] = low_hp_ally.id
        return hints

    def _finalization_phase(self, ctx: AIContext, state: AIState, updates: list[IntentUpdate]) -> tuple[AIState, ActionProposal]:
        """Phase 4: Output. Proposal generation."""
        actor = ctx.actor
        handler = STATE_HANDLERS.get(state, _FALLBACK)
            
        try:
            new_state, proposal = handler.handle(ctx)
            
            if self._goal_evaluator.is_goal_locked(ctx):
                new_state = state 
            
            # Combined typed updates
            final_typed = list(updates)
            if proposal.updates:
                final_typed.extend(proposal.updates)
            
            # Update consecutive_idle_ticks heuristic (authoritative proposal)
            if proposal.verb == ActionType.REST:
                new_idle = actor.mind.decision.consecutive_idle_ticks + 1
            else:
                new_idle = 0
            final_typed.append(MindUpdate(consecutive_idle_ticks=new_idle))
                
            # 3. Apply Action Style influence (AOA Stabilization: Tactical flavoring)
            final_reason = proposal.reason
            style = actor.mind.decision.action_style
            if style and style != "balanced":
                final_reason = f"[{style.upper()}] {final_reason}"
                
            # Finalize proposal AI state via model_copy (ActionProposal is a SimulationModel)
            proposal = proposal.model_copy(update={
                "new_ai_state": int(new_state),
                "updates": final_typed,
                "reason": final_reason
            })
            
            return new_state, proposal
                
        except Exception as e:
            logger.error("AI: Decision error for %s (%s): %s", actor.identity.display_name, state.name, e, exc_info=True)
            return state, ActionProposal(actor_id=actor.id, verb=ActionType.REST, reason="Decision Error Fallback")
