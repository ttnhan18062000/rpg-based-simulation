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
from src.core.gameplay.classes import SKILL_DEFS, SkillTarget, SkillType
from src.core.logic.event_interpreter import EventInterpreterService
from src.core.logic.social_state_applicator import SocialStateApplicator
from src.core.logic.knowledge_propagation import KnowledgePropagationService
from src.core.logic.memory_salience import MemorySalienceService
from src.core.gameplay.effects import StatusEffect, EffectType
from src.core.models.strategy import StrategicState
from src.actions.eat import EatAction
from src.actions.sleep import SleepAction
from src.core.gameplay.attributes import train_attributes
from src.core.logic.reputation_service import ReputationService
from src.systems.infrastructure.base import System

if TYPE_CHECKING:
    from src.core.models.world_state import WorldState
    from src.core.models.config import SimulationConfig
    from src.core.world.factions import FactionRegistry
    from src.systems.infrastructure.base import SystemContext
    from src.utils.event_emitter import EventEmitter
    from src.platform.rng import DeterministicRNG

logger = logging.getLogger(__name__)

class ActionSystem(System):
    """System for processing applied actions and tactical state changes."""

    def process_applied_actions(self, context: SystemContext, proposals: list[ActionProposal], applied: list[ActionProposal] | None = None) -> None:
        """Process state mutations and intent metadata for all ready entities."""
        applied = applied or []
        applied_ids = {p.actor_id for p in applied}
        # 1. Authoritative State Application (Unified Pipeline)
        self.apply_action_state_transitions(
            context.world, 
            context.config, 
            proposals,
            applied_ids,
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
        proposals: list[ActionProposal],
        applied_ids: set[int] | None = None,
        rng: DeterministicRNG | None = None,
        emit: Callable | None = None,
        faction_reg: FactionRegistry | None = None
    ) -> None:
        """Core side-effects applied identically in live and replay/recovery."""
        if applied_ids is None:
            applied_ids = {p.actor_id for p in proposals}
        
        for proposal in proposals:
            entity = world.entities.get(proposal.actor_id)
            if entity is None or not entity.combat.alive:
                continue
            
            is_physically_accepted = proposal.actor_id in applied_ids
            
            # --- Cognitive State Persistence [Milestone 7] ---
            # delib_updates partition contains internal state changes (Strategic, Mind, Perception, Navigation).
            # These are ALWAYS applied if the entity deliberated, even if their physical action failed.
            delib_updates = [up for up in (proposal.updates or []) if isinstance(up, (StrategicUpdate, MindUpdate, PerceptionUpdate))]
            if delib_updates:
                cls._apply_updates(world, entity, delib_updates, proposal, emit=emit)

            # [AOA STABILIZATION] Apply AI State transition and Reason regardless of physical outcome.
            if proposal.new_ai_state is not None:
                entity.mind.decision.ai_state = AIState(proposal.new_ai_state)
            if proposal.reason:
                entity.mind.decision.last_reason = proposal.reason
            
            # --- Rulebook Authority Boundary ---
            # If rejected by ConflictResolver, we skip physical side-effects.
            if not is_physically_accepted:
                continue

            # --- Physical Side-Effects (Authoritative) ---
            # 1. Fatigue Pressure
            if config.overhaul_features.get("use_combat_interaction_v2", True) and entity.progression.stamina_ratio < 0.15:
                if not any(e.source == "exhaustion" for e in entity.combat.effects):
                    entity.combat.add_effect(StatusEffect(
                        effect_type=EffectType.SLOW,
                        remaining_ticks=5,
                        source="exhaustion",
                        atk_mult=0.7,
                        spd_mult=0.5
                    ))

            # 2. Collect Physical Updates
            # We TRUST that ConflictResolver has already populated MOVE, ATTACK, and REST updates.
            # We ONLY enrich those that need system-level interpretation (ITEM, LOOT, HARVEST).
            physical_updates: list[IntentUpdate] = []
            if proposal.updates:
                physical_updates.extend([up for up in proposal.updates if not isinstance(up, (StrategicUpdate, MindUpdate, PerceptionUpdate, NavigationUpdate))])

            if proposal.verb == ActionType.USE_ITEM and proposal.target:
                physical_updates.extend(cls._get_use_item_updates(world, config, entity, proposal.target))
            elif proposal.verb == ActionType.LOOT:
                physical_updates.extend(cls._get_looting_updates(world, entity, proposal.target))
            elif proposal.verb == ActionType.HARVEST and proposal.target:
                physical_updates.extend(cls._get_harvesting_updates(world, entity, proposal.target))
            elif proposal.verb == ActionType.EAT:
                physical_updates.extend(EatAction.get_updates(proposal, world))
            elif proposal.verb == ActionType.SLEEP:
                physical_updates.extend(SleepAction.get_updates(proposal, world))
            elif proposal.verb == ActionType.USE_SKILL and not any(isinstance(up, CombatTraceUpdate) for up in physical_updates):
                # Only re-evaluate if NOT already populated by ConflictResolver
                skill_id = proposal.target[0] if isinstance(proposal.target, (tuple, list)) else None
                target_id = proposal.target[1] if isinstance(proposal.target, (tuple, list)) else (proposal.target if isinstance(proposal.target, int) else None)
                if skill_id:
                    physical_updates.extend(cls._get_use_skill_updates(world, config, rng, faction_reg, entity, skill_id, target_id, proposal=proposal, emit=emit))

            # 3. Social Interpretation Pass
            cls._process_social_interpretation(world, entity, physical_updates, proposal, rng)
            
            # Reputation
            rep_updates = [up for up in physical_updates if isinstance(up, ReputationUpdate)]
            for rup in rep_updates:
                ReputationService.apply_update(entity, rup)

            # 4. Contextual Side-Effects (Gossip)
            cls._process_proximity_gossip(world, entity, physical_updates)

            # 5. Global Stamina Costs (if not already handled)
            if config.overhaul_features.get("use_combat_interaction_v2", True):
                if not any(hasattr(up, "stamina_delta") and up.stamina_delta is not None for up in physical_updates):
                    if proposal.verb == ActionType.MOVE:
                         physical_updates.append(ProgressionUpdate(stamina_delta=-2, reason="Movement effort"))
                    elif proposal.verb != ActionType.SLEEP and proposal.verb != ActionType.EAT:
                         physical_updates.append(ProgressionUpdate(stamina_delta=-1, reason="Active effort"))

            # 6. Final Authoritative Application
            if physical_updates:
                cls._apply_updates(world, entity, physical_updates, proposal, emit=emit)

            # 7. Post-Action Synchronization
            if proposal.new_ai_state is not None:
                new_state = AIState(proposal.new_ai_state)
                if new_state == AIState.SLEEPING:
                    entity.mind.routine.is_sleeping = True
                elif entity.mind.routine.is_sleeping and new_state != AIState.SLEEPING:
                    entity.mind.routine.is_sleeping = False

            # 8. Attribute Training & Timing
            verb_name = proposal.verb.name if hasattr(proposal.verb, "name") else ActionType(proposal.verb).name
            train_attributes(entity, verb_name.lower())
            
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
                    if world.tick % 10 == 0:
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
                if up.stalemate_counter is not None:
                    nav.stalemate_counter = up.stalemate_counter
                if up.last_ai_state is not None:
                    nav.last_ai_state = up.last_ai_state
                if up.last_target_id is not None:
                    nav.last_target_id = up.last_target_id
                if up.intention is not None:
                    nav.intention = up.intention
                if up.blocked_ticks is not None:
                    nav.blocked_ticks = up.blocked_ticks
                if up.oscillation_counter is not None:
                    nav.oscillation_counter = up.oscillation_counter
                if up.last_route_hash is not None:
                    nav.last_route_hash = up.last_route_hash

            elif isinstance(up, ProgressionUpdate):
                if up.hp_delta is not None and up.hp_delta != 0:
                    old_hp = entity.combat.hp
                    entity.combat.hp = max(0, min(entity.combat.max_hp, entity.combat.hp + up.hp_delta))
                    logger.info("Tick %d: Entity %d HP %d -> %d (delta %d)", world.tick, entity.id, old_hp, entity.combat.hp, up.hp_delta)
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
                # Authoritative Speed/Leash Safety [AOA STABILIZATION]
                can_move = True
                if hasattr(entity.combat, "spd") and entity.combat.spd <= 0:
                    # Allow non-positional updates (facing, region)
                    if up.new_pos and up.new_pos != entity.spatial.pos:
                        can_move = False
                
                if can_move:
                    if up.new_pos: world.move_entity(entity.id, up.new_pos)
                    if up.facing: entity.spatial.facing = up.facing
                    if up.region_id: entity.spatial.region_id = up.region_id
                    if up.moved_this_tick is not None: entity.spatial.moved_this_tick = up.moved_this_tick

            elif isinstance(up, CombatTraceUpdate):
                res = up.result
                target = world.entities.get(res.defender_id)
                if target and target.combat.alive:
                    if res.details and getattr(res.details, "is_shattered", False):
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
        
        # 1. Prometheus Metrics (State Transition Tracking)
        if up.projects_add_or_update:
            for p in up.projects_add_or_update:
                found = False
                for existing in strat.projects:
                    if existing.project_id == p.project_id:
                        if existing.status != p.status:
                            from src.utils.metrics import SIM_STRATEGIC_PROJECT_STATUS
                            status_label = "completed" if p.status == StrategicStatus.RESOLVED else "abandoned" if p.status == StrategicStatus.ABANDONED else None
                            if status_label:
                                SIM_STRATEGIC_PROJECT_STATUS.labels(kind=p.kind.name.lower() if hasattr(p.kind, "name") else str(p.kind).lower(), status=status_label).inc()
                        found = True
                        break
                if not found:
                    from src.utils.metrics import SIM_STRATEGIC_PROJECT_STATUS
                    SIM_STRATEGIC_PROJECT_STATUS.labels(kind=p.kind.name.lower() if hasattr(p.kind, "name") else str(p.kind).lower(), status="started").inc()

        if up.contracts_add_or_update:
            for ct in up.contracts_add_or_update:
                for existing in strat.contracts:
                    if existing.contract_id == ct.contract_id:
                        if existing.status != ct.status and ct.status == StrategicStatus.ABANDONED:
                            from src.utils.metrics import SIM_STRATEGIC_CONTRACT_BREACHES
                            SIM_STRATEGIC_CONTRACT_BREACHES.labels(contract_kind=ct.kind.name.lower() if hasattr(ct.kind, "name") else str(ct.kind).lower(), reason="abandoned").inc()
                        break
        
        # 2. Delegate authoritative mutation to the StrategicState model [AOA STABILIZATION]
        strat.apply_update(up)
        
        # 3. Synchronize world-dependent metadata
        if world:
            strat.last_strategic_tick = world.tick

    @classmethod
    def _apply_biological_decay(cls, world: WorldState, config: SimulationConfig) -> None:
        """Authoritative time-based needs increment. [PHASE 3]"""
        for entity in world.entities.values():
            if not entity.combat.alive: continue
            routine = entity.mind.routine
            # DEBUG
            print(f"DEBUG: entity={entity.id} sleep_debt={type(routine.sleep_debt)} decay={type(config.sleep_decay_rate)}")
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
