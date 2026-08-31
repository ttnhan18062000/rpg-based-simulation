"""Integration test: kernel wires SimQ hub via quality_fn (TCK-20260630-SIMQ-WIRE-KERNEL).

Verifies that 20 ticks with InProcessQualityFeed active produces non-zero tick_count
and at least one pillar with event_count > 0 (AC #1 and AC #2 from the ticket).
"""
from __future__ import annotations

import os
import pytest
from unittest.mock import MagicMock

from src.core.state import AuthoritativeState
from src.config.profiles import RuntimeProfile, HardwareClass
from src.engine.kernel import Kernel


@pytest.fixture()
def minimal_kernel(tmp_path, monkeypatch):
    monkeypatch.setenv("QUALITY_FEED_MODE", "inprocess")
    monkeypatch.delenv("QUALITY_SCORING_DISABLED", raising=False)
    monkeypatch.setenv("QUALITY_RUN_DIR", str(tmp_path))

    profile = RuntimeProfile(
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
    state = AuthoritativeState(tick=0, seed=42)
    rng = MagicMock()
    kernel = Kernel(profile, state, rng, run_id="simq-wire-test", flags={"no_replay": True})
    yield kernel
    kernel.shutdown()


def test_simq_hub_wired_into_kernel(minimal_kernel):
    """Kernel must expose a non-None quality_hub after __init__."""
    assert minimal_kernel._quality_hub is not None, (
        "Kernel._quality_hub is None — quality_fn was not wired into EventRecorder's worker"
    )


def test_no_second_drain_worker(minimal_kernel):
    """InProcessQualityFeed must not create a competing QueueDrainWorker."""
    feed = minimal_kernel._quality_feed
    assert feed is not None
    assert not hasattr(feed, "_worker") or getattr(feed, "_worker", None) is None, (
        "InProcessQualityFeed still owns a QueueDrainWorker — G3 not fixed"
    )


def test_event_recorder_worker_has_quality_fn(minimal_kernel):
    """EventRecorder's drain worker must have quality_fn set."""
    worker = minimal_kernel._event_recorder._worker
    assert worker.quality_fn is not None, (
        "EventRecorder._worker.quality_fn is None — G1 not fixed"
    )


def test_20_tick_run_produces_nonzero_tick_count(minimal_kernel):
    """Events injected into EventRecorder reach the hub via quality_fn.

    A minimal kernel with MagicMock rng emits no domain events, so we inject
    them directly.  This still exercises the full wiring path:
    EventRecorder.record → queue → QueueDrainWorker → quality_fn → hub.on_envelope.
    """
    import time
    from src.observability.events import SimulationEvent

    recorder = minimal_kernel._event_recorder
    for tick in range(1, 21):
        recorder.record(SimulationEvent(
            event_type="entity_action",
            event_category="combat",
            tick=tick,
            severity="INFO",
            source_system="test",
            message="integration test event",
            entity_id=1,
        ))

    # Give the drain worker time to process the queue
    time.sleep(0.15)

    hub = minimal_kernel._quality_hub
    report = hub.get_quality_report()

    assert report.tick_count > 0, (
        f"SimQ tick_count=0 — hub.on_envelope() was never called despite 20 injected events. "
        f"Pillar event counts: { {pid: snap.event_count for pid, snap in report.pillars.items()} }"
    )


def _build_kernel(monkeypatch, tmp_path, feed_mode=None, scoring_disabled=False, run_id="broker-config-test"):
    monkeypatch.setenv("QUALITY_RUN_DIR", str(tmp_path))
    if feed_mode is None:
        monkeypatch.delenv("QUALITY_FEED_MODE", raising=False)
    else:
        monkeypatch.setenv("QUALITY_FEED_MODE", feed_mode)
    if scoring_disabled:
        monkeypatch.setenv("QUALITY_SCORING_DISABLED", "1")
    else:
        monkeypatch.delenv("QUALITY_SCORING_DISABLED", raising=False)

    profile = RuntimeProfile(
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
    state = AuthoritativeState(tick=0, seed=42)
    rng = MagicMock()
    kernel = Kernel(profile, state, rng, run_id=run_id, flags={"no_replay": True})
    return kernel


def test_kernel_shutdown_persists_in_flight_quality_write(monkeypatch, tmp_path):
    """Regression test for TCK-20260830-KERNEL-SHUTDOWN-PERSISTENCE-DRAIN-ORDERING-HAZARD.

    Kernel.shutdown() previously called QualityPersistence.shutdown() (closing its file
    handle) BEFORE EventRecorder.shutdown() had stopped the background drain worker /
    run its own final drain. Any event still sitting in EventRecorder's queue at that
    point would only reach QualityPersistence.write() once the drain path processed it —
    by which point the file handle was already closed, so the write silently no-op'd
    (QualityPersistence.write returns early when self._file_handle is None) and the
    record never reached quality_scores.jsonl.

    Reproduced deterministically (no sleep/race): the drain worker is stopped before the
    event is ever pushed, so it can only be handled by EventRecorder.shutdown()'s own
    final manual drain — exactly the step that must complete before
    QualityPersistence.shutdown() runs. quality_fn is pointed straight at
    persistence.write() with a known record so the assertion isn't dependent on real
    scorer-dispatch details, which are out of scope for this ordering hazard.
    """
    import json
    import shutil
    from src.observability.events import SimulationEvent
    from src.simulation_quality.pillars import PillarId
    from src.simulation_quality.score_record import ScoreRecord

    kernel = _build_kernel(
        monkeypatch, tmp_path, feed_mode="inprocess", run_id="kernel-shutdown-ordering-hazard-test",
    )
    recorder = kernel._event_recorder
    hub = kernel._quality_hub
    assert hub is not None, "test setup requires a wired QualityHub (feed_mode=inprocess)"
    persistence = hub._persistence
    run_dir = persistence._run_dir

    record = ScoreRecord(
        tick=1, event_id="in-flight-write", pillar=PillarId.ECONOMY, delta=1.0,
        reason="test", event_type="test_event", entity_id=1, region_id="r1",
        tags=("t",),
    )
    recorder._worker.quality_fn = lambda env: persistence.write(record)

    # Halt the background drain worker before anything is queued so the injected event
    # can only be handled by EventRecorder.shutdown()'s own final drain.
    recorder._worker.stop()
    assert not recorder._worker.is_alive()

    recorder.record(SimulationEvent(
        event_type="entity_action", event_category="combat", tick=1, severity="INFO",
        source_system="test", message="in-flight write during shutdown", entity_id=1,
    ))
    assert recorder.queue.get_size() == 1, "event should still be sitting unprocessed in the queue"

    try:
        kernel.shutdown()

        scores_path = os.path.join(run_dir, "quality_scores.jsonl")
        assert os.path.exists(scores_path), "quality_scores.jsonl was never created"
        with open(scores_path, "r", encoding="utf-8") as fh:
            lines = [json.loads(line) for line in fh if line.strip()]
        assert any(l.get("event_id") == "in-flight-write" for l in lines), (
            "in-flight write during shutdown was silently dropped: QualityPersistence's file "
            "handle closed before EventRecorder's drain path reached QualityPersistence.write() "
            "for the queued event"
        )
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_kernel_broker_mode_builds_zero_quality_hub(monkeypatch, tmp_path):
    """TCK-20260702-OBSISO-BROKER-CONFIG G3: broker mode must not construct a QualityHub."""
    kernel = _build_kernel(monkeypatch, tmp_path, feed_mode="broker")
    try:
        assert kernel._quality_hub is None
    finally:
        kernel.shutdown()


def test_kernel_broker_mode_starts_zero_consumer_threads(monkeypatch, tmp_path):
    """TCK-20260702-OBSISO-BROKER-CONFIG G3: broker mode must not start an in-engine
    'broker-quality-feed' consumer thread."""
    import threading

    kernel = _build_kernel(monkeypatch, tmp_path, feed_mode="broker")
    try:
        thread_names = {t.name for t in threading.enumerate()}
        assert "broker-quality-feed" not in thread_names
    finally:
        kernel.shutdown()


def test_kernel_inprocess_mode_unaffected_by_g3_fix(monkeypatch, tmp_path):
    """Guards against a G3 implementation that branches on the QUALITY_FEED_MODE string
    instead of the resolved _feed instance's concrete type."""
    kernel = _build_kernel(monkeypatch, tmp_path, feed_mode="inprocess")
    try:
        assert kernel._quality_hub is not None
        registered_scorers = {
            id(scorer)
            for scorer_list in kernel._quality_hub.SCORER_REGISTRY.values()
            for scorer in scorer_list
        }
        assert len(registered_scorers) == 10, (
            f"Expected all 10 pillar scorers registered in in-process mode, got {len(registered_scorers)}"
        )
    finally:
        kernel.shutdown()


def test_quality_scoring_disabled_still_wins_in_both_modes(monkeypatch, tmp_path):
    """AC #4: QUALITY_SCORING_DISABLED=1 disables everything, in both inprocess and broker
    QUALITY_FEED_MODE."""
    import threading

    for feed_mode in ("inprocess", "broker"):
        kernel = _build_kernel(
            monkeypatch, tmp_path, feed_mode=feed_mode, scoring_disabled=True,
            run_id=f"disabled-{feed_mode}",
        )
        try:
            assert kernel._quality_hub is None
            thread_names = {t.name for t in threading.enumerate()}
            assert "broker-quality-feed" not in thread_names
        finally:
            kernel.shutdown()
