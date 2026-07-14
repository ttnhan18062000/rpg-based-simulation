# TDD tests for Phase 10 feature flags
import pytest
from src.domains.optimization.feature_flags import FeatureMode, FeatureFlagManager

def test_all_enhancement_flags_default_to_off_or_shadow():
    manager = FeatureFlagManager()
    # By default, all should be OFF or SHADOW
    for flag in manager.get_all_flags():
        mode = manager.get_flag_mode(flag)
        assert mode in (FeatureMode.OFF, FeatureMode.SHADOW)

def test_feature_flag_off_skips_phase():
    manager = FeatureFlagManager()
    manager.set_flag_mode("ENABLE_SELF_MODEL_COGNITION", FeatureMode.OFF)
    assert not manager.is_enabled("ENABLE_SELF_MODEL_COGNITION")
    assert manager.get_flag_mode("ENABLE_SELF_MODEL_COGNITION") == FeatureMode.OFF

def test_feature_flag_shadow_emits_trace_without_state_mutation():
    manager = FeatureFlagManager()
    manager.set_flag_mode("ENABLE_SELF_MODEL_COGNITION", FeatureMode.SHADOW)
    assert manager.is_shadow("ENABLE_SELF_MODEL_COGNITION")
    assert not manager.is_enabled("ENABLE_SELF_MODEL_COGNITION") # Shadow is not ON for state mutation

def test_feature_flag_on_allows_state_update():
    manager = FeatureFlagManager()
    manager.set_flag_mode("ENABLE_SELF_MODEL_COGNITION", FeatureMode.ON)
    assert manager.is_enabled("ENABLE_SELF_MODEL_COGNITION")
    assert not manager.is_shadow("ENABLE_SELF_MODEL_COGNITION")

def test_feature_flag_matrix_is_serialized_in_run_manifest():
    manager = FeatureFlagManager()
    manager.set_flag_mode("ENABLE_SELF_MODEL_COGNITION", FeatureMode.STRICT)
    manifest = manager.serialize()
    assert manifest["ENABLE_SELF_MODEL_COGNITION"] == "STRICT"

def test_new_flag_registered_in_feature_flag_manager():
    manager = FeatureFlagManager()
    assert "ENABLE_INFORMATION_INTENT_EXECUTION" in manager.get_all_flags()
    assert manager.get_flag_mode("ENABLE_INFORMATION_INTENT_EXECUTION") == FeatureMode.OFF
