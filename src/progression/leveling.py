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
        base_hp: int = 100,
        base_atk: int = 10,
        base_def: int = 5,
        base_evasion: float = 0.05
    ) -> Dict[str, Any]:
        """
        Derive combat stats from attributes using standard RPG-core formulas.
        HP: base_hp + (vitality * 2) + (endurance * 0.5)
        ATK: base_atk + (strength * 0.5)
        DEF: base_def + (vitality * 0.3)
        Evasion: base_evasion + (agility * 0.001)
        """
        max_hp = base_hp + (attributes.vitality * 2) + int(attributes.endurance * 0.5)
        atk = base_atk + int(attributes.strength * 0.5)
        def_stat = base_def + int(attributes.vitality * 0.3)
        evasion = base_evasion + (attributes.agility * 0.001)
        
        return {
            "max_hp": max_hp,
            "atk": atk,
            "def_stat": def_stat,
            "evasion": evasion
        }

    @staticmethod
    def scale_combat_stats(
        current_combat: CombatComponent,
        new_level: int,
        role: int = EntityRole.MONSTER
    ) -> CombatComponent:
        """
        Produce a new CombatComponent with scaled stats.
        Monsters (Default): Each level up grants +10% to Max HP, ATK, and DEF.
        Heroes: Automatic scaling is SKIPPED (rely on manual AP distribution).
        """
        if role == EntityRole.HERO:
            # For Heroes, we only handle the healing surge on level up.
            # Stat growth comes from attributes.
            new_max_hp = current_combat.max_hp
            new_atk = current_combat.atk
            new_def = current_combat.def_stat
        else:
            # Monster auto-scaling
            multiplier = 1.1
            new_max_hp = int(current_combat.max_hp * multiplier)
            new_atk = int(current_combat.atk * multiplier)
            new_def = int(current_combat.def_stat * multiplier)
        
        # Healing Surge: Restore HP proportional to new max
        hp_ratio = current_combat.hp / current_combat.max_hp
        new_hp = int(new_max_hp * min(1.0, hp_ratio + 0.2))
        
        from dataclasses import replace
        return replace(
            current_combat,
            max_hp=new_max_hp,
            hp=new_hp,
            atk=new_atk,
            def_stat=new_def
        )
