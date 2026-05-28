# TDD tests for Phase 10 rollout profiles
import pytest
from src.domains.optimization.rollout_profiles import RolloutProfileManager, HardwareClass

def test_profile_class_a_enables_only_low_cost_features():
    manager = RolloutProfileManager()
    profile = manager.get_profile(HardwareClass.CLASS_A)
    assert profile.enabled_phases == ["ENABLE_WORLD_CAPABILITY_LAYER", "ENABLE_SELF_MODEL"]
    assert profile.shadow_phases == ["ENABLE_ADVENTURE_DECISION"]

def test_profile_class_b_enables_mid_stack_features():
    manager = RolloutProfileManager()
    profile = manager.get_profile(HardwareClass.CLASS_B)
    assert "ENABLE_COMBAT_ENGAGEMENT" in profile.enabled_phases
    assert "ENABLE_LIFE_ARC_CAMPAIGNS" not in profile.enabled_phases

def test_profile_class_c_can_enable_full_stack():
    manager = RolloutProfileManager()
    profile = manager.get_profile(HardwareClass.CLASS_C)
    assert len(profile.disabled_phases) == 0
    assert "ENABLE_LIFE_ARC_CAMPAIGNS" in profile.enabled_phases

def test_invalid_phase_in_profile_fails_fast():
    manager = RolloutProfileManager()
    with pytest.raises(ValueError, match="Invalid phase flag"):
        manager.create_custom_profile("CUSTOM", enabled=["INVALID_FLAG"])

def test_rollout_profile_serialized_in_manifest():
    manager = RolloutProfileManager()
    profile = manager.get_profile(HardwareClass.CLASS_A)
    serialized = profile.serialize()
    assert serialized["name"] == "CLASS_A"
    assert "ENABLE_SELF_MODEL" in serialized["enabled_phases"]
