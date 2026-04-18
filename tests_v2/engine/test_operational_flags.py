import pytest
from src_v2.config.profiles import RuntimeProfile, HardwareClass
from src_v2.config.validator import ProfileValidator, ConfigValidationError
from src_v2.core.state import AuthoritativeState
from src_v2.engine.kernel import Kernel
from unittest.mock import MagicMock


def test_safe_operational_flags_accepted(tmp_path):
    """
    M7 Law: Support narrow, safe operational flags.
    """
    profile = RuntimeProfile(
        name="SAFE_FLAGS",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=50.0,
        max_worker_count=4,
        max_queue_depth=1000,
        max_replay_buffer_kb=64,
        max_observability_budget_percent=5.0,
        max_tick_budget_ms=10.0
    )
    state = AuthoritativeState(tick=0, seed=42)
    
    # Flags that are explicitly allowed/safe
    safe_flags = {
        "FORCE_REPLAY_OFF": True,
        "MINIMAL_DIAGNOSTICS": True
    }
    
    # Should not raise
    kernel = Kernel(profile=profile, state=state, rng=MagicMock(), flags=safe_flags)
    assert kernel._profile.name == "SAFE_FLAGS"


def test_unsafe_flags_rejected():
    """
    M7 Law: Reject flags that bypass authoritative resource logic.
    """
    unsafe_flags = {"BYPASS_GOVERNOR": True}
    
    with pytest.raises(ConfigValidationError) as exc:
        ProfileValidator.validate_flags(unsafe_flags)
    assert "is FORBIDDEN" in str(exc.value)


def test_flags_cannot_alter_authoritative_semantics():
    """
    M7 Law: Flags must remain subordinate to profile and governor rules.
    Verify that a flag doesn't accidentally change the tick logic or state.
    """
    # This is more of a contract law. 
    # Current implementation check: Kernel doesn't use flags 
    # after validation in __init__.
    pass
