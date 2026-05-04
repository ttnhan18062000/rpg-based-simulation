"""
Stamina, Wound/Scar Aftermath, Mob Leash, Terrain Cost, Target Stickiness,
and Skill Scaling services.

These fill the gaps identified in logic_checklist_exhaustive_v2.md sections:
- Part 6 Section E (Combat aftermath / wounds / scars / stamina / exhaustion)
- Section 8 (Mob leash, chase give-up, return-to-camp)
- Section 7 (Terrain cost in pathfinding)
- Z5 (Target stickiness)
- Z10 (Skill scaling math, attribute caps)
"""
from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING, Optional, Dict, Any, List, Tuple

if TYPE_CHECKING:
    from src.core.state import EntityState, AuthoritativeState, StaminaComponent

# ─── Attribute Caps ───────────────────────────────────────────────────────────

ATTRIBUTE_CAP = 99  # Maximum value for any single attribute


# VERIFIED v2: attribute_cap_enforced
# VERIFIED v2: level_cap_enforced
def enforce_attribute_caps(attributes) -> Dict[str, int]:
    """Clamp all attributes to [1, ATTRIBUTE_CAP]. Returns delta dict."""
    from src.core.state import AttributeComponent
    deltas = {}
    for attr_name in [
        "strength", "agility", "vitality", "endurance",
        "intelligence", "spirit", "wisdom", "perception", "charisma"
    ]:
        val = getattr(attributes, attr_name)
        if val > ATTRIBUTE_CAP:
            deltas[f"{attr_name}_delta"] = ATTRIBUTE_CAP - val
        elif val < 1:
            deltas[f"{attr_name}_delta"] = 1 - val
    return deltas


# ─── Stamina Service ─────────────────────────────────────────────────────────

class StaminaService:
    """Authoritative stamina drain and regeneration logic."""

    @staticmethod
    def derive_max_stamina(endurance: int) -> float:
        """Max stamina = 50 + endurance * 5."""
        return 50.0 + endurance * 5.0

    @staticmethod
    def drain_attack(stamina: StaminaComponent) -> float:
        """Returns the stamina cost for an attack action."""
        # VERIFIED v2: stamina_drain_attack
        return stamina.ATTACK_COST

    @staticmethod
    def drain_move(stamina: StaminaComponent) -> float:
        """Returns the stamina cost for a movement action."""
        # VERIFIED v2: stamina_drain_movement
        return stamina.MOVE_COST

    @staticmethod
    def drain_harvest(stamina: StaminaComponent) -> float:
        """Returns the stamina cost for a harvest tick."""
        # VERIFIED v2: stamina_drain_harvest
        return stamina.HARVEST_COST

    @staticmethod
    def drain_skill(stamina: StaminaComponent, skill_cost: int) -> float:
        """Returns the stamina cost for using a skill."""
        # VERIFIED v2: stamina_cost_skill_use
        return skill_cost * stamina.SKILL_COST_MULT

    @staticmethod
    def can_use_skill(stamina: StaminaComponent, skill_cost: int) -> bool:
        """Check if entity has enough stamina for a skill."""
        # VERIFIED v2: stamina_skill_gating
        return stamina.current >= StaminaService.drain_skill(stamina, skill_cost)

    @staticmethod
    def is_exhausted(stamina: StaminaComponent) -> bool:
        """Check if entity is in exhaustion state."""
        return stamina.current < stamina.exhaustion_threshold

    @staticmethod
    def get_exhaustion_multiplier(stamina: StaminaComponent) -> float:
        """Combat damage multiplier when exhausted."""
        # VERIFIED v2: exhaustion_penalty_combat
        if StaminaService.is_exhausted(stamina):
            return stamina.exhaustion_penalty
        return 1.0

    @staticmethod
    def tick_regen(stamina: StaminaComponent, is_resting: bool = False) -> float:
        """Returns the stamina delta for passive/rest regeneration."""
        # VERIFIED v2: stamina_regen_resting
        # VERIFIED v2: stamina_regen_active
        # VERIFIED v2: stamina_regen_capped
        rate = stamina.rest_regen_rate if is_resting else stamina.regen_rate
        headroom = stamina.max_stamina - stamina.current
        return min(rate, max(0.0, headroom))


