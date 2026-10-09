"""The validator accepts one result per entity and no system results (TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE).

Entity id 0 was the slot of the ID-zero system results that carried a `DRAIN_DEBT` drain. Those results tied on the whole sort key and were
merged last-writer-wins per subsystem, which is why `TCK-20261004-PERF-M1-VALIDATOR-ONE-SYSTEM-RESULT-PER-SUBSYSTEM` limited them to one per
subsystem. Nothing produces them any more, so the validator rejects an entity-0 result outright and the sort key
`(class_priority, -local_priority, entity_id)` is unique per result.
"""
from __future__ import annotations

import pytest

from src.core.protocol_validator import ProtocolValidator, ProtocolViolationError
from src.core.updates import EntityUpdate
from src.core.work import WorkClass
from src.core.worker_protocol import WorkerResult


def _entity(entity_id: int, work_id: str = "") -> WorkerResult:
    return WorkerResult(
        source_packet_id=f"local:1:e{entity_id}", work_id=work_id or f"e{entity_id}", entity_id=entity_id,
        work_class=WorkClass.CRITICAL, update=EntityUpdate(entity_id=entity_id),
    )


def test_an_entity_zero_result_is_rejected():
    system_slot = WorkerResult(
        source_packet_id="local:1:s", work_id="s", entity_id=0, work_class=WorkClass.CRITICAL, update=EntityUpdate(entity_id=0),
    )
    with pytest.raises(ProtocolViolationError, match="System results"):
        ProtocolValidator.validate_result_batch([system_slot], {})
    with pytest.raises(ProtocolViolationError, match="System results"):
        ProtocolValidator.validate_result_batch([_entity(1), system_slot, _entity(2)], {})


def test_two_results_for_one_entity_are_rejected_in_either_order():
    pair = [_entity(7, "w1"), _entity(7, "w2")]
    for batch in (pair, list(reversed(pair))):
        with pytest.raises(ProtocolViolationError, match="entity 7"):
            ProtocolValidator.validate_result_batch(batch, {})


def test_valid_batch_shapes_are_accepted():
    ProtocolValidator.validate_result_batch([], {})
    ProtocolValidator.validate_result_batch([_entity(1)], {})
    ProtocolValidator.validate_result_batch([_entity(3), _entity(1), _entity(2)], {})


def test_a_worker_result_no_longer_carries_a_debt_update_or_a_subsystem():
    names = set(WorkerResult.__dataclass_fields__)
    assert "work_debt_update" not in names and "subsystem_id" not in names
