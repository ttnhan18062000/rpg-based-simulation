import pytest
from src.engine.executor import LocalSequentialExecutor
from src.core.state import AuthoritativeState, EntityState
from src.core.work import WorkItem, WorkClass
from src.platform.rng import DeterministicRNG

def test_local_executor_movement():
    """Verify that LocalSequentialExecutor handles ENTITY_MOVE correctly."""
    executor = LocalSequentialExecutor()
    entities = {
        1: EntityState(id=1, kind="agent", position=(0.0, 0.0), readiness=100.0)
    }
    state = AuthoritativeState(tick=0, seed=42, entities=entities)
    rng = DeterministicRNG(42)
    from src.config.profiles import RuntimeProfile, HardwareClass
    profile = RuntimeProfile(
        name="test", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512, max_cpu_percent=50.0, max_worker_count=1,
        max_queue_depth=10, max_replay_buffer_kb=0, max_tick_budget_ms=10.0,
        max_observability_budget_percent=5.0
    )
    
    work = [
        WorkItem(
            owner_id=1,
            work_id="test:1:move",
            work_kind="ENTITY_MOVE",
            work_class=WorkClass.CRITICAL,
            payload={"target_position": (10.0, 0.0)}
        )
    ]
    
    results = executor.execute(work, state, rng, profile)
    
    assert len(results) == 1
    res = results[0]
    assert res.entity_id == 1
    assert res.update.new_position == (1.0, 0.0) # Clamped step
    assert res.update.readiness_delta == -10.0
    assert "local:" in res.source_packet_id # Proof of local path

def test_local_executor_action():
    """Verify that LocalSequentialExecutor handles ENTITY_ACT correctly."""
    executor = LocalSequentialExecutor()
    entities = {
        1: EntityState(id=1, kind="agent", position=(0.0, 0.0), readiness=100.0)
    }
    state = AuthoritativeState(tick=0, seed=42, entities=entities)
    rng = DeterministicRNG(42)
    from src.config.profiles import RuntimeProfile, HardwareClass
    profile = RuntimeProfile(
        name="test", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512, max_cpu_percent=50.0, max_worker_count=1,
        max_queue_depth=10, max_replay_buffer_kb=0, max_tick_budget_ms=10.0,
        max_observability_budget_percent=5.0
    )
    
    work = [
        WorkItem(
            owner_id=1,
            work_id="test:1:act",
            work_kind="ENTITY_ACT",
            work_class=WorkClass.CRITICAL
        )
    ]
    
    results = executor.execute(work, state, rng, profile)
    
    assert len(results) == 1
    res = results[0]
    assert res.update.readiness_delta == -100.0
    assert res.update.new_position is None