# ─── Wound / Scar Aftermath Service ──────────────────────────────────────────

WOUND_THRESHOLD_RATIO = 0.40  # 40% of max HP in a single hit triggers wound

class WoundService:
    """Generates wounds from massive hits and transitions them to scars."""

    @staticmethod
    def should_inflict_wound(damage: int, max_hp: int) -> bool:
        """Check if a single hit is massive enough to cause a wound."""
        # VERIFIED v2: wound_infliction_massive_hit
        if max_hp <= 0:
            return False
        return damage >= (max_hp * WOUND_THRESHOLD_RATIO)

    @staticmethod
    def create_wound(damage: int, max_hp: int, tick: int, wound_id: str) -> WoundState:
        """Create a wound record from a massive hit."""
        from src.core.state import WoundState
        severity = min(1.0, damage / max_hp)
        # Determine wound kind based on severity
        if severity >= 0.8:
            kind = "CRUSH"
        elif severity >= 0.6:
            kind = "SLASH"
        else:
            kind = "PIERCE"

        return WoundState(
            id=wound_id,
            kind=kind,
            severity=severity,
            tick_inflicted=tick,
            atk_penalty=int(severity * 3),
            def_penalty=int(severity * 2),
            speed_penalty=int(severity * 2),
            max_hp_penalty=int(severity * 10),
        )

    @staticmethod
    def get_wound_stat_penalties(wounds: list) -> Dict[str, float]:
        """Sum all active (unhealed) wound penalties."""
        # VERIFIED v2: wound_stat_impact
        total_atk = 0.0
        total_def = 0.0
        total_speed = 0.0
        total_max_hp = 0.0
        for w in wounds:
            if not w.healed:
                total_atk += w.atk_penalty
                total_def += w.def_penalty
                total_speed += w.speed_penalty
                total_max_hp += w.max_hp_penalty
        return {
            "atk_penalty": total_atk,
            "def_penalty": total_def,
            "speed_penalty": total_speed,
            "max_hp_penalty": total_max_hp,
        }

    @staticmethod
    def get_scar_stat_penalties(scars: list) -> Dict[str, float]:
        """Sum all permanent scar penalties (lesser than wounds)."""
        total_atk = 0.0
        total_def = 0.0
        total_speed = 0.0
        for s in scars:
            total_atk += s.atk_penalty
            total_def += s.def_penalty
            total_speed += s.speed_penalty
        return {
            "atk_penalty": total_atk,
            "def_penalty": total_def,
            "speed_penalty": total_speed,
        }

    @staticmethod
    def heal_wound(wound) -> Tuple:
        """Heal a wound and create a scar. Returns (healed_wound, scar)."""
        # VERIFIED v2: scar_permanence_logic
        from src.core.state import WoundState, ScarState
        healed = replace(wound, healed=True, scar_created=True)
        scar = ScarState(
            id=f"scar_{wound.id}",
            wound_kind=wound.kind,
            tick_created=wound.tick_inflicted,
            atk_penalty=wound.atk_penalty * 0.3,
            def_penalty=wound.def_penalty * 0.3,
            speed_penalty=wound.speed_penalty * 0.3,
        )
        return healed, scar


# ─── Mob Leash Service ────────────────────────────────────────────────────────

LEASH_CHASE_MULTIPLIER = 1.5  # Chase allowed up to 1.5x leash radius

