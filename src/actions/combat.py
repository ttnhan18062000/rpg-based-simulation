"""CombatAction — validates and resolves attack proposals.

Damage calculation supports dual damage types (Physical / Magical) with
elemental tags.  The weapon’s damage_type determines which stat pair is
used (ATK/DEF vs MATK/MDEF).  Elemental tags on weapons apply a
vulnerability multiplier from the defender’s elem_vuln table.

Effective stats (base + equipment + status effects) are used throughout,
so territory debuffs and other effects are automatically applied.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.actions.base import ActionProposal
from src.actions.damage import get_damage_calculator
from src.core.models.enums import ActionType, DamageType, Domain, Element
from src.core.gameplay.faction import Faction, FactionRegistry
from src.core.gameplay.items.item_registry import ITEM_REGISTRY

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.core.models.world_state import WorldState
    from src.platform.rng import DeterministicRNG

logger = logging.getLogger(__name__)


class CombatAction:
    """Stateless handler for ATTACK proposals."""

    def __init__(self, config: SimulationConfig, rng: DeterministicRNG) -> None:
        self._config = config
        self._rng = rng

    def validate(self, proposal: ActionProposal, world: WorldState) -> bool:
        if proposal.verb != ActionType.ATTACK:
            return False

        attacker = world.entities.get(proposal.actor_id)
        if attacker is None or not attacker.combat.alive:
            return False

        if isinstance(proposal.target, str) and proposal.target.startswith("BUILDING:"):
            bid = proposal.target.split(":")[1]
            target_b = next((b for b in world.buildings if b.building_id == bid), None)
            if not target_b or not target_b.is_functional:
                return False
            # Range check
            dist = attacker.spatial.pos.manhattan(target_b.spatial.pos)
            if dist > self._get_weapon_range(attacker):
                return False
            return True

        target_id: int = proposal.target
        defender = world.entities.get(target_id)
        if defender is None or not defender.combat.alive:
            logger.debug(
                "Entity %d attack on %s failed — target dead or missing",
                proposal.actor_id,
                target_id,
            )
            return False

        # Range check — use weapon range (default 1 for melee)
        weapon_range = self._get_weapon_range(attacker)
        dist = attacker.spatial.pos.manhattan(defender.spatial.pos)
        if dist > weapon_range:
            logger.debug("Entity %d attack on %d failed — out of range (%d > %d)",
                         proposal.actor_id, target_id, dist, weapon_range)
            return False

        # Line-of-sight check for ranged attacks (distance > 1)
        if dist > 1 and not world.grid.has_line_of_sight(
                attacker.spatial.pos.x, attacker.spatial.pos.y, defender.spatial.pos.x, defender.spatial.pos.y):
            logger.debug("Entity %d ranged attack on %d blocked — no line of sight",
                         proposal.actor_id, target_id)
            return False

        return True

    def apply(self, proposal: ActionProposal, world: WorldState) -> None:
        attacker = world.entities.get(proposal.actor_id)
        if attacker is None:
            return

        if isinstance(proposal.target, str) and proposal.target.startswith("BUILDING:"):
            bid = proposal.target.split(":")[1]
            target_b = next((b for b in world.buildings if b.building_id == bid), None)
            if target_b:
                # Buildings take 50% damage from basic attacks
                if attacker.identity.hero_class != 0:
                    dmg = attacker.combat.atk * 0.5
                    target_b.take_damage(dmg)
                    logger.info(f"Tick {world.tick}: {attacker.kind} #{attacker.id} damaged {target_b.name} for {dmg:.1f}")
                    attacker.progression.stamina = max(0, attacker.progression.stamina - 5)
                    from src.core.gameplay.attributes import speed_delay
                    attacker.next_act_at += speed_delay(attacker.combat.spd, "attack")
            return

        target_id: int = proposal.target
        defender = world.entities.get(target_id)
        if defender is None:
            return

        tick = world.tick
        cfg = self._config
        dist = attacker.spatial.pos.manhattan(defender.spatial.pos)

        # --- Evasion check ---
        defender_evasion = defender.combat.evasion
        
        # Agility impact: hit chance
        luck_mod = attacker.combat.luck * 0.002
        effective_evasion = max(0.0, defender_evasion - luck_mod)
        if self._rng.next_bool(Domain.COMBAT, defender.id, tick + 3, effective_evasion):
            logger.info(
                "Tick %d: Entity %d (%s) attack EVADED by Entity %d (%s)",
                tick, attacker.id, attacker.kind, defender.id, defender.kind,
            )
            if hasattr(world, "event_bus") and world.event_bus:
                from src.core.data.events import CombatEvent
                world.event_bus.publish(CombatEvent(
                    attacker_id=attacker.id,
                    defender_id=defender.id,
                    damage=0,
                    is_crit=False,
                    is_evasion=True,
                    skill_used="attack",
                    attacker_hp=attacker.combat.hp,
                    defender_hp=defender.combat.hp
                ))
            from src.core.gameplay.attributes import speed_delay
            attacker.next_act_at += speed_delay(attacker.combat.spd, "attack")
            return

        # --- Determine damage type and element from weapon ---
        dmg_type = DamageType.PHYSICAL
        element = Element.NONE
        if attacker.inventory and attacker.inventory.weapon:
            weapon_tmpl = ITEM_REGISTRY.get(attacker.inventory.weapon)
            if weapon_tmpl:
                dmg_type = weapon_tmpl.damage_type
                element = weapon_tmpl.element

        # --- Damage calculation (strategy pattern) ---
        calculator = get_damage_calculator(dmg_type)
        dmg_ctx = calculator.resolve(attacker, defender)

        # Pillar 3: Fractional Armor Mitigation
        # Formula: dmg = raw_atk * (raw_atk / (raw_atk + def*2))
        # This ensures high-defense entities are chipped but not instantly slaughtered.
        atk_final = int(dmg_ctx.atk_power * dmg_ctx.atk_mult)
        def_final = int(dmg_ctx.def_power * dmg_ctx.def_mult)
        
        raw_damage = int(atk_final * (atk_final / (atk_final + def_final * 2.0 + 1.0)))
        raw_damage = max(raw_damage, 1)
        variance = self._rng.next_float(Domain.COMBAT, attacker.id, tick + 2)
        damage = int(raw_damage * (1.0 + cfg.damage_variance * (variance - 0.5)))
        damage = max(damage, 1)

        # --- Metrics: Combat Event ---
        from src.utils.metrics import SIM_COMBAT_EVENTS
        SIM_COMBAT_EVENTS.labels(
            attacker_faction=Faction(attacker.identity.faction).name.lower(),
            defender_faction=Faction(defender.identity.faction).name.lower()
        ).inc()

        # --- Elemental vulnerability modifier ---
        if element != Element.NONE:
            elem_mult = defender.elemental_vulnerability(element)
            damage = max(1, int(damage * elem_mult))

        # --- Crit check ---
        crit_rate = attacker.combat.crit_rate
        crit_rate += attacker.combat.luck * 0.003
        is_crit = self._rng.next_bool(Domain.COMBAT, attacker.id, tick + 1, min(crit_rate, 0.8))
        if is_crit:
            damage = int(damage * attacker.combat.crit_dmg)
            
        defender.combat.hp -= damage
        # Build damage descriptor
        dmg_label = "MAG" if dmg_type == DamageType.MAGICAL else "PHY"
        elem_label = ""
        if element != Element.NONE:
            elem_label = f" [{Element(element).name}]"
        logger.info(
            "TICK_ACTION_COMBAT: [%s]%s(L%s) hit [%s]%s(L%s) for %s dmg. Def HP: %s/%s",
            attacker.id, attacker.kind, attacker.progression.level,
            defender.id, defender.kind, defender.progression.level,
            damage,
            max(defender.combat.hp, 0),
            defender.combat.max_hp,
        )
        
        if hasattr(world, "event_bus") and world.event_bus:
            from src.core.data.events import CombatEvent
            world.event_bus.publish(CombatEvent(
                attacker_id=attacker.id,
                defender_id=defender.id,
                damage=damage,
                is_crit=is_crit,
                is_evasion=False,
                skill_used="attack",
                attacker_hp=attacker.combat.hp,
                defender_hp=defender.combat.hp
            ))

        # --- Nemesis System: Grudge tracking ---
        if hasattr(defender, "mind"):
            # Every hit increases the grudge proportional to % of max HP lost
            hp_lost_ratio = damage / defender.combat.max_hp
            grudge_gain = hp_lost_ratio * 50.0
            defender.mind.grudges[attacker.id] = defender.mind.grudges.get(attacker.id, 0.0) + grudge_gain
            # Small mood drop when taking damage (fear/despair)
            defender.mind.mood = max(0.0, defender.mind.mood - hp_lost_ratio * 0.2)
            
            # --- Narrative Memory: TRAUMA ---
            if hp_lost_ratio > 0.15: # Significant hit
                defender.mind.memory_log.append({
                    "tick": tick,
                    "type": "TRAUMA",
                    "desc": f"Took massive damage ({damage}) from {attacker.kind} #{attacker.id}",
                    "impact": -hp_lost_ratio * 100.0,
                    "source_id": attacker.id
                })
        
        if hasattr(attacker, "mind") and hp_lost_ratio > 0.2:
            # --- Narrative Memory: TRIUMPH ---
            attacker.mind.memory_log.append({
                "tick": tick,
                "type": "TRIUMPH",
                "desc": f"Dealt massive damage ({damage}) to {defender.kind} #{defender.id}",
                "impact": hp_lost_ratio * 50.0,
                "target_id": defender.id
            })

        # --- Threat generation (epic-05 F3) ---
        threat = damage * cfg.threat_damage_mult
        from src.core.gameplay.classes import HeroClass
        if attacker.progression.hero_class in (HeroClass.WARRIOR, HeroClass.CHAMPION):
            threat *= cfg.threat_tank_class_mult
        defender.mind.threat_table[attacker.id] = defender.mind.threat_table.get(attacker.id, 0.0) + threat
        # LOGGING: Milestone 8 - Trace threat generation
        import logging
        logging.getLogger("combat").debug("Threat generated: Entity %d -> Entity %d, +%.2f", attacker.id, defender.id, threat)

        from src.core.gameplay.attributes import speed_delay
        attacker.next_act_at += speed_delay(attacker.combat.spd, "attack")

        # Stamina cost
        attacker.progression.stamina = max(0, attacker.progression.stamina - 3)

        # --- Attribute training from combat ---
        if attacker.attributes and attacker.attribute_caps:
            from src.core.gameplay.attributes import train_attributes
            train_attributes(attacker.attributes, attacker.attribute_caps, dmg_ctx.train_action, stats=attacker.stats, race=attacker.kind, talents=attacker.talents, weakness=attacker.weakness)
        if defender.attributes and defender.attribute_caps and defender.combat.alive:
            from src.core.gameplay.attributes import train_attributes
            train_attributes(defender.attributes, defender.attribute_caps, "defend", stats=defender.stats, race=defender.kind, talents=defender.talents, weakness=defender.weakness)

        # --- Veterancy (epic-18 F1) ---
        from src.core.models.enums import VeterancyRank

        def check_veterancy_rank_up(entity, world_ref) -> None:
            """Check and apply veterancy rank ups."""
            old_rank = entity.veterancy_rank
            new_rank = old_rank
            pts = entity.veterancy_points
            
            if pts >= 500: new_rank = VeterancyRank.LEGEND
            elif pts >= 200: new_rank = VeterancyRank.ELITE
            elif pts >= 80: new_rank = VeterancyRank.VETERAN
            elif pts >= 25: new_rank = VeterancyRank.BLOODED
            
            if new_rank > old_rank:
                entity.veterancy_rank = new_rank
                rank_name = VeterancyRank(new_rank).name.title()
                logger.info("Tick %s: Entity %s (%s) promoted to %s!", tick, entity.id, entity.kind, rank_name)

        # +1 pt per hit dealt
        attacker.veterancy_points += 1
        check_veterancy_rank_up(attacker, world)
        
        # +1 pt per hit taken and survived
        if defender.combat.alive:
            defender.veterancy_points += 1
            # Near death survival +3 pt
            if defender.combat.hp_ratio < 0.25:
                defender.mind.memory_log.append({"tick": tick, "type": "SURVIVAL", "impact": 1.5})
                
            if defender.combat.hp_ratio < 0.15:
                defender.combat.max_hp += 1
                logger.info("TICK_ACTION_COMBAT: [%s] %s (%s) survived near-death, MaxHP increased to %s",
                            tick, defender.id, defender.kind, defender.combat.max_hp)
                
            check_veterancy_rank_up(defender, world)

        # --- XP award on kill ---
        if not defender.combat.alive:
            # --- Nemesis System: Bad Memories ---
            if hasattr(defender, "mind"):
                # Record the region where death occurred
                from src.core.world.regions import find_region_at
                region = find_region_at(defender.spatial.pos, world.regions)
                region_id = region.region_id if region else None
                if region_id:
                    # Mark this region as dangerous (-0.5 sentiment)
                    defender.mind.memory_locations[region_id] = defender.mind.memory_locations.get(region_id, 0.0) - 0.5
                # Record the killer in memory for a massive grudge after respawn
                defender.mind.memory["last_killer_id"] = attacker.id
                defender.mind.mood = 0.2 # Respawns in a fearful state
            
            # +5 points for a kill (+10 if higher level)
            xp_gain = 5
            if defender.progression.level > attacker.progression.level:
                xp_gain = 10
            
            # Application of RPG rules
            from src.core.models.enums import TraitType
            if TraitType.TACTICAL in attacker.identity.traits:
                xp_gain = int(xp_gain * 1.2)
                
            # xp_gain = int(xp_gain * attacker.progression.xp_mult)
            attacker.progression.xp += xp_gain
            attacker.veterancy_points += xp_gain
            # --- Milestone 11: Track death for regional control ---
            from src.core.world.regions import find_region_at
            region = find_region_at(defender.spatial.pos, world.regions)
            if region:
                key = (int(defender.identity.faction), region.region_id)
                world.faction_deaths_per_region[key] = world.faction_deaths_per_region.get(key, 0) + 1

            # --- Pillar 4: Corpse Node (Continuity) ---
            from src.core.models import CorpseNode
            if hasattr(world, "corpse_nodes") and (defender.identity.role == "hero" or defender.identity.is_world_boss):
                node_id = world._next_corpse_id
                world._next_corpse_id += 1
                
                # 80% Gold retention in corpse, 20% to killer
                corpse_gold = int(defender.progression.gold * 0.8)
                looted_gold = defender.progression.gold - corpse_gold
                attacker.progression.gold += looted_gold
                
                # Drop non-equipped inventory
                corpse_items = []
                if defender.inventory:
                    corpse_items = list(defender.inventory.items)
                    defender.inventory.items = [] # Wipe hero inventory
                
                node = CorpseNode(
                    node_id=node_id,
                    entity_id=defender.id,
                    pos=defender.spatial.pos,
                    items=corpse_items,
                    gold=corpse_gold,
                    created_tick=tick
                )
                world.corpse_nodes[node_id] = node
                logger.info("Tick %s: Entity %s died -> Created CorpseNode #%s at %s", tick, defender.id, node_id, defender.spatial.pos)
            else:
                # Normal loot for non-heroes
                attacker.progression.gold += defender.progression.gold
                defender.progression.gold = 0

            # --- Pillar 5: Nemesis Evolution ---
            from src.systems.lifecycle.evolution_system import EvolutionSystem
            EvolutionSystem.on_hero_slain(attacker, defender, world)

            logger.info(
                "Tick %s: Entity %s (%s) gained %s XP from killing Entity %s (%s) [XP: %s/%s]",
                tick, attacker.id, attacker.kind, xp_gain,
                defender.id, defender.kind,
                attacker.progression.xp, attacker.progression.xp_to_next,
            )
            # --- Quest progress: HUNT ---
            if attacker.quests:
                from src.core.gameplay.quests import QuestType
                for q in attacker.quests:
                    if q.quest_type == QuestType.HUNT and not q.completed:
                        if q.target_kind == defender.kind:
                            just_done = q.advance()
                            if just_done:
                                from src.utils.metrics import SIM_QUEST_STATUS_TOTAL
                                SIM_QUEST_STATUS_TOTAL.labels(type=q.quest_type.name.lower(), status="completed").inc()
                                attacker.progression.gold += q.gold_reward
                                attacker.progression.xp += q.xp_reward
                                logger.info(
                                    "Tick %s: Entity %s completed quest '%s' → +%s gold, +%s XP",
                                    tick, attacker.id, q.title,
                                    q.gold_reward, q.xp_reward,
                                )
                                if hasattr(world, "event_bus") and world.event_bus:
                                    from src.core.data.events import QuestEvent
                                    world.event_bus.publish(QuestEvent(
                                        entity_id=attacker.id,
                                        quest_title=q.title,
                                        quest_type=q.quest_type.name,
                                        status="completed",
                                        gold_reward=q.gold_reward,
                                        xp_reward=q.xp_reward
                                    ))
                    elif q.quest_type.name == "BOUNTY" and not q.completed:
                        # Bounty completion check: kind matches boss display name or kind
                        if defender.identity.is_world_boss and (q.target_kind == defender.identity.display_name or q.target_kind == defender.kind):
                            just_done = q.advance()
                            if just_done:
                                from src.utils.metrics import SIM_QUEST_STATUS_TOTAL
                                SIM_QUEST_STATUS_TOTAL.labels(type="bounty", status="completed").inc()
                                attacker.progression.gold += q.gold_reward
                                attacker.progression.xp += q.xp_reward
                                attacker.progression.fame += 100
                                logger.info(
                                    "Tick %s: Entity %s completed BOUNTY '%s' → +%s gold, +%s XP, +100 Fame",
                                    tick, attacker.id, q.title,
                                    q.gold_reward, q.xp_reward,
                                )
                                if hasattr(world, "event_bus") and world.event_bus:
                                    from src.core.data.events import QuestEvent
                                    world.event_bus.publish(QuestEvent(
                                        entity_id=attacker.id,
                                        quest_title=q.title,
                                        quest_type="BOUNTY",
                                        status="completed",
                                        gold_reward=q.gold_reward,
                                        xp_reward=q.xp_reward
                                    ))

            # --- Calamity-Specific Rewards (Titles) ---
            if defender.identity.is_world_boss:
                title = f"Slayer of {defender.identity.display_name}"
                if title not in attacker.titles:
                    attacker.titles.append(title)
                    # Titles grant a permanent 5% ATK boost (simplified as flat addition for now)
                    # In a property-based architecture, this would be computed in StatsProxy
                    attacker.stats.combat.atk = int(attacker.stats.combat.atk * 1.05)
                    logger.info("Tick %s: Hero %s earned Title: %s! Permanent +5%% ATK bonus applied.",
                                tick, attacker.id, title)
                    # Note: World events for titles are handled in WorldLoop or via logging

    @staticmethod
    def _get_weapon_range(entity) -> int:
        """Return the weapon range of the entity's equipped weapon (default 1 = melee)."""
        if entity.inventory and entity.inventory.weapon:
            weapon_tmpl = ITEM_REGISTRY.get(entity.inventory.weapon)
            if weapon_tmpl:
                return weapon_tmpl.weapon_range
        return 1

    @staticmethod
    def _calculate_xp(attacker, defender, cfg) -> int:
        """XP = base * defender_level * scale, bonus for higher-tier enemies.
        Mobs learn at half the rate of heroes."""
        base = cfg.xp_per_kill_base
        level_mult = max(1, defender.progression.level)
        tier_bonus = 1.0 + defender.identity.tier * 0.5
        xp = int(base * level_mult * tier_bonus)
        
        from src.core.models.enums import EntityRole
        if attacker.identity.role == EntityRole.MOB:
            xp = int(xp * 0.5)
            
        return max(xp, 1)
