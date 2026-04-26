import pytest
from src_legacy.config.profiles import RuntimeProfile, HardwareClass
from src_legacy.config.validator import ProfileValidator, ConfigValidationError
from src_legacy.core.state import AuthoritativeState
from src_legacy.engine.kernel import Kernel
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
    Verify that a flag doesn't accidentally change the authoritative outcome.
    """
    from src_legacy.engine.checkpoint import CanonicalStateHasher
    from src_legacy.platform.rng import DeterministicRNG
    
    profile = RuntimeProfile(
        name="TEST",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=10,
        max_replay_buffer_kb=64,
        max_observability_budget_percent=5.0,
        max_tick_budget_ms=16.6
    )
    state = AuthoritativeState(tick=0, seed=42)
    rng = MagicMock(spec=DeterministicRNG)
    
    # Run with flag A
    k1 = Kernel(profile=profile, state=state, rng=rng, flags={"FLAG_A": True})
    k1.tick_once()
    hash_a = CanonicalStateHasher.get_hash(k1.state)
    
    # Run with flag B
    k2 = Kernel(profile=profile, state=state, rng=rng, flags={"FLAG_B": True})
    k2.tick_once()
    hash_b = CanonicalStateHasher.get_hash(k2.state)
    
    # Authoritative outcome must be identical
    assert hash_a == hash_b
    assert k1.state.tick == k2.state.tick
