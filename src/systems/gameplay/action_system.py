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
from src.core.models.enums import AIState, ActionType, Element, GoalType, EmotionType, HeroClass
from src.core.entities.entity import Entity
from src.actions.base import (
    ActionProposal, IntentUpdate, MindUpdate, NavigationUpdate, CombatTraceUpdate,
    PerceptionUpdate, ProgressionUpdate, IdentityUpdate, InteractionUpdate, SpatialUpdate,
    WorldUpdate, BuildingUpdate, RoutineUpdate, ReputationUpdate
)
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
        # 0. Global Biological Decay (Authoritative State)
        cls._apply_biological_decay(world, config)
        
        for proposal in applied:
            entity = world.entities.get(proposal.actor_id)
            if entity is None or not entity.combat.alive:
                continue

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
                
                # AOA Stabilization: Robust extraction of skill info from AI proposals
                # AI proposals use target=(skill_id, enemy_id) for skills
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
                # AOA Pillar 1: Basic Attack Fallback
                # Map to 'Basic Attack' skill logic without requiring explicit SkillInstance
                # This ensures entities in simple tests can still fight.
                target_id = proposal.target
                all_updates.extend(cls._get_use_skill_updates(world, config, rng, faction_reg, entity, "Attack", target_id, proposal=proposal, emit=emit, ignore_skill_check=True))

            # Phase 2: Social Interpretation Pass
            cls._process_social_interpretation(world, entity, all_updates, proposal)
            
            # Phase 2: Social Convergence (Gossip)
            cls._process_proximity_gossip(world, entity, all_updates)

            # 3. Final Application (Authoritative Pipeline)
            if all_updates:
                cls._apply_updates(world, entity, all_updates, proposal)

            # 4. Direct State Transitions (AI Internal) - Apply AFTER updates possibly modify it
            if proposal.new_ai_state is not None:
                new_state = AIState(proposal.new_ai_state)
                if new_state != entity.mind.decision.ai_state:
                    # Authoritative Biological State Management [PHASE 3]
                    if new_state == AIState.SLEEPING:
                        entity.mind.routine.is_sleeping = True
                    elif entity.mind.routine.is_sleeping and new_state != AIState.SLEEPING:
                        entity.mind.routine.is_sleeping = False
                        
                    entity.mind.decision.ai_state = new_state
                    if entity.mind.decision.goal_committed_at == 0:
                         entity.mind.decision.goal_committed_at = world.tick
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
    def _apply_updates(cls, world: WorldState, actor: Entity, updates: list[IntentUpdate], proposal: ActionProposal) -> None:
        """Apply typed simulation side-effects (AOA Phase 5)."""
        from src.actions.base import MindUpdate, PerceptionUpdate, ProgressionUpdate, NavigationUpdate, SocialUpdate, RoutineUpdate
        
        for up in updates:
            # Stage 5: Multi-entity update support
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
                
                # Grudge / Emotion handling
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
                    from src.ai.beliefs import BeliefService
                    for target_id, new_belief in up.entity_memory.items():
                        BeliefService.merge_indirect_belief(entity, new_belief)
                if up.memory_log_add:
                    log = entity.mind.narrative.memory_log
                    log.extend(up.memory_log_add)
                    
                    # Phase 2: Intelligent Salience Pruning
                    from src.core.logic.memory_salience import MemorySalienceService
                    MemorySalienceService.prune(entity, world.tick, max_entries=50)
                
                if up.memory_locations_set:
                    entity.mind.narrative.memory_locations.update(up.memory_locations_set)

            elif isinstance(up, NavigationUpdate):
                nav = entity.mind.navigation
                if up.pos_history:
                    # AOA Stabilization: Replace history instead of extending to prevent bloat.
                    # The AI sends the full intended history (usually last 20 ticks).
                    nav.pos_history = up.pos_history[-20:]
                if up.cached_path is not None:
                    nav.cached_path = up.cached_path
                if up.target_pos is not None:
                    nav.cached_path_target = up.target_pos
                if up.chase_ticks is not None:
                    nav.chase_ticks = up.chase_ticks

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
                        if si:
                            si.cooldown_remaining = cd
                
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

                if up.effects_expire_all:
                    for etype in up.effects_expire_all:
                        for eff in entity.combat.effects:
                            if eff.effect_type == etype:
                                eff.remaining_ticks = 0

            elif isinstance(up, RoutineUpdate):
                # Phase 2 Stage 3: Authoritative biological state update
                if up.hunger_delta:
                    entity.mind.routine.hunger_level = max(0.0, min(1.0, entity.mind.routine.hunger_level + up.hunger_delta))
                if up.sleep_delta:
                    entity.mind.routine.sleep_debt = max(0.0, min(1.0, entity.mind.routine.sleep_debt + up.sleep_delta))
                if up.is_sleeping is not None:
                    entity.mind.routine.is_sleeping = up.is_sleeping

            elif isinstance(up, SpatialUpdate):
                # AOA Stabilization: Authoritative position update via WorldState
                # This ensures the spatial index is updated for AoE and navigation.
                world.move_entity(entity.id, up.new_pos)
                if up.facing:
                    entity.spatial.facing = up.facing
                if up.region_id:
                    entity.spatial.region_id = up.region_id

            elif isinstance(up, CombatTraceUpdate):
                # Authoritative Combat Result Application (Refactored for Mutation Purity)
                res = up.result
                target = world.entities.get(res.defender_id)
                if target and target.combat.alive:
                    target.combat.hp = max(0, target.combat.hp - res.damage)
                    
                    # AOA Stabilization: Handle Shattered (Frozen) expiration on target
                    if res.details and getattr(res.details, "is_shattered", False):
                        from src.core.gameplay.effects import EffectType
                        for eff in target.combat.effects:
                            if eff.effect_type == EffectType.FROZEN:
                                eff.remaining_ticks = 0
                    
                    # Generate Threat and Grudge on target (Defender)
                    # Use normalized fields from the proposal phase
                    threat_val = res.threat if res.threat > 0 else float(res.damage)
                    target.mind.perception.threat_table[entity.id] = target.mind.perception.threat_table.get(entity.id, 0.0) + threat_val
                    
                    grudge_val = res.grudge if res.grudge > 0 else float(res.damage) / 10.0
                    target.mind.emotion.grudges[entity.id] = target.mind.emotion.grudges.get(entity.id, 0.0) + grudge_val
                    
                    # Store trace for introspection (ring buffer)
                    target.combat.traces.append(res)
                    if len(target.combat.traces) > 20:
                        target.combat.traces = target.combat.traces[-20:]
                    
                    # Handle Trauma log if massive damage occurred (Use PerceptionUpdate)
                    if res.trauma > 0:
                        from src.core.aspects.mind import InterpretedEvent
                        from src.actions.base import PerceptionUpdate
                        cls._apply_updates(world, target, [PerceptionUpdate(
                            memory_log_add=[InterpretedEvent(
                                tick=world.tick, type="trauma", impact=-res.trauma,
                                details={"desc": f"Took massive damage ({res.damage}) from {entity.identity.display_name} #{entity.id}", "source_id": entity.id}
                            )]
                        )], proposal)
                    
                    # AOA Stabilization: Record Survival memory when hanging on by a thread
                    hp_ratio = target.combat.hp / max(1, target.combat.max_hp)
                    if target.combat.hp > 0 and hp_ratio < 0.2:
                        from src.core.aspects.mind import InterpretedEvent
                        from src.actions.base import PerceptionUpdate
                        
                        # Check local recent survival to prevent log spam
                        recent_survival = any(m.type == "survival" and m.tick > world.tick - 5 for m in target.mind.narrative.memory_log)
                        if not recent_survival:
                            cls._apply_updates(world, target, [PerceptionUpdate(
                                memory_log_add=[InterpretedEvent(
                                    tick=world.tick, type="survival", impact=-3.0,
                                    details={"desc": f"Nearly killed by {entity.identity.display_name} #{entity.id} (HP: {int(hp_ratio*100)}%)", "source_id": entity.id}
                                )]
                            )], proposal)

                    # NOTE: Memory pruning is already handled inside cls._apply_updates(PerceptionUpdate)
                    
                    # NOTE: Kill Recognition (Corpses, Rewards) moved to the proposal phase 
                    # for better visibility and deterministic capture.

            elif isinstance(up, WorldUpdate):
                # Authoritative World Mutation (Pillar 1 Stabilization)
                if up.new_corpse:
                    # Resolve ID if not already set (e.g. from workers)
                    node = up.new_corpse
                    if node.node_id == 0 and up.increment_corpse_id:
                        node.node_id = world._next_corpse_id
                        world._next_corpse_id += 1
                    
                    # Add to world state and spatial index
                    world.corpse_nodes[node.node_id] = node
                    # (Spatial index for nodes if applicable, but usually they are just static objects)
                    logger.info("Authoritatively created corpse node %d at %s", node.node_id, node.pos)

            elif isinstance(up, ReputationUpdate):
                # Phase 2: Authoritative Reputation Profile Mutation
                from src.core.logic.reputation_service import ReputationService
                ReputationService.apply_update(entity, up)

            elif isinstance(up, BuildingUpdate):
                # Authoritative Building Mutation (Pillar 1 Stabilization)
                target_b = next((b for b in world.buildings if b.building_id == up.building_id), None)
                if target_b:
                    if up.damage_amount > 0:
                        target_b.take_damage(up.damage_amount)
                        logger.info("Authoritative damage on building %s: %d", up.building_id, up.damage_amount)
                    if up.repair_amount > 0:
                        target_b.repair(up.repair_amount)
                        logger.info("Authoritative repair on building %s: %d", up.building_id, up.repair_amount)
                    if up.is_destroyed:
                        target_b.is_functional = False

            elif isinstance(up, InteractionUpdate):
                # AOA Stabilization: Authoritative interaction side-effects
                if up.corpse_id_to_remove is not None:
                    world.corpse_nodes.pop(up.corpse_id_to_remove, None)
                
                if up.home_storage_add:
                    # Logic for home storage if entity has one (standardizing update pattern)
                    pass
                if up.home_storage_remove:
                    pass
                
            elif isinstance(up, SocialUpdate):
                # Phase 2: Authoritative Social Registry Mutation
                from src.core.logic.relationship_service import RelationshipService
                RelationshipService.apply_update(world.social_registry, up, world.tick)
                
                # Fetch bond for milestone detection (simplified for transition)
                bond = world.social_registry.get_bond(up.source_id, up.target_id)
                old_vals = {
                    "trust": bond.trust - up.trust_delta,
                    "fear": bond.fear - up.fear_delta,
                    "rivalry": bond.rivalry - up.rivalry_delta,
                    "loyalty": bond.loyalty - up.loyalty_delta
                }
                new_vals = {
                    "trust": bond.trust,
                    "fear": bond.fear,
                    "rivalry": bond.rivalry,
                    "loyalty": bond.loyalty
                }
                
                # Phase 2: Narrative Milestone Detection
                from src.core.aspects.mind import SocialNarrative, InterpretedEvent
                from src.actions.base import PerceptionUpdate
                
                milestones = []
                # Trust Milestones
                for threshold, label in [(0.5, "ally"), (0.2, "friendly"), (-0.2, "distrust"), (-0.5, "hostile")]:
                     # Check if we crossed the threshold (in either direction)
                     if (old_vals["trust"] < threshold <= new_vals["trust"]) or (old_vals["trust"] >= threshold > new_vals["trust"]):
                         milestones.append(("trust", label, old_vals["trust"], new_vals["trust"]))
                
                # Rivalry Milestones
                if old_vals["rivalry"] < 0.8 <= new_vals["rivalry"]:
                    milestones.append(("rivalry", "nemesis", old_vals["rivalry"], new_vals["rivalry"]))
                
                if milestones:
                    for bond_type, label, old_v, new_v in milestones:
                        narrative = SocialNarrative(
                            target_id=up.target_id,
                            change_type=f"milestone_{label}",
                            bond_type=bond_type,
                            old_value=old_v,
                            new_value=new_v
                        )
                        entry = InterpretedEvent(
                            tick=world.tick,
                            type="social",
                            impact=abs(new_v - old_v) + 0.5, # Base narrative impact
                            details=narrative
                        )
                        # Emit a NEW update to the same entity (the one perceiving the change)
                        # Note: We append to 'updates' so the current loop picks it up immediately.
                        updates.append(PerceptionUpdate(memory_log_add=[entry]))

            elif isinstance(up, RoutineUpdate):
                # Phase 3: Biological State Transitions
                routine = entity.mind.routine
                if up.sleep_delta:
                    routine.sleep_debt = max(0.0, min(1.0, routine.sleep_debt + up.sleep_delta))
                if up.hunger_delta:
                    routine.hunger_level = max(0.0, min(1.0, routine.hunger_level + up.hunger_delta))
                if up.is_sleeping is not None:
                    routine.is_sleeping = up.is_sleeping

    @classmethod
    def _apply_biological_decay(cls, world: WorldState, config: SimulationConfig) -> None:
        """Authoritative time-based needs increment. [PHASE 3]"""
        for entity in world.entities.values():
            if not entity.combat.alive:
                continue
                
            routine = entity.mind.routine
            # 1. Steady accumulation
            routine.sleep_debt = max(0.0, min(1.0, routine.sleep_debt + config.sleep_decay_rate))
            routine.hunger_level = max(0.0, min(1.0, routine.hunger_level + config.hunger_decay_rate))
            
            # 2. Forced Sleep (Pass out if debt is critical)
            if routine.sleep_debt >= 1.0 and not routine.is_sleeping:
                routine.is_sleeping = True

            # 3. Recovery if sleeping
            if routine.is_sleeping:
                routine.sleep_debt = max(0.0, routine.sleep_debt - config.sleep_recovery_rate)
                if routine.sleep_debt <= 0.0:
                    routine.is_sleeping = False
                    
            # 3. [STAGE 5] Region Fatigue and Territory accumulation
            rid = entity.spatial.current_region_id
            if rid:
                current_fatigue = entity.mind.narrative.region_fatigue.get(rid, 0.0)
                # Increments slowly (0.01 per tick = 1.0 in 100 ticks)
                # Increments slowly (0.01 per tick = 1.0 in 100 ticks)
                entity.mind.narrative.region_fatigue[rid] = min(1.0, current_fatigue + 0.005)
    
    @classmethod
    def _get_use_skill_updates(cls, world: WorldState, config: SimulationConfig, rng: DeterministicRNG, faction_reg: FactionRegistry | None, entity: Entity, skill_id: str, target_id: int | None = None, proposal: ActionProposal | None = None, emit: Callable | None = None, ignore_skill_check: bool = False) -> list[IntentUpdate]:
        """Functional side-effects for skill usage. [AOA STABILIZATION]"""
        updates: list[IntentUpdate] = []
        # Support both 'Attack' and 'Basic Attack' as aliases for the fallback
        if skill_id == "Attack": skill_id = "Basic Attack"
        
        sdef = SKILL_DEFS.get(skill_id)
        if not sdef: return updates
        
        # 0. Basic Attack / Action check bypass [AOA STABILIZATION]
        if not ignore_skill_check:
            instance = next((si for si in entity.progression.skills if si.skill_id == skill_id), None)
            if not instance or not instance.is_ready(): return updates
            
            # 1. Cooldown/Stamina
            cost = instance.effective_stamina_cost(sdef.stamina_cost)
            if entity.progression.stamina < cost: return updates
            
            updates.append(ProgressionUpdate(
                stamina_delta=-cost,
                skill_cooldowns={skill_id: sdef.cooldown}
            ))
            power = instance.effective_power(sdef.power)
        else:
            # Fallback for entities without explicit skill instance (e.g. mobs or test entities)
            power = sdef.power
        # 2. Target Selection (AoE or Single)
        targets: list[Entity] = []
        if sdef.radius > 0:
            # AOA Pillar 4: Spatial Query Logic
            # Use target entity's pos, or proposal.target (landing spot), or default to self.
            from src.core.models.vectors import Vector2
            center = entity.spatial.pos
            if target_id and world.entities.get(target_id):
                center = world.entities[target_id].spatial.pos
            elif proposal and isinstance(proposal.target, Vector2):
                center = proposal.target
            potential = world.entities_at_radius(center, sdef.radius)
            for t in potential:
                if t.id != entity.id and t.combat.alive:
                    # AOA Stabilization: Robust hostile check with fallback
                    is_hostile = True
                    if faction_reg:
                        is_hostile = faction_reg.is_hostile(entity.identity.faction, t.identity.faction)
                    else:
                        is_hostile = (entity.identity.faction != t.identity.faction)
                        
                    if is_hostile:
                        targets.append(t)
        elif target_id:
            t = world.entities.get(target_id)
            if t and t.combat.alive: targets.append(t)
            
        # 3. Apply Damage and generate TraceUpdates
        from src.actions.combat import DamageResolutionService, CombatAftermathService
        for t in targets:
            damage, is_crit, is_evaded, trace_details = DamageResolutionService.resolve(
                attacker=entity,
                defender=t,
                world=world,
                config=config,
                skill_id=skill_id,
                power=power,
                rng=rng,
                faction_reg=faction_reg,
                override_damage_type=sdef.damage_type,
                override_element=sdef.element
            )
            
            # AFTERMATH (Memory, Grudges, Threat, Trace Update Generation)
            # In AOA, CombatAftermathService.process appends the CombatTraceUpdate to proposal.updates
            CombatAftermathService.process(
                attacker=entity,
                defender=t,
                world=world,
                damage=damage,
                is_crit=is_crit,
                is_evasion=is_evaded,
                config=config,
                proposal=proposal,
                trace_details=trace_details
            )
            
            # Update trace with skill-specific metadata
            for up in proposal.updates:
                if isinstance(up, CombatTraceUpdate) and (up.result.skill_name == "SKILL" or up.result.skill_name is None):
                    up.result.skill_name = sdef.name
                    up.result.metadata["aoe"] = sdef.radius > 0
                    up.result.metadata["power"] = power
            
            # Synchronize proposal updates into local returns
            if proposal and proposal.updates:
                for up in proposal.updates:
                    if up not in updates:
                        updates.append(up)
                        
            if emit:
                emit("combat", f"{entity.kind} hit {t.kind} with {sdef.name}",
                     (entity.id, t.id),
                     {"skill_id": skill_id, "skill_name": sdef.name, "damage": damage, "verb": "skill", "aoe": sdef.radius > 0})

        return updates

    @staticmethod
    def _get_use_item_updates(world: WorldState, config: SimulationConfig, entity: Entity, item_id: str) -> list[IntentUpdate]:
        updates: list[IntentUpdate] = []
        if entity.inventory and item_id in entity.inventory.items:
            template = ITEM_REGISTRY.get(item_id)
            if template:
                updates.append(ProgressionUpdate(inventory_remove=[item_id]))
                if template.heal_amount > 0:
                    updates.append(ProgressionUpdate(hp_delta=template.heal_amount))
                if template.hunger_reduction > 0:
                    updates.append(RoutineUpdate(hunger_delta=-template.hunger_reduction))
        return updates

    @staticmethod
    def _get_looting_updates(world: WorldState, entity: Entity, pos: Any) -> list[IntentUpdate]:
        updates: list[IntentUpdate] = []
        
        # 1. Ground Items
        items = world.pickup_items(pos)
        if items:
            updates.append(ProgressionUpdate(inventory_add=items))
            
        # 2. Corpse Nodes (AOA Stabilization: Unified Looting)
        # Search for corpse nodes at this position
        for nid, node in list(world.corpse_nodes.items()):
            if node.pos == pos:
                corpse_items = node.items or []
                corpse_gold = node.gold or 0
                
                if corpse_items or corpse_gold > 0:
                    updates.append(ProgressionUpdate(
                        inventory_add=corpse_items,
                        gold_delta=corpse_gold
                    ))
                
                # Mark for removal in the authoritative pipeline
                updates.append(InteractionUpdate(corpse_id_to_remove=nid))
                
                # [STAGE 5] Loot Narrative
                from src.core.aspects.mind import InterpretedEvent, LootNarrative
                loot_event = InterpretedEvent(
                    tick=world.tick,
                    type="loot",
                    impact=0.2 + (corpse_gold * 0.01),
                    details=LootNarrative(
                        gold_amount=corpse_gold,
                        source=f"corpse_{node.entity_id}"
                    )
                )
                updates.append(PerceptionUpdate(memory_log_add=[loot_event]))
                
        return updates

    @staticmethod
    def _get_harvesting_updates(world: WorldState, entity: Entity, pos: Any) -> list[IntentUpdate]:
        updates: list[IntentUpdate] = []
        node = world.resource_at(pos)
        if node and node.is_available:
            item_id = node.harvest()
            if item_id:
                updates.append(ProgressionUpdate(inventory_add=[item_id], stamina_delta=-2))
        return updates

    @classmethod
    def _process_social_interpretation(
        cls, 
        world: WorldState, 
        actor: Entity, 
        updates: list[IntentUpdate], 
        proposal: ActionProposal
    ) -> None:
        """Analyze applied updates to detect and apply social life events."""
        from src.actions.base import CombatTraceUpdate, SpatialUpdate
        
        # 1. Combat Events (Aftermath)
        for up in updates:
            if isinstance(up, CombatTraceUpdate):
                defender = world.get_entity(up.result.defender_id)
                if defender:
                    events = EventInterpreterService.interpret_combat_aftermath(actor, defender, up.result, world)
                    for event in events:
                        SocialStateApplicator.apply_interpreted_event(event, world)

        # 2. Positional/Tactical Events
        spatial_up = next((u for u in updates if isinstance(u, SpatialUpdate)), None)
        if spatial_up:
            event = EventInterpreterService.interpret_tactical_outcome(world, actor, spatial_up)
            if event:
                SocialStateApplicator.apply_interpreted_event(event, world)

    @classmethod
    def _process_proximity_gossip(cls, world: WorldState, actor: Entity, updates: list[IntentUpdate]) -> None:
        """Triggers gossip between actor and nearby entities if they have proximity history."""
        # Simple proximity check: entities within 5 range
        for other in world.entities.values():
            if other.id == actor.id or not other.combat.alive:
                continue
            
            dist = actor.spatial.pos.manhattan(other.spatial.pos)
            if dist <= 5:
                # Proximity exists — trigger gossip from actor to other
                up = KnowledgePropagationService.propagate_gossip(actor, other, world)
                if up:
                    updates.append(up)
                    
                # Reciprocal gossip (Other to Actor)
                up_back = KnowledgePropagationService.propagate_gossip(other, actor, world)
                if up_back:
                    updates.append(up_back)

    def _update_ai_derived_states(self, context: SystemContext, applied: list[ActionProposal]) -> None:
        world = context.world
        for p in applied:
            entity = world.entities.get(p.actor_id)
            if not entity or not entity.combat.alive: continue
            
            state = entity.mind.decision.ai_state
            if state == AIState.HUNT:
                entity.mind.navigation.chase_ticks += 1
            else:
                entity.mind.navigation.chase_ticks = 0
            
            if state == AIState.IDLE:
                entity.mind.decision.consecutive_idle_ticks += 1
            else:
                entity.mind.decision.consecutive_idle_ticks = 0

    def _update_combat_visualization(self, context: SystemContext, applied: list[ActionProposal]) -> None:
        """Placeholder for visualization-specific side effects (e.g. particle emissions).
        
        Currently, most combat events are emitted directly via CombatAftermathService.
        """
        pass
