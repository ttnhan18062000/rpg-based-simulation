import pytest
import threading
import time
from unittest.mock import MagicMock
from src.engine.worker_manager import WorkerManager
from src.core.worker_protocol import WorkerPacket, WorkerResult, ResultStatus
from src.core.work import WorkClass

def test_local_fallback_preserves_metadata():
    """Prove that even when executing locally, we get compute time and status."""
    manager = WorkerManager(max_workers=0) # Force local
    
    def worker_fn(packet: WorkerPacket) -> WorkerResult:
        time.sleep(0.01) # 10ms
        return WorkerResult(
            source_packet_id=packet.packet_id,
            work_id=packet.work_id,
            entity_id=packet.subject.id,
            work_class=packet.work_class,
            update=MagicMock()
        )

    packets = [
        WorkerPacket(
            packet_id="p1", work_id="w1", tick=1, world_time=0, seed=0,
            work_class=WorkClass.CRITICAL, subject=MagicMock(id=1),
            neighbor_view=[], work_kind="ACT", payload={}
        )
    ]
    
    results = manager.execute_batch(packets, worker_fn)
    assert len(results) == 1
    res = results[0]
    assert res.status == ResultStatus.SUCCESS
    assert res.compute_time_ns > 0
    assert res.work_id == "w1"

def test_crashed_worker_is_authoritative_noop():
    """Prove that a worker crash results in a FAILURE status and no-op update."""
    manager = WorkerManager(max_workers=1)
    
    def crashing_worker(packet: WorkerPacket) -> WorkerResult:
        raise RuntimeError("BOOM")

    packets = [
        WorkerPacket(
            packet_id="p1", work_id="crash_w", tick=1, world_time=0, seed=0,
            work_class=WorkClass.CRITICAL, subject=MagicMock(id=99),
            neighbor_view=[], work_kind="ACT", payload={}
        )
    ]
    
    results = manager.execute_batch(packets, crashing_worker)
    assert len(results) == 1
    res = results[0]
    assert res.status == ResultStatus.FAILURE
    assert res.entity_id == 99
    assert res.work_id == "crash_w"
    # Ensure update is present (no-op)
    assert res.update is not None
    assert res.update.entity_id == 99

def test_queue_overflow_preserves_total_count():
    """Prove that mixed concurrent and fallback execution produces 100% results."""
    # 1 worker, depth 2.
    # Total capacity 3.
    manager = WorkerManager(max_workers=1, max_queue_depth=2)
    
    def slow_worker(packet: WorkerPacket) -> WorkerResult:
        if "slow" in packet.work_id:
            time.sleep(0.05)
        return WorkerResult(
            source_packet_id=packet.packet_id,
            work_id=packet.work_id,
            entity_id=packet.subject.id,
            work_class=packet.work_class,
            update=MagicMock()
        )

    # Submit 10 packets.
    packets = [
        WorkerPacket(
            packet_id=f"p{i}", work_id=f"w{i}_slow", tick=1, world_time=0, seed=0,
            work_class=WorkClass.CRITICAL, subject=MagicMock(id=i),
            neighbor_view=[], work_kind="ACT", payload={}
        )
        for i in range(10)
    ]
    
    results = manager.execute_batch(packets, slow_worker)
    # MUST have exactly 10 results.
    assert len(results) == 10
    
    # Verify all have compute time
    for r in results:
        assert r.compute_time_ns > 0
