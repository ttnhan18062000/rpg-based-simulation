import pytest
from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.state import AuthoritativeState, EntityState
from src.engine.executor import LocalSequentialExecutor
from src.engine.scheduler import DeterministicScheduler
from src.platform.rng import DeterministicRNG

def test_debt_drainage_desimulation():
    """Prove that DRAIN_DEBT is resolved authoritatively via the executor."""
    profile = RuntimeProfile(
        name="test",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=1024,
        max_cpu_percent=90.0,
        max_worker_count=4, # Debt should drain by 4
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5.0,
        max_tick_budget_ms=100
    )
    
    # Initial state with some debt
    state = AuthoritativeState(
        tick=0,
        seed=42,
        entities={},
        work_debt={"KERNEL": 10} # 10 debt units
    )
    
    rng = DeterministicRNG(seed=42)
    
    # Kernel with local executor
    kernel = Kernel(profile, state=state, rng=rng, executor=LocalSequentialExecutor())
    
    # Run one tick
    kernel.tick_once()
    
    # Verify debt was drained
    assert kernel.state.work_debt["KERNEL"] == 6, f"Expected debt 6, got {kernel.state.work_debt['KERNEL']}"

def test_drain_debt_zero():
    """Verify debt doesn't go negative if drain exceeds debt."""
    profile = RuntimeProfile(
        name="test",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=1024,
        max_cpu_percent=90.0,
        max_worker_count=10, 
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5.0,
        max_tick_budget_ms=100
    )
    state = AuthoritativeState(tick=0, seed=42, entities={}, work_debt={"KERNEL": 5})
    rng = DeterministicRNG(seed=42)
    
    kernel = Kernel(profile, state=state, rng=rng, executor=LocalSequentialExecutor())
    
    kernel.tick_once()
    
    assert kernel.state.work_debt["KERNEL"] == 0
