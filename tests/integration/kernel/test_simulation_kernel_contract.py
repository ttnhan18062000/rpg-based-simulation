from dataclasses import dataclass
from typing import List
import pytest
from src.engine.phases import TickPhase, get_authoritative_phases
from src.config.profiles import HardwareClass
from src.engine.kernel import Kernel


def test_authoritative_phase_list():
    """Ensure the authoritative phase list matches the Milestone A contract."""
    phases = get_authoritative_phases()
    expected = [
        TickPhase.INIT,
        TickPhase.SCHEDULING,
        TickPhase.COLLECTION,
        TickPhase.RESOLUTION,
        TickPhase.CLEANUP,
        TickPhase.ADVANCEMENT
    ]
    assert phases == expected


def test_kernel_tick_execution_order():
    """
    Verify that the kernel tick executes phases in the strict contractual order.
    We'll use a subclass of Kernel to track method calls if needed, 
    but for Milestone A we verify the logical output of the 6-phase cycle.
    """
    from src.core.state import AuthoritativeState
    from src.config.profiles import RuntimeProfile
    from src.platform.rng import DeterministicRNG
    from unittest.mock import MagicMock
    
    profile = RuntimeProfile(
        name="test", 
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=1, 
        max_queue_depth=10, 
        max_replay_buffer_kb=64,
        max_observability_budget_percent=5.0,
        max_tick_budget_ms=16.6
    )
    state = AuthoritativeState(tick=0, seed=1)
    rng = MagicMock(spec=DeterministicRNG)
    rng.get_state.return_value = None

    kernel = Kernel(profile, state, rng)
    try:
        kernel.tick_once()

        # Assert side effects of the phases
        assert kernel.state.tick == 1
        assert kernel.state.world_time == 1
        # Check that status was updated in CLEANUP/ADVANCEMENT
        assert len(kernel.status.signal_history) == 1
        assert kernel.status.signal_history[-1].tick_compute_ms > 0
    finally:
        kernel.shutdown(timeout_s=1.0)
