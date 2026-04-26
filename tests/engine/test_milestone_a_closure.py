import os
import pytest
from src.engine.kernel import Kernel
from src.engine.apply import ApplyPath
from src.engine.scheduler import DeterministicScheduler
from src.engine.checkpoint import CanonicalStateHasher

AUTHORITATIVE_FILES = [
    "src/engine/kernel.py",
    "src/engine/apply.py",
    "src/engine/scheduler.py",
    "src/engine/checkpoint.py"
]

FORBIDDEN_PATTERNS = [
    "TODO",
    "FIXME",
    "EXPECTED_FAIL",
    "STUB"
]

def test_closure_no_placeholders():
    """
    Milestone A Guard: Ensure no unacknowledged placeholders in core runtime.
    Gated Exception: 'pass' is allowed only in non-authoritative branches 
    (observability, replay) or explicit gated no-ops in the scheduler.
    """
    root = os.getcwd()
    for rel_path in AUTHORITATIVE_FILES:
        abs_path = os.path.join(root, rel_path)
        with open(abs_path, "r") as f:
            content = f.read()
            for pattern in FORBIDDEN_PATTERNS:
                assert pattern not in content, f"Forbidden pattern '{pattern}' found in {rel_path}"
    
    # Check for unauthorized 'pass' blocks
    # Specifically, line-by-line check to ensure 'pass' is only where expected.
    with open(os.path.join(root, "src/engine/scheduler.py"), "r") as f:
        lines = f.readlines()
        pass_count = sum(1 for line in lines if "pass" in line)
        # We expect exactly 1 'pass' in the OPPORTUNISTIC branch
        assert pass_count == 1, "Unexpected 'pass' count in scheduler.py"


def test_milestone_a_structural_compliance():
    """Verify that all contractual files and classes exist."""
    assert issubclass(Kernel, object)
    assert hasattr(ApplyPath, "apply_generation")
    assert hasattr(DeterministicScheduler, "select_work")
    assert hasattr(CanonicalStateHasher, "get_hash")


def test_final_kernel_law_compliance():
    """
    Verify the 6-phase authoritative order is the primary structure.
    Checks that the Kernel has all 6 mandated phase methods.
    """
    mandated_phases = [
        "_phase_init",
        "_phase_scheduling",
        "_phase_collection",
        "_phase_resolution",
        "_phase_cleanup",
        "_phase_advancement"
    ]
    for phase in mandated_phases:
        assert hasattr(Kernel, phase), f"Kernel missing mandated phase method: {phase}"

    # Also verify the tick_once orchestrator calls them (simple source check)
    import inspect
    source = inspect.getsource(Kernel.tick_once)
    for phase in mandated_phases:
        assert phase in source, f"Kernel.tick_once does not orchestrate mandated phase: {phase}"


def test_milestone_a_baseline_isolation():
    """
    Law: The baseline must be runnable WITHOUT concurrency plumbing.
    Proof: Use a mock WorkerManager that raises an error if touched.
    """
    from unittest.mock import MagicMock
    from src.config.profiles import RuntimeProfile, HardwareClass
    from src.core.state import AuthoritativeState, EntityState
    from src.platform.rng import DeterministicRNG
    from src.engine.executor import LocalSequentialExecutor
    from src.engine.worker_manager import WorkerManager
    
    profile = RuntimeProfile(
        name="test", 
        hardware_class=HardwareClass.CLASS_C,
        max_ram_mb=512,
        max_cpu_percent=50.0,
        max_worker_count=0,
        max_queue_depth=10,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=100.0
    )
    state = AuthoritativeState(
        tick=0,
        seed=42,
        entities={1: EntityState(id=1, kind="agent", position=(0,0), readiness=100)}
    )
    rng = DeterministicRNG(42)
    
    # 1. Mock the WorkerManager and the Kernel's internal manager
    mock_manager = MagicMock(spec=WorkerManager)
    mock_manager.get_stats.return_value = {
        "worker_utilization": 0.0,
        "queue_utilization": 0.0,
        "active_workers": 0,
        "peak_active": 0,
        "peak_queued": 0
    }
    mock_manager.execute_batch.side_effect = Exception("CONCURRENCY_LEAK: WorkerManager touched during baseline run!")
    
    # 2. Initialize kernel with LocalSequentialExecutor
    executor = LocalSequentialExecutor()
    kernel = Kernel(profile, state, rng, executor=executor)
    
    # Force the mock manager into the kernel (Law: Audit kernel internal isolation)
    kernel._worker_manager = mock_manager
    
    # 3. Add work and tick
    # We need to ensure there IS work so the COLLECTION phase is actually non-empty
    # Entity in readiness 100 will be selected by the scheduler for an action
    
    # Run one tick
    # If the thread pool or packetization logic is touched, this will fail.
    kernel.tick_once()
    
    assert kernel.state.entities[1].readiness < 100
    assert not mock_manager.execute_batch.called, "WorkerManager was touched during Milestone A baseline run!"
