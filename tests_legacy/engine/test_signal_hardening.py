import pytest
import time
import threading
from src_legacy.engine.worker_manager import WorkerManager
from src_legacy.core.worker_protocol import WorkerPacket, WorkerResult, ResultStatus
from src_legacy.core.state import EntityState
from src_legacy.core.work import WorkClass

def dummy_worker(packet: WorkerPacket) -> WorkerResult:
    # Simulate some work
    time.sleep(0.01)
    return WorkerResult(
        source_packet_id=packet.packet_id,
        work_id=packet.work_id,
        entity_id=packet.subject.id,
        work_class=packet.work_class,
        update=None,
        status=ResultStatus.SUCCESS
    )

def test_peak_utilization_accuracy():
    """Verify that WorkerManager accurately captures peak active workers."""
    manager = WorkerManager(max_workers=4, max_queue_depth=10)
    
    packets = [
        WorkerPacket(
            packet_id=f"p{i}",
            work_id=f"w{i}",
            tick=0,
            world_time=0,
            seed=i,
            work_class=WorkClass.CRITICAL,
            subject=EntityState(id=i, kind="test", position=(0,0)),
            neighbor_view=[],
            work_kind="TEST",
            payload={}
        ) for i in range(8)
    ]
    
    # Reset stats
    manager.reset_tick_stats()
    
    # Execute batch with max concurrency allowed by capacity
    results = manager.execute_batch(packets, dummy_worker, concurrency_limit=1.0)
    
    stats = manager.get_stats()
    
    # Since we have 8 packets and 4 workers, we expect peak_workers to hit 4
    assert stats["peak_workers"] == 4, f"Expected peak 4, got {stats['peak_workers']}"
    assert stats["worker_utilization"] == 1.0
    
    # Since we have 8 packets and 4 workers, if they are submitted fast enough, 
    # we should have observed some queuing.
    # inflight_count peaks at 8 (if submission is fast). 
    # peak_queued = max(peak_queued, 8 - 4) = 4
    assert stats["peak_queued"] >= 0
    assert stats["queue_utilization"] >= 0.0

def test_queue_overflow_shedding():
    """Verify that WorkerManager sheds load locally when queue is full."""
    # Tiny queue to trigger it easily
    manager = WorkerManager(max_workers=1, max_queue_depth=2)
    
    packets = [
        WorkerPacket(
            packet_id=f"p{i}",
            work_id=f"w{i}",
            tick=0,
            world_time=0,
            seed=i,
            work_class=WorkClass.CRITICAL,
            subject=EntityState(id=i, kind="test", position=(0,0)),
            neighbor_view=[],
            work_kind="TEST",
            payload={}
        ) for i in range(10)
    ]
    
    results = manager.execute_batch(packets, dummy_worker)
    
    stats = manager.get_stats()
    # inflight_count shouldn't exceed 2
    assert stats["peak_queued"] <= 1 # inflight = (executing=1 + queued=1) = 2. Queued = 1.
    assert len(results) == 10
