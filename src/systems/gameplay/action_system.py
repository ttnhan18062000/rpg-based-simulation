"""ActionSystem handles post-resolution state mutations and tactical maneuvers.

Refactored for AOA Stabilization:
- Direct aspect access (spatial, combat, mind, progression).
- Explicit application of typed IntentUpdate records from side-effect-free AI decisions.
- Standardized state transitions and derived counter updates.
"""

from __future__ import annotations
import logging
import math
from typing import TYPE_CHECKING, Any, Callable
from src.core.models.enums import AIState, ActionType, Element, GoalType, EmotionType, HeroClass, StrategicStatus
from src.core.entities.entity import Entity
from src.actions.base import (
    ActionProposal, IntentUpdate, MindUpdate, NavigationUpdate, CombatTraceUpdate,
    PerceptionUpdate, ProgressionUpdate, IdentityUpdate, InteractionUpdate, SpatialUpdate,
    WorldUpdate, BuildingUpdate, RoutineUpdate, ReputationUpdate, StrategicUpdate
)
from src.core.models.reason_codes import ActionReason, ReasonCode
from src.core.gameplay.items.item_registry import ITEM_REGISTRY
from src.core.gameplay.classes import SKILL_DEFS
from src.core.logic.event_interpreter import EventInterpreterService
from src.core.logic.social_state_applicator import SocialStateApplicator
from src.core.logic.knowledge_propagation import KnowledgePropagationService
from src.actions.eat import EatAction
from src.actions.sleep import SleepAction
from src.systems.infrastructure.base import System

if TYPE_CHECKING:
    from src.core.models.world_state import WorldState
    from src.core.models.config import SimulationConfig
    from src.core.world.factions import FactionRegistry
    from src.systems.infrastructure.base import SystemContext
    from src.utils.event_emitter import EventEmitter

logger = logging.getLogger(__name__)

