"""CombatAction — validates and resolves attack proposals.

Refactored for AOA Stabilization:
- Decomposed monolithic apply() into specialized services.
- Removed legacy property shims and StatsProxy dependencies.
- Aligned with nested MindAspect (EmotionState, NarrativeMemory, etc.).
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.actions.base import ActionProposal
from src.actions.damage import get_damage_calculator
from src.core.models.enums import ActionType, DamageType, Domain, Element, EmotionType
from src.core.gameplay.faction import Faction, FactionRegistry
from src.core.gameplay.items.item_registry import ITEM_REGISTRY

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.core.models.world_state import WorldState
    from src.platform.rng import DeterministicRNG
    from src.core.entities.entity import Entity

logger = logging.getLogger(__name__)

class DamageResolutionService:
    @staticmethod
    def resolve(attacker: Entity, defender: Entity, world: WorldState, config: SimulationConfig, rng: DeterministicRNG) -> tuple[int, bool, bool, dict]:
        tick = world.tick
        
        # --- Evasion Check ---
        luck_mod = attacker.combat.luck * 0.002
        effective_evasion = max(0.0, defender.combat.evasion - luck_mod)
        if rng.next_bool(Domain.COMBAT, defender.id, tick + 3, effective_evasion):
            return 0, False, True, {"raw_damage": 0, "mitigation": 0, "elemental_mult": 1.0, "dmg_type": DamageType.PHYSICAL.name.lower(), "element": Element.NONE.name.lower()}

        # --- Determine Damage Type and Element ---
        dmg_type = DamageType.PHYSICAL
        element = Element.NONE
        if attacker.inventory and attacker.inventory.weapon:
            weapon_tmpl = ITEM_REGISTRY.get(attacker.inventory.weapon)
            if weapon_tmpl:
                dmg_type = weapon_tmpl.damage_type
                element = weapon_tmpl.element

        # --- Base Damage Calculation ---
        calculator = get_damage_calculator(dmg_type)
        dmg_ctx = calculator.resolve(attacker, defender)
        
        atk_final = int(dmg_ctx.atk_power * dmg_ctx.atk_mult)
        def_final = int(dmg_ctx.def_power * dmg_ctx.def_mult)
        
        # Pillar 3: Fractional Armor Mitigation
        raw_damage = int(atk_final * (atk_final / (atk_final + def_final * 2.0 + 1.0)))
        raw_damage = max(raw_damage, 1)
        
        # Variance
        variance = rng.next_float(Domain.COMBAT, attacker.id, tick + 2)
        damage = int(raw_damage * (1.0 + config.damage_variance * (variance - 0.5)))
        
        # Elemental vulnerability
        if element != Element.NONE:
            elem_mult = defender.combat.elemental_vulnerability(element)
            damage = int(damage * elem_mult)

        # Crit check
        crit_rate = attacker.combat.crit_rate + attacker.combat.luck * 0.003
        is_crit = rng.next_bool(Domain.COMBAT, attacker.id, tick + 1, min(crit_rate, 0.8))
        if is_crit:
            damage = int(damage * attacker.combat.crit_dmg)

        # Return rich detail for traces
        return max(damage, 1), is_crit, False, {
            "raw_damage": raw_damage,
            "mitigation": int(atk_final - raw_damage),
            "elemental_mult": elem_mult if element != Element.NONE else 1.0,
            "dmg_type": dmg_type.name.lower() if hasattr(dmg_type, "name") else DamageType(dmg_type).name.lower(),
            "element": element.name.lower() if hasattr(element, "name") else Element(element).name.lower()
        }

class CombatAftermathService:
    @staticmethod
    def process(attacker: Entity, defender: Entity, world: WorldState, damage: int, is_crit: bool, is_evasion: bool, config: SimulationConfig, proposal: ActionProposal, trace_details: dict | None = None):
        tick = world.tick
        
        # Emit combat event for monitoring and E2E tests
        skill_label = "attack"
        if proposal.reason == "Opportunity Attack":
            skill_label = "OPPORTUNITY_ATTACK"
        elif proposal.verb.name == "USE_SKILL" if hasattr(proposal.verb, "name") else proposal.verb == 40: # 40 is USE_SKILL
            # In AOA, skills are usually handled via ActionSystem, but we keep this for consistency if called here
            skill_label = "SKILL"

        if hasattr(world, "event_bus") and world.event_bus:
            from src.core.data.events import CombatEvent
            world.event_bus.publish(CombatEvent(
                attacker_id=attacker.id, defender_id=defender.id,
                damage=damage, is_crit=is_crit, is_evasion=is_evasion,
                skill_used=skill_label,
                attacker_hp=attacker.combat.hp, defender_hp=defender.combat.hp
            ))

        # Rich Trace Generation (AOA Phase 5)
        from src.actions.base import CombatTraceUpdate, CombatTraceDetails
        trace = CombatTraceUpdate(
            tick=tick, attacker_id=attacker.id, defender_id=defender.id,
            damage=damage, is_crit=is_crit, is_evasion=is_evasion,
            skill_used=skill_label,
            details=CombatTraceDetails(
                raw_damage=trace_details.get("raw_damage", 0) if trace_details else 0,
                mitigated_damage=trace_details.get("mitigation", 0) if trace_details else 0,
                elemental_mult=trace_details.get("elemental_mult", 1.0) if trace_details else 1.0
            )
        )
        proposal.updates.append(trace)
        
        # Award veterancy for successful hit
        if not is_evasion:
            attacker.progression.veterancy_points += 1 # Legacy mutation for unit tests
            from src.actions.base import ProgressionUpdate
            proposal.updates.append(ProgressionUpdate(veterancy_points_delta=1))

        if is_evasion:
            return

        # Nemesis & Memory (Emotion/Narrative)
        hp_lost_ratio = damage / max(1, defender.combat.max_hp)
        
        # Updates instead of direct mutation
        from src.actions.base import MindUpdate, PerceptionUpdate
        proposal.updates.append(MindUpdate(
            emotion_delta={EmotionType.PANIC: hp_lost_ratio * 0.5}, # Dummy logic for example
            mood=-hp_lost_ratio * 0.2
        ))
        
        if hp_lost_ratio > 0.15:
            from src.core.aspects.mind import MemoryLogEntry
            proposal.updates.append(PerceptionUpdate(
                memory_log_add=[MemoryLogEntry(
                    tick=tick, type="TRAUMA", impact=-hp_lost_ratio * 100.0,
                    details={"desc": f"Took massive damage ({damage}) from {attacker.identity.display_name} #{attacker.id}", "source_id": attacker.id}
                )]
            ))
            
        # Threat Table (PerceptionUpdate)
        base_threat = damage * config.threat_damage_mult
        from src.core.models.enums import HeroClass
        hclass = getattr(attacker.progression, "hero_class", None)
        hclass_name = hclass.name if hasattr(hclass, "name") else (HeroClass(hclass).name if hclass is not None else "")
        if hclass_name == "WARRIOR": base_threat *= 1.5
        elif hclass_name in ("PALADIN", "GUARDIAN", "TANK"): base_threat *= 2.0
            
        proposal.updates.append(PerceptionUpdate(
            threat_table_delta={attacker.id: base_threat} # We need this in PerceptionUpdate!
        ))

class KillRewardService:
    @staticmethod
    def resolve_kill(killer: Entity, victim: Entity, world: WorldState, proposal: ActionProposal):
        tick = world.tick
        from src.actions.base import ProgressionUpdate
        
        # XP Gain
        xp_gain = 5 if victim.progression.level <= killer.progression.level else 10
        # Killer gets XP/Gold/Veterancy
        killer.progression.veterancy_points += 5 # Legacy mutation for unit tests
        proposal.updates.append(ProgressionUpdate(gold_delta=victim.progression.gold, xp_delta=xp_gain, veterancy_points_delta=5))
        
        # Gold/Corpse
        from src.core.models.world_objects import CorpseNode
        if victim.identity.faction == Faction.HERO_GUILD:
            node_id = world._next_corpse_id
            world._next_corpse_id += 1
            
            gold_to_corpse = int(victim.progression.gold * 0.8)
            # Re-adjust killer gold (we already added full gold above, so remove the corpse portion)
            proposal.updates.append(ProgressionUpdate(gold_delta=-gold_to_corpse))
            
            node = CorpseNode(
                node_id=node_id, entity_id=victim.id, pos=victim.spatial.pos,
                items=list(victim.inventory.items) if victim.inventory else [],
                gold=gold_to_corpse, created_tick=tick
            )
            world.corpse_nodes[node_id] = node
        else:
            # Victim loses gold (already given to killer)
            # In AOA, we assume victim will be removed or reset soon.
            pass
            
        # World Boss Rewards (AOA Hardening)
        if victim.identity.is_world_boss:
            killer.progression.fame += 100
            title = f"Slayer of {victim.identity.display_name}"
            if title not in killer.identity.titles:
                killer.identity.titles.append(title)
            logger.info("Entity %d earned 'World Boss Slayer' rewards for killing %d", killer.id, victim.id)
            
        # Death Event
        if hasattr(world, "event_bus") and world.event_bus:
            from src.core.data.events import DeathEvent
            world.event_bus.publish(DeathEvent(
                entity_id=victim.id, killer_id=killer.id,
                x=int(victim.spatial.pos.x), y=int(victim.spatial.pos.y),
                level_at_death=victim.progression.level,
                is_permadeath=bool(getattr(victim.identity, "is_permadeath", False))
            ))

class CombatAction:
    """Stateless handler for ATTACK proposals."""

    def __init__(self, config: SimulationConfig, rng: DeterministicRNG) -> None:
        self._config = config
        self._rng = rng

    def validate(self, proposal: ActionProposal, world: WorldState) -> bool:
        attacker = world.entities.get(proposal.actor_id)
        if not attacker or not attacker.combat.alive: return False
        
        from src.actions.base import BuildingTarget
        if isinstance(proposal.target, BuildingTarget):
            # Building attack validation
            target_b = next((b for b in world.buildings if b.building_id == proposal.target.building_id), None)
            if not target_b or not target_b.is_functional: return False
            dist = attacker.spatial.pos.manhattan(target_b.pos)
            return dist <= self._get_weapon_range(attacker)
            
        target_id: int = proposal.target
        defender = world.entities.get(target_id)
        if not defender or not defender.combat.alive: return False
        
        # 1. Distance check
        dist = attacker.spatial.pos.manhattan(defender.spatial.pos)
        weapon_range = self._get_weapon_range(attacker)
        if dist > weapon_range: return False
        
        # 2. Line of Sight check for ranged attacks (range > 1)
        if weapon_range > 1 and dist > 1:
            if not world.grid.has_line_of_sight(
                int(attacker.spatial.pos.x), int(attacker.spatial.pos.y),
                int(defender.spatial.pos.x), int(defender.spatial.pos.y)
            ):
                return False
                
        return True

    def apply(self, proposal: ActionProposal, world: WorldState) -> None:
        attacker = world.entities.get(proposal.actor_id)
        if not attacker: return

        from src.actions.base import BuildingTarget
        if isinstance(proposal.target, BuildingTarget):
            # Building damage application
            target_b = next((b for b in world.buildings if b.building_id == proposal.target.building_id), None)
            if target_b:
                damage = int(attacker.combat.atk * 0.5) # Buildings take 50% damage from basic attacks
                target_b.take_damage(damage)
                logger.info("Entity %d sabotaged building %s for %d damage", attacker.id, target_b.building_id, damage)
            return

        defender = world.entities.get(proposal.target)
        if not defender: return

        # RESOLVE
        damage, is_crit, is_evasion, trace_details = DamageResolutionService.resolve(
            attacker, defender, world, self._config, self._rng
        )

        # APPLY STATE CHANGES
        if not is_evasion:
            defender.combat.hp -= damage
            defender.combat.validate()
        
        # AFTERMATH (Memory, Grudges, Threat)
        CombatAftermathService.process(attacker, defender, world, damage, is_crit, is_evasion, self._config, proposal, trace_details)

        # TOUGHNESS HARDENING (design-04)
        if not is_evasion and defender.combat.alive:
            if defender.combat.hp / defender.combat.max_hp < 0.15:
                defender.combat.max_hp += 1
                defender.combat.validate()

        # KILL RESOLUTION
        if not defender.combat.alive:
            KillRewardService.resolve_kill(attacker, defender, world, proposal)

    @staticmethod
    def _get_weapon_range(entity: Entity) -> int:
        if entity.inventory and entity.inventory.weapon:
            weapon_tmpl = ITEM_REGISTRY.get(entity.inventory.weapon)
            if weapon_tmpl:
                return weapon_tmpl.weapon_range
        return 1
