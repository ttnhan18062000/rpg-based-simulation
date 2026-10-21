"""A WorkItem's priority reaches its WorkerResult, and the commit key orders higher local_priority first (TCK-20261021-WORK-ITEM-PRIORITY-LOOKUP-KEY-MISMATCH).

The executor looked the priority up by a work id built in a different format from the packet's, so every result carried 0. Both sides now use ``packet_work_id``.
"""
from __future__ import annotations

from src.config.profiles import HardwareClass, RuntimeProfile
from src.core.builder import V2EntityBuilder
from src.core.concurrency_law import ConcurrencyLaw
from src.core.state import AuthoritativeState
from src.core.updates import EMPTY_ENTITY_UPDATE
from src.core.work import WorkClass, WorkItem, packet_work_id
from src.core.worker_protocol import ResultStatus, WorkerResult
from src.engine.executor import ConcurrentExecutionAdapter
from src.platform.rng import DeterministicRNG


class _EchoManager:
    """A worker manager whose workers answer every packet with priority 0, as a result that did not copy the packet's would."""

    def execute_batch(self, packets, worker_fn, concurrency_limit=1.0):
        return [
            WorkerResult(
                source_packet_id=p.packet_id, work_id=p.work_id, entity_id=p.subject.id, work_class=p.work_class,
                update=EMPTY_ENTITY_UPDATE, status=ResultStatus.SUCCESS, class_priority=p.class_priority, local_priority=0,
            )
            for p in packets
        ]


def _profile() -> RuntimeProfile:
    return RuntimeProfile(
        name="t", hardware_class=HardwareClass.CLASS_B, max_ram_mb=1024, max_cpu_percent=100.0, max_worker_count=1,
        max_queue_depth=100, max_replay_buffer_kb=0, max_observability_budget_percent=0.0, max_tick_budget_ms=16.6,
    )


def _state():
    entities = {i: V2EntityBuilder(i).combat(hp=100, alive=True).location(10.0 + i, 10.0).build() for i in (1, 2, 3)}
    return AuthoritativeState(tick=4, seed=42, world_time=104, entities=entities)


def _items(priorities):
    return [
        WorkItem(owner_id=eid, work_id=f"4:entity_brain:{eid}", work_class=WorkClass.CRITICAL, work_kind="ENTITY_BRAIN", priority=pr)
        for eid, pr in priorities.items()
    ]


def _execute(priorities):
    return ConcurrentExecutionAdapter(_EchoManager()).execute(_items(priorities), _state(), DeterministicRNG(42), _profile())


def test_a_set_priority_reaches_the_result():
    results = {r.entity_id: r.local_priority for r in _execute({1: 0, 2: 7, 3: 3})}
    assert results == {1: 0, 2: 7, 3: 3}


def test_an_unset_priority_stays_zero():
    assert {r.local_priority for r in _execute({1: 0, 2: 0, 3: 0})} == {0}


def test_a_set_priority_changes_the_commit_order_higher_first():
    ordered = sorted(_execute({1: 0, 2: 7, 3: 3}), key=ConcurrencyLaw.commit_key)
    assert [r.entity_id for r in ordered] == [2, 3, 1]  # 7, 3, 0: higher local_priority is earlier
    flat = sorted(_execute({1: 0, 2: 0, 3: 0}), key=ConcurrencyLaw.commit_key)
    assert [r.entity_id for r in flat] == [1, 2, 3]  # no priority: entity id ascending, as before


def test_class_priority_still_ranks_before_local_priority():
    low_class = WorkerResult(source_packet_id="a", work_id="a", entity_id=9, work_class=WorkClass.PERIODIC, update=EMPTY_ENTITY_UPDATE,
                             status=ResultStatus.SUCCESS, class_priority=10, local_priority=99)
    high_class = WorkerResult(source_packet_id="b", work_id="b", entity_id=1, work_class=WorkClass.CRITICAL, update=EMPTY_ENTITY_UPDATE,
                              status=ResultStatus.SUCCESS, class_priority=0, local_priority=0)
    assert sorted([low_class, high_class], key=ConcurrencyLaw.commit_key)[0] is high_class  # CRITICAL (0) before PERIODIC (10), whatever the local priority


def test_the_packet_work_id_text_is_unchanged_and_is_not_the_scheduler_id():
    assert packet_work_id(4, 2, "ENTITY_BRAIN") == "4:2:ENTITY_BRAIN"
    assert _items({2: 0})[0].work_id != packet_work_id(4, 2, "ENTITY_BRAIN")