class ActionSystem(System):
    """System for processing applied actions and tactical state changes."""

    def process_applied_actions(self, context: SystemContext, applied: list[ActionProposal]) -> None:
        """Process state mutations and intent metadata for all ready entities."""
        # 1. Authoritative State Application (Unified Pipeline)
        self.apply_action_state_transitions(
            context.world, 
            context.config, 
            applied, 
            context.rng,
            emit=context.emit,
            faction_reg=context.faction_reg
        )

        # 2. Tactical & Visualization Updates (Context Dependent)
        self._update_ai_derived_states(context, applied)
        self._update_combat_visualization(context, applied)

    @classmethod
    def apply_action_state_transitions(
        cls, 
        world: WorldState, 
        config: SimulationConfig, 
        applied: list[ActionProposal],
        rng: DeterministicRNG,
        emit: Callable | None = None,
        faction_reg: FactionRegistry | None = None
    ) -> None:
        """Core side-effects applied identically in live and replay/recovery."""
        # Biological Decay moved to PreSystemsPhase in Milestone 1.
        
        for proposal in applied:
            entity = world.entities.get(proposal.actor_id)
            if entity is None or not entity.combat.alive:
                continue

            # --- Rulebook Authority Boundary [Milestone 1] ---
            from src.core.logic.legality_service import LegalityService
            from src.core.models.types import LocationTarget, BuildingTarget
            
            # Authoritative legality check before generating ANY updates
            is_legal = True
            rejection_reason = ""
            
            if config.overhaul_features.get("use_legality_v2", True):
                if proposal.verb == ActionType.MOVE:
                    target_pos = proposal.target
                    # [Milestone 7] Consolidated Legality v2: Range check + Occupancy
                    if not LegalityService.check_range(entity.spatial.pos, target_pos, 1):
                        is_legal = False
                        proposal.reason = ActionReason(code=ReasonCode.OUT_OF_RANGE, metadata={"max_range": 1}, is_rejection=True)
                        rejection_reason = proposal.reason.reason_text
                    elif not LegalityService.check_occupancy(target_pos, world, ignore_entity_id=entity.id):
                        is_legal = False
                        proposal.reason = ActionReason(code=ReasonCode.OCCUPANCY_VIOLATION, metadata={"pos": target_pos.to_dict() if hasattr(target_pos, "to_dict") else str(target_pos)}, is_rejection=True)
                        rejection_reason = proposal.reason.reason_text
                elif proposal.verb == ActionType.ATTACK:
                    if isinstance(proposal.target, int):
                        target_ent = world.entities.get(proposal.target)
                        if not target_ent or not target_ent.combat.alive:
                            is_legal = False
                            proposal.reason = ActionReason(code=ReasonCode.TARGET_INVALID, is_rejection=True)
                            rejection_reason = proposal.reason.reason_text
                        else:
                            from src.actions.combat import CombatAction
                            weapon_range = CombatAction._get_weapon_range(entity)
                            if not LegalityService.check_range(entity.spatial.pos, target_ent.spatial.pos, weapon_range):
                                is_legal = False
                                proposal.reason = ActionReason(code=ReasonCode.OUT_OF_RANGE, metadata={"max_range": weapon_range}, is_rejection=True)
                                rejection_reason = proposal.reason.reason_text
                    elif isinstance(proposal.target, BuildingTarget):
                        target_b = next((b for b in world.buildings if b.building_id == proposal.target.building_id), None)
                        if not target_b:
                            is_legal = False
                            proposal.reason = ActionReason(code=ReasonCode.TARGET_INVALID, metadata={"type": "building"}, is_rejection=True)
                            rejection_reason = proposal.reason.reason_text
                        else:
                            from src.actions.combat import CombatAction
                            weapon_range = CombatAction._get_weapon_range(entity)
                            if not LegalityService.check_range(entity.spatial.pos, target_b.pos, weapon_range):
                                is_legal = False
                                proposal.reason = ActionReason(code=ReasonCode.OUT_OF_RANGE, metadata={"max_range": weapon_range}, is_rejection=True)
                                rejection_reason = proposal.reason.reason_text
            
            if not is_legal:
                if not isinstance(proposal.reason, ActionReason):
                    proposal.reason = f"REJECTED: {rejection_reason or 'Unknown Legality Error'}"
                
                logger.warning("Rejected illegal proposal from entity %d: %s (%s)", entity.id, proposal.verb, rejection_reason)
                entity.mind.decision.last_reason = proposal.reason
                continue
            # -------------------------------------------------

            # Milestone 5: Fatigue Pressure
            # Entities with < 15% stamina are EXHAUSTED (EffectType.SLOW + ATK penalty)
            if config.overhaul_features.get("use_combat_interaction_v2", True) and entity.progression.stamina_ratio < 0.15:
                # Check if already has fatigue to avoid stacking
                if not any(e.source == "exhaustion" for e in entity.combat.effects):
                    from src.core.gameplay.effects import StatusEffect, EffectType
                    entity.combat.add_effect(StatusEffect(
                        effect_type=EffectType.SLOW,
                        remaining_ticks=5, # Short duration, reapplied if still low
                        source="exhaustion",
                        atk_mult=0.7,
                        spd_mult=0.5
                    ))

            # Unified Update Collection
            all_updates: list[IntentUpdate] = []
            if proposal.updates:
                all_updates.extend(proposal.updates)

            # 2. Update Generation (Functional Side-Effects)
            if proposal.verb == ActionType.USE_ITEM and proposal.target:
                all_updates.extend(cls._get_use_item_updates(world, config, entity, proposal.target))
            elif proposal.verb == ActionType.LOOT:
                all_updates.extend(cls._get_looting_updates(world, entity, proposal.target))
            elif proposal.verb == ActionType.HARVEST and proposal.target:
                all_updates.extend(cls._get_harvesting_updates(world, entity, proposal.target))
            elif proposal.verb == ActionType.EAT:
                all_updates.extend(EatAction.get_updates(proposal, world))
            elif proposal.verb == ActionType.SLEEP:
                all_updates.extend(SleepAction.get_updates(proposal, world))
            elif proposal.verb == ActionType.USE_SKILL:
                skill_id = proposal.metadata.get("skill_id")
                target_id = proposal.metadata.get("target_id")
                
                if isinstance(proposal.target, (tuple, list)) and len(proposal.target) == 2:
                    skill_id = proposal.target[0]
                    target_id = proposal.target[1]
                elif isinstance(proposal.target, int):
                    target_id = proposal.target
                
                if skill_id:
                    all_updates.extend(cls._get_use_skill_updates(world, config, rng, faction_reg, entity, skill_id, target_id, proposal=proposal, emit=emit))
                else:
                    logger.warning("Entity %d proposed USE_SKILL but no skill_id found in target or metadata", entity.id)

            elif proposal.verb == ActionType.ATTACK and isinstance(proposal.target, int):
                target_id = proposal.target
                all_updates.extend(cls._get_use_skill_updates(world, config, rng, faction_reg, entity, "Attack", target_id, proposal=proposal, emit=emit, ignore_skill_check=True))

            # Phase 2: Social Interpretation Pass
            cls._process_social_interpretation(world, entity, all_updates, proposal, rng)
            
            # Milestone 2: Social Convergence (Gossip)
            cls._process_proximity_gossip(world, entity, all_updates)

            # Milestone 5: Global Stamina Costs
            if config.overhaul_features.get("use_combat_interaction_v2", True):
                if proposal.verb == ActionType.MOVE:
                     all_updates.append(ProgressionUpdate(stamina_delta=-2, reason="Movement effort"))
                elif proposal.verb == ActionType.USE_SKILL:
                     # Standard skill cost is handled in _get_use_skill_updates
                     pass
                elif proposal.verb != ActionType.SLEEP and proposal.verb != ActionType.EAT:
                     # Minor drain for all other active verbs
                     all_updates.append(ProgressionUpdate(stamina_delta=-1, reason="Active effort"))

            # 3. Final Application (Authoritative Pipeline)
            if all_updates:
                cls._apply_updates(world, entity, all_updates, proposal, emit=emit)

            # 4. Direct State Transitions (AI Internal)
            if proposal.new_ai_state is not None:
                new_state = AIState(proposal.new_ai_state)
                if new_state != entity.mind.decision.ai_state:
                    if new_state == AIState.SLEEPING:
                        entity.mind.routine.is_sleeping = True
                    elif entity.mind.routine.is_sleeping and new_state != AIState.SLEEPING:
                        entity.mind.routine.is_sleeping = False
                        
                    entity.mind.decision.ai_state = new_state
                 
            if proposal.reason:
                entity.mind.decision.last_reason = proposal.reason

            # 5. Attribute Training
            from src.core.gameplay.attributes import train_attributes
            verb_name = proposal.verb.name if hasattr(proposal.verb, "name") else ActionType(proposal.verb).name
            train_attributes(entity, verb_name.lower())

            # 6. Cooldown Management
            speed = entity.combat.spd
            entity.next_act_at += 1.0 / max(0.1, speed / 10.0)

    @classmethod
    def _apply_updates(cls, world: WorldState, actor: Entity, updates: list[IntentUpdate], proposal: ActionProposal, emit: EventEmitter | None = None) -> None:
        """Apply typed simulation side-effects (AOA Phase 5)."""
        from src.actions.base import (
            MindUpdate, PerceptionUpdate, ProgressionUpdate, NavigationUpdate, 
            SocialUpdate, RoutineUpdate, StrategicUpdate, SocialEventUpdate
        )
        
        for up in updates:
            entity = actor
            if up.target_id is not None:
                target = world.entities.get(up.target_id)
                if target:
                    entity = target
                else:
                    logger.warning("IntentUpdate specified target_id %d but entity not found", up.target_id)
                    continue

            if isinstance(up, MindUpdate):
                decision = entity.mind.decision
                if up.new_ai_state is not None:
                    decision.ai_state = up.new_ai_state
                if up.goal_scores:
                    decision.goal_scores = up.goal_scores
                if up.last_goal:
                    decision.last_goal = up.last_goal
                if up.driver_details is not None:
                    decision.driver_details = up.driver_details
                if up.goal_committed_at is not None:
                    decision.goal_committed_at = up.goal_committed_at
                
                if up.grudge_delta:
                    for tid, delta in up.grudge_delta.items():
                        entity.mind.emotion.grudges[tid] = entity.mind.emotion.grudges.get(tid, 0.0) + delta
                
                if up.emotion_delta:
                    for em, delta in up.emotion_delta.items():
                        field_name = em.name.lower()
                        current = getattr(entity.mind.emotion, field_name, 0.0)
                        setattr(entity.mind.emotion, field_name, max(0.0, min(1.0, current + delta)))
                
                if up.emotion_set:
                    for em, val in up.emotion_set.items():
                        field_name = em.name.lower()
                        setattr(entity.mind.emotion, field_name, max(0.0, min(1.0, val)))

            elif isinstance(up, PerceptionUpdate):
                if up.threat_delta:
                    for tid, delta in up.threat_delta.items():
                        entity.mind.perception.threat_table[tid] = entity.mind.perception.threat_table.get(tid, 0.0) + delta
                if up.entity_memory:
                    for target_id, new_belief in up.entity_memory.items():
                        existing = entity.mind.perception.entity_memory.get(target_id)
                        if existing:
                            entity.mind.perception.entity_memory[target_id] = existing.model_copy(update=new_belief.model_dump(exclude_unset=True))
                        else:
                            entity.mind.perception.entity_memory[target_id] = new_belief

                if up.turning_points_add:
                    for tp in up.turning_points_add:
                        entity.mind.narrative.add_turning_point(tp)

                if up.memory_log_add:
                    log = entity.mind.narrative.memory_log
                    log.extend(up.memory_log_add)
                    from src.core.logic.memory_salience import MemorySalienceService
                    MemorySalienceService.prune(entity, world.tick, max_entries=50)
                
                if up.memory_locations_set:
                    entity.mind.narrative.memory_locations.update(up.memory_locations_set)

            elif isinstance(up, NavigationUpdate):
                nav = entity.mind.navigation
                if up.pos_history:
                    nav.pos_history = up.pos_history[-20:]
                if up.cached_path is not None:
                    nav.cached_path = up.cached_path
                if up.target_pos is not None:
                    nav.cached_path_target = up.target_pos
                if up.chase_ticks is not None:
                    nav.chase_ticks = up.chase_ticks
                if up.intention is not None:
                    nav.intention = up.intention
                if up.blocked_ticks is not None:
                    nav.blocked_ticks = up.blocked_ticks

            elif isinstance(up, ProgressionUpdate):
                if up.hp_delta:
                    entity.combat.hp = max(0, min(entity.combat.max_hp, entity.combat.hp + up.hp_delta))
                if up.max_hp_delta:
                    entity.combat.max_hp_base += up.max_hp_delta
                    entity.combat.hp = max(0, min(entity.combat.max_hp, entity.combat.hp + up.max_hp_delta))
                if up.stamina_delta:
                    entity.progression.stamina = max(0, min(entity.progression.max_stamina, entity.progression.stamina + up.stamina_delta))
                if up.combat_target_id is not None:
                    entity.combat.combat_target_id = up.combat_target_id
                if up.gold_delta: entity.progression.gold += up.gold_delta
                if up.xp_delta: entity.progression.xp += up.xp_delta
                if up.veterancy_points_delta: entity.progression.veterancy_points += up.veterancy_points_delta
                if up.fame_delta: entity.progression.fame += up.fame_delta
                if up.titles_add:
                    for title in up.titles_add:
                        if title not in entity.identity.titles:
                            entity.identity.titles.append(title)
                if up.skill_cooldowns:
                    for sid, cd in up.skill_cooldowns.items():
                        si = next((s for s in entity.progression.skills if s.skill_id == sid), None)
                        if si: si.cooldown_remaining = cd
                if up.skills_add:
                    from src.core.gameplay.classes import SkillInstance
                    for s in up.skills_add:
                        if isinstance(s, str):
                             entity.progression.skills.append(SkillInstance(skill_id=s))
                        else:
                             entity.progression.skills.append(s)
                if up.inventory_add:
                    if entity.inventory:
                        entity.inventory.items.extend(up.inventory_add)
                if up.inventory_remove:
                    if entity.inventory:
                        for item in up.inventory_remove:
                            if item in entity.inventory.items:
                                entity.inventory.items.remove(item)
                if up.effects_add:
                    for eff in up.effects_add:
                        entity.combat.add_effect(eff)
                if up.effects_expire_all:
                    for etype in up.effects_expire_all:
                        for eff in entity.combat.effects:
                            if eff.effect_type == etype:
                                eff.remaining_ticks = 0
                if up.consequences_add:
                    for cons in up.consequences_add:
                        entity.combat.add_consequence(cons)
                if up.consequences_remove:
                    entity.combat.consequences = [c for c in entity.combat.consequences if c.id not in up.consequences_remove]

            elif isinstance(up, RoutineUpdate):
                if up.hunger_delta:
                    entity.mind.routine.hunger_level = max(0.0, min(1.0, entity.mind.routine.hunger_level + up.hunger_delta))
                if up.sleep_delta:
                    entity.mind.routine.sleep_debt = max(0.0, min(1.0, entity.mind.routine.sleep_debt + up.sleep_delta))
                if up.is_sleeping is not None:
                    entity.mind.routine.is_sleeping = up.is_sleeping

            elif isinstance(up, SpatialUpdate):
                world.move_entity(entity.id, up.new_pos)
                if up.facing: entity.spatial.facing = up.facing
                if up.region_id: entity.spatial.region_id = up.region_id

            elif isinstance(up, CombatTraceUpdate):
                res = up.result
                target = world.entities.get(res.defender_id)
                if target and target.combat.alive:
                    if res.details and getattr(res.details, "is_shattered", False):
                        from src.core.gameplay.effects import EffectType
                        for eff in target.combat.effects:
                            if eff.effect_type == EffectType.FROZEN: eff.remaining_ticks = 0
                    
                    threat_val = res.threat if res.threat > 0 else float(res.damage)
                    target.mind.perception.threat_table[entity.id] = target.mind.perception.threat_table.get(entity.id, 0.0) + threat_val
                    
                    grudge_val = res.grudge if res.grudge > 0 else float(res.damage) / 10.0
                    target.mind.emotion.grudges[entity.id] = target.mind.emotion.grudges.get(entity.id, 0.0) + grudge_val
                    
                    target.combat.traces.append(res)
                    if len(target.combat.traces) > 20:
                        target.combat.traces = target.combat.traces[-20:]
                    
                    if res.trauma > 0:
                        from src.core.aspects.mind import InterpretedEvent
                        cls._apply_updates(world, target, [PerceptionUpdate(
                            memory_log_add=[InterpretedEvent(
                                tick=world.tick, type="trauma", impact=-res.trauma,
                                details={"desc": f"Took massive damage ({res.damage}) from {entity.identity.display_name} #{entity.id}", "source_id": entity.id}
                            )]
                        )], proposal, emit=emit)

            elif isinstance(up, WorldUpdate):
                if up.new_corpse:
                    node = up.new_corpse
                    if node.node_id == 0 and up.increment_corpse_id:
                        node.node_id = world._next_corpse_id
                        world._next_corpse_id += 1
                    world.corpse_nodes[node.node_id] = node

            elif isinstance(up, ReputationUpdate):
                from src.core.logic.reputation_service import ReputationService
                ReputationService.apply_update(entity, up)

            elif isinstance(up, BuildingUpdate):
                target_b = next((b for b in world.buildings if b.building_id == up.building_id), None)
                if target_b:
                    if up.damage_amount > 0: target_b.take_damage(up.damage_amount)
                    if up.repair_amount > 0: target_b.repair(up.repair_amount)
                    if up.is_destroyed: target_b.is_functional = False

            elif isinstance(up, InteractionUpdate):
                if up.corpse_id_to_remove is not None:
                    world.corpse_nodes.pop(up.corpse_id_to_remove, None)
                
            elif isinstance(up, SocialUpdate):
                from src.core.logic.relationship_service import RelationshipService
                RelationshipService.apply_update(world.social_registry, up, world.tick)
                
                bond = world.social_registry.get_bond(up.source_id, up.target_id)
                old_vals = {"trust": bond.trust - up.trust_delta, "fear": bond.fear - up.fear_delta, "rivalry": bond.rivalry - up.rivalry_delta, "loyalty": bond.loyalty - up.loyalty_delta}
                new_vals = {"trust": bond.trust, "fear": bond.fear, "rivalry": bond.rivalry, "loyalty": bond.loyalty}
                
                milestones = []
                for threshold, label in [(0.5, "ally"), (0.2, "friendly"), (-0.2, "distrust"), (-0.5, "hostile")]:
                     if (old_vals["trust"] < threshold <= new_vals["trust"]) or (old_vals["trust"] >= threshold > new_vals["trust"]):
                         milestones.append(("trust", label, old_vals["trust"], new_vals["trust"]))
                if old_vals["rivalry"] < 0.8 <= new_vals["rivalry"]:
                    milestones.append(("rivalry", "nemesis", old_vals["rivalry"], new_vals["rivalry"]))
                
                if milestones:
                    from src.core.aspects.mind import SocialNarrative, InterpretedEvent
                    for bond_type, label, old_v, new_v in milestones:
                        narrative = SocialNarrative(target_id=up.target_id, change_type=f"milestone_{label}", bond_type=bond_type, old_value=old_v, new_value=new_v)
                        entry = InterpretedEvent(tick=world.tick, type="social", impact=abs(new_v - old_v) + 0.5, details=narrative)
                        updates.append(PerceptionUpdate(memory_log_add=[entry]))

            elif isinstance(up, SocialEventUpdate):
                from src.actions.base import PerceptionUpdate
                from src.core.aspects.mind import InterpretedEvent
                for evt in up.events_add:
                    # 1. Add to actor's narrative memory (semantic interpretation)
                    actor.mind.narrative.add_interpreted_life_event(evt)
                    # 2. Derive systemic social updates (relationships, reputation)
                    applicator_updates = SocialStateApplicator.apply_interpreted_event(evt, world, rng=None) # RNG pass-through if needed
                    if applicator_updates:
                        # Recursively apply the derived systemic updates
                        cls._apply_updates(world, actor, applicator_updates, proposal, emit=emit)

            elif isinstance(up, StrategicUpdate):
                cls.apply_strategic_update(entity, up, world, emit)

    @staticmethod
    def apply_strategic_update(entity: Entity, up: StrategicUpdate, world: WorldState | None = None, emit: EventEmitter | None = None) -> None:
        """Authoritatively applies strategic stratum mutations. [AOA AUTHORITATIVE]"""
        from src.core.models.enums import StrategicStatus
        strat = entity.mind.strategic
        
        # 1. Directives
        if up.directives_add:
            for d in up.directives_add:
                found = False
                for i, existing in enumerate(strat.directives):
                    if existing.directive_id == d.directive_id:
                        strat.directives[i] = d
                        found = True
                        break
                if not found: strat.directives.append(d)
        if up.directives_remove:
            strat.directives = [d for d in strat.directives if d.directive_id not in up.directives_remove]
        
        # 2. Projects
        if up.projects_add_or_update:
            for p in up.projects_add_or_update:
                found = False
                for i, existing in enumerate(strat.projects):
                    if existing.project_id == p.project_id:
                        if existing.status != p.status:
                            from src.utils.metrics import SIM_STRATEGIC_PROJECT_STATUS
                            status_label = "completed" if p.status == StrategicStatus.RESOLVED else "abandoned" if p.status == StrategicStatus.ABANDONED else None
                            if status_label:
                                SIM_STRATEGIC_PROJECT_STATUS.labels(kind=p.kind.name.lower() if hasattr(p.kind, "name") else str(p.kind).lower(), status=status_label).inc()
                        strat.projects[i] = p
                        found = True
                        break
                if not found:
                    strat.projects.append(p)
                    from src.utils.metrics import SIM_STRATEGIC_PROJECT_STATUS
                    SIM_STRATEGIC_PROJECT_STATUS.labels(kind=p.kind.name.lower() if hasattr(p.kind, "name") else str(p.kind).lower(), status="started").inc()
        if up.projects_remove:
            strat.projects = [p for p in strat.projects if p.project_id not in up.projects_remove]
            
        # 3. Focus/Locks
        if up.current_project_id is not None: strat.current_project_id = up.current_project_id
        if up.current_objective_id is not None: strat.current_objective_id = up.current_objective_id
        if up.interrupted_project_id is not None: strat.interrupted_project_id = up.interrupted_project_id
        if up.project_lock_until is not None: strat.project_lock_until = up.project_lock_until
            
        # 4. Concerns
        if up.concerns_add_or_update:
            for c in up.concerns_add_or_update:
                found = False
                for i, existing in enumerate(strat.concerns):
                    if existing.concern_id == c.concern_id:
                        strat.concerns[i] = c
                        found = True
                        break
                if not found: strat.concerns.append(c)
        if up.concerns_remove:
            strat.concerns = [c for c in strat.concerns if c.concern_id not in up.concerns_remove]
            
        # 5. Leads & Knowledge Continuity
        if up.leads_add_or_update:
            for ld in up.leads_add_or_update:
                found = False
                for i, existing in enumerate(strat.leads):
                    if existing.lead_id == ld.lead_id:
                        strat.leads[i] = ld
                        found = True
                        break
                if not found: strat.leads.append(ld)
        if up.leads_remove:
            strat.leads = [ld for ld in strat.leads if ld.lead_id not in up.leads_remove]
        if up.tested_lead_ids:
            for lid in up.tested_lead_ids:
                if lid not in strat.tested_lead_ids: strat.tested_lead_ids.append(lid)
            
        # 6. Memory & Spatial
        if up.last_interpreted_event_tick is not None: strat.last_interpreted_event_tick = up.last_interpreted_event_tick
        if up.candidate_zones_add_or_update:
            for cz in up.candidate_zones_add_or_update:
                found = False
                for i, existing in enumerate(strat.candidate_zones):
                    if existing.zone_id == cz.zone_id:
                        strat.candidate_zones[i] = cz
                        found = True
                        break
                if not found: strat.candidate_zones.append(cz)
        if up.candidate_zones_remove:
            strat.candidate_zones = [cz for cz in strat.candidate_zones if cz.zone_id not in up.candidate_zones_remove]
        if up.hypotheses_add_or_update:
            for hy in up.hypotheses_add_or_update:
                found = False
                for i, existing in enumerate(strat.hypotheses):
                    if existing.hypothesis_id == hy.hypothesis_id:
                        strat.hypotheses[i] = hy
                        found = True
                        break
                if not found: strat.hypotheses.append(hy)
        if up.hypotheses_remove:
            strat.hypotheses = [hy for hy in strat.hypotheses if hy.hypothesis_id not in up.hypotheses_remove]
            
        # 8. Social Obligations
        if up.obligations_add_or_update:
            for o in up.obligations_add_or_update:
                found = False
                for i, existing in enumerate(strat.obligations):
                    if existing.obligation_id == o.obligation_id:
                        strat.obligations[i] = o
                        found = True
                        break
                if not found: strat.obligations.append(o)
        if up.obligations_remove:
            strat.obligations = [o for o in strat.obligations if o.obligation_id not in up.obligations_remove]
        if up.contracts_add_or_update:
            for ct in up.contracts_add_or_update:
                found = False
                for i, existing in enumerate(strat.contracts):
                    if existing.contract_id == ct.contract_id:
                        # [TCK-20260415-HARDENING] Metric increment only on status transition
                        if existing.status != ct.status:
                             if ct.status == StrategicStatus.ABANDONED:
                                 from src.utils.metrics import SIM_STRATEGIC_CONTRACT_BREACHES
                                 SIM_STRATEGIC_CONTRACT_BREACHES.labels(contract_kind=ct.kind.name.lower() if hasattr(ct.kind, "name") else str(ct.kind).lower(), reason="abandoned").inc()
                        
                        strat.contracts[i] = ct
                        found = True
                        break
                if not found: 
                    strat.contracts.append(ct)
                    # Note: We don't increment "started" metrics for contracts here yet to avoid over-counting during bootstrap
        
        if up.contracts_remove:
            strat.contracts = [ct for ct in strat.contracts if ct.contract_id not in up.contracts_remove]
        if up.offers_add_or_update:
            for off in up.offers_add_or_update:
                found = False
                for i, existing in enumerate(strat.offers):
                    if existing.offer_id == off.offer_id:
                        strat.offers[i] = off
                        found = True
                        break
                if not found: strat.offers.append(off)
        if up.offers_remove:
            strat.offers = [off for off in strat.offers if off.offer_id not in up.offers_remove]
            
        # 9. Blockers & Metrics
        if up.blockers_add_or_update:
            for bl in up.blockers_add_or_update:
                found = False
                for i, existing in enumerate(strat.blockers):
                    if existing.blocker_id == bl.blocker_id:
                        strat.blockers[i] = bl
                        found = True
                        break
                if not found: strat.blockers.append(bl)
        if up.blockers_remove:
            strat.blockers = [bl for bl in strat.blockers if bl.blocker_id not in up.blockers_remove]
        if up.engaged_ticks is not None: strat.engaged_ticks = up.engaged_ticks
        if world: strat.last_strategic_tick = world.tick
        
        # [phase_3_intel_capacity]
        if up.source_trust_updates:
            strat.source_trust.update(up.source_trust_updates)
        
        # 10. Cognitive Bounding Metrics [phase_2_intel_capacity]
        if up.last_capacity_profile is not None: strat.last_capacity_profile = up.last_capacity_profile
        if up.active_slice_used is not None: strat.active_slice_used = up.active_slice_used
        if up.active_concerns_used is not None: strat.active_concerns_used = up.active_concerns_used
        if up.retained_leads_used is not None: strat.retained_leads_used = up.retained_leads_used
        if up.candidate_zones_used is not None: strat.candidate_zones_used = up.candidate_zones_used
        if up.ally_evaluations_used is not None: strat.ally_evaluations_used = up.ally_evaluations_used
        if up.detour_depth_used is not None: strat.detour_depth_used = up.detour_depth_used
        if up.dropped_candidates_count is not None: strat.dropped_candidates_count = up.dropped_candidates_count
        if up.latent_concerns_count is not None: strat.latent_concerns_count = up.latent_concerns_count
        if up.is_overloaded is not None: strat.is_overloaded = up.is_overloaded
        if up.overload_score is not None: strat.overload_score = up.overload_score
        if up.primary_overload_source is not None: strat.primary_overload_source = up.primary_overload_source
        if up.last_overload_tick is not None: strat.last_overload_tick = up.last_overload_tick
        
        # 11. Traceability
        if up.strategic_drivers:
            strat.recent_drivers = up.strategic_drivers

    @classmethod
    def _apply_biological_decay(cls, world: WorldState, config: SimulationConfig) -> None:
        """Authoritative time-based needs increment. [PHASE 3]"""
        for entity in world.entities.values():
            if not entity.combat.alive: continue
            routine = entity.mind.routine
            routine.sleep_debt = max(0.0, min(1.0, routine.sleep_debt + config.sleep_decay_rate))
            routine.hunger_level = max(0.0, min(1.0, routine.hunger_level + config.hunger_decay_rate))
            if routine.sleep_debt >= 1.0 and not routine.is_sleeping: routine.is_sleeping = True
            if routine.is_sleeping:
                routine.sleep_debt = max(0.0, routine.sleep_debt - config.sleep_recovery_rate)
                if routine.sleep_debt <= 0.0: routine.is_sleeping = False
            rid = entity.spatial.current_region_id
            if rid:
                current_fatigue = entity.mind.narrative.region_fatigue.get(rid, 0.0)
                entity.mind.narrative.region_fatigue[rid] = min(1.0, current_fatigue + 0.005)
    
    @classmethod
    def _get_use_skill_updates(cls, world: WorldState, config: SimulationConfig, rng: DeterministicRNG, faction_reg: FactionRegistry | None, entity: Entity, skill_id: str, target_id: int | None = None, proposal: ActionProposal | None = None, emit: Callable | None = None, ignore_skill_check: bool = False) -> list[IntentUpdate]:
        """Functional side-effects for skill usage. [AOA STABILIZATION]"""
        updates: list[IntentUpdate] = []
        if skill_id == "Attack": skill_id = "Basic Attack"
        sdef = SKILL_DEFS.get(skill_id)
        if not sdef: return updates
        if not ignore_skill_check:
            instance = next((si for si in entity.progression.skills if si.skill_id == skill_id), None)
            if not instance or not instance.is_ready(): return updates
            cost = instance.effective_stamina_cost(sdef.stamina_cost)
            if entity.progression.stamina < cost: return updates
            updates.append(ProgressionUpdate(stamina_delta=-cost, skill_cooldowns={skill_id: sdef.cooldown}))
            power = instance.effective_power(sdef.power)
        else:
            power = sdef.power
        targets: list[Entity] = []
        if sdef.radius > 0:
            from src.core.models.vectors import Vector2
            center = entity.spatial.pos
            from src.core.models.types import LocationTarget
            if target_id and world.entities.get(target_id): center = world.entities[target_id].spatial.pos
            elif proposal and isinstance(proposal.target, Vector2): center = proposal.target
            elif proposal and isinstance(proposal.target, LocationTarget): center = proposal.target.pos
            potential = world.entities_at_radius(center, sdef.radius)
            for t in potential:
                if t.id != entity.id and t.combat.alive:
                    is_hostile = faction_reg.is_hostile(entity.identity.faction, t.identity.faction) if faction_reg else (entity.identity.faction != t.identity.faction)
                    if is_hostile: targets.append(t)
        elif target_id:
            t = world.entities.get(target_id)
            if t and t.combat.alive: targets.append(t)
        from src.actions.combat import DamageResolutionService, CombatAftermathService
        for t in targets:
            damage, is_crit, is_evaded, trace_details = DamageResolutionService.resolve(attacker=entity, defender=t, world=world, config=config, skill_id=skill_id, power=power, rng=rng, faction_reg=faction_reg, override_damage_type=sdef.damage_type, override_element=sdef.element)
            CombatAftermathService.process(attacker=entity, defender=t, world=world, damage=damage, is_crit=is_crit, is_evasion=is_evaded, config=config, proposal=proposal, rng=rng, trace_details=trace_details)
            for up in proposal.updates:
                if isinstance(up, CombatTraceUpdate) and (up.result.skill_name == "SKILL" or up.result.skill_name is None):
                    up.result.skill_name = sdef.name
                    up.result.metadata["aoe"] = sdef.radius > 0
                    up.result.metadata["power"] = power
            if proposal and proposal.updates:
                for up in proposal.updates:
                    if up not in updates: updates.append(up)
            if emit: emit("combat", f"{entity.kind} hit {t.kind} with {sdef.name}", (entity.id, t.id), {"skill_id": skill_id, "skill_name": sdef.name, "damage": damage, "verb": "skill", "aoe": sdef.radius > 0})
        return updates

    @staticmethod
    def _get_use_item_updates(world: WorldState, config: SimulationConfig, entity: Entity, item_id: str) -> list[IntentUpdate]:
        updates: list[IntentUpdate] = []
        if entity.inventory and item_id in entity.inventory.items:
            template = ITEM_REGISTRY.get(item_id)
            if template:
                updates.append(ProgressionUpdate(inventory_remove=[item_id]))
                if template.heal_amount > 0: updates.append(ProgressionUpdate(hp_delta=template.heal_amount))
                if template.hunger_reduction > 0: updates.append(RoutineUpdate(hunger_delta=-template.hunger_reduction))
        return updates

    @staticmethod
    def _get_looting_updates(world: WorldState, entity: Entity, pos: Any) -> list[IntentUpdate]:
        updates: list[IntentUpdate] = []
        items = world.pickup_items(pos)
        if items: updates.append(ProgressionUpdate(inventory_add=items))
        for nid, node in list(world.corpse_nodes.items()):
            if node.pos == pos:
                corpse_items, corpse_gold = node.items or [], node.gold or 0
                if corpse_items or corpse_gold > 0: updates.append(ProgressionUpdate(inventory_add=corpse_items, gold_delta=corpse_gold))
                updates.append(InteractionUpdate(corpse_id_to_remove=nid))
                from src.core.aspects.mind import InterpretedEvent, LootNarrative
                loot_event = InterpretedEvent(tick=world.tick, type="loot", impact=0.2 + (corpse_gold * 0.01), details=LootNarrative(gold_amount=corpse_gold, source=f"corpse_{node.entity_id}"))
                updates.append(PerceptionUpdate(memory_log_add=[loot_event]))
        return updates

    @staticmethod
    def _get_harvesting_updates(world: WorldState, entity: Entity, pos: Any) -> list[IntentUpdate]:
        updates: list[IntentUpdate] = []
        node = world.resource_at(pos)
        if node and node.is_available:
            item_id = node.harvest()
            if item_id: updates.append(ProgressionUpdate(inventory_add=[item_id], stamina_delta=-2))
        return updates

    @classmethod
    def _process_social_interpretation(cls, world: WorldState, actor: Entity, updates: list[IntentUpdate], proposal: ActionProposal, rng: DeterministicRNG | None = None) -> None:
        from src.actions.base import CombatTraceUpdate, SpatialUpdate
        for up in updates:
            if isinstance(up, CombatTraceUpdate):
                defender = world.get_entity(up.result.defender_id)
                if defender:
                    events = EventInterpreterService.interpret_combat_aftermath(actor, defender, up.result, world, rng)
                    for event in events:
                        social_up = SocialStateApplicator.apply_interpreted_event(event, world, rng)
                        if social_up: updates.extend(social_up)
        spatial_up = next((u for u in updates if isinstance(u, SpatialUpdate)), None)
        if spatial_up:
            event = EventInterpreterService.interpret_tactical_outcome(world, actor, spatial_up, rng)
            if event:
                social_up = SocialStateApplicator.apply_interpreted_event(event, world, rng)
                if social_up: updates.extend(social_up)

    @classmethod
    def _process_proximity_gossip(cls, world: WorldState, actor: Entity, updates: list[IntentUpdate]) -> None:
        for other in world.entities.values():
            if other.id == actor.id or not other.combat.alive: continue
            dist = actor.spatial.pos.manhattan(other.spatial.pos)
            if dist <= 5:
                p_up, s_up = KnowledgePropagationService.propagate_gossip(actor, other, world)
                if p_up: updates.append(p_up)
                if s_up: updates.append(s_up)
                p_up_back, s_up_back = KnowledgePropagationService.propagate_gossip(other, actor, world)
                if p_up_back: updates.append(p_up_back)
                if s_up_back: updates.append(s_up_back)

    def _update_ai_derived_states(self, context: SystemContext, applied: list[ActionProposal]) -> None:
        world = context.world
        for p in applied:
            entity = world.entities.get(p.actor_id)
            if not entity or not entity.combat.alive: continue
            state = entity.mind.decision.ai_state
            if state == AIState.HUNT: entity.mind.navigation.chase_ticks += 1
            else: entity.mind.navigation.chase_ticks = 0
            if state == AIState.IDLE: entity.mind.decision.consecutive_idle_ticks += 1
            else: entity.mind.decision.consecutive_idle_ticks = 0

    def _update_combat_visualization(self, context: SystemContext, applied: list[ActionProposal]) -> None:
        pass
