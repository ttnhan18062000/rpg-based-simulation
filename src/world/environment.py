from __future__ import annotations
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from src.core.state import RegionState, EntityState
from src.core.enums import Faction

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState

class EnvironmentService:
    """
    Manages the impact of regional hazards, weather, and auras on entities.
    VERIFIED v2: EnvironmentService
    """

    @staticmethod
    def calculate_hazard_drain(region: RegionState, entity: EntityState) -> int:
        """
        Calculates the HP/Readiness drain for an entity in a region.
        Scales with hazard_level and calamity_intensity.
        """
        # Formula: hazard_level * (1.0 + calamity_intensity)
        # Scaled to integer for HP damage
        base_drain = region.hazard_level * (1.0 + region.calamity_intensity)
        
        if "MIASMA" in region.active_modifiers:
            base_drain *= 1.5
            
        return int(base_drain * 10.0) # Scale by 10 for meaningful impact

    @staticmethod
    def get_weather_multipliers(region: RegionState) -> Dict[str, float]:
        """
        Returns stat multipliers based on current weather.
        """
        mults = {
            "move_speed": 1.0,
            "perception": 1.0,
            "evasion": 1.0,
            "stamina_drain": 1.0
        }
        
        if region.weather == "STORM":
            mults["perception"] = 0.7
            mults["evasion"] = 0.8
            mults["move_speed"] = 0.8
        elif region.weather == "RAIN":
            mults["perception"] = 0.9
            mults["evasion"] = 0.9
        elif region.weather == "SNOW":
            mults["move_speed"] = 0.7
            mults["stamina_drain"] = 1.2
        elif region.weather == "BLIZZARD":
            mults["move_speed"] = 0.5
            mults["perception"] = 0.5
            mults["stamina_drain"] = 1.5
            
        return mults

    @staticmethod
    def get_aura_multipliers(state: AuthoritativeState, entity: EntityState) -> Dict[str, float]:
        """
        Returns stat multipliers based on nearby strongholds (Aura of Despair).
        """
        mults = {
            "move_speed": 1.0,
            "readiness_regen": 1.0
        }
        
        from src.core.enums import Faction
        if entity.identity.faction == Faction.HERO_GUILD:
            for s in state.entities.values():
                # Any active monster stronghold
                if s.kind == "stronghold" and s.combat.alive:
                    from src.engine.legality import LegalityServiceV2
                    dist = LegalityServiceV2.get_manhattan_dist(entity.position, s.position)
                    if dist < 12:
                        # Aura of Despair: -30% speed, -20% readiness recovery
                        mults["move_speed"] = min(mults["move_speed"], 0.7)
                        mults["readiness_regen"] = min(mults["readiness_regen"], 0.8)
                        
        return mults

    @staticmethod
    def get_modifier_multipliers(region: RegionState) -> Dict[str, float]:
        """
        Returns penalties based on active regional modifiers.
        """
        mults = {
            "stamina_drain": 1.0,
            "hp_regen": 1.0
        }
        
        if "FROST" in region.active_modifiers:
            mults["stamina_drain"] *= 1.2
        if "HEAT" in region.active_modifiers:
            mults["stamina_drain"] *= 1.3
        if "CURSE" in region.active_modifiers:
            mults["hp_regen"] = 0.0 # No healing
            
        return mults

