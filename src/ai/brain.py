"""AIBrain — stateless decision engine with Utility AI goal selection.

Pillar-Oriented Architecture (AOA Stabilization):
1.  Read-Only Sensing: AI decision cycle does not mutate the actor state.
2.  Intent Collection: All state changes (memory, mood, pathing) are proposed as metadata.
3.  Phase Decomposition: Explicit perception, appraisal, and deliberation phases.
"""

from __future__ import annotations
import logging
from typing import Any, TYPE_CHECKING

from src.core.models.enums import AIState, ActionType, GoalType, EmotionType, Domain
from src.actions.base import (
    ActionProposal, IntentUpdate, MindUpdate, NavigationUpdate, PerceptionUpdate, ProgressionUpdate
)
from src.core.aspects.mind import DecisionDriver, MemoryRecord, MemoryLogEntry
from src.ai.goals import GoalEvaluator
from src.ai.perception import Perception
from src.ai.states import AIContext, STATE_HANDLERS, IdleHandler
from src.ai.beliefs import BeliefService
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
        # Subjective Refresh: update/create BeliefRecords for visible entities
        current_memory = actor.mind.perception.entity_memory
        proposed_beliefs: dict[int, Any] = {}
        for e in ctx.visible:
            belief = BeliefService.refresh_belief_from_observation(actor, e, snapshot.tick)
            proposed_beliefs[e.id] = belief

        history = list(actor.mind.navigation.pos_history)
        history.append(actor.spatial.pos)
        if len(history) > 10:
            history.pop(0)
            
        updates.append(PerceptionUpdate(
            attention_pool=attention_pool,
            entity_memory=proposed_beliefs if proposed_beliefs else None
        ))
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
        
        # 1. Subjective Decay: unobserved entities become stale and lose confidence
        BeliefService.decay_stale_beliefs(actor, snapshot.tick)
        
        # Memory Management (Pruning stale entries)
        memory_remove: list[int] = []
        
        # Current memory and visibility
        current_memory = mind.perception.entity_memory
        visible_ids = {e.id for e in ctx.visible}
        attention_set = set(mind.perception.attention_pool)
            
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
        
        # 4. [PHASE 2] Social Appraisal
        from src.core.logic.social_appraisal import SocialAppraisalService
        from src.core.aspects.mind import SocialStance
        
        # Calculate subjective biases based on visible entities and global registry
        social_biases = SocialAppraisalService.calculate_social_motives(
            actor, list(ctx.visible), snapshot.social_registry
        )
        
        updates.append(MindUpdate(
            social_update=SocialStance(
                known_bonds=mind.social.known_bonds,
                faction_standing=mind.social.faction_standing,
                social_utility_biases=social_biases
            )
        ))

        if memory_remove:
            updates.append(PerceptionUpdate(
                memory_remove=memory_remove
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
                
            # AOA Phase 7: Locational sentiment influence on DREAD/JOY
            sentiment = mind.narrative.memory_locations.get(rid, 0.0)
            if sentiment < -0.5:
                # Additive dread for high-trauma regions
                updates.append(MindUpdate(emotion_delta={EmotionType.DREAD: 0.05}))
            elif sentiment > 1.5:
                # Additive joy for sanctuary regions (discovery boost)
                updates.append(MindUpdate(emotion_delta={EmotionType.JOY: 0.02}))

        # 4. HP-Based Appraisal (Panic Increment)
        from src.ai.states.base import should_flee
        if should_flee(actor, ctx.config):
            updates.append(MindUpdate(emotion_delta={EmotionType.PANIC: 0.1}))

        # 5. [PHASE 1] Subjective Motive Appraisal (Personality + Long-term Motives)
        last_appraisal = mind.decision.last_appraisal_tick
        if snapshot.tick - last_appraisal >= 10: # Throttled processing
            from src.core.aspects.mind import PersonalMotive
            pers = mind.decision.personality
            
            # 1. Update Motive Progress/Frustration (naive for now)
            # Check if current goal matches any motive 'kind'
            current_goal = mind.decision.last_goal
            updated_motives: list[PersonalMotive] = []
            for m in mind.decision.motives:
                new_m = m.model_copy()
                if current_goal and m.kind.split("_")[-1] in current_goal.name.lower():
                    new_m.progress = min(1.0, m.progress + 0.05)
                    new_m.frustration = max(0.0, m.frustration - 0.1)
                else:
                    new_m.frustration = min(1.0, m.frustration + 0.01)
                updated_motives.append(new_m)
            
            # 2. Calculate utility biases for deliberation
            biases = {g: 1.0 for g in GoalType}
            for m in updated_motives:
                if not m.active: continue
                # Map motive kind to GoalType (heuristic)
                target_goal = None
                if "wealth" in m.kind or "loot" in m.kind: target_goal = GoalType.LOOT
                if "strength" in m.kind or "combat" in m.kind: target_goal = GoalType.COMBAT
                if "safety" in m.kind: target_goal = GoalType.FLEE
                if "explore" in m.kind: target_goal = GoalType.EXPLORE
                
                if target_goal:
                    # Priority + frustration increases bias
                    biases[target_goal] *= (1.0 + (m.priority * 0.2) + (m.frustration * 0.5))
            
            # 3. Apply Personality and Social Baseline Biases
            driver_details: list[DecisionDriver] = []
            
            p_agg = 0.5 + pers.aggression
            biases[GoalType.COMBAT] *= p_agg
            driver_details.append(DecisionDriver(kind="personality", label="Aggression", weight=p_agg))
            
            p_greed = 0.5 + pers.greed
            biases[GoalType.LOOT] *= p_greed
            driver_details.append(DecisionDriver(kind="personality", label="Greed", weight=p_greed))
            
            p_caution = 0.5 + pers.caution
            biases[GoalType.FLEE] *= p_caution
            biases[GoalType.REST] *= p_caution
            driver_details.append(DecisionDriver(kind="personality", label="Caution", weight=p_caution))
            
            p_curiosity = 0.5 + pers.curiosity
            biases[GoalType.EXPLORE] *= p_curiosity
            driver_details.append(DecisionDriver(kind="personality", label="Curiosity", weight=p_curiosity))
            
            # [PHASE 2] Apply Social Biases from appraisal phase
            for gtype, s_bias in social_biases.items():
                if s_bias != 0:
                    weight = 1.0 + s_bias
                    biases[gtype] *= weight
                    driver_details.append(DecisionDriver(kind="social", label=f"Social Bias: {gtype.name}", weight=weight))
            
            # [PHASE 3] Apply Emotional Biases
            emo = mind.emotion
            if emo.dread > 0.3:
                weight = 1.0 + emo.dread
                biases[GoalType.FLEE] *= weight
                biases[GoalType.EXPLORE] *= (1.0 - (emo.dread * 0.5))
                driver_details.append(DecisionDriver(kind="emotion", label="Dread", weight=weight))
            if emo.joy > 0.3:
                weight = 1.0 + (emo.joy * 0.3)
                biases[GoalType.EXPLORE] *= weight
                biases[GoalType.SOCIAL] *= (1.0 + (emo.joy * 0.2))
                driver_details.append(DecisionDriver(kind="emotion", label="Joy", weight=weight))
            if emo.panic > 0.5:
                biases[GoalType.FLEE] *= 2.0
                driver_details.append(DecisionDriver(kind="emotion", label="Panic", weight=2.0))
            
            # [PHASE 3] Biological Need Biases (Authoritative)
            from src.core.logic.routine_service import RoutineService
            routine_biases = RoutineService.calculate_routine_biases(actor, snapshot.hour)
            for gtype, weight in routine_biases.items():
                biases[gtype] *= weight
                if weight > 1.2:
                    driver_details.append(DecisionDriver(kind="biological", label=f"Routine: {gtype.name}", weight=weight))
                elif weight < 0.8:
                    driver_details.append(DecisionDriver(kind="biological", label=f"Routine Penalty: {gtype.name}", weight=weight))
            
            # [STAGE 5] Long-Term Memory and Narrative Biasing
            log = mind.narrative.memory_log
            if log:
                # 1. Trauma Avoidance (Recent trauma from specific kinds)
                recent_trauma = [m for m in log[-10:] if m.type == "trauma"]
                for t in recent_trauma:
                    if hasattr(t.details, "target_kind"):
                        # Heuristic: if we took a lot of damage from a 'goblin', be more cautious
                        biases[GoalType.FLEE] *= (1.0 + t.impact * 0.2)
                        biases[GoalType.COMBAT] *= (1.0 - t.impact * 0.1)
                
                # 2. Combat Confidence (Recent victories)
                recent_kills = [m for m in log[-10:] if m.type == "combat" and getattr(m.details, "was_fatal", False)]
                if recent_kills:
                    biases[GoalType.COMBAT] *= (1.0 + len(recent_kills) * 0.15)
            
            # [STAGE 5] Region Fatigue (Territory History)
            rid = actor.spatial.current_region_id
            if rid:
                fatigue = mind.narrative.region_fatigue.get(rid, 0.0)
                if fatigue > 0.6:
                    # High fatigue: desire to return to town/safety
                    biases[GoalType.EXPLORE] *= (1.0 - (fatigue - 0.6) * 2.0) # 0.6 to 1.0 -> 0.0 to 0.8 reduction
                    biases[GoalType.REST] *= (1.0 + fatigue)
                    biases[GoalType.SLEEP] *= (1.0 + fatigue * 0.5)
            
            # 4. Generate Decision Drivers (Explainability)
            drivers: list[str] = []
            if pers.aggression > 0.7: driver_details.append(DecisionDriver(kind="personality", label="Aggressive nature", weight=1.2))
            if pers.greed > 0.7: driver_details.append(DecisionDriver(kind="personality", label="Greedy instincts", weight=1.1))
            if pers.caution > 0.7: driver_details.append(DecisionDriver(kind="personality", label="Cautious mindset", weight=1.3))
            if pers.curiosity > 0.7: driver_details.append(DecisionDriver(kind="personality", label="Curious explorer", weight=1.1))
            
            # Active Motives and Region Awareness
            rid = actor.spatial.current_region_id
            if rid and mind.narrative.region_fatigue.get(rid, 0.0) > 0.7:
                driver_details.append(DecisionDriver(kind="narrative", label=f"Familiar with {rid}", weight=1.0))
            if any(m.type == "trauma" for m in mind.narrative.memory_log[-5:]):
                driver_details.append(DecisionDriver(kind="narrative", label="Recent trauma", weight=1.2))
            if any(m.type == "combat" and getattr(m.details, "was_fatal", False) for m in mind.narrative.memory_log[-5:]):
                driver_details.append(DecisionDriver(kind="narrative", label="Confident from victories", weight=1.3))
            
            # Social Appraisal and Relationship Influence
            for gtype, s_bias in social_biases.items():
                if s_bias > 0.5:
                    if gtype == GoalType.FLEE: driver_details.append(DecisionDriver(kind="social", label="Socially wary / Hostile reputation", weight=1.2))
                    if gtype == GoalType.SOCIAL or gtype == GoalType.GUARD: driver_details.append(DecisionDriver(kind="social", label="Strong social bond", weight=1.3))
                    if gtype == GoalType.COMBAT: driver_details.append(DecisionDriver(kind="social", label="Social rivalry / Outcast threat", weight=1.1))

            # Emotional State and Stress Influence
            if emo.dread > 0.6: driver_details.append(DecisionDriver(kind="emotion", label="Traumatized by area / Lingering dread", weight=1.4))
            if emo.joy > 0.6: driver_details.append(DecisionDriver(kind="emotion", label="Feeling joyful / Safe haven", weight=1.1))
            if emo.panic > 0.7: driver_details.append(DecisionDriver(kind="emotion", label="Blind panic", weight=2.0))

            # Physiological Needs and Biological Drivers
            for gtype, weight in routine_biases.items():
                if weight > 1.2:
                    driver_details.append(DecisionDriver(kind="biological", label=f"Routine: {gtype.name}", weight=weight))
                elif weight < 0.8:
                    driver_details.append(DecisionDriver(kind="biological", label=f"Routine Penalty: {gtype.name}", weight=weight))

            for m in updated_motives:
                if m.active and m.frustration > 0.5:
                    driver_details.append(DecisionDriver(kind="motive", label=f"Motivated: {m.kind.replace('_', ' ')}", weight=1.0 + m.frustration * 0.5))
            
            # Cognitive Decay and State Normalization
            decay = {
                EmotionType.PANIC: -0.05,
                EmotionType.DREAD: -0.02,
                EmotionType.JOY: -0.01,
                EmotionType.STUCK: -0.2
            }
            updates.append(MindUpdate(emotion_delta=decay))

            # Belief-based drivers (Top saliency)
            high_threats = [b for b in mind.perception.entity_memory.values() if b.threat.overall > 0.7 and b.confidence > 0.5]
            if high_threats:
                driver_details.append(DecisionDriver(kind="belief", label=f"Sensed danger: {len(high_threats)} threats", weight=1.5))
            
            low_conf = [b for b in mind.perception.entity_memory.values() if b.confidence < 0.3 and b.stale_ticks > 0]
            if low_conf:
                driver_details.append(DecisionDriver(kind="belief", label="Wary: uncertain of targets", weight=1.1))
            
            updates.append(MindUpdate(
                motives=updated_motives,
                motive_utility_biases=biases,
                decision_drivers=[d.label for d in driver_details],
                driver_details=driver_details,
                last_appraisal_tick=snapshot.tick
            ))

        # 6. Memory Pruning (Heuristic management)
        # Note: This is now handled authoritatively in ActionSystem post-resolution.

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
            
        rng_val = self._rng.next_float(Domain.AI_DECISION, actor.id, ctx.snapshot.tick + 50)
        pers = actor.mind.decision.personality
        # Cautious entities are less random (lower temp), Curious/Aggressive ones more so?
        # Actually, let's use caution as a steadiness factor.
        temp = 0.05 + (1.0 - pers.caution) * 0.4
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
        
        if actor.mind.decision.personality.loyalty > 0.7:
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
