"""The event file keeps every event that passed the mode filter, whatever the in-memory buffer does.

``record()`` used to return BEFORE the queue push when the 5000-event buffer held only CRITICAL events, so every later non-critical event never reached
the file or the SimQ feed (and neither did the shutdown tally events the rpg gate reads). The buffer is now a diagnostic view: it evicts, and each
eviction is counted in ``buffer_evicted_count``, but the queue push always happens.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from src.observability.event_recorder import EventRecorder
from src.observability.events import SimulationEvent

GATE_TALLIES = ("rpg_gate_ledger_tally", "death_ledger_tally", "starvation_channel_tally")


def _ev(tick: int, severity: str, event_type: str = "test_event") -> SimulationEvent:
    return SimulationEvent(event_type=event_type, event_category="lifecycle", tick=tick, severity=severity, source_system="test", message="", entity_id=1)


def _recorder(run_dir: str, max_events: int, quality=None) -> EventRecorder:
    recorder = EventRecorder(run_dir=run_dir, max_events=max_events, enabled=True, quality_fn=quality)
    recorder.queue.max_size = 100_000  # the queue is not under test here: only the in-memory buffer is small
    return recorder


def _file_events(recorder: EventRecorder):
    return [json.loads(line) for line in Path(recorder.filepath).read_text(encoding="utf-8").splitlines()]


@pytest.fixture
def run_dir(tmp_path):
    path = tmp_path / "run"
    yield str(path)
    shutil.rmtree(path, ignore_errors=True)


def test_a_buffer_full_of_critical_events_still_sends_every_later_event_to_the_file_and_the_quality_feed(run_dir):
    seen = []
    recorder = _recorder(run_dir, max_events=5, quality=lambda env: seen.append(env.event_type))
    for tick in range(5):
        recorder.record(_ev(tick, "CRITICAL", "crit"))
    for tick in range(5, 15):
        recorder.record(_ev(tick, "INFO", "info") if tick % 2 else _ev(tick, "WARNING", "warn"))
    recorder.shutdown()
    on_file = [e["event_type"] for e in _file_events(recorder)]
    assert on_file.count("crit") == 5 and on_file.count("info") == 5 and on_file.count("warn") == 5
    assert seen.count("info") == 5 and seen.count("warn") == 5
    assert len(recorder.events) == 5 and all(e.severity == "CRITICAL" for e in recorder.events)  # the buffer stayed bounded


def test_the_three_gate_shutdown_tallies_survive_a_buffer_full_of_critical_events(run_dir, monkeypatch):
    recorder = _recorder(run_dir, max_events=4)
    for tick in range(4):
        recorder.record(_ev(tick, "CRITICAL", "crit"))
    tallies = [lambda counts, name=name: SimulationEvent(event_type=name, event_category="lifecycle", tick=9, severity="WARNING", source_system="test", message="", payload={"n": 1})
               for name in GATE_TALLIES]
    monkeypatch.setattr(EventRecorder, "closing_event_sources", tallies)
    recorder.shutdown()
    assert {e["event_type"] for e in _file_events(recorder)} >= set(GATE_TALLIES)


def test_the_eviction_counter_counts_only_buffer_evictions(run_dir):
    recorder = _recorder(run_dir, max_events=3)
    for tick in range(10):
        recorder.record(_ev(tick, "INFO"))
    recorder.shutdown()
    assert recorder.buffer_evicted_count == 7 and recorder.dropped_event_count == 7
    assert recorder._events_dropped_by_mode == 0 and recorder.queue.dropped_count == 0
    assert len(_file_events(recorder)) == 10  # evicted from memory, not lost from the file
    assert recorder.get_stats()["buffer_evicted_count"] == 7


def test_an_incoming_critical_event_replaces_the_oldest_when_the_buffer_holds_only_critical_events(run_dir):
    recorder = _recorder(run_dir, max_events=2)
    for tick in range(3):
        recorder.record(_ev(tick, "CRITICAL", f"c{tick}"))
    recorder.shutdown()
    assert [e.event_type for e in recorder.events] == ["c1", "c2"]
    assert recorder.buffer_evicted_count == 1
    assert [e["event_type"] for e in _file_events(recorder)] == ["c0", "c1", "c2"]


def test_the_lowest_severity_present_is_evicted_first_and_the_counts_follow_the_buffer(run_dir):
    recorder = _recorder(run_dir, max_events=3)
    for sev, name in (("WARNING", "w"), ("DEBUG", "d"), ("INFO", "i")):
        recorder.record(_ev(1, sev, name))
    recorder.record(_ev(2, "INFO", "i2"))
    assert sorted(e.event_type for e in recorder.events) == ["i", "i2", "w"]  # the DEBUG one went
    recorder.events.clear()  # something replaced the buffer from outside: the per-severity counts must heal
    for tick in range(3):
        recorder.record(_ev(tick, "INFO", f"n{tick}"))
    recorder.record(_ev(9, "INFO", "n9"))
    assert [e.event_type for e in recorder.events] == ["n1", "n2", "n9"]
    recorder.shutdown()


@pytest.mark.slow
def test_a_full_mode_kernel_run_keeps_every_non_critical_event_in_the_file(tmp_path, monkeypatch):
    """A real FULL-mode run with a 25-event buffer (so the buffer is permanently full): the file holds exactly what the recorder counted."""
    from src.observability.config import ObservabilityConfig, ObservabilityMode
    from tools.test_architecture.rpg_gate_run import build_kernel

    ObservabilityConfig.set_override_mode(ObservabilityMode.FULL)
    run_id = "lossless_file_test"
    kernel = None
    try:
        kernel = build_kernel("urban_political", 42, run_id)
        kernel.event_recorder.max_events = 25
        for _ in range(60):
            kernel.tick_once()
        recorder = kernel.event_recorder
        counted = dict(recorder.event_count_by_type)
        evicted = recorder.buffer_evicted_count
        kernel.shutdown()
        on_file = {}
        for event in _file_events(recorder):
            on_file[event["event_type"]] = on_file.get(event["event_type"], 0) + 1
    finally:
        ObservabilityConfig.set_override_mode(None)
        shutil.rmtree(Path("data") / "runs" / run_id, ignore_errors=True)
    assert sum(counted.values()) > 25 and evicted > 0
    for event_type, n in counted.items():
        assert on_file.get(event_type, 0) == n, f"{event_type}: {n} recorded, {on_file.get(event_type, 0)} in the file"
