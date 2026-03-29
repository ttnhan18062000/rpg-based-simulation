"""ActionSystem handles post-resolution state mutations and tactical maneuvers."""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, Any

from src.core.models.enums import ActionType, AIState, Domain, SkillTarget, SkillType, DamageType, HeroClass
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
        """Process state mutations (looting, items) for successfully applied actions."""
        world = context.world
        for proposal in applied:
            entity = world.entities.get(proposal.actor_id)
            if entity is None or not entity.combat.alive:
                continue

            # Apply state transition
            if hasattr(proposal, "new_ai_state") and proposal.new_ai_state is not None:
                entity.mind.ai_state = proposal.new_ai_state

            if proposal.verb == ActionType.USE_ITEM and proposal.target:
                self._handle_use_item(context, entity, proposal.target)
            elif proposal.verb == ActionType.LOOT and proposal.target:
                self._handle_looting(context, entity, proposal.target)
            elif proposal.verb == ActionType.HARVEST and proposal.target:
                self._handle_harvesting(context, entity, proposal.target)
            elif proposal.verb == ActionType.USE_SKILL and proposal.target:
                target_data = proposal.target if isinstance(proposal.target, tuple) else (proposal.target, None)
                self._handle_use_skill(context, entity, target_data[0], target_data[1])

        # Visualization and tactical state updates
        self._update_combat_visualization(context, applied)
        self._update_ai_derived_states(context, applied)

    def _handle_use_item(self, context: SystemContext, entity: Any, item_id: str) -> None:
        """Handle consumable usage including healing and act delay."""
        if entity.inventory and entity.inventory.remove_item(item_id):
            template = ITEM_REGISTRY.get(item_id)
            if template and template.heal_amount > 0:
                old_hp = entity.combat.hp
                entity.combat.hp = min(entity.combat.hp + template.heal_amount, entity.combat.max_hp)
                healed = entity.combat.hp - old_hp
                
                if context.emit:
                    context.emit("item", f"Entity {entity.id} used {item_id} → healed {healed}",
                              entity_ids=(entity.id,),
                              metadata={"item_id": item_id, "healed": healed})
            
            # Action delay penalty
            from src.core.gameplay.attributes import speed_delay
            entity.next_act_at += speed_delay(entity.combat.spd, "use_item", entity.combat.interaction_speed)

    def _handle_looting(self, context: SystemContext, entity: Any, pos: Any) -> None:
        """Handle ground looting and chest interactions."""
        from src.core.models import Vector2
        if not isinstance(pos, Vector2):
            return
            
        world = context.world
        items = world.pickup_items(pos)
        if items and entity.inventory:
            looted_items = []
            for iid in items:
                if not entity.inventory.add_item(iid):
                    world.drop_items(pos, [iid])
                else:
                    entity.inventory.auto_equip_best(iid)
                    looted_items.append(iid)
                    
            if looted_items and hasattr(world, "event_bus") and world.event_bus:
                from src.core.data.events import LootEvent
                from src.core.gameplay.items.item_registry import ITEM_REGISTRY
                for iid in looted_items:
                    tmpl = ITEM_REGISTRY.get(iid)
                    name = tmpl.name if tmpl else iid
                    world.event_bus.publish(LootEvent(
                        entity_id=entity.id,
                        item_id=iid,
                        item_name=name,
                        source="ground"
                    ))
        
        # Check for chests
        self._try_loot_chest(context, entity, pos)
        
        # Action delay
        from src.core.gameplay.attributes import speed_delay
        entity.next_act_at += speed_delay(entity.stats.combat.spd, "loot", entity.stats.interaction_speed)

    def _try_loot_chest(self, context: SystemContext, entity: Any, pos: Any) -> None:
        """If there's an available treasure chest at pos, loot it."""
        from src.core.gameplay.items.items import CHEST_LOOT_TABLES
        world = context.world
        
        for chest in world.treasure_chests.values():
            if chest.pos == pos and chest.is_available:
                # Check guard
                if chest.guard_entity_id is not None:
                    guard = world.entities.get(chest.guard_entity_id)
                    if guard and guard.combat.alive:
                        continue
                
                # Generate loot
                loot_table = CHEST_LOOT_TABLES.get(chest.tier, [])
                loot_items = []
                for item_id, chance, min_c, max_c in loot_table:
                    roll = context.rng.next_float(Domain.LOOT, entity.id, world.tick + chest.chest_id)
                    if roll < chance:
                        count = context.rng.next_int(Domain.LOOT, entity.id, world.tick + chest.chest_id + 10, min_c, max_c)
                        loot_items.extend([item_id] * count)
                
                if loot_items:
                    world.drop_items(pos, loot_items)
                    
                chest.loot(world.tick, respawn_ticks=150 + chest.identity.tier * 50)
                logger.info("Tick %d: Entity %d looted chest %d", world.tick, entity.id, chest.chest_id)
                break

    def _handle_harvesting(self, context: SystemContext, entity: Any, pos: Any) -> None:
        """Handle resource harvesting."""
        world = context.world
        node = world.resource_at(pos)
        if node and node.is_available and entity.inventory:
            item_id = node.harvest()
            if item_id and entity.inventory.add_item(item_id):
                entity.progression.stamina = max(0, entity.progression.stamina - 2)
                if context.emit:
                    context.emit("harvest", f"Entity {entity.id} harvested {item_id}",
                              entity_ids=(entity.id,),
                              metadata={"item_id": item_id})
        
        # Action delay
        from src.core.gameplay.attributes import speed_delay
        entity.next_act_at += speed_delay(entity.combat.spd, "harvest", entity.combat.interaction_speed)

    def _handle_use_skill(self, context: SystemContext, entity: Any, skill_id: str, target_id: int | None = None) -> None:
        """Execute a combat or utility skill, applying effects to target(s)."""
        sdef = SKILL_DEFS.get(skill_id)
        if not sdef or sdef.skill_type != SkillType.ACTIVE:
            return

        instance = next((si for si in entity.progression.skills if si.skill_id == skill_id), None)
        if not instance:
            # print(f"DEBUG_ACTION_SKILL: Entity {entity.id} does not have skill {skill_id}")
            return
            
        if not instance.is_ready():
            # print(f"DEBUG_ACTION_SKILL: Skill {skill_id} on CD for Entity {entity.id} (CD={instance.cooldown_remaining})")
            return

        cost = instance.effective_stamina_cost(sdef.stamina_cost)
        if entity.progression.stamina < cost:
            # print(f"DEBUG_ACTION_SKILL: No stamina for {skill_id} (Need {cost}, Has {entity.progression.stamina})")
            return
            
        # Resolve targets
        targets = self._resolve_skill_targets(context, entity, sdef, target_id)

        # --- Metrics: Skill Event ---
        from src.core.gameplay.faction import Faction
        from src.utils.metrics import SIM_SKILL_EVENTS
        SIM_SKILL_EVENTS.labels(
            attacker_faction=Faction(entity.identity.faction).name.lower(),
            skill_name=sdef.name.lower().replace(" ", "_")
        ).inc()

        # Consume stamina
        if entity.progression.stamina < cost:
            return
        entity.progression.stamina -= cost

        # Resolve targets
        targets = self._resolve_skill_targets(context, entity, sdef, target_id)
        
        # Apply effects
        hit_count = 0
        for target in targets:
            if self._apply_skill_effect(context, entity, target, sdef, instance):
                hit_count += 1

        # Trigger cooldown
        instance.use(sdef.cooldown)
        instance.times_used += 1
        # Mastery increase (small chance/amount per use)
        instance.mastery = min(100.0, instance.mastery + 0.1)

        if context.emit:
            context.emit("skill", f"Entity {entity.id} used {sdef.name} → hit {hit_count} targets",
                      entity_ids=(entity.id,),
                      metadata={
                          "skill_id": skill_id,
                          "skill_name": sdef.name,
                          "hits": hit_count,
                          "verb": "USE_SKILL",
                          "aoe": sdef.radius > 0
                      })

        # Action delay
        from src.core.gameplay.attributes import speed_delay
        entity.next_act_at += speed_delay(entity.combat.spd, "use_skill", 1.0)

    def _resolve_skill_targets(self, context: SystemContext, entity: Any, sdef: Any, primary_target_id: int | None = None) -> list[Any]:
        """Find all entities affected by the skill based on its target type and radius."""
        from src.core.gameplay.faction import Faction
        world = context.world
        reg = context.faction_reg  # FactionRegistry is passed as 'faction_reg' in SystemContext
        targets = []

        if sdef.target == SkillTarget.SELF:
            return [entity]

        # For targeted skills, find the primary target first
        if not primary_target_id:
            primary_target_id = entity.combat_target_id
        primary_target = world.entities.get(primary_target_id) if primary_target_id else None

        # Area of Effect logic
        radius = sdef.radius or 0
        is_melee_aoe = (sdef.range or 1) <= 1
        
        # Ranged check: must have a target in range for offensive targeted skills
        if sdef.target in (SkillTarget.SINGLE_ENEMY, SkillTarget.AREA_ENEMIES):
            if not is_melee_aoe and (not primary_target or not primary_target.combat.alive):
                # Fallback: if it's a ranged AoE but target is gone/invalid, center on actor's current target or actor
                pass
            if primary_target and primary_target.combat.alive:
                dist = entity.spatial.pos.manhattan(primary_target.spatial.pos)
                if dist > (sdef.range or 1):
                    return []

        if radius > 0:
            # For melee-range AoE skills like Whirlwind, center on caster.
            # Ranged AoE (radius > 0 and range > 1) centers on the primary target.
            center = entity.spatial.pos if is_melee_aoe else (primary_target.spatial.pos if primary_target else entity.spatial.pos)
            potential = world.spatial_index.query_radius(center, radius)
            # LOGGING: Find out why AoE results in 0 hits
            logger.debug("Skill %s AoE at %s radius %d -> %d potentials", sdef.skill_id, center, radius, len(potential))
            
            # Use local targets list to avoid overriding external variables
            aoe_targets = []
            for oid in potential:
                other = world.entities.get(oid)
                if not other or not other.combat.alive:
                    continue
                
                # Precise distance check (since spatial hash is bucket-based)
                dist = other.spatial.pos.manhattan(center)
                if dist > radius:
                    continue

                # Hostility/Ally check
                is_hostile = reg.is_hostile(entity.identity.faction, other.identity.faction)
                
                added = False
                if sdef.target == SkillTarget.AREA_ENEMIES and is_hostile:
                    targets.append(other)
                    added = True
                elif sdef.target == SkillTarget.AREA_ALLIES and not is_hostile:
                    targets.append(other)
                    added = True
                elif sdef.target == SkillTarget.AREA_ALLIES and other.id == entity.id:
                    targets.append(other)
                    added = True
                
                if added:
                    logger.debug("  Hit: Entity %d (%s) at dist %d", other.id, other.kind, dist)
                    aoe_targets.append(other)
            
            # If an AoE hit anything, those (and only those) are our targets
            if aoe_targets:
                return aoe_targets
        elif primary_target:
            targets.append(primary_target)

        return targets

    def _apply_skill_effect(self, context: SystemContext, attacker: Any, defender: Any, sdef: Any, instance: Any) -> bool:
        """Apply the specific effect (damage, heal, buff) of a skill to a single target."""
        if sdef.skill_type != SkillType.ACTIVE:
            return False

        # Calculate base power (modified by mastery)
        power_mult = instance.effective_power(sdef.power)
        
        # Damage logic (Physical vs Magical)
        from src.actions.damage import get_damage_calculator
        calc = get_damage_calculator(sdef.damage_type)
        ctx = calc.resolve(attacker, defender)
        
        # Base damage formula: (Atk * Mult - Def/2) * Power
        raw_dmg = max(1, int(ctx.atk_power * ctx.atk_mult - ctx.def_power * ctx.def_mult // 2))
        final_dmg = int(raw_dmg * power_mult)

        # Falloff based on distance if AoE
        dist_from_center = 0
        is_aoe = sdef.radius > 0
        if is_aoe and attacker.combat_target_id != defender.id:
            center_ent = context.world.entities.get(attacker.combat_target_id) if attacker.combat_target_id else None
            center_pos = center_ent.spatial.pos if center_ent else attacker.spatial.pos
            dist_from_center = defender.spatial.pos.manhattan(center_pos)
            final_dmg = int(final_dmg * (1.0 - dist_from_center * sdef.aoe_falloff))

        actual_dmg = max(1, final_dmg)
        
        # --- Status Effect Combos ---
        for eff in list(defender.combat.effects):
            from src.core.gameplay.effects import EffectType
            # FROZEN + PHYSICAL -> SHATTER
            if eff.effect_type == EffectType.FROZEN and sdef.damage_type == DamageType.PHYSICAL:
                actual_dmg = int(actual_dmg * 1.5)
                eff.remaining_ticks = 0 # Remove Frozen
                if context.emit:
                    context.emit("combat", f"COMBO: SHATTER on {defender.id}!", (attacker.id, defender.id))
            
            # WET + MAGICAL (Lightning) -> OVERLOAD
            # Check sdef.name or add a specific element to SkillDef
            # For now, let's assume all MAGICAL vs WET triggers a small bonus
            elif eff.effect_type == EffectType.WET and sdef.damage_type == DamageType.MAGICAL:
                actual_dmg = int(actual_dmg * 1.3)
                if context.emit:
                    context.emit("combat", f"COMBO: OVERLOAD on {defender.id}!", (attacker.id, defender.id))

        # Apply damage
        defender.combat.hp -= actual_dmg
        
        # Low HP trigger
        if defender.combat.alive and defender.combat.hp_ratio < 0.2:
            last_surv = defender.mind.memory.get("last_survival_tick", -100)
            tick = context.world.tick if hasattr(context.world, "tick") else 0
            if tick - last_surv >= 20:  # At most once per 20 ticks
                defender.mind.memory_log.append({
                    "tick": tick,
                    "type": "SURVIVAL",
                    "desc": f"Survived near-death against {attacker.kind}",
                    "impact": -3.0,
                })
                defender.mind.memory["last_survival_tick"] = tick

        # --- Threat generation ---
        from src.core.gameplay.classes import HeroClass
        threat = final_dmg * context.config.threat_damage_mult
        if attacker.progression.hero_class in (HeroClass.WARRIOR, HeroClass.CHAMPION):
            threat *= context.config.threat_tank_class_mult
        defender.mind.threat_table[attacker.id] = defender.mind.threat_table.get(attacker.id, 0.0) + threat

        if context.emit:
            context.emit("skill", f"Skill {sdef.name} hit {defender.id} for {final_dmg} damage",
                      entity_ids=(attacker.id, defender.id),
                      metadata={
                          "skill_id": sdef.skill_id,
                          "skill_name": sdef.name,
                          "damage": final_dmg,
                          "aoe": is_aoe,
                          "dist_from_center": dist_from_center,
                          "verb": "USE_SKILL"
                      })

        # XP/Fame awards and Narrative Memory on kill
        if not defender.combat.alive:
            attacker.progression.xp += 10 # Simplified
            attacker.progression.gold += defender.progression.gold
            defender.progression.gold = 0
            
            # Milestone 6: Narrative Memory (Glory/Trauma)
            tick = context.world.tick if hasattr(context.world, "tick") else 0
            
            # Glory for Attacker
            attacker.mind.memory_log.append({
                "tick": tick,
                "type": "GLORY",
                "desc": f"Slayed {defender.kind} (ID:{defender.id})",
                "impact": 5.0 if not defender.identity.is_world_boss else 50.0
            })
            attacker.mind.emotional_state["bravery"] = min(1.0, attacker.mind.emotional_state.get("bravery", 0.5) + 0.05)
            
            if attacker.identity.hero_class != 0:
                attacker.progression.fame += 50
                attacker.identity.reputation += 20.0
                
                # Milestone 6: Hero Renown Broadcast
                if hasattr(context.world, "event_bus") and context.world.event_bus:
                    from src.core.data.events import RenownEvent
                    context.world.event_bus.publish(RenownEvent(
                        entity_id=attacker.id,
                        glory_type="boss_kill",
                        description=f"Slayed the legendary {defender.kind}",
                        renown_gain=20.0
                    ))
                
                if context.emit:
                    context.emit("renown", f"HERO {attacker.id} HAS ACHIEVED LEGENDARY FAME BY SLAYING {defender.kind}!",
                                entity_ids=(attacker.id,),
                                metadata={"type": "boss_kill", "renown_gain": 20.0})
                
            # Trauma for nearby Allies of Defender
            for eid, ent in context.world.entities.items():
                if ent.combat.alive and ent.identity.faction == defender.identity.faction and eid != defender.id:
                    dist = abs(ent.spatial.pos.x - defender.spatial.pos.x) + abs(ent.spatial.pos.y - defender.spatial.pos.y)
                    if dist <= 5: # Vision-ish range
                        ent.mind.memory_log.append({
                            "tick": tick,
                            "type": "TRAUMA",
                            "desc": f"Witnessed death of ally {defender.kind}",
                            "impact": -10.0
                        })
                        ent.mind.emotional_state["bravery"] = max(0.0, ent.mind.emotional_state.get("bravery", 0.5) - 0.1)

            # Milestone 6: Regional Suppression tracking
            reg_id = defender.current_region_id
            if reg_id:
                key = (int(defender.identity.faction), reg_id)
                deaths = context.world.faction_deaths_per_region.get(key, 0)
                context.world.faction_deaths_per_region[key] = deaths + 1

                # Milestone 7: Region Control shifts
                control = context.world.region_control.get(reg_id, 0.0)
                shift = 2.0 # default monster kill
                if defender.identity.faction == Faction.HERO_GUILD:
                    shift = -10.0 # hero death is a big blow
                elif defender.identity.is_world_boss:
                    shift = 50.0 # boss kill is a massive victory
                
                context.world.region_control[reg_id] = max(-100.0, min(100.0, control + shift))
        
        return True

    def handle_tactical_maneuvers(self, context: SystemContext, applied: list[ActionProposal], pre_positions: dict) -> None:
        """Process opportunity attacks and chase closing."""
        self._process_opportunity_attacks(context, applied, pre_positions)
        self._process_chase_closing(context)

    def _process_opportunity_attacks(self, context: SystemContext, applied: list[ActionProposal], pre_positions: dict) -> None:
        """Detect and execute opportunity attacks on fleeing enemies."""
        cfg = context.config
        world = context.world
        reg = context.faction_reg
        mult = cfg.opportunity_attack_damage_mult
        
        for proposal in applied:
            if proposal.verb != ActionType.MOVE:
                continue
            mover = world.entities.get(proposal.actor_id)
            if not mover or not mover.combat.alive:
                continue
            old_pos = pre_positions.get(proposal.actor_id)
            if not old_pos:
                continue
            
            # Find hostiles adjacent to OLD pos
            for eid in sorted(world.entities.keys()):
                ent = world.entities[eid]
                if eid == mover.id or not ent.combat.alive or ent.kind == "generator":
                    continue
                if not reg.is_hostile(mover.identity.faction, ent.identity.faction):
                    continue
                
                # Check adjacency to old pos
                old_dist = abs(ent.spatial.pos.x - old_pos[0]) + abs(ent.spatial.pos.y - old_pos[1])
                if old_dist != 1:
                    continue
                    
                # Did they move AWAY?
                new_dist = mover.spatial.pos.manhattan(ent.spatial.pos)
                if new_dist <= old_dist:
                    continue
                # OA Damage
                atk = ent.combat.atk
                df = mover.combat.def_
                raw = max(1, int(atk * mult) - df // 2)
                mover.combat.hp -= raw
                
                if context.emit:
                    context.emit("tactical", f"Entity {ent.id} Opportunity Attack → {mover.id} for {raw} dmg",
                              entity_ids=(ent.id, mover.id),
                              metadata={"verb": "OPPORTUNITY_ATTACK", "damage": raw})

    def _process_chase_closing(self, context: SystemContext) -> None:
        """SPD-based chase closing: faster hunters gain a bonus tile."""
        cfg = context.config
        world = context.world
        
        # Process in deterministic ID order
        for entity in sorted(world.entities.values(), key=lambda e: e.id):
            if not entity.combat.alive or entity.mind.ai_state != AIState.HUNT or entity.chase_ticks < 2:
                continue
            
            # Find current target
            target = self._find_nearest_hostile(context, entity)
            if not target:
                continue
                
            hunter_spd = entity.combat.spd
            target_spd = target.combat.spd
            if hunter_spd <= target_spd:
                continue
                
            interval = max(1, math.ceil(cfg.chase_spd_closing_base * target_spd / hunter_spd))
            if entity.chase_ticks % interval != 0:
                continue
                
            # Bonus move
            from src.ai.perception import Perception
            dir = Perception.direction_toward(entity.spatial.pos, target.spatial.pos)
            new_pos = entity.spatial.pos + dir
            if world.grid.is_walkable(new_pos):
                world.move_entity(entity.id, new_pos)
                if context.emit:
                    context.emit("movement", f"Entity {entity.id} sprints closer to {target.id}",
                              entity_ids=(entity.id,),
                              metadata={"verb": "CHASE_SPRINT", "actor_id": entity.id})

    def _update_combat_visualization(self, context: SystemContext, applied: list[ActionProposal]) -> None:
        """Update entity combat targets for UI/visualization from recent actions."""
        world = context.world
        from src.core.models.enums import ActionType
        acted: set[int] = set()
        for proposal in applied:
            actor = world.entities.get(proposal.actor_id)
            if not actor:
                continue
            acted.add(actor.id)

            if proposal.verb == ActionType.ATTACK:
                actor.combat_target_id = proposal.target
            elif proposal.verb == ActionType.USE_SKILL:
                # Skill target_id is often a tuple (skill_id, target_id)
                if isinstance(proposal.target, tuple) and len(proposal.target) == 2:
                    actor.combat_target_id = proposal.target[1]
                elif isinstance(proposal.target, int):
                    actor.combat_target_id = proposal.target
            elif proposal.verb in (ActionType.MOVE, ActionType.USE_ITEM, ActionType.HARVEST, ActionType.LOOT, ActionType.REST):
                # These actions don't change combat target unless state changes.
                # If they already had a target, keep it!
                pass
            else:
                actor.combat_target_id = None
        
        # Clear target for entities that are no longer in combat or hunt state.
        for entity in world.entities.values():
            if entity.id in acted:
                continue
            # Only clear target if definitely NOT in a combat state.
            if entity.mind.ai_state not in (AIState.COMBAT, AIState.HUNT, AIState.FLEE):
                entity.combat_target_id = None

    def _update_ai_derived_states(self, context: SystemContext, applied: list[ActionProposal]) -> None:
        """Update secondary AI metrics like chase_ticks and idle_ticks."""
        world = context.world
        for proposal in applied:
            entity = world.entities.get(proposal.actor_id)
            if not entity or not entity.combat.alive: continue
            
            # State update
            if proposal.new_ai_state is not None:
                entity.mind.ai_state = AIState(proposal.new_ai_state)
            if proposal.reason:
                entity.last_reason = proposal.reason
            
            # Derived counters
            if entity.mind.ai_state == AIState.HUNT:
                entity.chase_ticks += 1
            else:
                entity.chase_ticks = 0
                
            if entity.mind.ai_state == AIState.IDLE:
                entity.consecutive_idle_ticks += 1
            else:
                entity.consecutive_idle_ticks = 0

    def _find_nearest_hostile(self, context: SystemContext, entity: Any) -> Any:
        """Find the nearest visible hostile entity."""
        world = context.world
        reg = context.faction_reg
        best_dist = 999
        best_target = None
        potential = sorted(world.spatial_index.query_radius(entity.spatial.pos, entity.combat.vision_range))
        for oid in potential:
            other = world.entities.get(oid)
            if not other or not other.combat.alive or other.id == entity.id:
                continue
            if not reg.is_hostile(entity.identity.faction, other.identity.faction):
                continue
            d = entity.spatial.pos.manhattan(other.spatial.pos)
            if d < best_dist:
                best_dist = d
                best_target = other
        return best_target
