# Compliance IDs: SOC-142, STRAT-166, STRAT-169, STRAT-170, STRAT-171, STRAT-172, STRAT-173, STRAT-174, STRAT-178, STRAT-179, SUB-156
from __future__ import annotations
from typing import Dict
from src.core.state import PersonalityComponent

class PersonalityService:
    """Provides utility modifiers based on personality traits."""

    @staticmethod
    def get_goal_modifiers(personality: PersonalityComponent) -> Dict[str, float]:
        """
        Returns a map of GoalKind -> utility_modifier.
        Modifier is a float added to 1.0 (e.g. 0.2 means +20% utility).
        """
        mods = {}
        
        # Greed biases resource/loot goals
        if personality.greed != 0.0:
            mods["harvesting"] = personality.greed * 0.5
            mods["loot"] = personality.greed * 0.5
            mods["trade"] = personality.greed * 0.3
            
        # Bravery biases combat vs fleeing
        if personality.bravery != 0.0:
            mods["combat"] = personality.bravery * 0.4
            mods["flee"] = -personality.bravery * 0.6 # Brave entities flee less
            mods["combat_engage"] = personality.bravery * 0.5
            mods["combat_retreat"] = -personality.bravery * 0.5
            
        # Sociability biases social goals
        if personality.sociability != 0.0:
            mods["social"] = personality.sociability * 0.5
            
        # Industry biases work goals
        if personality.industry != 0.0:
            mods["harvesting"] = mods.get("harvesting", 0.0) + personality.industry * 0.3
            mods["crafting"] = personality.industry * 0.4
            mods["resolve_blocker"] = personality.industry * 0.3

            
        return mods
