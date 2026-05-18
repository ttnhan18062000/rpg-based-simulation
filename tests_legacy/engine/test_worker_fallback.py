import pytest
import threading
import time
from src_legacy.engine.worker_manager import WorkerManager
from src_legacy.core.worker_protocol import WorkerPacket, WorkerResult
from src_legacy.core.updates import EntityUpdate
from src_legacy.core.work import WorkClass
from unittest.mock import MagicMock


def test_queue_saturation_triggers_local_fallback():
    """
    M8 Law: If queue is full, fall back to synchronous execution.
    """
    # Max depth of 2.
    manager = WorkerManager(max_workers=1, max_queue_depth=2)
    
    main_thread_id = threading.current_thread().ident
    execution_threads = []
    lock = threading.Lock()

    def tracking_worker(packet: WorkerPacket) -> WorkerResult:
        with lock:
            execution_threads.append(threading.current_thread().ident)
        # Hold and block the single worker thread to keep the queue occupied
        if threading.current_thread().ident != main_thread_id:
            time.sleep(0.1)
        return WorkerResult(
            source_packet_id=packet.packet_id, 
            work_id=packet.work_id,
            entity_id=packet.subject.id, 
            work_class=packet.work_class,
            update=MagicMock()
        )

    # Submit 10 packets.
    # 1st packet: Goes to worker thread (Inflight = 1)
    # 2nd packet: Inflight = 1 < Depth 2. Goes to worker queue (Inflight = 2)
    # 3rd packet: Inflight = 2 == Depth 2. Goes to LOCAL fallback.
    # ... and so on.
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
        for i in range(10)
    ]
    
    manager.execute_batch(packets, tracking_worker)
    
    # We should see at least one execution in the main thread
    assert main_thread_id in execution_threads
    
    # Total executions must still be 10
    assert len(execution_threads) == 10
    manager.shutdown()


def test_force_local_override():
    """
    Verify that max_workers=0 results in 100% main-thread execution.
    """
    manager = WorkerManager(max_workers=0)
    main_thread_id = threading.current_thread().ident
    
    def worker_fn(packet: WorkerPacket) -> WorkerResult:
        assert threading.current_thread().ident == main_thread_id
        return WorkerResult(
            source_packet_id=packet.packet_id, 
            work_id=packet.work_id,
            entity_id=0, 
            work_class=packet.work_class,
            update=MagicMock()
        )

    packets = [
        WorkerPacket(
            packet_id="test:0", 
            work_id="w:0",
            tick=0, world_time=0, seed=0, 
            work_class=WorkClass.CRITICAL,
            subject=MagicMock(id=0), 
            neighbor_view=[], 
            work_kind="ACT", 
            payload={}
        )
    ]
    manager.execute_batch(packets, worker_fn)
