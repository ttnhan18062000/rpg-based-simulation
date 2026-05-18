"""CombatAction — validates and resolves attack proposals.

Refactored for AOA Stabilization:
- Decomposed monolithic apply() into specialized services.
- Removed legacy property shims and StatsProxy dependencies.
- Aligned with nested MindAspect (EmotionState, NarrativeMemory, etc.).
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src_legacy.actions.base import ActionProposal, CombatTraceUpdate, PerceptionUpdate, MindUpdate, ProgressionUpdate, SocialUpdate
from src_legacy.actions.damage import get_damage_calculator
from src_legacy.core.models.enums import ActionType, DamageType, Domain, Element, EmotionType, ConsequenceKind, HeroClass
from src_legacy.core.models.consequence import Consequence
from src_legacy.core.gameplay.faction import Faction, FactionRegistry
from src_legacy.core.gameplay.items.item_registry import ITEM_REGISTRY
from src_legacy.core.models.combat import CombatTraceRecord, CombatTraceDetails
from src_legacy.core.logic.social_interpretation import SocialInterpretationService
from src_legacy.core.aspects.mind import InterpretedEvent, CombatNarrative

if TYPE_CHECKING:
    from src_legacy.config import SimulationConfig
    from src_legacy.core.models.world_state import WorldState
    from src_legacy.platform.rng import DeterministicRNG
    from src_legacy.core.entities.entity import Entity

logger = logging.getLogger(__name__)

class DamageResolutionService:
    @staticmethod
    def resolve(
        attacker: Entity, 
        defender: Entity, 
        world: WorldState, 
        config: SimulationConfig, 
        rng: DeterministicRNG, 
        skill_id: str | None = None,
        power: float = 1.0, 
        faction_reg: FactionRegistry | None = None,
        override_damage_type: DamageType | None = None, 
        override_element: Element | None = None,
        context_modifiers: dict[str, float] | None = None
    ) -> tuple[int, bool, bool, dict]:
        tick = world.tick
        
        # --- Evasion Check ---
        luck_mod = attacker.combat.luck * 0.002
        effective_evasion = max(0.0, defender.combat.evasion - luck_mod)
        if rng.next_bool(Domain.COMBAT, defender.id, tick + 3, effective_evasion):
            return 0, False, True, {"raw_damage": 0, "mitigation": 0, "elemental_mult": 1.0, "dmg_type": DamageType.PHYSICAL.name.lower(), "element": Element.NONE.name.lower()}

        # --- Determine Damage Type and Element ---
        dmg_type = override_damage_type
        element = override_element
        
        if dmg_type is None or element is None:
            if attacker.inventory and attacker.inventory.weapon:
                weapon_tmpl = ITEM_REGISTRY.get(attacker.inventory.weapon)
                if weapon_tmpl:
                    if dmg_type is None: dmg_type = weapon_tmpl.damage_type
                    if element is None: element = weapon_tmpl.element
        
        # Fallbacks
        if dmg_type is None: dmg_type = DamageType.PHYSICAL
        if element is None: element = Element.NONE

        # --- Base Damage Calculation ---
        calculator = get_damage_calculator(dmg_type)
        dmg_ctx = calculator.resolve(attacker, defender)
        
        # Milestone 2: Contextual Multipliers
        atk_context = context_modifiers.get("atk_mult", 1.0) if context_modifiers else 1.0
        def_context = context_modifiers.get("def_mult", 1.0) if context_modifiers else 1.0
        
        atk_final = int(dmg_ctx.atk_power * dmg_ctx.atk_mult * power * atk_context)
        def_final = int(dmg_ctx.def_power * dmg_ctx.def_mult * def_context)
        
        # Pillar 3: Fractional Armor Mitigation
        raw_damage = int(atk_final * (atk_final / (atk_final + def_final * 2.0 + 1.0)))
        raw_damage = max(raw_damage, 1)
        
        # Variance
        variance = rng.next_float(Domain.COMBAT, attacker.id, tick + 2)
        damage = int(raw_damage * (1.0 + config.damage_variance * (variance - 0.5)))
        
        # Elemental vulnerability
        elem_mult = 1.0
        if element != Element.NONE:
            elem_mult = defender.combat.elemental_vulnerability(element)
            damage = int(damage * elem_mult)

        # Crit check
        crit_rate = attacker.combat.crit_rate + attacker.combat.luck * 0.003
        is_crit = rng.next_bool(Domain.COMBAT, attacker.id, tick + 1, min(crit_rate, 0.8))
        if is_crit:
            damage = int(damage * attacker.combat.crit_dmg)

        # Pillar 3: Status Combinations (Shatter — Frozen targets take extra damage)
        from src_legacy.core.gameplay.effects import EffectType
        has_frozen = any(e.effect_type == EffectType.FROZEN for e in defender.combat.effects)
        if has_frozen:
            damage = int(damage * 1.5)

        # Return rich detail for traces
        return max(damage, 1), is_crit, False, {
            "raw_damage": raw_damage,
            "mitigation": int(atk_final - raw_damage),
            "elemental_mult": elem_mult,
            "dmg_type": dmg_type.name.lower() if hasattr(dmg_type, "name") else DamageType(dmg_type).name.lower(),
            "element": element.name.lower() if hasattr(element, "name") else Element(element).name.lower(),
            "has_shattered": has_frozen,
            "has_high_ground": context_modifiers.get("has_high_ground", False) if context_modifiers else False,
            "is_flanked": context_modifiers.get("is_flanked", False) if context_modifiers else False,
            "has_cover": context_modifiers.get("has_cover", False) if context_modifiers else False,
            "is_moving": context_modifiers.get("is_moving", False) if context_modifiers else False
        }

class CombatAftermathService:
    @classmethod
    def process(cls, attacker: Entity, defender: Entity, world: WorldState, damage: int, is_crit: bool, is_evasion: bool, config: SimulationConfig, proposal: ActionProposal, rng: DeterministicRNG, trace_details: dict | None = None):
        tick = world.tick
        
        # Emit combat event for monitoring and E2E tests
        skill_label = "attack"
        if proposal.reason == "Opportunity Attack":
            skill_label = "OPPORTUNITY_ATTACK"
        elif (hasattr(proposal.verb, "name") and proposal.verb.name == "USE_SKILL") or (not hasattr(proposal.verb, "name") and proposal.verb == 40): # 40 is USE_SKILL
            skill_label = "SKILL"

        if hasattr(world, "event_bus") and world.event_bus:
            from src_legacy.core.data.events import CombatEvent
            world.event_bus.publish(CombatEvent(
                attacker_id=attacker.id, defender_id=defender.id,
                damage=damage, is_crit=is_crit, is_evasion=is_evasion,
                skill_used=skill_label,
                attacker_hp=attacker.combat.hp, defender_hp=defender.combat.hp,
                is_aoe=getattr(proposal, "is_aoe", False)
            ))

        # Rich Trace Generation (AOA Phase 5)
        trace = CombatTraceUpdate(
            result=CombatTraceRecord(
                tick=tick, 
                attacker_id=attacker.id, 
                defender_id=defender.id,
                damage=damage, 
                skill_name=skill_label,
                details=CombatTraceDetails(
                    raw_damage=trace_details.get("raw_damage", 0) if trace_details else 0,
                    mitigated_damage=trace_details.get("mitigation", 0) if trace_details else 0,
                    elemental_mult=trace_details.get("elemental_mult", 1.0) if trace_details else 1.0,
                    is_crit=is_crit,
                    is_evaded=is_evasion,
                    is_shattered=trace_details.get("has_shattered", False) if trace_details else False,
                    has_high_ground=trace_details.get("has_high_ground", False) if trace_details else False,
                    is_flanked=trace_details.get("is_flanked", False) if trace_details else False,
                    has_cover=trace_details.get("has_cover", False) if trace_details else False,
                    is_moving=trace_details.get("is_moving", False) if trace_details else False
                )
            )
        )
        # awarding veterancy for hit
        if not is_evasion:
            proposal.updates.append(ProgressionUpdate(veterancy_points_delta=1))
            
        proposal.updates.append(trace)
        
        # AOA Phase 1 Recovery: Propose actual HP reduction for the defender
        if damage > 0:
            proposal.updates.append(ProgressionUpdate(
                target_id=defender.id,
                hp_delta=-damage
            ))

        if is_evasion:
            return

        # Phase 1: Relationship/Social Awareness Integration
        hp_lost_ratio = damage / max(1, defender.combat.max_hp)
        if hp_lost_ratio > 0.0:
             social_up = SocialInterpretationService.get_harm_deltas(attacker, defender, hp_lost_ratio)
             proposal.updates.append(social_up)
        
        # --- Nemesis & Memory (Emotion/Narrative) ---
        proposal.updates.append(MindUpdate(
            emotion_delta={EmotionType.PANIC: hp_lost_ratio * 0.5},
            mood=-hp_lost_ratio * 0.2
        ))
        
        # AOA Stabilization: Fully normalize all combat side-effects into the trace object
        if hp_lost_ratio > 0.15:
            trace.result.trauma = hp_lost_ratio * 100.0
            
        # Threat Table
        base_threat = damage * config.threat_damage_mult
        hclass = getattr(attacker.progression, "hero_class", HeroClass.NONE)
        if hclass == HeroClass.NONE:
            hclass = getattr(attacker.identity, "hero_class", HeroClass.NONE)
            
        hclass_val = int(hclass)
        if hclass_val == int(HeroClass.WARRIOR): 
            base_threat *= 1.5
        elif hclass_val == int(HeroClass.TANK):
            base_threat *= 2.0
            
        trace.result.threat = base_threat
        
        # Grudge generation
        trace.result.grudge = float(damage) / 10.0

        # Phase 5: Narrative Memory Generation [STAGE 5]
        
        # Narrative for Attacker (The Glory)
        attacker_narrative = InterpretedEvent(
            tick=tick,
            type="combat",
            impact=0.5 + (hp_lost_ratio * 2.0),
            details=CombatNarrative(
                target_id=defender.id,
                target_kind=getattr(defender, "kind", "unknown"),
                damage_dealt=damage,
                was_fatal=(defender.combat.hp - damage) <= 0
            )
        )
        proposal.updates.append(PerceptionUpdate(memory_log_add=[attacker_narrative]))
        
        # Narrative for Defender (The Trauma)
        defender_narrative = InterpretedEvent(
            tick=tick,
            type="trauma",
            impact=1.0 + (hp_lost_ratio * 3.0),
            details=CombatNarrative(
                target_id=attacker.id,
                target_kind=getattr(attacker, "kind", "unknown"),
                damage_dealt=damage,
                was_fatal=(defender.combat.hp - damage) <= 0
            )
        )
        # Note: In AOA, defender updates must be explicitly routed in ActionSystem.
        # But for now, we append them to proposal.updates; ActionSystem handles routing by target_id.
        proposal.updates.append(PerceptionUpdate(target_id=defender.id, memory_log_add=[defender_narrative]))

        # --- Milestone 5: Persistent Combat Consequences (Wounds) ---
        cls._inflict_consequences(attacker, defender, damage, is_crit, world, proposal, config, rng)

    @classmethod
    def _inflict_consequences(cls, attacker: Entity, defender: Entity, damage: int, is_crit: bool, world: WorldState, proposal: ActionProposal, config: SimulationConfig, rng: DeterministicRNG):
        """Roll for and apply wounds/scars based on hit severity. [Milestone 5]"""
        max_hp = max(1, defender.combat.max_hp)
        hp_lost_ratio = damage / max_hp
        tick = world.tick
        
        # Thresholds
        is_massive = hp_lost_ratio > 0.25
        wound_chance = 0.0
        if is_massive: wound_chance = 1.0
        elif is_crit: wound_chance = 0.4
        elif hp_lost_ratio > 0.15: wound_chance = 0.2
        
        if not rng.next_bool(Domain.COMBAT, defender.id, tick + 7, wound_chance):
            return

        # Generate Wound
        wound_id = f"wnd_{tick}_{defender.id}"
        
        # Basic Wound Templates
        roll = rng.next_float(Domain.COMBAT, defender.id, tick + 8)
        
        if roll < 0.25:
            # Leg Wound
            c = Consequence(id=wound_id, kind=ConsequenceKind.WOUND, tag="Leg Wound", spd_mult=0.8, severity=2, remaining_ticks=300)
        elif roll < 0.50:
            # Arm Wound
            c = Consequence(id=wound_id, kind=ConsequenceKind.WOUND, tag="Arm Wound", atk_mult=0.85, severity=2, remaining_ticks=250)
        elif roll < 0.75:
            # Chest Wound
            c = Consequence(id=wound_id, kind=ConsequenceKind.WOUND, tag="Grievous Chest Wound", max_stamina_mult=0.7, spd_mult=0.9, severity=3, remaining_ticks=400)
        else:
            # Head Wound
            c = Consequence(id=wound_id, kind=ConsequenceKind.WOUND, tag="Head Trauma", atk_mult=0.9, def_mult=0.9, severity=3, remaining_ticks=200)

        # Scarring (10% chance on massive hit or fatal blow avoided)
        if (is_massive or (defender.combat.hp - damage) < (max_hp * 0.1)) and rng.next_bool(Domain.COMBAT, defender.id, tick + 9, 0.1):
             scar_id = f"scr_{tick}_{defender.id}"
             scar = Consequence(id=scar_id, kind=ConsequenceKind.SCAR, tag="Combat Scar", spd_mult=0.98, severity=1, remaining_ticks=-1)
             proposal.updates.append(ProgressionUpdate(target_id=defender.id, consequences_add=[scar]))

        proposal.updates.append(ProgressionUpdate(target_id=defender.id, consequences_add=[c]))

class KillRewardService:
    @staticmethod
    def resolve_kill(killer: Entity, victim: Entity, world: WorldState, proposal: ActionProposal):
        tick = world.tick
        
        # XP Gain
        xp_gain = 5 if victim.progression.level <= killer.progression.level else 10
        # Killer gets XP/Gold/Veterancy
        proposal.updates.append(ProgressionUpdate(gold_delta=victim.progression.gold, xp_delta=xp_gain, veterancy_points_delta=5))
        
        # Gold/Corpse (AOA Stabilization: Authoritative World Update)
        from src_legacy.core.models.world_objects import CorpseNode
        if victim.identity.faction == Faction.HERO_GUILD:
            gold_to_corpse = int(victim.progression.gold * 0.8)
            # Re-adjust killer gold (we already added full gold above, so remove the corpse portion)
            proposal.updates.append(ProgressionUpdate(gold_delta=-gold_to_corpse))
            
            # Instead of mutating world directly, we emit a WorldUpdate
            from src_legacy.actions.base import WorldUpdate
            node = CorpseNode(
                node_id=0, # To be determined by resolver/ActionSystem
                entity_id=victim.id, 
                pos=victim.spatial.pos,
                items=list(victim.inventory.items) if victim.inventory else [],
                gold=gold_to_corpse, 
                created_tick=tick
            )
            proposal.updates.append(WorldUpdate(new_corpse=node, increment_corpse_id=True))
        
        # World Boss Rewards (AOA Stabilization: Authoritative Progression Update)
        if victim.identity.is_world_boss:
            title = f"Slayer of {victim.identity.display_name}"
            proposal.updates.append(ProgressionUpdate(
                fame_delta=100,
                titles_add=[title] if title not in killer.identity.titles else []
            ))
            logger.info("Tasking authoritative rewards for kill on %d", victim.id)
            
        # Death Event
        if hasattr(world, "event_bus") and world.event_bus:
            from src_legacy.core.data.events import DeathEvent
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
        
        from src_legacy.core.models.reason_codes import ActionReason, ReasonCode
        from src_legacy.actions.base import BuildingTarget
        if isinstance(proposal.target, BuildingTarget):
            # Building attack validation
            target_b = next((b for b in world.buildings if b.building_id == proposal.target.building_id), None)
            if not target_b or not target_b.is_functional: 
                proposal.reason = ActionReason(code=ReasonCode.TARGET_INVALID, metadata={"detail": "Building destroyed or missing"}, is_rejection=True)
                return False
            from src_legacy.core.logic.legality_service import LegalityService
            dist = LegalityService.get_distance(attacker.spatial.pos, target_b.pos)
            weapon_range = self._get_weapon_range(attacker)
            if dist > weapon_range:
                proposal.reason = ActionReason(code=ReasonCode.OUT_OF_RANGE, metadata={"max_range": weapon_range, "actual_dist": dist}, is_rejection=True)
                return False
            return True
            
        target_id: int = proposal.target
        defender = world.entities.get(target_id)
        if not defender or not defender.combat.alive: 
            proposal.reason = ActionReason(code=ReasonCode.TARGET_INVALID, metadata={"target_id": target_id}, is_rejection=True)
            return False
        
        # 1. Authoritative Rulebook checks
        from src_legacy.core.logic.legality_service import LegalityService
        
        target_pos = defender.spatial.pos
        weapon_range = self._get_weapon_range(attacker)
        
        # Consolidation [Milestone 1]: Singular legality path for targeting
        success, reason = LegalityService.verify_targeting_legality(
            attacker.spatial.pos, target_pos, weapon_range, world, requires_los=True
        )
        if not success:
            proposal.reason = reason
            return False
            
        return True

    def apply(self, proposal: ActionProposal, world: WorldState) -> None:
        attacker = world.entities.get(proposal.actor_id)
        if not attacker: return

        from src_legacy.actions.base import BuildingTarget
        if isinstance(proposal.target, BuildingTarget):
            # Authoritative Building Mutation (AOA Stabilization)
            target_b = next((b for b in world.buildings if b.building_id == proposal.target.building_id), None)
            if target_b:
                damage = int(attacker.combat.atk * 0.5) # Buildings take 50% damage from basic attacks
                from src_legacy.actions.base import BuildingUpdate
                proposal.updates.append(BuildingUpdate(building_id=target_b.building_id, damage_amount=damage))
                logger.info("Entity %d tasked sabotage on building %s for %d", attacker.id, target_b.building_id, damage)
            return

        defender = world.entities.get(proposal.target)
        if not defender: return

        # AOA Stabilization: Explicit combat target synchronization
        # Required for AI tactical focus and skirmish logic.
        attacker.combat.combat_target_id = defender.id
        attacker.mind.navigation.engagement_target_id = defender.id # [Milestone 2] Stickiness
        if defender.combat.alive:
            defender.combat.combat_target_id = attacker.id
            defender.mind.navigation.engagement_target_id = attacker.id # [Milestone 2] Stickiness

        # Milestone 5: Stamina pressure (Basic attack costs 8 stamina)
        proposal.updates.append(ProgressionUpdate(stamina_delta=-8))

        # Milestone 2: Contextual Modifiers
        from src_legacy.core.logic.legality_service import LegalityService
        
        tactical_flags = {
            "has_high_ground": LegalityService.check_high_ground(attacker.spatial.pos, defender.spatial.pos, world),
            "is_flanked": LegalityService.check_flanking(defender.id, world),
            "has_cover": LegalityService.check_cover(attacker.spatial.pos, defender.spatial.pos, world),
            "is_moving": attacker.spatial.moved_this_tick
        }
        
        atk_mult = 1.0
        def_mult = 1.0
        if tactical_flags["has_high_ground"]:
            atk_mult *= (1.0 + self._config.high_ground_atk_bonus)
        if tactical_flags["is_flanked"]:
            atk_mult *= (1.0 + self._config.flanking_atk_bonus)
        if tactical_flags["is_moving"]:
            atk_mult *= (1.0 - self._config.moved_atk_penalty)
        if tactical_flags["has_cover"]:
            def_mult *= (1.0 + self._config.ranged_cover_def_bonus)
            
        context_modifiers = {
            "atk_mult": atk_mult,
            "def_mult": def_mult,
            **tactical_flags
        }

        # RESOLVE
        damage, is_crit, is_evasion, trace_details = DamageResolutionService.resolve(
            attacker=attacker, 
            defender=defender, 
            world=world, 
            config=self._config, 
            rng=self._rng,
            context_modifiers=context_modifiers
        )

        # AFTERMATH (Memory, Grudges, Threat)
        CombatAftermathService.process(attacker, defender, world, damage, is_crit, is_evasion, self._config, proposal, self._rng, trace_details)

        # KILL RECOGNITION (Pillar 1 Convergence: Proposed in Apply Phase)
        if not is_evasion and (defender.combat.hp - damage) <= 0:
            KillRewardService.resolve_kill(attacker, defender, world, proposal)

        # TOUGHNESS HARDENING (design-04)
        if not is_evasion and (defender.combat.hp - damage) > 0:
            # Check threshold against predicted HP after damage is applied
            if (defender.combat.hp - damage) / defender.combat.max_hp < 0.15:
                proposal.updates.append(ProgressionUpdate(
                    target_id=defender.id,
                    max_hp_delta=1
                ))

    @staticmethod
    def _get_weapon_range(entity: Entity) -> int:
        if entity.inventory and entity.inventory.weapon:
            weapon_tmpl = ITEM_REGISTRY.get(entity.inventory.weapon)
            print(f"DEBUG_RANGE: Entity={entity.id}, Weapon={entity.inventory.weapon}, Found={weapon_tmpl is not None}, Range={weapon_tmpl.weapon_range if weapon_tmpl else 'N/A'}")
            if weapon_tmpl:
                return weapon_tmpl.weapon_range
        print(f"DEBUG_RANGE: Entity={entity.id}, No weapon, returning 1")
        return 1