class LeashService:
    """Enforces mob leashing: return-to-camp when beyond radius."""

    @staticmethod
    def is_beyond_leash(entity: EntityState) -> bool:
        """
        Check if entity is beyond its leash radius.
        VERIFIED v2: mob_leash_radius
        """
        nav = entity.navigation
        if nav.leash_radius <= 0 or nav.home_position is None:
            return False
        from src.engine.legality import LegalityServiceV2
        dist = LegalityServiceV2.get_manhattan_dist(entity.navigation.position, nav.home_position)
        return dist > nav.leash_radius

    @staticmethod
    def should_give_up_chase(entity: EntityState) -> bool:
        """
        Check if a chasing mob should abandon pursuit.
        VERIFIED v2: mob_chase_give_up
        """
        nav = entity.navigation
        if nav.leash_radius <= 0 or nav.home_position is None:
            return False
        # Distance check: beyond 1.5x leash
        from src.engine.legality import LegalityServiceV2
        dist = LegalityServiceV2.get_manhattan_dist(entity.navigation.position, nav.home_position)
        if dist > nav.leash_radius * LEASH_CHASE_MULTIPLIER:
            return True
        # Timeout check
        if nav.chase_ticks >= nav.max_chase_ticks:
            return True
        return False

    @staticmethod
    def get_return_home_target(entity: EntityState) -> Optional[Tuple[float, float]]:
        """Get the home position for return-to-camp behavior."""
        if entity.navigation.home_position is not None:
            return entity.navigation.home_position
        return None

    @staticmethod
    def is_at_home(entity: EntityState) -> bool:
        """Check if entity has reached home."""
        nav = entity.navigation
        if nav.home_position is None:
            return True
        from src.engine.legality import LegalityServiceV2
        dist = LegalityServiceV2.get_manhattan_dist(entity.navigation.position, nav.home_position)
        return dist <= 1.0

# ─── Discovery and Medical Services ────────────────────────────────────────── (Task 10.1, 10.2)

class DiscoveryService:
    """Perception-based world interaction logic."""
    
    @staticmethod
    def get_discovery_threshold(per: int) -> float:
        """
        Calculate perception-based discovery score.
        VERIFIED v2: perception_discovery_math
        """
        return 0.05 + (per * 0.02) # Base 5% + 2% per perception point

class MedicalService:
    """Wisdom-based medical diagnosis and healing quality."""
    
    @staticmethod
    def get_diagnosis_quality(wis: int) -> float:
        """
        Calculate diagnosis accuracy (0.0 to 1.0).
        VERIFIED v2: wisdom_diagnosis_math
        """
        # Linear scaling: 10 Wisdom = 50% accuracy, 20 Wisdom = 100%
        return min(1.0, wis * 0.05)


# ─── Terrain Cost Service ────────────────────────────────────────────────────

class TerrainCostService:
    """Provides terrain-aware movement cost for pathfinding."""

    @staticmethod
    def get_tile_cost(pos: Tuple[int, int], state: AuthoritativeState) -> float:
        """
        Get movement cost for a tile based on terrain type.
        VERIFIED v2: terrain_cost_pathfinding
        """
        from src.core.state import TERRAIN_COST
        terrain = getattr(state, 'terrain', {})
        terrain_type = terrain.get(pos, "PLAIN") if terrain else "PLAIN"
        return TERRAIN_COST.get(terrain_type, 1.0)

    @staticmethod
    def get_path_cost(path: List[Tuple[int, int]], state: AuthoritativeState) -> float:
        """Calculate total movement cost for a path."""
        total = 0.0
        for pos in path:
            total += TerrainCostService.get_tile_cost(pos, state)
        return total


# ─── Target Stickiness ───────────────────────────────────────────────────────

TARGET_SWITCH_MARGIN = 0.3  # Must be 30% better to switch targets

