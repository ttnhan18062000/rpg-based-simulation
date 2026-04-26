import pytest
from unittest.mock import MagicMock
from src.engine.worker_manager import WorkerManager
from src.core.worker_protocol import WorkerPacket, WorkerResult, ResultStatus
from src.core.state import EntityState

def dummy_worker(packet: WorkerPacket) -> WorkerResult:
    # Simulate some work
    import time
    from src.core.work import WorkClass
    time.sleep(0.01)
    return WorkerResult(
        source_packet_id=packet.packet_id,
        work_id=packet.work_id,
        entity_id=packet.subject.id,
        work_class=packet.work_class,
        update=MagicMock(),
        status=ResultStatus.SUCCESS
    )

def test_worker_concurrency_throttling():
    """Verify that WorkerManager respects the concurrency_limit."""
    # Pool size 4
    wm = WorkerManager(max_workers=4, max_queue_depth=100)
    
    from src.core.work import WorkClass
    # 1. Full Capacity (concurrency_limit = 1.0)
    packets = [
        WorkerPacket(packet_id=f"p{i}", work_id=f"w{i}", tick=0, world_time=0, seed=i, 
                     work_class=WorkClass.CRITICAL,
                     subject=EntityState(id=i+1, kind="TEST", position=(0,0), properties={}), 
                     neighbor_view=[], work_kind="TEST", payload={})
        for i in range(10)
    ]
    
    results = wm.execute_batch(packets, dummy_worker, concurrency_limit=1.0)
    stats = wm.get_stats()
    
    # Peak active should be exactly 4 (max_workers)
    assert stats["peak_workers"] == 4
    assert len(results) == 10
    
    # 2. Throttled Capacity (concurrency_limit = 0.5 -> 2 workers)
    wm.reset_tick_stats()
    results = wm.execute_batch(packets, dummy_worker, concurrency_limit=0.5)
    stats = wm.get_stats()
    
    # Peak active should be 2 (50% of 4)
    assert stats["peak_workers"] == 2
    assert len(results) == 10
    
    # 3. Minimal Capacity (concurrency_limit = 0.25 -> 1 worker)
    wm.reset_tick_stats()
    results = wm.execute_batch(packets, dummy_worker, concurrency_limit=0.25)
    stats = wm.get_stats()
    
    # Peak active should be 1
    assert stats["peak_workers"] == 1
    assert len(results) == 10

def test_worker_concurrency_rounding():
    """Verify that rounding always allows at least 1 worker."""
    wm = WorkerManager(max_workers=4, max_queue_depth=100)
    from src.core.work import WorkClass
    packets = [WorkerPacket(packet_id="p1", work_id="w1", tick=0, world_time=0, seed=0, 
                           work_class=WorkClass.CRITICAL,
                           subject=EntityState(id=1, kind="TEST", position=(0,0), properties={}), 
                           neighbor_view=[], work_kind="TEST", payload={})]
    
    # Extremely low limit (0.01) should still round up to 1 worker
    wm.execute_batch(packets, dummy_worker, concurrency_limit=0.01)
    stats = wm.get_stats()
    assert stats["peak_workers"] == 1
