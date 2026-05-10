"""
Genetics and Skill Scaling Systems.

Covers:
- LEG-RPG-144: Innate Talents (Genetics)
- LEG-RPG-145: Skill Scaling (Types)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict
from enum import Enum


class SkillType(str, Enum):
    """Skill scaling type."""
    PHYSICAL = "PHYSICAL"
    MAGICAL = "MAGICAL"
    ELEMENTAL = "ELEMENTAL"
    HYBRID = "HYBRID"


@dataclass(frozen=True, slots=True)
class GeneticProfile:
    """
    Innate talent multipliers derived from genetics.
    These are permanent and do not change with level.
    """
    strength_mult: float = 1.0
    agility_mult: float = 1.0
    intelligence_mult: float = 1.0
    wisdom_mult: float = 1.0
    constitution_mult: float = 1.0
    charisma_mult: float = 1.0


@dataclass(frozen=True, slots=True)
class SkillDefinition:
    """Definition of a learnable skill."""
    id: str
    name: str
    skill_type: SkillType
    base_power: float = 10.0
    primary_attribute: str = "strength"  # Which attribute drives scaling
    secondary_attribute: str = ""  # Optional secondary scaling
    level_requirement: int = 1


class GeneticsSystem:
    """
    Derives effective attribute values from base stats + genetic multipliers.
    """

    @staticmethod
    def apply_genetic_profile(
        base_stats: Dict[str, int],
        profile: GeneticProfile
    ) -> Dict[str, float]:
        """
        LEG-RPG-144: Talent multipliers from genetic profile affect attribute scaling.
        """
        multiplier_map = {
            "strength": profile.strength_mult,
            "agility": profile.agility_mult,
            "intelligence": profile.intelligence_mult,
            "wisdom": profile.wisdom_mult,
            "constitution": profile.constitution_mult,
            "charisma": profile.charisma_mult
        }

        effective = {}
        for attr, base_value in base_stats.items():
            mult = multiplier_map.get(attr, 1.0)
            effective[attr] = base_value * mult

        return effective

    @staticmethod
    def generate_profile_from_seed(seed: int) -> GeneticProfile:
        """
        Generate a deterministic genetic profile from a seed.
        Each multiplier ranges from 0.8 to 1.3.
        """
        import hashlib
        h = hashlib.md5(str(seed).encode()).hexdigest()

        def _extract(offset: int) -> float:
            val = int(h[offset:offset + 2], 16) / 255.0
            return 0.8 + val * 0.5  # Range: 0.8 to 1.3

        return GeneticProfile(
            strength_mult=round(_extract(0), 3),
            agility_mult=round(_extract(2), 3),
            intelligence_mult=round(_extract(4), 3),
            wisdom_mult=round(_extract(6), 3),
            constitution_mult=round(_extract(8), 3),
            charisma_mult=round(_extract(10), 3)
        )


class SkillScalingSystem:
    """
    Computes skill power based on skill type and attribute ownership.
    """

    @staticmethod
    def compute_skill_power(
        skill: SkillDefinition,
        effective_stats: Dict[str, float]
    ) -> float:
        """
        LEG-RPG-145: Physical/Magical/Elemental skills scale differently.

        Scaling formulas:
        - PHYSICAL: base * (1 + primary_stat/100)
        - MAGICAL: base * (1 + primary_stat/80 + secondary_stat/200)
        - ELEMENTAL: base * (1 + primary_stat/90) * 1.1 (element bonus)
        - HYBRID: base * (1 + (primary + secondary) / 150)
        """
        primary = effective_stats.get(skill.primary_attribute, 10.0)
        secondary = effective_stats.get(skill.secondary_attribute, 0.0) if skill.secondary_attribute else 0.0

        if skill.skill_type == SkillType.PHYSICAL:
            return skill.base_power * (1 + primary / 100)
        elif skill.skill_type == SkillType.MAGICAL:
            return skill.base_power * (1 + primary / 80 + secondary / 200)
        elif skill.skill_type == SkillType.ELEMENTAL:
            return skill.base_power * (1 + primary / 90) * 1.1
        elif skill.skill_type == SkillType.HYBRID:
            return skill.base_power * (1 + (primary + secondary) / 150)
        else:
            return skill.base_power
