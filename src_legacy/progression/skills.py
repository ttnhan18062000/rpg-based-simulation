from __future__ import annotations
from typing import Dict, Any
from src_legacy.core.state import AttributeComponent
from src_legacy.core.skills import SkillDefinition, SkillKind

class SkillScalingService:
    @staticmethod
    def calculate_scaled_power(
        skill: SkillDefinition,
        attributes: AttributeComponent
    ) -> float:
        """
        Calculate the effective power of a skill based on entity attributes.
        Follows PH8 Task 8.4: Physical, Magical, and Elemental scaling law.
        """
        # Base scaling logic
        # Physical: Scales with Strength (0.02 per point -> +2% power)
        # Magical: Scales with Intelligence (0.03 per point -> +3% power)
        # Elemental: Scales with Spirit (0.025 per point) + Wisdom (0.01 per point)
        
        from src_legacy.core.skills import SkillCategory
        
        category = skill.category
        
        scaling_factor = 1.0
        if category == SkillCategory.PHYSICAL:
            scaling_factor = 1.0 + (attributes.strength * 0.02)
        elif category == SkillCategory.MAGICAL:
            scaling_factor = 1.0 + (attributes.intelligence * 0.03)
        elif category == SkillCategory.ELEMENTAL:
            scaling_factor = 1.0 + (attributes.spirit * 0.025) + (attributes.wisdom * 0.01)
            
        return skill.power * scaling_factor

    @staticmethod
    def get_passive_bonus(
        skill: SkillDefinition,
        attributes: AttributeComponent
    ) -> float:
        """
        Calculate passive bonus (e.g. evasion, crit) from passive skills.
        """
        if skill.kind != SkillKind.PASSIVE:
            return 0.0
            
        # Example: Swift Reflexes scales with Agility
        if skill.id == "swift_reflexes":
            return skill.power * (1.0 + attributes.agility * 0.01)
            
        return skill.power
