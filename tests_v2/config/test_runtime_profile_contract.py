import pytest
from pydantic import ValidationError
from src_v2.config.profiles import RuntimeProfile, HardwareClass


def test_valid_profile_instantiation():
    """Ensure a valid profile can be created."""
    data = {
        "name": "developer-high",
        "hardware_class": HardwareClass.CLASS_B,
        "max_ram_mb": 4096,
        "max_cpu_percent": 80.0,
        "max_worker_count": 4,
        "max_queue_depth": 1000,
        "max_replay_buffer_kb": 512,
        "max_observability_budget_percent": 5.0,
        "max_tick_budget_ms": 16.6
    }
    profile = RuntimeProfile(**data)
    assert profile.name == "developer-high"
    assert profile.max_ram_mb == 4096


def test_invalid_profile_rejection():
    """Ensure missing or invalid fields trigger validation errors."""
    # Missing field
    with pytest.raises(ValidationError):
        RuntimeProfile(name="broken")
        
    # Negative value
    with pytest.raises(ValidationError):
        RuntimeProfile(
            name="negative",
            hardware_class=HardwareClass.CLASS_B,
            max_ram_mb=-10,  # Invalid
            max_cpu_percent=80.0,
            max_worker_count=4,
            max_queue_depth=1000,
            max_replay_buffer_kb=512,
            max_observability_budget_percent=5.0,
            max_tick_budget_ms=16.6
        )


def test_profile_immutability():
    """Ensure profiles are frozen as per the contract."""
    profile = RuntimeProfile(
        name="frozen",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_cpu_percent=80.0,
        max_worker_count=4,
        max_queue_depth=1000,
        max_replay_buffer_kb=512,
        max_observability_budget_percent=5.0,
        max_tick_budget_ms=16.6
    )
    with pytest.raises(ValidationError):
        profile.max_ram_mb = 2048