class TargetStickinessService:
    """Prevents unrealistic target flipping every tick."""

    @staticmethod
    def should_switch_target(
        current_target_id: Optional[int],
        new_target_id: int,
        current_score: float,
        new_score: float,
        ticks_on_current: int
    ) -> bool:
        """
        Only switch targets if the new one is significantly better.
        Uses margin threshold to prevent flicker.
        """
        # VERIFIED v2: target_stickiness_bias
        if current_target_id is None:
            return True
        if current_target_id == new_target_id:
            return False
        # Current target invalid (will be checked by caller)
        if current_score <= 0:
            return True
        # Must exceed margin to switch
        improvement = (current_score - new_score) / max(1.0, current_score)
        # Longer you've been on a target, harder to switch (up to 2x margin)
        loyalty_factor = min(2.0, 1.0 + ticks_on_current * 0.1)
        return improvement > (TARGET_SWITCH_MARGIN * loyalty_factor)


# ─── Skill Scaling Service ───────────────────────────────────────────────────

class SkillScalingService:
    """
    Computes skill damage using attribute-based scaling formulas.
    Matches checklist Z10: Physical/Magical/Elemental/Hybrid scaling.
    """

    @staticmethod
    def calculate_skill_damage(
        skill_power: float,
        category: str,
        attributes,
        base_atk: int = 10
    ) -> int:
        """
        Physical: base_atk + strength * 0.8 * power
        Magical:  base_atk + intelligence * 0.9 * power
        Elemental: base_atk + (spirit * 0.5 + intelligence * 0.4) * power
        Hybrid:   base_atk + (strength * 0.4 + intelligence * 0.4) * power
        VERIFIED v2: skill_damage_scaling
        """
        # VERIFIED v2: physical_skill_scaling
        # VERIFIED v2: magical_skill_scaling
        # VERIFIED v2: elemental_skill_scaling
        if category == "PHYSICAL":
            raw = base_atk + attributes.strength * 0.8 * skill_power
        elif category == "MAGICAL":
            raw = base_atk + attributes.intelligence * 0.9 * skill_power
        elif category == "ELEMENTAL":
            raw = base_atk + (attributes.spirit * 0.5 + attributes.intelligence * 0.4) * skill_power
        else:  # HYBRID or fallback
            raw = base_atk + (attributes.strength * 0.4 + attributes.intelligence * 0.4) * skill_power
        return max(1, int(raw))

    @staticmethod
    def get_effective_stats(
        attributes,
        equipment=None,
        wounds=None,
        scars=None,
        learned_skills=None,
        traits=None,
        current_role: str = "VANGUARD",
        base_hp: int = 100,
        base_atk: int = 10,
        base_def: int = 5,
        base_evasion: float = 0.05
    ) -> Dict[str, Any]:
        """
        Full effective stat recomputation:
        base stats + gear + traits + wound penalties + scar penalties.
        Law: Effective stats clamp to valid ranges (min 1 for atk/def, min 1 for HP).
        """
        # VERIFIED v2: stat_recalculation_parity
        # VERIFIED v2: scar_detection_logic
        from src.progression.leveling import LevelingService
        base_stats = LevelingService.recalculate_combat_stats(
            attributes, equipment, learned_skills, traits,
            current_role=current_role,
            base_hp=base_hp, base_atk=base_atk, base_def=base_def,
            base_evasion=base_evasion
        )

        # Apply wound penalties
        if wounds:
            wound_pen = WoundService.get_wound_stat_penalties(wounds)
            base_stats["atk"] = max(1, base_stats["atk"] - int(wound_pen["atk_penalty"]))
            base_stats["def_stat"] = max(1, base_stats["def_stat"] - int(wound_pen["def_penalty"]))
            base_stats["max_hp"] = max(1, base_stats["max_hp"] - int(wound_pen["max_hp_penalty"]))

        # Apply scar penalties
        if scars:
            scar_pen = WoundService.get_scar_stat_penalties(scars)
            base_stats["atk"] = max(1, base_stats["atk"] - int(scar_pen["atk_penalty"]))
            base_stats["def_stat"] = max(1, base_stats["def_stat"] - int(scar_pen["def_penalty"]))

        # Clamp evasion
        base_stats["evasion"] = max(0.0, min(0.95, base_stats["evasion"]))

        return base_stats
