import pytest
from src_v2.config.validator import ProfileValidator, ConfigValidationError

def test_hard_forbidden_flags():
    """
    Law: Forbidden operational flags MUST be rejected at startup.
    """
    forbidden = ["BYPASS_GOVERNOR", "FORCE_NORMAL", "DISABLE_RESOURCE_CEILINGS"]
    
    for flag in forbidden:
        with pytest.raises(ConfigValidationError, match=f"flag '{flag}' is FORBIDDEN"):
            ProfileValidator.validate_flags({flag: True})

def test_safe_flags_allowed():
    """
    Only diagnostic or observational flags are permitted.
    """
    safe = {"LOG_LEVEL": "DEBUG", "REPLAY_MODE": "DEBUG_WINDOWED"}
    # Should not raise
    ProfileValidator.validate_flags(safe)

def test_contradictory_replay_config():
    """
    Law: Contradictory config (REPLAY_ENABLED + 0KB buffer) MUST be rejected.
    """
    from src_v2.config.profiles import RuntimeProfile, HardwareClass
    
    profile = RuntimeProfile(
        name="no_buffer",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=128,
        max_cpu_percent=50,
        max_worker_count=2,
        max_queue_depth=100,
        max_replay_buffer_kb=0, # 0KB
        max_observability_budget_percent=5,
        max_tick_budget_ms=10.0
    )
    
    with pytest.raises(ConfigValidationError, match="0KB replay buffer"):
        ProfileValidator.validate_flags({"REPLAY_ENABLED": True}, profile)
