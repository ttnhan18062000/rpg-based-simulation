"""A pooled chunk that raises answers each of its packets with a FAILURE no-op; the other chunks still commit (TCK-20261021-WORKER-CHUNK-EXCEPTION-DROPS-RESULTS-WITHOUT-FAILURE-NOOPS).

bounded_concurrency_contract §4: a worker failure is a deterministic authoritative no-op that consumes the entity's single result slot. A chunk future that raised used to
drop all of its results. There is no timeout on ``future.result()``: a hung chunk is the watchdog's, not the commit path's.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.core.updates import EntityUpdate
from src.core.work import WorkClass
from src.core.worker_protocol import ResultStatus, WorkerResult
from src.engine.worker_manager import WorkerManager, failure_no_op


def _packet(eid: int):
    """The manager reads only the packet's ids, class and subject id, so a stand-in carries them."""
    return SimpleNamespace(packet_id=f"1:{eid}", work_id=f"1:{eid}:ENTITY_BRAIN", work_class=WorkClass.CRITICAL, subject=SimpleNamespace(id=eid))


def _ok(packet) -> WorkerResult:
    return WorkerResult(
        source_packet_id=packet.packet_id, work_id=packet.work_id, entity_id=packet.subject.id, work_class=packet.work_class,
        update=EntityUpdate(entity_id=packet.subject.id), status=ResultStatus.SUCCESS,
    )


class _ManagerWhoseChunkRaises(WorkerManager):
    """``_wrap_work`` raising escapes the chunk worker, so the chunk's future raises (a worker error inside one packet is already caught per packet)."""

    def __init__(self, bad_entities, **kw) -> None:
        super().__init__(**kw)
        self._bad = set(bad_entities)

    def _wrap_work(self, packet, fn, pooled=True):
        if packet.subject.id in self._bad:
            raise RuntimeError("chunk crashed")
        return super()._wrap_work(packet, fn, pooled)


def _run(bad, n=8, workers=2):
    manager = _ManagerWhoseChunkRaises(bad, max_workers=workers, max_queue_depth=100)
    try:
        return manager.execute_batch([_packet(i) for i in range(1, n + 1)], _ok)
    finally:
        manager.shutdown()


def test_a_raising_chunk_gives_failure_no_ops_for_exactly_its_entities():
    # 8 packets, 2 workers: chunks of 2 -> (1,2) (3,4) (5,6) (7,8); entity 3 crashes the chunk (3,4)
    results = _run({3})
    by_entity = {r.entity_id: r for r in results}
    assert sorted(by_entity) == list(range(1, 9)), "every entity keeps exactly one result"
    assert len(results) == 8
    failed = {e for e, r in by_entity.items() if r.status is ResultStatus.FAILURE}
    assert failed == {3, 4}
    assert all(by_entity[e].status is ResultStatus.SUCCESS for e in (1, 2, 5, 6, 7, 8)), "the other chunks still commit"


def test_a_failure_no_op_is_an_empty_update_for_its_own_entity_with_the_packets_ids():
    r = {x.entity_id: x for x in _run({3})}[4]
    assert r.status is ResultStatus.FAILURE and r.source_packet_id == "1:4" and r.work_id == "1:4:ENTITY_BRAIN"
    assert r.update == EntityUpdate(entity_id=4)
    assert r == failure_no_op(_packet(4))


def test_the_result_order_is_the_submission_order_whether_or_not_a_chunk_failed():
    ok = [r.entity_id for r in _run(set())]
    failed = [r.entity_id for r in _run({3})]
    assert ok == failed == list(range(1, 9))


def test_a_run_with_no_raising_chunk_is_unchanged():
    assert all(r.status is ResultStatus.SUCCESS for r in _run(set()))


@pytest.mark.parametrize("bad", [{1}, {7}, {1, 3, 5, 7}])
def test_any_failing_chunk_pattern_keeps_one_result_per_entity(bad):
    results = _run(bad)
    assert sorted(r.entity_id for r in results) == list(range(1, 9))
