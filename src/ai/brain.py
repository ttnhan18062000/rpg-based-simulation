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
    ActionProposal, IntentUpdate, MindUpdate, NavigationUpdate, PerceptionUpdate, 
    ProgressionUpdate, StrategicUpdate
)
from src.core.aspects.mind import DecisionDriver, MemoryRecord, MemoryLogEntry
from src.ai.goals import GoalEvaluator
from src.ai.perception import Perception
from src.ai.states import AIContext, STATE_HANDLERS, IdleHandler
from src.ai.beliefs import BeliefService
from src.core.gameplay.faction import FactionRegistry
from src.ai.strategy.candidate_builder import StrategicCandidateBuilder
from src.ai.strategy.strategic_evaluator import StrategicEvaluator
from src.ai.strategy.objective_to_goal_mapper import ObjectiveToGoalMapper
from src.core.models.strategy import ObjectiveKind # [PHASE 3]

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

    __slots__ = (
        "_config", "_rng", "_faction_reg", "_goal_evaluator",
        "_strat_builder", "_strat_evaluator", "_obj_mapper"
    )

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
        self._strat_builder = StrategicCandidateBuilder()
        self._strat_evaluator = StrategicEvaluator()
        self._obj_mapper = ObjectiveToGoalMapper()

    _DECISION_STATES = frozenset({
        AIState.IDLE, AIState.WANDER,
        AIState.HUNT, AIState.COMBAT, AIState.FLEE,
        AIState.RESTING_IN_TOWN, AIState.GUARD_CAMP,
    })

    def decide(self, actor: Entity, snapshot: Snapshot) -> tuple[AIState, ActionProposal]:
        """Run the AI Cognitive Pipeline for *actor*."""
        typed_updates: list[IntentUpdate] = []
        
        # --- Phase 1: Input (Sensory & Perception) ---
        ctx, social_biases = self._sensory_perception_phase(actor, snapshot, typed_updates)
        
        # --- Phase 2: Strategic Appraisal (Macro-Interest) [phase_2_stage_1-5] ---
        strategic_objective = self._strategic_appraisal_phase(actor, snapshot, typed_updates, ctx)
        
        # --- Phase 3: Internal State (Memory & Appraisal) ---
        self._memory_appraisal_phase(ctx, typed_updates, social_biases, strategic_objective)
        
        # --- Phase 4: Deliberation (Planning) ---
        selected_state = self._deliberation_tactical_phase(ctx, typed_updates)
        
        # --- Phase 5: Output (Proposal) ---
        return self._finalization_phase(ctx, selected_state, typed_updates)

    def _sensory_perception_phase(self, actor: Entity, snapshot: Snapshot, updates: list[IntentUpdate]) -> tuple[AIContext, dict[GoalType, float]]:
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

        # 5. [PHASE 2] Social Appraisal
        from src.core.logic.social_appraisal import SocialAppraisalService
        from src.core.aspects.mind import SocialStance
        
        social_biases = SocialAppraisalService.calculate_social_motives(
            actor, list(ctx.visible), snapshot.social_registry
        )
        
        # 6. [PHASE 3] Cluster/Clique Coordination Bias
        if actor.identity.cluster_id:
            my_faction = int(actor.identity.faction)
            my_cluster = actor.identity.cluster_id
            
            cluster_allies = [e for e in ctx.visible 
                             if int(e.identity.faction) == my_faction 
                             and getattr(e.identity, 'cluster_id', None) == my_cluster]
            
            if cluster_allies:
                for ally in cluster_allies:
                    ally_goal = ally.mind.decision.last_goal
                    if ally_goal is not None:
                        social_biases[ally_goal] = social_biases.get(ally_goal, 0.0) + 0.15
                
                # Normalize and limit social biases from clusters (cap social consensus)
                for gtype in list(social_biases.keys()):
                    social_biases[gtype] = min(0.6, social_biases[gtype])

        updates.append(MindUpdate(
            social_update=SocialStance(
                known_bonds=actor.mind.social.known_bonds,
                faction_standing=actor.mind.social.faction_standing,
                social_utility_biases=social_biases
            )
        ))
                
        return ctx, social_biases

    def _strategic_appraisal_phase(self, actor: Entity, snapshot: Snapshot, updates: list[IntentUpdate], ctx: AIContext) -> str | None:
        """Phase 2: Strategic Appraisal. Select core commitment and derive objectives."""
        # 1. Slice [phase_2_stage_4]
        candidates = self._strat_builder.build_decision_slice(ctx)
        
        # 2. Evaluate [phase_2_stage_2, phase_2_stage_3, phase_2_stage_7]
        decision = self._strat_evaluator.evaluate(ctx, candidates)
        
        # 3. Apply updates if any changes occurred [phase_2_stage_8]
        up = decision.updates
        
        # 4. Attach drivers for observability [phase_2_stage_9]
        if decision.selected_id:
             up.strategic_drivers.append(DecisionDriver(
                 kind="strategic",
                 label=f"Commitment: {decision.selected_kind}",
                 weight=1.0, # Placeholder for ranking score
                 description=decision.reason
             ))
             
        has_changes = any([
            up.directives_add, up.directives_remove,
            up.projects_add_or_update, up.projects_remove,
            up.concerns_add_or_update, up.concerns_remove,
            up.obligations_add_or_update, up.obligations_remove,
            up.contracts_add_or_update, up.contracts_remove,
            up.leads_add_or_update, up.leads_remove,
            up.current_project_id is not None,
            up.current_objective_id is not None,
            up.interrupted_project_id is not None,
            up.strategic_drivers
        ])
        
        if has_changes:
             updates.append(up)
             
        # Return objective ID (could be empty string if none)
        return up.current_objective_id or actor.mind.strategic.current_objective_id

    def _memory_appraisal_phase(self, ctx: AIContext, updates: list[IntentUpdate], social_biases: dict[GoalType, float], strategic_objective_id: str | None = None) -> None:
        """Phase 1 Stage 8: Internal State (Strategic Knowledge). Project-specific appraisal and Emotional influence."""
        from src.actions.base import (
            PerceptionUpdate, MindUpdate, NavigationUpdate, ProgressionUpdate
        )
        actor = ctx.actor
        mind = actor.mind
        snapshot = ctx.snapshot
        
        # 1. Subjective Decay
        BeliefService.decay_stale_beliefs(actor, snapshot.tick)
        
        # Memory Management
        memory_remove: list[int] = []
        from src.ai.states.base import get_dead_memory_ids
        dead_ids = get_dead_memory_ids(actor, snapshot)
        memory_remove.extend(dead_ids)
            
        # 2. Aging and Mortality
        prog = actor.progression
        updates.append(ProgressionUpdate(age_ticks_delta=1))
        if prog.age_ticks + 1 >= prog.longevity_limit:
            updates.append(ProgressionUpdate(hp_delta=-actor.combat.hp))

        if memory_remove:
            updates.append(PerceptionUpdate(memory_remove=memory_remove))

        # 3. Stuck detection
        nav_up = next((u for u in updates if isinstance(u, NavigationUpdate)), None)
        history = nav_up.pos_history if nav_up else mind.navigation.pos_history
        
        emotion_set = {}
        if len(history) >= 5 and all(p == history[0] for p in history):
            emotion_set[EmotionType.STUCK] = 1.0
        else:
            emotion_set[EmotionType.STUCK] = 0.0

        # 4. Regional & Local Trauma (Scars) [PHASE 4 STAGE 3]
        rid = actor.spatial.current_region_id
        if rid:
            # Discovery narrative (Existing)
            if rid not in mind.narrative.memory_locations:
                from src.core.aspects.mind import MemoryLogEntry, DiscoveryNarrative
                discovery = MemoryLogEntry(
                    tick=snapshot.tick,
                    type="discovery",
                    impact=2.0,
                    details=DiscoveryNarrative(location_id=rid, location_name=rid, rarity="common")
                )
                updates.append(PerceptionUpdate(memory_log_add=[discovery], memory_locations_set={rid: 2.0}))
                
            # Sentiment from Memory (Existing)
            sentiment = mind.narrative.memory_locations.get(rid, 0.0)
            if sentiment < -0.5:
                updates.append(MindUpdate(emotion_delta={EmotionType.DREAD: 0.05}))
            elif sentiment > 1.5:
                updates.append(MindUpdate(emotion_delta={EmotionType.JOY: 0.02}))
                
            # NEW: Subjective appraisal of Regional Danger
            region_metric = snapshot.region_consequence_registry.get(rid)
            if region_metric and region_metric.danger_level > 0.3:
                # Dangerous regions spike DREAD based on caution
                dread_spike = region_metric.danger_level * 0.1 * mind.decision.personality.caution
                updates.append(MindUpdate(emotion_delta={EmotionType.DREAD: dread_spike}))

        # NEW: Localized Scar Awareness
        nearby_scars = Perception.visible_scars(actor, snapshot, scan_range=10)
        if nearby_scars:
            max_severity = max(s.severity for s in nearby_scars)
            # Standing near a 'scar' (Battlefield/Raid) spikes DREAD immediately
            scar_dread = max_severity * 0.15 * mind.decision.personality.caution
            updates.append(MindUpdate(emotion_delta={EmotionType.DREAD: scar_dread}))
            
            # If extremely severe, add a memory log entry about the 'chilling' atmosphere
            if max_severity > 0.8:
                from src.core.aspects.mind import InterpretedEvent
                # Check recent history to prevent log spam
                has_recent_scar = any(m.type == "environment" and m.tick > snapshot.tick - 100 for m in mind.narrative.memory_log)
                if not has_recent_scar:
                    updates.append(PerceptionUpdate(memory_log_add=[InterpretedEvent(
                        tick=snapshot.tick,
                        type="environment",
                        impact=-1.5,
                        details={"desc": "The atmosphere here is chilling; traces of a violent struggle remain.", "kind": "trauma_zone"}
                    )]))

        # 5. HP-Based Appraisal
        from src.ai.states.base import should_flee
        if should_flee(actor, ctx.config):
            updates.append(MindUpdate(emotion_delta={EmotionType.PANIC: 0.1}))

        # 6. Subjective Motive Appraisal (Personality + Social + Biological)
        last_appraisal = mind.decision.last_appraisal_tick
        if snapshot.tick - last_appraisal >= 10:
            from src.core.aspects.mind import PersonalMotive
            pers = mind.decision.personality
            
            # Update Motives
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
            
            # Base Biases from Personality
            biases = {g: 1.0 for g in GoalType}
            biases[GoalType.COMBAT] *= (0.5 + pers.aggression)
            biases[GoalType.LOOT] *= (0.5 + pers.greed)
            biases[GoalType.FLEE] *= (0.5 + pers.caution)
            biases[GoalType.REST] *= (0.5 + pers.caution)
            biases[GoalType.EXPLORE] *= (0.5 + pers.curiosity)
            driver_details: list[DecisionDriver] = []
            
            # Apply LifeRole Biases [PHASE 3]
            from src.core.models.enums import LifeRole
            role = actor.identity.world_role
            role_biases: dict[GoalType, float] = {}
            if role == LifeRole.GUARD or role == LifeRole.SENTRY:
                role_biases[GoalType.GUARD] = 1.5
            elif role == LifeRole.RAIDER:
                role_biases[GoalType.COMBAT] = 1.2
                role_biases[GoalType.LOOT] = 1.2
            elif role == LifeRole.CRAFTER or role == LifeRole.BLACKSMITH:
                role_biases[GoalType.CRAFT] = 1.5
            elif role == LifeRole.MERCHANT:
                role_biases[GoalType.TRADE] = 1.5
                role_biases[GoalType.SOCIAL] = 1.2
            elif role == LifeRole.HERO:
                role_biases[GoalType.EXPLORE] = 1.2
                role_biases[GoalType.LOOT] = 1.2
            elif role == LifeRole.HOUSEHOLDER:
                role_biases[GoalType.REST] = 1.2
                role_biases[GoalType.EAT] = 1.2

            for gtype, weight in role_biases.items():
                biases[gtype] *= weight
                driver_details.append(DecisionDriver(kind="role", label=f"Role: {role.name}", weight=weight))

            # Apply Social Biases
            for gtype, s_bias in social_biases.items():
                if s_bias != 0:
                    weight = 1.0 + s_bias
                    biases[gtype] *= weight
                    driver_details.append(DecisionDriver(kind="social", label=f"Social Bias: {gtype.name}", weight=weight))
            
            # Emotional Biases
            emo = mind.emotion
            if emo.dread > 0.3:
                biases[GoalType.FLEE] *= (1.0 + emo.dread)
                biases[GoalType.EXPLORE] *= (1.0 - (emo.dread * 0.5))
            if emo.joy > 0.3:
                biases[GoalType.EXPLORE] *= (1.0 + emo.joy * 0.3)
                biases[GoalType.SOCIAL] *= (1.0 + emo.joy * 0.2)
            if emo.panic > 0.5:
                biases[GoalType.FLEE] *= 2.0
            
            # Biological/Routine Biases
            from src.core.logic.routine_service import RoutineService
            routine_biases = RoutineService.calculate_routine_biases(actor, snapshot.hour, snapshot.tick)
            # 10. Group Coordination Biases (Phase 3 Stage 4)
            for gid, group in snapshot.group_registry.items():
                if actor.id in group.member_ids:
                    # Shared Goal Bias: Derived from group cohesion
                    cohesion_bonus = group.cohesion_level * 0.5
                    weight = 1.0 + cohesion_bonus
                    biases[group.shared_goal] *= weight
                    driver_details.append(DecisionDriver(
                        kind="social", 
                        label=f"Group Coordination ({group.shared_goal.name})", 
                        weight=float(weight)
                    ))
                    
                    # Proximity Bias: If not the leader, stay near the group's current anchor/leader
                    if group.leader_id and group.leader_id != actor.id:
                        if group.anchor_pos:
                            dist = actor.spatial.pos.manhattan(group.anchor_pos)
                            if dist > 10:
                                # Strongly bias Social (proxy for following/regrouping) if too far
                                follow_weight = 1.5 + (dist / 20.0)
                                biases[GoalType.SOCIAL] *= follow_weight
                                driver_details.append(DecisionDriver(
                                    kind="social", 
                                    label="Following Leader", 
                                    weight=float(follow_weight)
                                ))
                    break
            
            # 2. Map Strategic Intent to Tactical Biases [phase_2_stage_6]
            # We need the ObjectiveRecord to pass to the mapper. 
            # It might be in the entity's state OR just proposed in self._strategic_appraisal_phase.
            target_obj = None
            if strategic_objective_id:
                 strat_up = next((u for u in updates if isinstance(u, StrategicUpdate)), None)
                 if strat_up:
                      # Check newly proposed projects
                      for p in strat_up.projects_add_or_update:
                           target_obj = next((o for o in p.objectives if o.objective_id == strategic_objective_id), None)
                           if target_obj: break
                 
                 if not target_obj:
                      # Check existing projects in entity state
                      for p in actor.mind.strategic.projects:
                           target_obj = next((o for o in p.objectives if o.objective_id == strategic_objective_id), None)
                           if target_obj: break

            strategic_biases = self._obj_mapper.get_tactical_biases(ctx, target_obj)
            
            # Apply Strategic Biases to the existing tactical map [phase_2_stage_6]
            for gt, st_bias in strategic_biases.items():
                biases[gt] *= st_bias
                if st_bias != 1.0:
                    driver_details.append(DecisionDriver(
                        kind="strategic", 
                        label=f"Strategic Alignment [{target_obj.objective_id if target_obj else 'None'}]: {gt.name}", 
                        weight=float(st_bias)
                    ))

            updates.append(MindUpdate(
                motives=updated_motives,
                motive_utility_biases=biases,
                driver_details=driver_details,
                last_appraisal_tick=snapshot.tick
            ))

        # Normalization decay
        decay = {EmotionType.PANIC: -0.05, EmotionType.DREAD: -0.02, EmotionType.JOY: -0.01, EmotionType.STUCK: -0.2}
        updates.append(MindUpdate(emotion_delta=decay))
        if emotion_set:
            updates.append(MindUpdate(emotion_set=emotion_set))

    def _deliberation_tactical_phase(self, ctx: AIContext, updates: list[IntentUpdate]) -> AIState:
        """Phase 3: Deliberation. Choose the next state."""
        actor = ctx.actor
        if actor.mind.decision.ai_state not in self._DECISION_STATES:
            return actor.mind.decision.ai_state

        if self._goal_evaluator.is_goal_locked(ctx):
            return actor.mind.decision.ai_state

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
        temp = 0.05 + (1.0 - actor.mind.decision.personality.caution) * 0.4
        selected = self._goal_evaluator.select(goal_scores, rng_val, temperature=temp)
        
        if selected:
            current_val = boredom_updates.get(selected.goal, current_boredom.get(selected.goal, 1.0))
            boredom_updates[selected.goal] = max(0.1, current_val * 0.8)
            
            updates.append(MindUpdate(
                goal_scores={s.goal: s.score for s in goal_scores},
                last_goal=selected.goal,
                goal_committed_at=ctx.snapshot.tick if selected.goal != actor.mind.decision.last_goal else None,
                boredom_delta=boredom_updates,
                new_ai_state=int(selected.target_state)
            ))
            return selected.target_state
            
        if boredom_updates:
            updates.append(MindUpdate(boredom_delta=boredom_updates))
        return actor.mind.decision.ai_state

    def _finalization_phase(self, ctx: AIContext, state: AIState, updates: list[IntentUpdate]) -> tuple[AIState, ActionProposal]:
        """Phase 4: Output. Proposal generation."""
        actor = ctx.actor
        handler = STATE_HANDLERS.get(state, _FALLBACK)
        try:
            new_state, proposal = handler.handle(ctx)
            final_typed = list(updates)
            if proposal.updates:
                final_typed.extend(proposal.updates)
            
            if proposal.verb == ActionType.REST:
                new_idle = actor.mind.decision.consecutive_idle_ticks + 1
            else:
                new_idle = 0
            final_typed.append(MindUpdate(consecutive_idle_ticks=new_idle))
                
            proposal = proposal.model_copy(update={
                "new_ai_state": int(new_state),
                "updates": final_typed
            })
            return new_state, proposal
        except Exception as e:
            logger.error("AI Error for %s: %s", actor.id, e, exc_info=True)
            return state, ActionProposal(actor_id=actor.id, verb=ActionType.REST, reason="Error Fallback")
