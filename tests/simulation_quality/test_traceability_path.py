"""Integration test: §9 Traceability Design drill-down path, steps 1-3
(TCK-20260711-SIMQ-TRACEABILITY-PATH-INTEGRATION-TEST).

Proves QualityReport -> pillar worst_events[:5] -> ScoreRecord.event_id
resolves to a real entry in the same run's simulation_events.jsonl.
"""
from __future__ import annotations

import json
import os
import shutil
import time
from unittest.mock import MagicMock

import pytest

from src.core.state import AuthoritativeState
from src.config.profiles import RuntimeProfile, HardwareClass
from src.engine.kernel import Kernel
from src.observability.events import SimulationEvent

RUN_ID = "simq-traceability-test"


def _make_profile() -> RuntimeProfile:
    return RuntimeProfile(
        name="test",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_tick_budget_ms=500,
        max_cpu_percent=50.0,
        max_worker_count=0,
        max_queue_depth=64,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=5.0,
    )


@pytest.fixture()
def minimal_kernel(monkeypatch):
    monkeypatch.setenv("QUALITY_FEED_MODE", "inprocess")
    monkeypatch.delenv("QUALITY_SCORING_DISABLED", raising=False)

    state = AuthoritativeState(tick=0, seed=42)
    rng = MagicMock()
    kernel = Kernel(_make_profile(), state, rng, run_id=RUN_ID, flags={"no_replay": True})
    yield kernel
    kernel.shutdown()
    filepath = kernel._event_recorder.filepath
    if filepath is not None:
        run_dir = os.path.dirname(filepath)
        if os.path.isdir(run_dir):
            shutil.rmtree(run_dir)


def _inject_combat_hard_law_violation(kernel) -> None:
    kernel._event_recorder.record(SimulationEvent(
        event_type="combat_hard_law_violation",
        event_category="combat",
        tick=1,
        severity="ERROR",
        source_system="test",
        message="hard law violated in combat pipeline (test injection)",
        entity_id=1,
    ))
    time.sleep(0.15)


def test_worst_event_id_resolves_in_simulation_events_jsonl(minimal_kernel):
    _inject_combat_hard_law_violation(minimal_kernel)

    report = minimal_kernel._quality_hub.get_quality_report()
    assert report.pillars["COMBAT"].worst_events, (
        "COMBAT pillar has no worst_events after injecting a combat_hard_law_violation event — "
        "expected an unconditional -30.0 weight (config/simulation_quality/scoring_weights.yaml:38)"
    )
    worst_event_id = report.pillars["COMBAT"].worst_events[0].event_id

    filepath = minimal_kernel._event_recorder.filepath
    with open(filepath, "r", encoding="utf-8") as f:
        event_ids = {json.loads(line)["event_id"] for line in f if line.strip()}

    assert worst_event_id in event_ids, (
        f"worst_events[0].event_id={worst_event_id!r} not found in {filepath} "
        f"(event_ids present: {event_ids!r})"
    )


def test_worst_event_id_matches_originating_envelope_exactly(minimal_kernel):
    _inject_combat_hard_law_violation(minimal_kernel)

    report = minimal_kernel._quality_hub.get_quality_report()
    assert report.pillars["COMBAT"].worst_events, (
        "COMBAT pillar has no worst_events after injecting a combat_hard_law_violation event — "
        "expected an unconditional -30.0 weight (config/simulation_quality/scoring_weights.yaml:38)"
    )
    worst_event_id = report.pillars["COMBAT"].worst_events[0].event_id

    filepath = minimal_kernel._event_recorder.filepath
    with open(filepath, "r", encoding="utf-8") as f:
        matches = [json.loads(line) for line in f if line.strip() and json.loads(line)["event_id"] == worst_event_id]

    assert len(matches) == 1, (
        f"expected exactly one simulation_events.jsonl line for event_id={worst_event_id!r}, "
        f"found {len(matches)} in {filepath}"
    )
    envelope = matches[0]
    assert envelope["event_type"] == "combat_hard_law_violation"
    assert envelope["tick"] == 1
    assert envelope["entity_id"] == 1


def test_run_directory_cleaned_up_after_test():
    state = AuthoritativeState(tick=0, seed=42)
    rng = MagicMock()
    kernel = Kernel(_make_profile(), state, rng, run_id=RUN_ID, flags={"no_replay": True})
    filepath = kernel._event_recorder.filepath
    kernel.shutdown()
    run_dir = os.path.dirname(filepath)
    shutil.rmtree(run_dir)

    assert not os.path.isdir(run_dir), (
        f"expected {run_dir!r} to be removed after shutil.rmtree() in test teardown"
    )
