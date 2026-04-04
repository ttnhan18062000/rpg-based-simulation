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
    PerceptionUpdate, ProgressionUpdate, IdentityUpdate, InteractionUpdate, SpatialUpdate
)
from src.core.gameplay.items.item_registry import ITEM_REGISTRY
from src.core.gameplay.classes import SKILL_DEFS
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
        for proposal in applied:
            entity = world.entities.get(proposal.actor_id)
            if entity is None or not entity.combat.alive:
                continue

            # Unified Update Collection
            all_updates: list[IntentUpdate] = []
            if proposal.updates:
                all_updates.extend(proposal.updates)

            # 1. Direct State Transitions (AI Internal)
            if proposal.new_ai_state is not None:
                new_state = AIState(proposal.new_ai_state)
                if new_state != entity.mind.decision.ai_state:
                    entity.mind.decision.ai_state = new_state
                    if entity.mind.decision.goal_committed_at == 0:
                         entity.mind.decision.goal_committed_at = world.tick
            if proposal.reason:
                entity.mind.decision.last_reason = proposal.reason

            # 2. Update Generation (Functional Side-Effects)
            if proposal.verb == ActionType.USE_ITEM and proposal.target:
                all_updates.extend(cls._get_use_item_updates(world, config, entity, proposal.target))
            elif proposal.verb == ActionType.LOOT:
                all_updates.extend(cls._get_looting_updates(world, entity, proposal.target))
            elif proposal.verb == ActionType.HARVEST and proposal.target:
                all_updates.extend(cls._get_harvesting_updates(world, entity, proposal.target))
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

            # 3. Final Application (Authoritative Pipeline)
            if all_updates:
                cls._apply_updates(world, entity, all_updates, proposal)

            # 4. Attribute Training
            from src.core.gameplay.attributes import train_attributes
            verb_name = proposal.verb.name if hasattr(proposal.verb, "name") else ActionType(proposal.verb).name
            train_attributes(entity, verb_name.lower())

            # 5. Cooldown Management
            speed = entity.combat.spd
            entity.next_act_at += 1.0 / max(0.1, speed / 10.0)

    @classmethod
    def _apply_updates(cls, world: WorldState, entity: Entity, updates: list[IntentUpdate], proposal: ActionProposal) -> None:
        """Apply typed simulation side-effects (AOA Phase 5)."""
        from src.actions.base import MindUpdate, PerceptionUpdate, ProgressionUpdate, NavigationUpdate
        
        for up in updates:
            if isinstance(up, MindUpdate):
                decision = entity.mind.decision
                if up.new_ai_state is not None:
                    decision.ai_state = up.new_ai_state
                if up.goal_scores:
                    decision.goal_scores = up.goal_scores
                if up.last_goal:
                    decision.last_goal = up.last_goal
                
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
                    entity.mind.perception.entity_memory.update(up.entity_memory)
                if up.memory_log_add:
                    log = entity.mind.narrative.memory_log
                    log.extend(up.memory_log_add)
                    # Capping memory log to prevent O(T^2) deep-copy bloat (AOA Stabilization)
                    if len(log) > 50:
                        entity.mind.narrative.memory_log = log[-50:]
                
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
                
                if up.stamina_delta:
                    entity.progression.stamina = max(0, min(entity.progression.max_stamina, entity.progression.stamina + up.stamina_delta))
                
                if up.gold_delta: entity.progression.gold += up.gold_delta
                if up.xp_delta: entity.progression.xp += up.xp_delta
                
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

            elif isinstance(up, SpatialUpdate):
                # AOA Stabilization: Authoritative position update via WorldState
                # This ensures the spatial index is updated for AoE and navigation.
                world.move_entity(entity.id, up.new_pos)
                if up.facing:
                    entity.spatial.facing = up.facing
                if up.region_id:
                    entity.spatial.region_id = up.region_id

            elif isinstance(up, CombatTraceUpdate):
                # Authoritative Combat Result Application
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
                    # AOA Stabilization: Use threat from metadata (which includes class multipliers)
                    threat_val = res.metadata.get("threat", float(res.damage))
                    target.mind.perception.threat_table[entity.id] = target.mind.perception.threat_table.get(entity.id, 0.0) + threat_val
                    
                    grudge_val = res.metadata.get("grudge", float(res.damage) / 10.0)
                    target.mind.emotion.grudges[entity.id] = target.mind.emotion.grudges.get(entity.id, 0.0) + grudge_val
                    
                    # Store trace for introspection (ring buffer)
                    target.combat.traces.append(res)
                    if len(target.combat.traces) > 20:
                        target.combat.traces = target.combat.traces[-20:]
                    
                    # Handle Trauma log if massive damage occurred
                    if "trauma" in res.metadata:
                        from src.core.aspects.mind import MemoryLogEntry
                        trauma_impact = res.metadata["trauma"]
                        target.mind.narrative.memory_log.append(MemoryLogEntry(
                            tick=world.tick, type="trauma", impact=-trauma_impact,
                            details={"desc": f"Took massive damage ({res.damage}) from {entity.identity.display_name} #{entity.id}", "source_id": entity.id}
                        ))
                    
                    # AOA Stabilization: Record Survival memory when hanging on by a thread (<20% HP)
                    # This drives the "survival" bias in flee/prevention scores.
                    hp_ratio = target.combat.hp / max(1, target.combat.max_hp)
                    if target.combat.hp > 0 and hp_ratio < 0.2:
                        from src.core.aspects.mind import MemoryLogEntry
                        # Check if we already recorded a survival event this tick or recently
                        recent_survival = any(m.type == "survival" and m.tick > world.tick - 5 for m in target.mind.narrative.memory_log)
                        if not recent_survival:
                            target.mind.narrative.memory_log.append(MemoryLogEntry(
                                tick=world.tick, type="survival", impact=-3.0,
                                details={"desc": f"Nearly killed by {entity.identity.display_name} #{entity.id} (HP: {int(hp_ratio*100)}%)", "source_id": entity.id}
                            ))

                    if len(target.mind.narrative.memory_log) > 50:
                        target.mind.narrative.memory_log = target.mind.narrative.memory_log[-50:]
                    
                    # AOA Stabilization: Authoritative Kill Recognition
                    # Triggered only when HP reaches 0 during a CombatTraceUpdate (Pillar 3/Pillar 5 convergence)
                    if not target.combat.alive:
                        from src.actions.combat import KillRewardService
                        KillRewardService.resolve_kill(entity, target, world, proposal)

            elif isinstance(up, InteractionUpdate):
                # AOA Stabilization: Authoritative interaction side-effects
                if up.corpse_id_to_remove is not None:
                    world.corpse_nodes.pop(up.corpse_id_to_remove, None)
                
                if up.home_storage_add:
                    # Logic for home storage if entity has one (standardizing update pattern)
                    pass
                if up.home_storage_remove:
                    pass

    @classmethod
    def _get_use_skill_updates(cls, world: WorldState, config: SimulationConfig, rng: DeterministicRNG, faction_reg: FactionRegistry | None, entity: Entity, skill_id: str, target_id: int | None = None, proposal: ActionProposal | None = None, emit: Callable | None = None) -> list[IntentUpdate]:
        """Functional side-effects for skill usage. [AOA STABILIZATION]"""
        updates: list[IntentUpdate] = []
        sdef = SKILL_DEFS.get(skill_id)
        if not sdef: return updates
        
        instance = next((si for si in entity.progression.skills if si.skill_id == skill_id), None)
        if not instance or not instance.is_ready(): return updates
        
        # 1. Cooldown/Stamina
        cost = instance.effective_stamina_cost(sdef.stamina_cost)
        if entity.progression.stamina < cost: return updates
        
        updates.append(ProgressionUpdate(
            stamina_delta=-cost,
            skill_cooldowns={skill_id: sdef.cooldown}
        ))
        
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
        power = instance.effective_power(sdef.power)
        from src.actions.combat import DamageResolutionService, CombatAftermathService
        for t in targets:
            damage, is_crit, is_evaded, trace_details = DamageResolutionService.resolve(
                attacker=entity,
                defender=t,
                world=world,
                config=config,
                rng=rng,
                skill_power=power,
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

    def handle_tactical_maneuvers(self, context: SystemContext, applied: list[ActionProposal], pre_positions: dict) -> None:
        """Process opportunity attacks."""
        self._process_opportunity_attacks(context, applied, pre_positions)

    def _process_opportunity_attacks(self, context: SystemContext, applied: list[ActionProposal], pre_positions: dict) -> None:
        world = context.world
        reg = context.faction_reg
        mult = context.config.opportunity_attack_damage_mult
        
        for proposal in applied:
            if proposal.verb != ActionType.MOVE: continue
            mover = world.entities.get(proposal.actor_id)
            if not mover or not mover.combat.alive: continue
            old_pos = pre_positions.get(proposal.actor_id)
            if not old_pos: continue
            
            for eid, ent in world.entities.items():
                if eid == mover.id or not ent.combat.alive: continue
                if not reg.is_hostile(mover.identity.faction, ent.identity.faction): continue
                
                # Manhattan adjacency to old position
                if abs(ent.spatial.pos.x - old_pos.x) + abs(ent.spatial.pos.y - old_pos.y) == 1:
                    raw = max(1, int(ent.combat.atk * mult) - mover.combat.def_ // 2)
                    mover.combat.hp = max(0, mover.combat.hp - raw)
                    
                    context.emit("combat", f"{ent.id} used opportunity attack on {mover.id}",
                                 (ent.id, mover.id),
                                 {"attacker_id": ent.id, "damage": raw, "skill_id": "OPPORTUNITY_ATTACK"})

    def _update_combat_visualization(self, context: SystemContext, applied: list[ActionProposal]) -> None:
        world = context.world
        acted = {p.actor_id for p in applied}
        for p in applied:
            actor = world.entities.get(p.actor_id)
            if actor and p.verb in (ActionType.ATTACK, ActionType.USE_SKILL):
                actor.combat.combat_target_id = p.target
        
        for entity in world.entities.values():
            if entity.id not in acted:
                if entity.mind.decision.ai_state not in (AIState.COMBAT, AIState.HUNT):
                    entity.combat.combat_target_id = None

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
