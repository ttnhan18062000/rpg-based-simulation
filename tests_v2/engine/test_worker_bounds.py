import pytest
import time
import threading
from src_v2.engine.worker_manager import WorkerManager
from src_v2.core.worker_protocol import WorkerPacket, WorkerResult
from src_v2.core.work import WorkClass
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
