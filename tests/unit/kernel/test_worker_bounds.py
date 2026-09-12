import pytest
import time
import threading
from src.engine.worker_manager import WorkerManager
from src.core.worker_protocol import WorkerPacket, WorkerResult
from src.core.work import WorkClass
from unittest.mock import MagicMock


def test_worker_count_upper_bound():
    """
    M8 Law: No more than max_workers threads should be active.
    """
    max_workers = 3
    manager = WorkerManager(max_workers=max_workers)
    
    unique_threads = set()
    lock = threading.Lock()
    
    def thread_id_worker(packet: WorkerPacket) -> WorkerResult:
        with lock:
            unique_threads.add(threading.current_thread().ident)
        time.sleep(0.05) # Hold thread
        return WorkerResult(
            source_packet_id=packet.packet_id, 
            work_id=packet.work_id,
            entity_id=packet.subject.id, 
            work_class=packet.work_class,
            update=MagicMock()
        )

    packets = [
        WorkerPacket(
            packet_id=f"test:{i}", 
            work_id=f"w:{i}",
            tick=0, world_time=0, seed=i, 
            work_class=WorkClass.CRITICAL,
            subject=MagicMock(id=i), 
            neighbor_view=[], 
            work_kind="ACT", 
            payload={}
        )
        for i in range(10) # 10 tasks for 3 workers
    ]
    
    manager.execute_batch(packets, thread_id_worker)
    
    # We should have seen exactly or fewer than max_workers distinct threads 
    # being used by the pool for these tasks.
    assert len(unique_threads) <= max_workers
    manager.shutdown()


def test_worker_pool_shutdown():
    """
    Verify clean termination of the pool.
    """
    manager = WorkerManager(max_workers=2)
    manager.shutdown()
    assert manager._pool is None


def test_worker_utilization_is_zero_when_workers_disabled():
    """TCK-20260911-WORKER-UTILIZATION-ZERO-WORKERS-DEGRADED-MISTRIGGER: max_workers<=0 means
    workers are deliberately disabled (synchronous execution) -- worker_utilization must report
    0.0 (metric inapplicable), not 1.0 (which ResourceGovernor reads as genuine 90%+ saturation
    and escalates to DEGRADED unconditionally, regardless of real load)."""
    manager = WorkerManager(max_workers=0)
    stats = manager.get_stats()
    assert stats["worker_utilization"] == 0.0
    manager.shutdown()


def test_worker_utilization_reflects_real_saturation_when_workers_enabled():
    """Confirms the fix above does not regress the normal (max_workers > 0) case: real worker
    pressure must still be reported accurately, not silently zeroed."""
    max_workers = 2
    manager = WorkerManager(max_workers=max_workers)
    barrier = threading.Barrier(max_workers + 1)

    def blocking_worker(packet: WorkerPacket) -> WorkerResult:
        barrier.wait()  # Ensures both workers are active simultaneously before either returns
        return WorkerResult(
            source_packet_id=packet.packet_id,
            work_id=packet.work_id,
            entity_id=packet.subject.id,
            work_class=packet.work_class,
            update=MagicMock()
        )

    packets = [
        WorkerPacket(
            packet_id=f"test:{i}",
            work_id=f"w:{i}",
            tick=0, world_time=0, seed=i,
            work_class=WorkClass.CRITICAL,
            subject=MagicMock(id=i),
            neighbor_view=[],
            work_kind="ACT",
            payload={}
        )
        for i in range(max_workers)
    ]

    def _release_barrier():
        barrier.wait()

    releaser = threading.Thread(target=_release_barrier)
    releaser.start()
    manager.execute_batch(packets, blocking_worker)
    releaser.join()

    stats = manager.get_stats()
    assert stats["worker_utilization"] == 1.0  # peak_active == max_workers, real saturation
    manager.shutdown()
