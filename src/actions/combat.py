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
from src.core.models.enums import ActionType, DamageType, Domain, Element
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
    def resolve(attacker: Entity, defender: Entity, world: WorldState, config: SimulationConfig, rng: DeterministicRNG) -> tuple[int, bool, bool, DamageType, Element]:
        tick = world.tick
        
        # --- Evasion Check ---
        luck_mod = attacker.combat.luck * 0.002
        effective_evasion = max(0.0, defender.combat.evasion - luck_mod)
        if rng.next_bool(Domain.COMBAT, defender.id, tick + 3, effective_evasion):
            return 0, False, True, DamageType.PHYSICAL, Element.NONE

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
            "dmg_type": dmg_type.name.lower(),
            "element": element.name.lower()
        }

class CombatAftermathService:
    @staticmethod
    def process(attacker: Entity, defender: Entity, world: WorldState, damage: int, is_crit: bool, is_evasion: bool, config: SimulationConfig, proposal: ActionProposal, trace_details: dict | None = None):
        tick = world.tick
        
        # Emit combat event for monitoring and E2E tests
        skill_label = "attack"
        if proposal.reason == "Opportunity Attack":
            skill_label = "OPPORTUNITY_ATTACK"
        elif proposal.intent_metadata and "skill_used" in proposal.intent_metadata:
            skill_label = proposal.intent_metadata["skill_used"].upper() # Standardize for E2E

        if hasattr(world, "event_bus") and world.event_bus:
            from src.core.data.events import CombatEvent
            world.event_bus.publish(CombatEvent(
                attacker_id=attacker.id, defender_id=defender.id,
                damage=damage, is_crit=is_crit, is_evasion=is_evasion,
                attacker_hp=attacker.combat.hp, defender_hp=defender.combat.hp
            ))

        # Record Trace for introspection (ring buffer)
        if hasattr(defender.combat, "traces"):
            trace = {
                "tick": world.tick,
                "attacker_id": attacker.id,
                "defender_id": defender.id,
                "skill_used": skill_label,
                "damage": damage,
                "is_crit": is_crit,
                "is_evasion": is_evasion
            }
            if trace_details:
                trace.update(trace_details)
            
            defender.combat.traces.append(trace)
            if len(defender.combat.traces) > 10:
                defender.combat.traces.pop(0)

        if is_evasion:
            return

        # Nemesis & Memory (Emotion/Narrative)
        hp_lost_ratio = damage / defender.combat.max_hp
        defender.mind.emotion.grudges[attacker.id] = defender.mind.emotion.grudges.get(attacker.id, 0.0) + (hp_lost_ratio * 50.0)
        defender.mind.emotion.mood = max(0.0, defender.mind.emotion.mood - hp_lost_ratio * 0.2)
        
        if hp_lost_ratio > 0.15:
            defender.mind.narrative.memory_log.append({
                "tick": tick, "type": "TRAUMA", "desc": f"Took massive damage ({damage}) from {attacker.kind} #{attacker.id}",
                "impact": -hp_lost_ratio * 100.0, "source_id": attacker.id
            })
            
        # Threat Table (AOA Hardening: Class-based Multipliers)
        base_threat = damage * config.threat_damage_mult
        
        # Apply class-specific multipliers for tanks
        from src.core.models.enums import HeroClass
        hclass = getattr(attacker.progression, "hero_class", None)
        if hclass == HeroClass.WARRIOR:
            base_threat *= 1.5
        # Add other tank classes here if they exist (e.g. PALADIN, GUARDIAN)
        elif hclass and hclass.name in ("PALADIN", "GUARDIAN", "TANK"):
            base_threat *= 2.0
            
        defender.mind.perception.threat_table[attacker.id] = defender.mind.perception.threat_table.get(attacker.id, 0.0) + base_threat

class KillRewardService:
    @staticmethod
    def resolve_kill(killer: Entity, victim: Entity, world: WorldState):
        tick = world.tick
        
        # XP Gain
        xp_gain = 5 if victim.progression.level <= killer.progression.level else 10
        killer.progression.xp += xp_gain
        
        # Gold/Corpse
        from src.core.models.world_objects import CorpseNode
        if victim.identity.faction == Faction.HERO_GUILD:
            node_id = world._next_corpse_id
            world._next_corpse_id += 1
            
            gold_to_corpse = int(victim.progression.gold * 0.8)
            killer.progression.gold += (victim.progression.gold - gold_to_corpse)
            
            node = CorpseNode(
                node_id=node_id, entity_id=victim.id, pos=victim.spatial.pos,
                items=list(victim.inventory.items) if victim.inventory else [],
                gold=gold_to_corpse, created_tick=tick
            )
            world.corpse_nodes[node_id] = node
        else:
            killer.progression.gold += victim.progression.gold
            victim.progression.gold = 0
            
        # World Boss Rewards (AOA Hardening)
        if victim.identity.is_world_boss:
            killer.progression.fame += 100
            title = f"Slayer of {victim.identity.display_name}"
            if title not in killer.identity.titles:
                killer.identity.titles.append(title)
            logger.info("Entity %d earned 'World Boss Slayer' rewards for killing %d", killer.id, victim.id)

class CombatAction:
    """Stateless handler for ATTACK proposals."""

    def __init__(self, config: SimulationConfig, rng: DeterministicRNG) -> None:
        self._config = config
        self._rng = rng

    def validate(self, proposal: ActionProposal, world: WorldState) -> bool:
        attacker = world.entities.get(proposal.actor_id)
        if not attacker or not attacker.combat.alive: return False
        
        # ... simplified range/LoS logic ...
        target_id: int = proposal.target
        defender = world.entities.get(target_id)
        if not defender or not defender.combat.alive: return False
        
        dist = attacker.spatial.pos.manhattan(defender.spatial.pos)
        if dist > self._get_weapon_range(attacker): return False
        return True

    def apply(self, proposal: ActionProposal, world: WorldState) -> None:
        attacker = world.entities.get(proposal.actor_id)
        defender = world.entities.get(proposal.target)
        if not attacker or not defender: return

        # RESOLVE
        damage, is_crit, is_evasion, trace_details = DamageResolutionService.resolve(
            attacker, defender, world, self._config, self._rng
        )

        # APPLY STATE CHANGES
        if not is_evasion:
            defender.combat.hp -= damage
        
        # AFTERMATH (Memory, Grudges, Threat)
        CombatAftermathService.process(attacker, defender, world, damage, is_crit, is_evasion, self._config, proposal, trace_details)

        # TOUGHNESS HARDENING (design-04)
        if not is_evasion and defender.combat.alive:
            if defender.combat.hp / defender.combat.max_hp < 0.15:
                defender.combat.max_hp += 1

        # KILL RESOLUTION
        if not defender.combat.alive:
            KillRewardService.resolve_kill(attacker, defender, world)

        # DELAY
        from src.core.gameplay.attributes import speed_delay
        attacker.next_act_at += speed_delay(attacker.combat.spd, "attack")

    @staticmethod
    def _get_weapon_range(entity: Entity) -> int:
        if entity.inventory and entity.inventory.weapon:
            weapon_tmpl = ITEM_REGISTRY.get(entity.inventory.weapon)
            if weapon_tmpl:
                return weapon_tmpl.weapon_range
        return 1
