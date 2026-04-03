"""ActionSystem handles post-resolution state mutations and tactical maneuvers.

Refactored for AOA Stabilization:
- Direct aspect access (spatial, combat, mind, progression).
- Explicit application of typed IntentUpdate records from side-effect-free AI decisions.
- Standardized state transitions and derived counter updates.
"""

from __future__ import annotations
import logging
import math
from typing import TYPE_CHECKING, Any
from src.core.models.enums import AIState, ActionType, Element, GoalType, EmotionType, HeroClass
from src.core.entities.entity import Entity
from src.actions.base import (
    ActionProposal, IntentUpdate, MindUpdate, NavigationUpdate, CombatTraceUpdate,
    PerceptionUpdate, ProgressionUpdate, IdentityUpdate, InteractionUpdate
)
from src.core.gameplay.items.item_registry import ITEM_REGISTRY
from src.core.gameplay.classes import SKILL_DEFS
from src.systems.infrastructure.base import System

if TYPE_CHECKING:
    from src.actions.base import ActionProposal
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
        emit: Callable | None = None,
        faction_reg: FactionRegistry | None = None
    ) -> None:
        """Core side-effects that MUST be applied identically in live and replay/recovery."""
        for proposal in applied:
            entity = world.entities.get(proposal.actor_id)
            if entity is None or not entity.combat.alive:
                continue

            # Unified Update Collection
            all_updates: list[IntentUpdate] = []
            if proposal.updates:
                all_updates.extend(proposal.updates)

            # 1. State Transitions (AI Internal)
            if proposal.new_ai_state is not None:
                new_state = AIState(proposal.new_ai_state)
                if new_state != entity.mind.decision.ai_state:
                    entity.mind.decision.ai_state = new_state
                    if entity.mind.decision.goal_committed_at == 0:
                         entity.mind.decision.goal_committed_at = world.tick
            if proposal.reason:
                entity.mind.decision.last_reason = proposal.reason

            # 2. Verb-Specific Logic (Update Generation)
            if proposal.verb == ActionType.ATTACK and isinstance(proposal.target, int):
                target = world.entities.get(proposal.target)
                if target and target.combat.alive:
                    damage = 0
                    for up in proposal.updates:
                        if isinstance(up, CombatTraceUpdate):
                            damage = up.damage
                            break
                    if damage > 0:
                        # 1. Threat Generation
                        mult = 1.5 if entity.progression.hero_class == HeroClass.WARRIOR else 1.0
                        target.mind.perception.threat_table[entity.id] = target.mind.perception.threat_table.get(entity.id, 0.0) + damage * mult
                        
                        # 2. Emotion & Memory Generation (AOA Pillar 2: Phased Appraisal)
                        # High-tier enemies (tier > 0) generate grudges and trauma
                        if entity.identity.tier > 0 or "boss" in entity.kind.lower():
                            # Grudge update
                            target.mind.emotion.grudges[entity.id] = target.mind.emotion.grudges.get(entity.id, 0.0) + (damage / 10.0)
                            
                            # Trauma Memory Log (if damage is significant > 5% max HP)
                            if damage > (target.combat.max_hp * 0.05):
                                from src.core.aspects.mind import MemoryLogEntry, CombatNarrative
                                trauma_entry = MemoryLogEntry(
                                    tick=world.tick,
                                    type="trauma",
                                    impact=-0.2, # Negative impact
                                    details=CombatNarrative(
                                        target_id=entity.id,
                                        target_kind=entity.kind,
                                        damage_dealt=damage,
                                        was_fatal=not target.combat.alive
                                    )
                                )
                                target.mind.narrative.memory_log.append(trauma_entry)
                        
                        # 3. Combat Trace Recording (Target side)
                        for up in proposal.updates:
                            if isinstance(up, CombatTraceUpdate) and target.combat:
                                from src.core.aspects.combat import CombatTraceRecord
                                target.combat.traces.append(CombatTraceRecord(
                                    tick=up.tick,
                                    attacker_id=up.attacker_id,
                                    defender_id=up.defender_id,
                                    damage=up.damage,
                                    is_crit=up.is_crit,
                                    is_evasion=up.is_evasion,
                                    skill_used=up.skill_used,
                                    raw_damage=up.details.raw_damage,
                                    mitigated_damage=up.details.mitigated_damage,
                                    absorbed_damage=up.details.absorbed_damage,
                                    crit_multiplier=up.details.crit_multiplier,
                                    evasion_chance=up.details.evasion_chance,
                                    elemental_mult=up.details.elemental_mult
                                ))

            if proposal.verb == ActionType.USE_ITEM and proposal.target:
                all_updates.extend(cls._get_use_item_updates(world, config, entity, proposal.target))
            elif proposal.verb == ActionType.LOOT:
                all_updates.extend(cls._get_looting_updates(world, entity, proposal.target))
            elif proposal.verb == ActionType.HARVEST and proposal.target:
                all_updates.extend(cls._get_harvesting_updates(world, entity, proposal.target))
            elif proposal.verb == ActionType.USE_SKILL and proposal.target:
                # Handle both single target_id and [skill_id, target_id] tuple/list
                t = proposal.target
                if isinstance(t, (list, tuple)) and len(t) == 2:
                    sid, tid = t
                else:
                    sid, tid = t, None # Fallback (should be handled by callers)
                
                all_updates.extend(cls._get_use_skill_updates(world, config, faction_reg, entity, sid, tid, emit=emit))

            # 3. Final Application (Unambiguous Entry Point)
            if all_updates:
                cls._apply_updates(world, entity, all_updates)

            # 4. Attribute Training
            from src.core.gameplay.attributes import train_attributes
            verb_name = proposal.verb.name if hasattr(proposal.verb, "name") else ActionType(proposal.verb).name
            train_attributes(entity, verb_name.lower())

            # 5. Cooldown Management
            speed = entity.combat.spd
            entity.next_act_at += 1.0 / max(0.1, speed / 10.0)


    @staticmethod
    def _apply_updates(world: WorldState, entity: Entity, updates: list[IntentUpdate]) -> None:
        """Apply typed simulation side-effects (AOA Phase 5)."""

        for up in updates:
            if isinstance(up, MindUpdate):
                decision = entity.mind.decision
                if up.goal_scores:
                    decision.goal_scores = up.goal_scores
                if up.last_goal:
                    decision.last_goal = up.last_goal
                if up.goal_committed_at is not None:
                    decision.goal_committed_at = up.goal_committed_at
                if up.boredom_delta:
                    decision.boredom_multipliers.update(up.boredom_delta)
                if up.new_ai_state is not None:
                    decision.ai_state = AIState(up.new_ai_state)
                if up.consecutive_idle_ticks is not None:
                    decision.consecutive_idle_ticks = up.consecutive_idle_ticks
                if up.goals_add:
                    for g in up.goals_add:
                        if g not in decision.goals:
                            decision.goals.append(g)
                if up.goals_remove:
                    for g in up.goals_remove:
                        if g in decision.goals:
                            decision.goals.remove(g)
                
                emotion = entity.mind.emotion
                if up.emotion_delta:
                    for k, v in up.emotion_delta.items():
                        if k == EmotionType.PANIC: emotion.panic = max(0.0, min(1.0, emotion.panic + v))
                        elif k == EmotionType.STUCK: emotion.stuck = max(0.0, min(1.0, emotion.stuck + v))
                        elif k == EmotionType.BRAVERY: emotion.bravery = max(0.0, min(1.0, emotion.bravery + v))
                if up.emotion_set:
                    for k, v in up.emotion_set.items():
                        if k == EmotionType.PANIC: emotion.panic = v
                        elif k == EmotionType.STUCK: emotion.stuck = v
                        elif k == EmotionType.BRAVERY: emotion.bravery = v
                if up.mood is not None:
                    emotion.mood = up.mood
                if up.grudge_delta:
                    for eid, delta in up.grudge_delta.items():
                        emotion.grudges[eid] = emotion.grudges.get(eid, 0.0) + delta
            
            elif isinstance(up, PerceptionUpdate):
                perc = entity.mind.perception
                if up.entity_memory:
                    # Force coercion of dicts to MemoryRecord (AOA Stabilization)
                    from src.core.aspects.mind import MemoryRecord
                    for eid, rec in up.entity_memory.items():
                        if isinstance(rec, dict):
                            perc.entity_memory[eid] = MemoryRecord.model_validate(rec)
                        else:
                            perc.entity_memory[eid] = rec
                
                if up.memory_stale_delta:
                    for eid, delta in up.memory_stale_delta.items():
                        perc.memory_stale_ticks[eid] = perc.memory_stale_ticks.get(eid, 0) + delta
                if up.memory_remove:
                    for eid in up.memory_remove:
                        perc.entity_memory.pop(eid, None)
                        perc.memory_stale_ticks.pop(eid, None)
                if up.attention_pool is not None:
                    perc.attention_pool = up.attention_pool
                if up.terrain_memory:
                    perc.terrain_memory.update(up.terrain_memory)
                if up.memory_log_add:
                    entity.mind.narrative.memory_log.extend(up.memory_log_add)
                if up.threat_table_delta:
                    for eid, delta in up.threat_table_delta.items():
                        perc.threat_table[eid] = perc.threat_table.get(eid, 0.0) + delta
            
            elif isinstance(up, NavigationUpdate):
                nav = entity.mind.navigation
                # Force coercion of Vector2 (AOA Stabilization)
                from src.core.models.vectors import Vector2
                
                if up.pos_history:
                    nav.pos_history = [
                        Vector2.model_validate(p) if isinstance(p, dict) else p 
                        for p in up.pos_history
                    ]
                if up.cached_path is not None:
                    nav.cached_path = [
                        Vector2.model_validate(p) if isinstance(p, dict) else p 
                        for p in up.cached_path
                    ]
                if up.target_pos:
                    nav.cached_path_target = Vector2.model_validate(up.target_pos) if isinstance(up.target_pos, dict) else up.target_pos
                if up.chase_ticks is not None:
                    nav.chase_ticks = up.chase_ticks
            
            elif isinstance(up, ProgressionUpdate):
                prog = entity.progression
                if up.gold_delta:
                    prog.gold = max(0, prog.gold + up.gold_delta)
                if up.xp_delta:
                    prog.xp += up.xp_delta
                if up.veterancy_points_delta:
                    prog.veterancy_points += up.veterancy_points_delta
                if up.hp_delta:
                    entity.combat.hp = max(0, min(entity.combat.max_hp, entity.combat.hp + up.hp_delta))
                if up.stamina_delta:
                    prog.stamina = max(0, min(prog.max_stamina, prog.stamina + up.stamina_delta))
                
                if entity.inventory:
                    for iid in up.inventory_add:
                        entity.inventory.add_item(iid)
                    for iid in up.inventory_remove:
                        entity.inventory.remove_item(iid)
                
                if up.skills_add:
                    from src.core.gameplay.classes import SkillInstance
                    for s in up.skills_add:
                        prog.skills.append(s if isinstance(s, SkillInstance) else SkillInstance(skill_id=s))
                        
                if up.attribute_cap_delta:
                    for k, v in up.attribute_cap_delta.items():
                        setattr(prog.attribute_caps, k, getattr(prog.attribute_caps, k) + v)
                        
                if up.quest_add:
                    prog.quests.extend(up.quest_add)
                
                if up.effects_add:
                    for ef in up.effects_add:
                        entity.combat.add_effect(ef)
                if up.effects_remove:
                    for ident in up.effects_remove:
                        entity.combat.remove_effect(ident)

            elif isinstance(up, IdentityUpdate):
                ident = entity.identity
                if up.recipes_learn:
                    ident.known_recipes.update(up.recipes_learn)
                if up.craft_target is not None:
                    ident.craft_target = up.craft_target
                if up.hero_class is not None:
                    ident.hero_class = up.hero_class
                if up.reputation_delta:
                    ident.reputation += up.reputation_delta

            elif isinstance(up, InteractionUpdate):
                inter = entity.interaction
                if up.loot_progress_delta:
                    inter.loot_progress += up.loot_progress_delta
                if up.loot_progress_set is not None:
                    inter.loot_progress = up.loot_progress_set
                
                if entity.inventory:
                    if up.home_storage_upgrade:
                        entity.inventory.home_storage.upgrade()
                    if up.home_storage_add:
                        for iid in up.home_storage_add:
                            entity.inventory.home_storage.add_item(iid)
                    if up.home_storage_remove:
                        for iid in up.home_storage_remove:
                            entity.inventory.home_storage.remove_item(iid)
                
                if up.corpse_id_to_remove is not None:
                    # Authoritative Corpse Recovery (AOA Final Convergence)
                    nodes = getattr(world, "corpse_nodes", {})
                    corpse = nodes.get(up.corpse_id_to_remove)
                    if corpse:
                        # 1. Gain Items/Gold
                        entity.progression.gold += getattr(corpse, "gold", 0)
                        if entity.inventory:
                            for iid in getattr(corpse, "items", []):
                                entity.inventory.add_item(iid)
                        # 2. Cleanup (Direct authoritative removal)
                        world.corpse_nodes.pop(up.corpse_id_to_remove, None)
            
            elif isinstance(up, CombatTraceUpdate):
                if hasattr(entity.combat, "traces"):
                    # Convert trace updates to records (AOA Stabilization)
                    from src.core.aspects.combat import CombatTraceRecord
                    trace = CombatTraceRecord(
                        tick=up.tick,
                        attacker_id=up.attacker_id,
                        defender_id=up.defender_id,
                        damage=up.damage,
                        is_crit=up.is_crit,
                        is_evasion=up.is_evasion,
                        skill_used=up.skill_used,
                        raw_damage=up.details.raw_damage,
                        mitigated_damage=up.details.mitigated_damage,
                        absorbed_damage=up.details.absorbed_damage,
                        crit_multiplier=up.details.crit_multiplier,
                        evasion_chance=up.details.evasion_chance,
                        elemental_mult=up.details.elemental_mult
                    )
                    entity.combat.traces.append(trace)


    @staticmethod
    def _get_use_item_updates(world: WorldState, config: SimulationConfig, entity: Entity, item_id: str) -> list[IntentUpdate]:
        """Generate updates for using an item (AOA Convergence)."""
        updates: list[IntentUpdate] = []
        if entity.inventory and item_id in entity.inventory.items:
            template = ITEM_REGISTRY.get(item_id)
            if template:
                # 1. Removal
                updates.append(ProgressionUpdate(inventory_remove=[item_id]))
                # 2. Heal
                if template.heal_amount > 0:
                    updates.append(ProgressionUpdate(hp_delta=template.heal_amount))
                
                from src.core.gameplay.attributes import speed_delay
                entity.next_act_at += speed_delay(entity.combat.spd, "use_item")
        return updates

    @staticmethod
    def _get_looting_updates(world: WorldState, entity: Entity, pos: Any) -> list[IntentUpdate]:
        """Generate updates for looting from the ground (AOA Convergence)."""
        updates: list[IntentUpdate] = []
        
        # 1. Standard Ground Items
        items = world.pickup_items(pos) # Authoritative removal from world
        if items:
            updates.append(ProgressionUpdate(inventory_add=items))
            updates.append(InteractionUpdate(loot_progress_set=0))
        
        # 2. Corpse Containers (AOA Convergence Patch)
        nodes = getattr(world, "corpse_nodes", {})
        for cid, node in list(nodes.items()): # Use list to avoid mutation during iteration
             # pos is usually a Vector2 or tuple (x, y)
             node_pos = getattr(node, "pos", None)
             if node_pos and node_pos == pos:
                 updates.append(InteractionUpdate(corpse_id_to_remove=cid))

        from src.core.gameplay.attributes import speed_delay
        entity.next_act_at += speed_delay(entity.combat.spd, "loot")
        return updates

    @staticmethod
    def _get_harvesting_updates(world: WorldState, entity: Entity, pos: Any) -> list[IntentUpdate]:
        """Generate updates for harvesting a resource (AOA Convergence)."""
        updates: list[IntentUpdate] = []
        node = world.resource_at(pos)
        if node and node.is_available:
            item_id = node.harvest() # Authoritative harvest
            if item_id:
                updates.append(ProgressionUpdate(inventory_add=[item_id], stamina_delta=-2))
                updates.append(InteractionUpdate(loot_progress_set=0))
        
        from src.core.gameplay.attributes import speed_delay
        entity.next_act_at += speed_delay(entity.combat.spd, "harvest")
        return updates

    @classmethod
    def _get_use_skill_updates(cls, world: WorldState, config: SimulationConfig, faction_reg: FactionRegistry | None, entity: Entity, skill_id: str, target_id: int | None = None, emit: Callable | None = None) -> list[IntentUpdate]:
        """Generate updates for using a skill (AOA Convergence)."""
        updates: list[IntentUpdate] = []
        sdef = SKILL_DEFS.get(skill_id)
        if not sdef: return updates
        
        instance = next((si for si in entity.progression.skills if si.skill_id == skill_id), None)
        if not instance or not instance.is_ready(): return updates
        
        cost = instance.effective_stamina_cost(sdef.stamina_cost)
        if entity.progression.stamina < cost: return updates
        
        # 1. Authoritative Cooldown/Stamina Side-Effects
        entity.progression.stamina -= cost
        instance.use(sdef.cooldown)
        
        targets: list[tuple[Entity, int]] = [] # (Target, distance from center)
        center = entity.spatial.pos
        if sdef.radius > 0:
            if target_id and world.entities.get(target_id):
                 center = world.entities[target_id].spatial.pos
            potential = world.entities_at_radius(center, sdef.radius)
            for target in potential:
                if not target or not target.combat.alive or target.id == entity.id: continue
                if faction_reg and faction_reg.is_hostile(entity.identity.faction, target.identity.faction):
                    dist = int(math.sqrt((target.spatial.pos.x - center.x)**2 + (target.spatial.pos.y - center.y)**2))
                    targets.append((target, dist))
        elif target_id:
            t = world.entities.get(target_id)
            if t and t.combat.alive: 
                targets.append((t, 0))
        
        for target, dist in targets:
            power = instance.effective_power(sdef.power)
            # AoE Falloff: 100% at center, 50% at edge (linear)
            falloff = 1.0
            if sdef.radius > 0:
                falloff = max(0.5, 1.0 - (dist / (sdef.radius + 1)) * 0.5)
            
            raw = int(entity.combat.atk * power * falloff)
            mitigation = target.combat.def_ // 2
            damage = max(1, raw - mitigation)
            
            # --- SIDE-EFFECTS (Targets) ---
            # HP Damage (Direct mutation on target aspect)
            target.combat.hp = max(0, target.combat.hp - damage)
            
            # Threat Generation (Direct mutation on target mind)
            mult = 1.5 if entity.progression.hero_class == HeroClass.WARRIOR else 1.0
            target.mind.perception.threat_table[entity.id] = target.mind.perception.threat_table.get(entity.id, 0.0) + damage * mult

            if emit:
                emit("skill", f"{entity.kind} hit {target.kind} with {sdef.name} for {damage} damage",
                     entity_ids=(entity.id, target.id),
                     metadata={
                         "skill_name": sdef.name,
                         "damage": damage,
                         "aoe": sdef.radius > 0,
                         "dist_from_center": dist,
                         "actor_id": entity.id,
                         "target_id": target.id
                     })
            
        from src.core.gameplay.attributes import speed_delay
        entity.next_act_at += speed_delay(entity.combat.spd, "use_skill")
        return updates


    def handle_tactical_maneuvers(self, context: SystemContext, applied: list[ActionProposal], pre_positions: dict) -> None:
        """Process opportunity attacks and chase closing."""
        self._process_opportunity_attacks(context, applied, pre_positions)

    def _process_opportunity_attacks(self, context: SystemContext, applied: list[ActionProposal], pre_positions: dict) -> None:
        cfg = context.config
        world = context.world
        reg = context.faction_reg
        mult = cfg.opportunity_attack_damage_mult
        
        for proposal in applied:
            if proposal.verb != ActionType.MOVE: continue
            mover = world.entities.get(proposal.actor_id)
            if not mover or not mover.combat.alive: continue
            old_pos = pre_positions.get(proposal.actor_id)
            if not old_pos: continue
            
            for eid in sorted(world.entities.keys()):
                ent = world.entities[eid]
                if eid == mover.id or not ent.combat.alive: continue
                if not reg.is_hostile(mover.identity.faction, ent.identity.faction): continue
                
                # Simple adjacency check
                dx = abs(ent.spatial.pos.x - old_pos[0])
                dy = abs(ent.spatial.pos.y - old_pos[1])
                if dx + dy == 1:
                    # Opportunity Attack
                    raw = max(1, int(ent.combat.atk * mult) - mover.combat.def_ // 2)
                    mover.combat.hp -= raw

    def _update_combat_visualization(self, context: SystemContext, applied: list[ActionProposal]) -> None:
        world = context.world
        acted: set[int] = set()
        for proposal in applied:
            actor = world.entities.get(proposal.actor_id)
            if not actor: continue
            acted.add(actor.id)
            if proposal.verb in (ActionType.ATTACK, ActionType.USE_SKILL):
                actor.combat.combat_target_id = proposal.target
        
        for entity in world.entities.values():
            if entity.id in acted: continue
            if entity.mind.decision.ai_state not in (AIState.COMBAT, AIState.HUNT):
                entity.combat.combat_target_id = None

    def _update_ai_derived_states(self, context: SystemContext, applied: list[ActionProposal]) -> None:
        world = context.world
        for proposal in applied:
            entity = world.entities.get(proposal.actor_id)
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
