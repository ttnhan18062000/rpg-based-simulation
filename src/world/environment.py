from __future__ import annotations
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from src.core.state import RegionState, EntityState
from src.core.enums import Faction

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState

class EnvironmentService:
    """
    Manages the impact of regional hazards, weather, and auras on entities.
    """

    @staticmethod
    def calculate_hazard_drain(region: RegionState, entity: EntityState) -> float:
        """
        Calculates the HP/Readiness drain for an entity in a region.
        Scales with hazard_level and calamity_intensity.
        """
        base_drain = region.hazard_level * (1.0 + region.calamity_intensity)
        
        # Certain modifiers increase drain
        if "MIASMA" in region.active_modifiers:
            base_drain *= 1.5
            
        return base_drain

    @staticmethod
    def get_weather_modifiers(region: RegionState) -> Dict[str, float]:
        """
        Returns stat multipliers based on current weather.
        """
        mods = {
            "move_speed": 1.0,
            "perception": 1.0,
            "evasion": 1.0
        }
        
        if region.weather == "STORM":
            mods["perception"] = 0.7
            mods["evasion"] = 0.8
        elif region.weather == "RAIN":
            mods["perception"] = 0.9
        elif region.weather == "SNOW":
            mods["move_speed"] = 0.8
            
        return mods

    @staticmethod
    def get_aura_effects(state: AuthoritativeState, entity: EntityState) -> Dict[str, float]:
        """
        Returns stat multipliers based on nearby strongholds (Aura of Despair).
        """
        mods = {
            "move_speed": 1.0
        }
        
        if entity.identity.faction == Faction.HERO_GUILD:
            for s in state.entities.values():
                if s.kind == "stronghold" and s.combat.alive:
                    from src.engine.legality import LegalityServiceV2
                    dist = LegalityServiceV2.get_manhattan_dist(entity.position, s.position)
                    if dist < 12:
                        # Aura of Despair: -30% speed
                        mods["move_speed"] = min(mods["move_speed"], 0.7)
                        
        return mods

    @staticmethod
    def get_environmental_penalties(region: RegionState) -> Dict[str, float]:
        """
        Returns penalties based on active modifiers.
        """
        penalties = {
            "hp_regen": 1.0,
            "stamina_drain": 1.0
        }
        
        if "FROST" in region.active_modifiers:
            penalties["stamina_drain"] = 1.2
        if "HEAT" in region.active_modifiers:
            penalties["stamina_drain"] = 1.3
            
        return penalties
