from enum import Enum
from typing import Dict, Any, List

class FeatureMode(str, Enum):
    OFF = "OFF"
    SHADOW = "SHADOW"
    ON = "ON"
    STRICT = "STRICT"

class FeatureFlagManager:
    """Manages Phase 10 feature rollout modes."""
    def __init__(self, overrides: Dict[str, FeatureMode] = None) -> None:
        self._flags: Dict[str, FeatureMode] = {
            "ENABLE_WORLD_CAPABILITY_LAYER": FeatureMode.OFF,
            "ENABLE_SELF_MODEL_COGNITION": FeatureMode.OFF,
            "ENABLE_ADVENTURE_ROUTING": FeatureMode.OFF,
            "ENABLE_COMBAT_ENGAGEMENT": FeatureMode.OFF,
            "ENABLE_BELIEF_ASSIMILATION": FeatureMode.OFF,
            "ENABLE_PROGRESSION_EVOLUTION": FeatureMode.OFF,
            "ENABLE_SOCIAL_COOPERATION": FeatureMode.OFF,
            "ENABLE_WORLD_EMERGENCE": FeatureMode.OFF,
            "ENABLE_LIFE_ARC_CAMPAIGNS": FeatureMode.OFF,
            "ENABLE_ENHANCED_TRACE_EVENTS": FeatureMode.OFF,
        }
        if overrides:
            for k, v in overrides.items():
                if k in self._flags:
                    self._flags[k] = v

    def get_all_flags(self) -> List[str]:
        return list(self._flags.keys())

    def get_flag_mode(self, flag: str) -> FeatureMode:
        return self._flags.get(flag, FeatureMode.OFF)

    def set_flag_mode(self, flag: str, mode: FeatureMode) -> None:
        if flag in self._flags:
            self._flags[flag] = mode

    def is_enabled(self, flag: str) -> bool:
        return self._flags.get(flag) in (FeatureMode.ON, FeatureMode.STRICT)

    def is_shadow(self, flag: str) -> bool:
        return self._flags.get(flag) == FeatureMode.SHADOW

    def serialize(self) -> Dict[str, str]:
        return {k: v.value for k, v in self._flags.items()}
