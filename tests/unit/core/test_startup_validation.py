import pytest
from src.config.profiles import RuntimeProfile, HardwareClass
from src.config.validator import ProfileValidator, ConfigValidationError
from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.platform.rng import DeterministicRNG

def test_aggressive_budget_warning(caplog):
    """M7 Law: Class C + low budget should warn but not reject."""
    profile = RuntimeProfile(
        name="tight_class_c",
        hardware_class=HardwareClass.CLASS_C,
        max_ram_mb=128,
        max_cpu_percent=50,
        max_worker_count=2,
        max_queue_depth=100,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=5,
        max_tick_budget_ms=2.0 # Very tight for Class C
    )
    ProfileValidator.validate_profile(profile)
    assert "Feasibility not certified until M9" in caplog.text

def test_too_low_budget_rejection():
    """M7 Law: Sub-ms budget is hard rejected."""
    profile = RuntimeProfile(
        name="impossible",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=128,
        max_cpu_percent=50,
        max_worker_count=2,
        max_queue_depth=100,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=5,
        max_tick_budget_ms=0.5 # Sub-ms
    )
    with pytest.raises(ConfigValidationError, match="sub-millisecond"):
        ProfileValidator.validate_profile(profile)

def test_insufficient_ram_for_replay():
    """M7 Law: Replay requires minimum RAM."""
    profile = RuntimeProfile(
        name="low_ram_replay",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=16, # Too low for replay
        max_cpu_percent=50,
        max_worker_count=2,
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5,
        max_tick_budget_ms=10.0
    )
    with pytest.raises(ConfigValidationError, match="insufficient RAM allowance"):
        ProfileValidator.validate_profile(profile)

def test_contradictory_flags():
    """M7 Law: SURVIVAL_ONLY vs REPLAY_ENABLED is mutually exclusive."""
    flags = {"SURVIVAL_ONLY": True, "REPLAY_ENABLED": True}
    with pytest.raises(ConfigValidationError, match="mutually exclusive"):
        ProfileValidator.validate_flags(flags)

def test_forbidden_flag():
    """M7 Law: BYPASS_GOVERNOR is hard-forbidden."""
    flags = {"BYPASS_GOVERNOR": True}
    with pytest.raises(ConfigValidationError, match="FORBIDDEN"):
        ProfileValidator.validate_flags(flags)

def test_replay_flag_without_buffer():
    """M7 Law: REPLAY_ENABLED needs buffer KB > 0."""
    profile = RuntimeProfile(
        name="no_buffer",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=128,
        max_cpu_percent=50,
        max_worker_count=2,
        max_queue_depth=100,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=5,
        max_tick_budget_ms=10.0
    )
    flags = {"REPLAY_ENABLED": True}
    with pytest.raises(ConfigValidationError, match="0KB replay buffer"):
        ProfileValidator.validate_flags(flags, profile)
