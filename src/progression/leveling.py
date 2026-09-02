from __future__ import annotations
import math
from typing import Dict, Any, Optional, Set
from src.core.state import CombatComponent, AttributeComponent, EquipmentComponent, IdentityComponent
from src.core.updates import IdentityUpdate
from src.core.enums import EntityRole

class LevelingService:
    @staticmethod
    def get_xp_required(level: int) -> int:
        """
        Calculate XP required to REACH the next level.
        Formula: 100 * (level ** 1.5)
        VERIFIED v2: xp_threshold_formula
        """
        if level <= 0:
            return 100
        return int(100 * (level ** 1.5))

    @staticmethod
    def process_progression(identity: IdentityComponent, xp_gain: int) -> IdentityUpdate:
        """
        Authoritative entry point for progression updates.
        Handles XP accumulation and triggers level-up if threshold met.
        """
        if xp_gain <= 0:
            return IdentityUpdate()
            
        new_xp = identity.evolution_points + xp_gain
        current_level = identity.evolution_level
        
        # Enforce Level 99 Cap
        # VERIFIED v2: level_cap_enforced
        if current_level >= 99:
            return IdentityUpdate(evolution_points_delta=xp_gain) # Still track XP but no level up
            
        xp_needed = LevelingService.get_xp_required(current_level)
        
        if new_xp >= xp_needed:
            # Level Up!
            return LevelingService._execute_level_up(identity, new_xp, xp_needed)
        else:
            return IdentityUpdate(evolution_points_delta=xp_gain)

    @staticmethod
    def get_unlocked_skills(level: int) -> list[str]:
        """Returns skills that unlock at a specific level."""
        # PH8: Skill Unlock thresholds
        thresholds = {
            2: ["power_strike"],
            5: ["swift_reflexes"],
            10: ["fireball"]
        }
        return thresholds.get(level, [])

    @staticmethod
    def _execute_level_up(identity: IdentityComponent, total_xp: int, cost: int) -> IdentityUpdate:
        """Handles the actual level-up state change."""
        new_level = identity.evolution_level + 1
        rem_xp = total_xp - cost
        
        # Rewards: 5 AP per level
        ap_gain = 5
        
        # Skill Unlocks
        unlocked = LevelingService.get_unlocked_skills(new_level)
        
        return IdentityUpdate(
            evolution_level_set=new_level,
            evolution_points_delta=-identity.evolution_points + rem_xp,
            unspent_ap_delta=ap_gain,
            learned_skills=unlocked
        )

    @staticmethod
    def recalculate_combat_stats(
        attributes: AttributeComponent,
        equipment: Optional[EquipmentComponent] = None,
        learned_skills: Optional[Set[str]] = None,
        traits: Optional[Set[str]] = None,
        current_role: str = "VANGUARD",
        base_hp: int = 100,
        base_atk: int = 10,
        base_def: int = 5,
        base_evasion: float = 0.05
    ) -> Dict[str, Any]:
        """
        Derive combat stats from attributes, equipment, and passive skills.
        VERIFIED v2: stat_recalculation_parity
        HP: base_hp + (vitality * 2) + (endurance * 0.5) + gear_hp
        ATK: base_atk + (strength * 0.5) + gear_atk
        DEF: base_def + (vitality * 0.3) + gear_def
        Evasion: base_evasion + (agility * 0.001) + gear_evasion + skill_passive
        """
        from src.core.items import ItemRegistry
        from src.core.skills import SKILL_REGISTRY, SkillKind
        from src.core.state import EquipSlot
        
        # 1. Base from Attributes
        max_hp = base_hp + (attributes.vitality * 2) + int(attributes.endurance * 0.5)
        atk = base_atk + int(attributes.strength * 0.5)
        def_stat = base_def + int(attributes.vitality * 0.3)
        evasion = base_evasion + (attributes.agility * 0.001)
        readiness_speed = max(1.0, 10.0 + (attributes.agility - 5) * 1.0)
        atk_range = 1
        
        # 2. Add Equipment Bonuses
        # VERIFIED v2: equipment_bonus_application
        total_weight = 0.0
        if equipment:
            for slot, item_id in equipment.slots.items():
                if not item_id: continue
                defn = ItemRegistry.get(item_id)
                if not defn: continue
                
                # Phase 8: Durability Check (Broken equipment provides no bonuses)
                item_durability = equipment.durability.get(slot, 100.0)
                is_broken = item_durability <= 0
                
                if not is_broken:
                    atk += defn.properties.get("atk_bonus", 0)
                    def_stat += defn.properties.get("def_bonus", 0)
                    max_hp += defn.properties.get("hp_bonus", 0)
                    evasion += defn.properties.get("evasion_bonus", 0.0)
                    
                    # Main hand range overrides base range if it's a weapon
                    if slot == EquipSlot.MAIN_HAND and "range" in defn.properties:
                        atk_range = defn.properties["range"]
                
                total_weight += defn.weight

        # 3. Add Passive Skill Bonuses
        # VERIFIED v2: passive_skill_bonus_application
        if learned_skills:
            for skill_id in learned_skills:
                skill = SKILL_REGISTRY.get(skill_id)
                if skill and skill.kind == SkillKind.PASSIVE:
                    # For now we only have swift_reflexes in registry as passive
                    if skill_id == "swift_reflexes":
                        evasion += skill.power
                    # Add other passives here as they are added to registry
        
        # 3.1. Add Trait Bonuses (Task 6.3)
        if traits:
            # Simple mapping for now
            if "Tough" in traits:
                max_hp += 20
            if "Quick" in traits:
                evasion += 0.02
            if "Strong" in traits:
                atk += 3
        
        # 4. Movement Cost Scaling (PH8)
        # VERIFIED v2: encumbrance_movement_scaling
        move_cost = 10.0 + (total_weight / 5.0) - (attributes.agility * 0.1)
        move_cost = max(5.0, move_cost) # Minimum cost 5.0
        
        # 5. Tactical Role Derivation (Task 6.4)
        # Logic: Highest primary attribute defines role
        # Str -> VANGUARD, Agi -> SKIRMISHER, Vit -> PROTECTOR
        role_scores = {
            "VANGUARD": attributes.strength,
            "SKIRMISHER": attributes.agility,
            "PROTECTOR": attributes.vitality
        }
        # Get role with max score (deterministic fallback to VANGUARD)
        new_role = max(role_scores, key=role_scores.get)
        
        # Apply Hysteresis (Task 6.4)
        # Only switch if the new leader is at least 5 points ahead of current role's score
        current_role_score = role_scores.get(current_role, 0)
        if role_scores[new_role] <= current_role_score + 5:
            derived_role = current_role
        else:
            derived_role = new_role
            
        return {
            "max_hp": max_hp,
            "atk": atk,
            "def_stat": def_stat,
            "evasion": evasion,
            "range": atk_range,
            "move_cost": move_cost,
            "tactical_role": derived_role,
            "readiness_speed": readiness_speed
        }

