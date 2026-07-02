import pytest
from unittest.mock import MagicMock, call
from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.config.profiles import RuntimeProfile
from src.engine.worker_manager import WorkerManager
from src.engine.replay_manager import ReplayManager

def test_kernel_authoritative_phase_sequence():
    """
    M1 Law: Verification of the 7-phase authoritative loop.
    This test proves that tick_once executes phases in the EXACT contract order.
    """
    # 1. Setup minimal mocks
    from src.config.profiles import HardwareClass
    profile = RuntimeProfile(
        name="test", 
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024, 
        max_tick_budget_ms=10.0,
        max_cpu_percent=50.0,
        max_worker_count=4,
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5.0
    )
    state = AuthoritativeState(tick=0, seed=42)
    rng = MagicMock()
    
    # Create kernel
    kernel = Kernel(profile, state, rng)
    try:
        # 2. Setup patchers
        from unittest.mock import patch

        with patch.object(Kernel, '_phase_init') as m_init, \
             patch.object(Kernel, '_phase_scheduling') as m_sched, \
             patch.object(Kernel, '_phase_collection') as m_coll, \
             patch.object(Kernel, '_phase_resolution') as m_res, \
             patch.object(Kernel, '_phase_cleanup') as m_clean, \
             patch.object(Kernel, '_phase_advancement') as m_adv, \
             patch.object(Kernel, '_phase_persistence') as m_persist:

            # 3. Execution
            kernel.tick_once()

            # 4. Proof of Order
            manager = MagicMock()
            manager.attach_mock(m_init, "_phase_init")
            manager.attach_mock(m_sched, "_phase_scheduling")
            manager.attach_mock(m_coll, "_phase_collection")
            manager.attach_mock(m_res, "_phase_resolution")
            manager.attach_mock(m_clean, "_phase_cleanup")
            manager.attach_mock(m_adv, "_phase_advancement")
            manager.attach_mock(m_persist, "_phase_persistence")

            # Trigger second time to capture logic
            kernel.tick_once()

            expected_calls = [
                call._phase_init(),
                call._phase_scheduling(),
                call._phase_collection(),
                call._phase_resolution(),
                call._phase_cleanup(),
                call._phase_advancement(),
                call._phase_persistence()
            ]

            assert manager.mock_calls == expected_calls, f"Phase sequence drift detected! Actual: {manager.mock_calls}"
    finally:
        kernel.shutdown()
