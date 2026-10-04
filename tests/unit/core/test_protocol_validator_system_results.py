"""At most one debt-update system result per subsystem per batch (TCK-20261004-PERF-M1-VALIDATOR-ONE-SYSTEM-RESULT-PER-SUBSYSTEM).

The kernel merges ID-zero system results into `work_debt_updates[subsystem_id]` last-writer-wins, and
such results tie on the whole sort key. Two results for one subsystem would therefore make the committed
state depend on arrival order. The validator makes that batch impossible (PERF-M1-T04 outcome).
"""
from __future__ import annotations

import pytest

from src.core.concurrency_law import ConcurrencyLaw
from src.core.protocol_validator import ProtocolValidator, ProtocolViolationError
from src.core.updates import EntityUpdate
from src.core.work import WorkClass
from src.core.worker_protocol import WorkerResult


def _drain(subsystem: str, value: int, work_id: str) -> WorkerResult:
    return WorkerResult(
        source_packet_id=f"local:1:{work_id}", work_id=work_id, entity_id=0, work_class=WorkClass.DEFERRED,
        update=EntityUpdate(entity_id=0), class_priority=ConcurrencyLaw.get_class_priority(WorkClass.DEFERRED),
        work_debt_update=value, subsystem_id=subsystem,
    )


def _entity(entity_id: int) -> WorkerResult:
    return WorkerResult(
        source_packet_id=f"local:1:e{entity_id}", work_id=f"e{entity_id}", entity_id=entity_id,
        work_class=WorkClass.CRITICAL, update=EntityUpdate(entity_id=entity_id),
    )


@pytest.mark.parametrize("values", [(-2, -5), (-5, -2), (-2, -2)])
def test_two_debt_updates_for_one_subsystem_are_rejected_in_either_order(values):
    first, second = (_drain("SYS_A", values[0], "a1"), _drain("SYS_A", values[1], "a2"))
    for batch in ([first, second], [second, first]):
        with pytest.raises(ProtocolViolationError, match="SYS_A"):
            ProtocolValidator.validate_result_batch(batch, {})


def test_the_duplicate_is_rejected_even_with_other_results_between_them():
    batch = [_drain("SYS_A", -2, "a1"), _entity(3), _drain("SYS_B", -2, "b1"), _drain("SYS_A", -2, "a2")]
    with pytest.raises(ProtocolViolationError, match="SYS_A"):
        ProtocolValidator.validate_result_batch(batch, {})


def test_valid_batch_shapes_are_still_accepted():
    ProtocolValidator.validate_result_batch([_drain("SYS_A", -2, "a1")], {})                      # one system result
    ProtocolValidator.validate_result_batch(                                                       # distinct subsystems
        [_drain("SYS_A", -2, "a1"), _drain("SYS_B", -2, "b1"), _drain("SYS_C", -1, "c1")], {})
    ProtocolValidator.validate_result_batch([_entity(1), _entity(2), _drain("SYS_A", -2, "a1")], {})  # entity + system
    ProtocolValidator.validate_result_batch([], {})


def test_a_system_result_without_a_debt_update_is_not_counted():
    """Only results that carry a `work_debt_update` are merged by subsystem, so only those are limited."""
    plain = WorkerResult(
        source_packet_id="local:1:p", work_id="p", entity_id=0, work_class=WorkClass.DEFERRED,
        update=EntityUpdate(entity_id=0), subsystem_id="SYS_A",
    )
    ProtocolValidator.validate_result_batch([plain, _drain("SYS_A", -2, "a1")], {})
