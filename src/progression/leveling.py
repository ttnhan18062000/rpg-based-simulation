from __future__ import annotations
import math
from typing import Dict, Any
from src.core.state import CombatComponent, AttributeComponent
from src.core.enums import EntityRole

class LevelingService:
    @staticmethod
    def get_xp_required(level: int) -> int:
        """
        Calculate XP required to REACH the next level.
        Formula: 100 * (level ** 1.5)
        """
        if level <= 0:
            return 100
        return int(100 * (level ** 1.5))

    @staticmethod
    def recalculate_combat_stats(
        attributes: AttributeComponent,
        equipment: Optional[EquipmentComponent] = None,
        learned_skills: Optional[Set[str]] = None,
        base_hp: int = 100,
        base_atk: int = 10,
        base_def: int = 5,
        base_evasion: float = 0.05
    ) -> Dict[str, Any]:
        """
        Derive combat stats from attributes, equipment, and passive skills.
        HP: base_hp + (vitality * 2) + (endurance * 0.5) + gear_hp
        ATK: base_atk + (strength * 0.5) + gear_atk
        DEF: base_def + (vitality * 0.3) + gear_def
        Evasion: base_evasion + (agility * 0.001) + gear_evasion + skill_passive
        """
        from src.core.items import ItemRegistry
        from src.core.skills import SKILL_REGISTRY, SkillKind
        
        # 1. Base from Attributes
        max_hp = base_hp + (attributes.vitality * 2) + int(attributes.endurance * 0.5)
        atk = base_atk + int(attributes.strength * 0.5)
        def_stat = base_def + int(attributes.vitality * 0.3)
        evasion = base_evasion + (attributes.agility * 0.001)
        atk_range = 1
        
        # 2. Add Equipment Bonuses
        if equipment:
            for slot, item_id in equipment.slots.items():
                if not item_id: continue
                defn = ItemRegistry.get(item_id)
                if not defn: continue
                
                atk += defn.properties.get("atk_bonus", 0)
                def_stat += defn.properties.get("def_bonus", 0)
                max_hp += defn.properties.get("hp_bonus", 0)
                evasion += defn.properties.get("evasion_bonus", 0.0)
                
                # Main hand range overrides base range if it's a weapon
                if slot == "MAIN_HAND" and "range" in defn.properties:
                    atk_range = defn.properties["range"]

        # 3. Add Passive Skill Bonuses
        if learned_skills:
            for skill_id in learned_skills:
                skill = SKILL_REGISTRY.get(skill_id)
                if skill and skill.kind == SkillKind.PASSIVE:
                    # For now we only have swift_reflexes in registry as passive
                    if skill_id == "swift_reflexes":
                        evasion += skill.power
                    # Add other passives here as they are added to registry
        
        return {
            "max_hp": max_hp,
            "atk": atk,
            "def_stat": def_stat,
            "evasion": evasion,
            "range": atk_range
        }

