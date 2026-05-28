from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List
from src.domains.optimization.feature_flags import FeatureFlagManager, FeatureMode

class HardwareClass(str, Enum):
    CLASS_A = "CLASS_A" # Low spec (e.g. mobile, lightweight runtime)
    CLASS_B = "CLASS_B" # Mid spec (e.g. standard desktop / single server)
    CLASS_C = "CLASS_C" # High spec / full enhanced stack

@dataclass(frozen=True, slots=True)
class RolloutProfile:
    name: str
    hardware_class: HardwareClass
    enabled_phases: List[str]
    shadow_phases: List[str]
    disabled_phases: List[str]
    max_ram_mb: int
    tick_budget_ms: float
    max_trace_events: int

    def serialize(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "hardware_class": self.hardware_class.value,
            "enabled_phases": self.enabled_phases,
            "shadow_phases": self.shadow_phases,
            "disabled_phases": self.disabled_phases,
            "max_ram_mb": self.max_ram_mb,
            "tick_budget_ms": self.tick_budget_ms,
            "max_trace_events": self.max_trace_events
        }

class RolloutProfileManager:
    """Manages profile matrices for Phase 10 optimization."""
    def __init__(self) -> None:
        self.ff_manager = FeatureFlagManager()
        valid_flags = set(self.ff_manager.get_all_flags())

        self._profiles = {
            HardwareClass.CLASS_A: RolloutProfile(
                name="CLASS_A",
                hardware_class=HardwareClass.CLASS_A,
                enabled_phases=["ENABLE_WORLD_CAPABILITY_LAYER", "ENABLE_SELF_MODEL"],
                shadow_phases=["ENABLE_ADVENTURE_DECISION"],
                disabled_phases=[
                    "ENABLE_COMBAT_ENGAGEMENT", "ENABLE_INFORMATION_BELIEF",
                    "ENABLE_PROGRESSION_CONVERSION", "ENABLE_COOPERATION",
                    "ENABLE_WORLD_EMERGENCE", "ENABLE_LIFE_ARC_CAMPAIGNS",
                    "ENABLE_ENHANCED_TRACE_EVENTS"
                ],
                max_ram_mb=512,
                tick_budget_ms=10.0,
                max_trace_events=1000
            ),
            HardwareClass.CLASS_B: RolloutProfile(
                name="CLASS_B",
                hardware_class=HardwareClass.CLASS_B,
                enabled_phases=[
                    "ENABLE_WORLD_CAPABILITY_LAYER", "ENABLE_SELF_MODEL",
                    "ENABLE_ADVENTURE_DECISION", "ENABLE_COMBAT_ENGAGEMENT",
                    "ENABLE_INFORMATION_BELIEF", "ENABLE_PROGRESSION_CONVERSION"
                ],
                shadow_phases=["ENABLE_COOPERATION", "ENABLE_WORLD_EMERGENCE"],
                disabled_phases=["ENABLE_LIFE_ARC_CAMPAIGNS", "ENABLE_ENHANCED_TRACE_EVENTS"],
                max_ram_mb=2048,
                tick_budget_ms=25.0,
                max_trace_events=5000
            ),
            HardwareClass.CLASS_C: RolloutProfile(
                name="CLASS_C",
                hardware_class=HardwareClass.CLASS_C,
                enabled_phases=[
                    "ENABLE_WORLD_CAPABILITY_LAYER", "ENABLE_SELF_MODEL",
                    "ENABLE_ADVENTURE_DECISION", "ENABLE_COMBAT_ENGAGEMENT",
                    "ENABLE_INFORMATION_BELIEF", "ENABLE_PROGRESSION_CONVERSION",
                    "ENABLE_COOPERATION", "ENABLE_WORLD_EMERGENCE",
                    "ENABLE_LIFE_ARC_CAMPAIGNS", "ENABLE_ENHANCED_TRACE_EVENTS"
                ],
                shadow_phases=[],
                disabled_phases=[],
                max_ram_mb=8192,
                tick_budget_ms=50.0,
                max_trace_events=20000
            )
        }

    def get_profile(self, hw_class: HardwareClass) -> RolloutProfile:
        return self._profiles[hw_class]

    def create_custom_profile(self, name: str, enabled: List[str], shadow: List[str] = None) -> RolloutProfile:
        valid_flags = set(self.ff_manager.get_all_flags())
        shadow = shadow or []
        for flag in enabled + shadow:
            if flag not in valid_flags:
                raise ValueError(f"Invalid phase flag: {flag}")
        disabled = [f for f in valid_flags if f not in enabled and f not in shadow]
        return RolloutProfile(
            name=name,
            hardware_class=HardwareClass.CLASS_B,
            enabled_phases=enabled,
            shadow_phases=shadow,
            disabled_phases=disabled,
            max_ram_mb=2048,
            tick_budget_ms=25.0,
            max_trace_events=5000
        )
