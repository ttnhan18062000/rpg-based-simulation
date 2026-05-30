import os
import pytest
from src.observability.config import ObservabilityMode, ObservabilityConfig

@pytest.fixture(autouse=True)
def cleanup_overrides():
    # Make sure we clean up overrides before and after each test
    ObservabilityConfig.clear_all_overrides()
    # Remove any test environment variables that might interfere
    for key in list(os.environ.keys()):
        if key.startswith("OBS_") or key.startswith("SIM_OBS_") or key.startswith("RPG_OBS_"):
            del os.environ[key]
    yield
    ObservabilityConfig.clear_all_overrides()
    for key in list(os.environ.keys()):
        if key.startswith("OBS_") or key.startswith("SIM_OBS_") or key.startswith("RPG_OBS_"):
            del os.environ[key]

def test_default_mode_resolves_to_light():
    assert ObservabilityConfig.get_mode() == ObservabilityMode.LIGHT
    # LIGHT mode should have runtime profiling enabled, but not behavior normalization
    assert ObservabilityConfig.is_runtime_profiling_enabled() is True
    assert ObservabilityConfig.is_raw_events_enabled() is True
    assert ObservabilityConfig.is_behavior_normalization_enabled() is False

def test_off_mode_disables_all_flags():
    ObservabilityConfig.set_override_mode(ObservabilityMode.OFF)
    assert ObservabilityConfig.get_mode() == ObservabilityMode.OFF
    assert ObservabilityConfig.is_runtime_profiling_enabled() is False
    assert ObservabilityConfig.is_raw_events_enabled() is False
    assert ObservabilityConfig.is_behavior_normalization_enabled() is False

def test_debug_mode_enables_all_flags():
    ObservabilityConfig.set_override_mode(ObservabilityMode.DEBUG)
    assert ObservabilityConfig.get_mode() == ObservabilityMode.DEBUG
    assert ObservabilityConfig.is_runtime_profiling_enabled() is True
    assert ObservabilityConfig.is_behavior_normalization_enabled() is True
    assert ObservabilityConfig.is_dashboard_export_enabled() is True

def test_programmatic_flag_override():
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)
    assert ObservabilityConfig.is_behavior_normalization_enabled() is False
    
    # Programmatic override of a specific flag
    ObservabilityConfig.set_flag_override("OBS_BEHAVIOR_NORMALIZATION", True)
    assert ObservabilityConfig.is_behavior_normalization_enabled() is True
    
    # Other flags remain unaffected
    assert ObservabilityConfig.is_dashboard_export_enabled() is False
    
    # Clearing programmatic overrides
    ObservabilityConfig.set_flag_override("OBS_BEHAVIOR_NORMALIZATION", None)
    assert ObservabilityConfig.is_behavior_normalization_enabled() is False

def test_environment_variable_flag_override():
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)
    assert ObservabilityConfig.is_behavior_normalization_enabled() is False

    os.environ["OBS_BEHAVIOR_NORMALIZATION"] = "true"
    assert ObservabilityConfig.is_behavior_normalization_enabled() is True

    os.environ["SIM_OBS_DASHBOARD_EXPORT"] = "1"
    assert ObservabilityConfig.is_dashboard_export_enabled() is True

    os.environ["RPG_OBS_LIVE_STREAM"] = "yes"
    assert ObservabilityConfig.is_live_stream_enabled() is True
