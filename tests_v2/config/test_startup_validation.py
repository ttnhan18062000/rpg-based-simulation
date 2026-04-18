import pytest
from src_v2.config.profiles import RuntimeProfile, HardwareClass
from src_v2.config.validator import ProfileValidator, ConfigValidationError
from src_v2.core.state import AuthoritativeState
from src_v2.engine.kernel import Kernel
from unittest.mock import MagicMock


def test_startup_validation_rejects_impossible_budget():
    """
    M7 Law: Reject config if observability budget is dangerously high.
    """
    profile = RuntimeProfile(
        name="UNSAFE",
        hardware_class=HardwareClass.CLASS_C,
        max_ram_mb=64,
        max_cpu_percent=90.0,
        max_worker_count=1,
        max_queue_depth=10,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=60.0, # ERR: >50%
        max_tick_budget_ms=10.0
    )
    
    with pytest.raises(ConfigValidationError) as exc:
        ProfileValidator.validate_profile(profile)
    assert "excessively high" in str(exc.value)


def test_startup_validation_rejects_inconsistent_ram():
    """
    M7 Law: Reject if replay buffer is requested on tiny ram devices.
    """
    profile = RuntimeProfile(
        name="INCONSISTENT",
        hardware_class=HardwareClass.CLASS_C,
        max_ram_mb=8, # Low RAM
        max_cpu_percent=90.0,
        max_worker_count=1,
        max_queue_depth=10,
        max_replay_buffer_kb=1024, # Needs RAM
        max_observability_budget_percent=5.0,
        max_tick_budget_ms=10.0
    )
    
    with pytest.raises(ConfigValidationError) as exc:
        ProfileValidator.validate_profile(profile)
    assert "inconsistent configuration" in str(exc.value)


def test_startup_validation_rejects_forbidden_flags():
    """
    M7 Law: Reject forbidden operational flags.
    """
    flags = {"FORCE_NORMAL": True}
    with pytest.raises(ConfigValidationError) as exc:
        ProfileValidator.validate_flags(flags)
    assert "is FORBIDDEN" in str(exc.value)


def test_kernel_reverses_invalid_startup(tmp_path):
    """
    M7 Law: Kernel must invoke validation during __init__.
    """
    # Create an invalid profile
    profile = RuntimeProfile(
        name="BAD_KERNEL",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=50.0,
        max_worker_count=4,
        max_queue_depth=1000,
        max_replay_buffer_kb=64,
        max_observability_budget_percent=99.0, # UNSAFE
        max_tick_budget_ms=10.0
    )
    
    state = AuthoritativeState(tick=0, seed=42)
    
    with pytest.raises(ConfigValidationError):
        Kernel(profile=profile, state=state, rng=MagicMock())
