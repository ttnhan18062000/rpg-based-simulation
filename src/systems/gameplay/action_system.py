"""ActionSystem handles post-resolution state mutations and tactical maneuvers.

Refactored for AOA Stabilization:
- Direct aspect access (spatial, combat, mind, progression).
- Explicit application of 'intent_metadata' from side-effect-free AI decisions.
- Standardized state transitions and derived counter updates.
"""

from __future__ import annotations
import logging
import math
from typing import TYPE_CHECKING, Any
from src.core.models.enums import AIState, ActionType, Element
from src.core.entities.entity import Entity
from src.actions.base import ActionProposal, IntentUpdate, MindUpdate, NavigationUpdate, CombatTraceUpdate
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
        world = context.world
        for proposal in applied:
            entity = world.entities.get(proposal.actor_id)
            if entity is None or not entity.combat.alive:
                continue

            # 1. Apply State Transitions
            if proposal.new_ai_state is not None:
                new_state = AIState(proposal.new_ai_state)
                if new_state != entity.mind.decision.ai_state:
                    entity.mind.decision.ai_state = new_state
                    # Only reset commitment if it's currently 0 (initial goal selection)
                    if entity.mind.decision.goal_committed_at == 0:
                         entity.mind.decision.goal_committed_at = world.tick
            if proposal.reason:
                entity.mind.decision.last_reason = proposal.reason

            # 2. Apply Intent Updates (Phase 5)
            if proposal.updates:
                self._apply_updates(entity, proposal.updates)

            # 2.1 Legacy Metadata Bucket (Compatibility)
            if proposal.intent_metadata:
                self._apply_intent_metadata(entity, proposal.intent_metadata)

            # 2.5 Authoritative Attribute Training
            from src.core.gameplay.attributes import train_attributes
            train_attributes(entity, proposal.verb.name.lower())

            # 3. Handle Verb-Specific Logic
            if proposal.verb == ActionType.USE_ITEM and proposal.target:
                self._handle_use_item(context, entity, proposal.target)
            elif proposal.verb == ActionType.LOOT:
                self._handle_looting(context, entity, proposal.target)
            elif proposal.verb == ActionType.HARVEST and proposal.target:
                self._handle_harvesting(context, entity, proposal.target)
            elif proposal.verb == ActionType.USE_SKILL and proposal.target:
                target_data = proposal.target if isinstance(proposal.target, tuple) else (proposal.target, None)
                self._handle_use_skill(context, entity, target_data[0], target_data[1])

        # 4. Tactical & Visualization Updates
        self._update_ai_derived_states(context, applied)
        self._update_combat_visualization(context, applied)

    def _apply_updates(self, entity: Entity, updates: list[IntentUpdate]) -> None:
        """Apply typed simulation side-effects (AOA Phase 5)."""
        for up in updates:
            if isinstance(up, MindUpdate):
                if up.goal_scores:
                    entity.mind.decision.goal_scores = up.goal_scores
                if up.last_goal:
                    entity.mind.decision.last_goal = up.last_goal
                if up.boredom_delta:
                    entity.mind.decision.boredom_multipliers.update(up.boredom_delta)
                if up.new_ai_state is not None:
                    entity.mind.decision.ai_state = AIState(up.new_ai_state)
            
            elif isinstance(up, NavigationUpdate):
                if up.pos_history:
                    entity.mind.navigation.pos_history = up.pos_history
                if up.cached_path:
                    entity.mind.navigation.cached_path = up.cached_path
                if up.target_pos:
                    entity.mind.navigation.cached_path_target = up.target_pos
            
            elif isinstance(up, CombatTraceUpdate):
                if hasattr(entity.combat, "traces"):
                    entity.combat.traces.append({
                        "tick": up.tick,
                        "attacker_id": up.attacker_id,
                        "defender_id": up.defender_id,
                        "damage": up.damage,
                        "is_crit": up.is_crit,
                        "is_evasion": up.is_evasion,
                        "skill_used": up.skill_used,
                        **up.details
                    })

    def _apply_intent_metadata(self, entity: Any, metadata: dict[str, Any]) -> None:
        """Apply side-effects proposed by the AI during the decision phase."""
        mind = entity.mind
        
        # Decision updates
        if "boredom_update" in metadata:
            mind.decision.boredom_multipliers.update(metadata["boredom_update"])
        if "goal_scores" in metadata:
            mind.decision.goal_scores = dict(metadata["goal_scores"])
        if "last_goal" in metadata:
            mind.decision.last_goal = metadata["last_goal"]
        
        # Navigation updates
        if "pos_history" in metadata:
            mind.navigation.pos_history = list(metadata["pos_history"])
        if "cached_path" in metadata:
            mind.navigation.cached_path = list(metadata["cached_path"])
        if "cached_path_target" in metadata:
            mind.navigation.cached_path_target = metadata["cached_path_target"]
            
        # Perception updates
        if "attention_pool" in metadata:
            mind.perception.attention_pool = list(metadata["attention_pool"])
        if "memory_update" in metadata:
            # Atomic update or merge
            mind.perception.entity_memory.update(metadata["memory_update"])
        if "memory_stale_update" in metadata:
            mind.perception.memory_stale_ticks.update(metadata["memory_stale_update"])
        if "memory_remove" in metadata:
            for rid in metadata["memory_remove"]:
                mind.perception.entity_memory.pop(rid, None)
                mind.perception.memory_stale_ticks.pop(rid, None)
            
        # Emotion updates
        if "emotion_stuck" in metadata:
            mind.emotion.emotional_state["stuck"] = metadata["emotion_stuck"]
        if "emotion_panic" in metadata:
            mind.emotion.emotional_state["panic"] = metadata["emotion_panic"]

        # Interaction / AOA Stabilization updates
        if "loot_progress_inc" in metadata:
            entity.interaction.loot_progress += metadata["loot_progress_inc"]
        if "loot_progress_reset" in metadata:
            entity.interaction.loot_progress = metadata["loot_progress_reset"]
            
        if "recover_gold" in metadata:
            entity.progression.gold += metadata["recover_gold"]
        if "gold_add" in metadata:
            entity.progression.gold += metadata["gold_add"]
        if "gold_remove" in metadata:
            entity.progression.gold = max(0, entity.progression.gold - metadata["gold_remove"])
            
        if "recover_items" in metadata:
            if entity.inventory:
                for iid in metadata["recover_items"]:
                    entity.inventory.add_item(iid)
        if "inventory_add" in metadata:
            if entity.inventory:
                for iid in metadata["inventory_add"]:
                    entity.inventory.add_item(iid)
        if "inventory_remove" in metadata:
            if entity.inventory:
                for iid in metadata["inventory_remove"]:
                    entity.inventory.remove_item(iid)
                    
        if "hp_add" in metadata:
            entity.combat.hp = min(entity.combat.max_hp, entity.combat.hp + metadata["hp_add"])
        if "stamina_add" in metadata:
            entity.progression.stamina = min(entity.progression.max_stamina, entity.progression.stamina + metadata["stamina_add"])
            
        if "recipe_learn" in metadata:
            for rid in metadata["recipe_learn"]:
                if rid not in entity.identity.known_recipes:
                    entity.identity.known_recipes.append(rid)
        if "craft_target_set" in metadata:
            entity.identity.craft_target = metadata["craft_target_set"]
            
        if "hero_class_set" in metadata:
            entity.identity.hero_class = metadata["hero_class_set"]
        if "attribute_cap_add" in metadata:
            caps = entity.progression.attribute_caps
            bonus = metadata["attribute_cap_add"]
            if caps and bonus:
                for field, val in bonus.items():
                    if hasattr(caps, field):
                        setattr(caps, field, getattr(caps, field) + val)
        
        if "quest_add" in metadata:
            # Quests live in ProgressionAspect
            for q in metadata["quest_add"]:
                entity.progression.quests.append(q)
                
        if "goals_add" in metadata:
            for goal in metadata["goals_add"]:
                if goal not in mind.decision.goals:
                    mind.decision.goals.append(goal)
                    
        if "terrain_memory_update" in metadata:
            entity.mind.perception.terrain_memory.update(metadata["terrain_memory_update"])
            
        if "home_storage_upgrade" in metadata:
            if entity.inventory and entity.inventory.home_storage:
                entity.inventory.home_storage.upgrade()
        if "home_storage_add" in metadata:
            if entity.inventory and entity.inventory.home_storage:
                for iid in metadata["home_storage_add"]:
                    entity.inventory.home_storage.add_item(iid)

        if "skills_add" in metadata:
            # metadata["skills_add"] should be a list of SkillInstance or IDs
            from src.core.gameplay.classes import SkillInstance
            for s in metadata["skills_add"]:
                inst = s if isinstance(s, SkillInstance) else SkillInstance(skill_id=s)
                entity.progression.skills.append(inst)

        if "corpse_pop" in metadata:
            from src.systems.infrastructure.base import SystemContext
            context: SystemContext = getattr(self, "_context", None)
            if context:
                context.world.corpse_nodes.pop(metadata["corpse_pop"], None)

        if "chase_ticks" in metadata:
            if entity.mind and entity.mind.navigation:
                entity.mind.navigation.chase_ticks = metadata["chase_ticks"]
        if "loot_progress_inc" in metadata:
            if entity.interaction:
                entity.interaction.loot_progress += metadata["loot_progress_inc"]
        if "loot_progress_reset" in metadata:
            if entity.interaction:
                entity.interaction.loot_progress = metadata["loot_progress_reset"]
        if "memory_remove" in metadata:
            if entity.mind and entity.mind.perception:
                for eid in metadata["memory_remove"]:
                    entity.mind.perception.entity_memory.pop(eid, None)

    def _handle_use_item(self, context: SystemContext, entity: Any, item_id: str) -> None:
        if entity.inventory and entity.inventory.remove_item(item_id):
            template = ITEM_REGISTRY.get(item_id)
            if template and template.heal_amount > 0:
                old_hp = entity.combat.hp
                entity.combat.hp = min(entity.combat.hp + template.heal_amount, entity.combat.max_hp)
                healed = entity.combat.hp - old_hp
                if context.emit:
                    context.emit("item", f"Entity {entity.id} used {item_id} healed {healed}", (entity.id,), {"item_id": item_id})
            
            from src.core.gameplay.attributes import speed_delay
            entity.next_act_at += speed_delay(entity.combat.spd, "use_item")

    def _handle_looting(self, context: SystemContext, entity: Any, pos: Any) -> None:
        world = context.world
        items = world.pickup_items(pos)
        if items and entity.inventory:
            for iid in items:
                if not entity.inventory.add_item(iid):
                    world.drop_items(pos, [iid])
                else:
                    entity.inventory.auto_equip_best(iid)
        
        entity.interaction.loot_progress = 0
        from src.core.gameplay.attributes import speed_delay
        entity.next_act_at += speed_delay(entity.combat.spd, "loot")

    def _handle_harvesting(self, context: SystemContext, entity: Any, pos: Any) -> None:
        node = context.world.resource_at(pos)
        if node and node.is_available and entity.inventory:
            item_id = node.harvest()
            if item_id and entity.inventory.add_item(item_id):
                entity.progression.stamina = max(0, entity.progression.stamina - 2)
        
        entity.interaction.loot_progress = 0
        from src.core.gameplay.attributes import speed_delay
        entity.next_act_at += speed_delay(entity.combat.spd, "harvest")

    def _handle_use_skill(self, context: SystemContext, entity: Any, skill_id: str, target_id: int | None = None) -> None:
        sdef = SKILL_DEFS.get(skill_id)
        if not sdef: return
        
        # Check skill instance
        instance = next((si for si in entity.progression.skills if si.skill_id == skill_id), None)
        if not instance or not instance.is_ready(): return
        
        cost = instance.effective_stamina_cost(sdef.stamina_cost)
        if entity.progression.stamina < cost: return
        
        entity.progression.stamina -= cost
        instance.use(sdef.cooldown)
        
        # Skill effects (AOA Stabilization)
        world = context.world
        targets: list[Entity] = []
        
        if sdef.radius > 0:
            # AoE Skill: Find targets in radius
            center = entity.spatial.pos
            if target_id and world.entities.get(target_id):
                 center = world.entities[target_id].spatial.pos
            
            # Use high-level WorldState API for nearby entities
            potential = world.entities_at_radius(center, sdef.radius)
            for target in potential:
                if not target or not target.combat.alive or target.id == entity.id:
                    continue
                if context.faction_reg.is_hostile(entity.identity.faction, target.identity.faction):
                    targets.append(target)
            
            if not targets:
                # AOA Pillar 3: Deterministic Brute-force Fallback for minimal test arenas
                # If high-level spatial query fails, we scan all entities as a last resort
                # but only for small radii (to avoid O(N^2) explosion in large worlds)
                if sdef.radius <= 3:
                    for target in world.entities.values():
                        if not target or not target.combat.alive or target.id == entity.id:
                            continue
                        if center.manhattan(target.spatial.pos) <= sdef.radius:
                            if context.faction_reg.is_hostile(entity.identity.faction, target.identity.faction):
                                targets.append(target)
                
                if not targets:
                    logger.warning("SKILL_EXEC: %s used %s at %s, but found 0 targets in radius %d", 
                                   entity.identity.display_name, skill_id, center, sdef.radius)
        elif target_id:
            # Single Target
            t = world.entities.get(target_id)
            if t and t.combat.alive:
                targets.append(t)
        
        # Apply damage/effects
        for target in targets:
            power = instance.effective_power(sdef.power)
            
            # Simple physical damage for now
            raw = int(entity.combat.atk * power)
            mitigation = target.combat.def_ // 2
            damage = max(1, raw - mitigation)
            
            target.combat.hp -= damage
            
            # Emit skill event for monitoring and E2E tests
            skill_name = skill_id.replace("_", " ").title()
            if skill_id == "rain_of_arrows":
                skill_name = "Rain of Arrows"
            context.emit("skill", f"{entity.identity.display_name} hit {target.identity.display_name} with {skill_id} for {damage} damage", 
                         entity_ids=(entity.id, target.id), 
                         metadata={
                             "verb": "USE_SKILL",
                             "damage": damage, 
                             "skill_id": skill_id, 
                             "skill_name": skill_name, 
                             "aoe": sdef.radius > 0,
                             "is_aoe": sdef.radius > 0,
                             "type": "skill_hit"
                         })
            
            if not target.combat.alive:
                 context.emit("death", f"{target.identity.display_name} killed by {entity.identity.display_name}'s {skill_id}", 
                              entity_ids=(target.id, entity.id))

        from src.core.gameplay.attributes import speed_delay
        entity.next_act_at += speed_delay(entity.combat.spd, "use_skill")

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
                actor.combat.combat_target_id = proposal.target if isinstance(proposal.target, int) else None
        
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
