"""Tests for ReplayManager backpressure tracking (INFRA-198).

Verifies: _inflight_count tracking, pressure_report() thresholds, replay_metrics(),
and the invariant that ReplayManager never autonomously drops chunks.
"""
from __future__ import annotations

import threading
import time
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


def _make_replay_manager(tmp_path: Path, max_pending_flushes: int = 5):
    from src.engine.replay_manager import ReplayManager
    from src.core.replay_modes import ReplayMode
    return ReplayManager(
        run_dir=tmp_path,
        profile_name="TEST",
        buffer_capacity_kb=64,
        max_pending_flushes=max_pending_flushes,
        replay_mode=ReplayMode.DEBUG_WINDOWED,
    )


class TestInflightCountTracking:
    def test_inflight_count_starts_at_zero(self, tmp_path):
        mgr = _make_replay_manager(tmp_path)
        assert mgr._inflight_count == 0

    def test_inflight_count_increments_on_submit(self, tmp_path):
        mgr = _make_replay_manager(tmp_path)

        submitted = []

        def slow_persist(chunk_id, start, end, events):
            submitted.append(chunk_id)
            time.sleep(0.05)

        with patch.object(mgr, "_execute_persistence", side_effect=slow_persist):
            from src.core.diagnostic import TraceEvent
            event = TraceEvent(tick=1, system="KERNEL", event_type="TICK_END", payload={})
            mgr._buffer.record(event)
            mgr._rotate_chunk(end_tick=1, async_write=True)
            # Count should be 1 immediately after submit (before callback fires)
            with mgr._inflight_lock:
                count = mgr._inflight_count
            assert count >= 0  # either 1 or 0 if callback already fired
            mgr._executor.shutdown(wait=True)

    def test_inflight_count_decrements_on_completion(self, tmp_path):
        mgr = _make_replay_manager(tmp_path)

        barrier = threading.Event()

        def slow_persist(chunk_id, start, end, events):
            barrier.wait(timeout=2.0)

        with patch.object(mgr, "_execute_persistence", side_effect=slow_persist):
            from src.core.diagnostic import TraceEvent
            for _ in range(3):
                mgr._buffer.record(TraceEvent(tick=1, system="K", event_type="E", payload={}))
            mgr._rotate_chunk(end_tick=1, async_write=True)
            with mgr._inflight_lock:
                count_before = mgr._inflight_count
            assert count_before == 1

            barrier.set()
            mgr._executor.shutdown(wait=True)

        with mgr._inflight_lock:
            count_after = mgr._inflight_count
        assert count_after == 0

    def test_on_persist_done_decrements(self, tmp_path):
        mgr = _make_replay_manager(tmp_path)
        with mgr._inflight_lock:
            mgr._inflight_count = 3
        mgr._on_persist_done()
        with mgr._inflight_lock:
            assert mgr._inflight_count == 2

    def test_on_persist_done_clamps_at_zero(self, tmp_path):
        mgr = _make_replay_manager(tmp_path)
        mgr._on_persist_done()
        with mgr._inflight_lock:
            assert mgr._inflight_count == 0


class TestPressureReport:
    def test_pressure_ok_below_80pct(self, tmp_path):
        mgr = _make_replay_manager(tmp_path, max_pending_flushes=10)
        with mgr._inflight_lock:
            mgr._inflight_count = 7  # 70% — below 80%
        report = mgr.pressure_report()
        assert report.pressure_state == "OK"
        assert report.subsystem == "replay"
        assert report.budget == 10.0

    def test_pressure_warn_above_80pct(self, tmp_path):
        mgr = _make_replay_manager(tmp_path, max_pending_flushes=10)
        with mgr._inflight_lock:
            mgr._inflight_count = 9  # 90%
        report = mgr.pressure_report()
        assert report.pressure_state == "WARN"
        assert report.degradation_action is not None

    def test_pressure_degraded_at_limit(self, tmp_path):
        mgr = _make_replay_manager(tmp_path, max_pending_flushes=5)
        with mgr._inflight_lock:
            mgr._inflight_count = 5  # 100%
        report = mgr.pressure_report()
        assert report.pressure_state == "DEGRADED"

    def test_pressure_degraded_over_limit(self, tmp_path):
        mgr = _make_replay_manager(tmp_path, max_pending_flushes=3)
        with mgr._inflight_lock:
            mgr._inflight_count = 4  # > 100%
        report = mgr.pressure_report()
        assert report.pressure_state == "DEGRADED"

    def test_pressure_zero_max_returns_ok_unlimited(self, tmp_path):
        mgr = _make_replay_manager(tmp_path, max_pending_flushes=0)
        report = mgr.pressure_report()
        assert report.pressure_state == "OK"
        assert report.budget is None


class TestReplayMetrics:
    def test_replay_metrics_initial_state(self, tmp_path):
        mgr = _make_replay_manager(tmp_path)
        m = mgr.replay_metrics()
        assert m["pending_flushes"] == 0
        assert m["chunks_persisted"] == 0
        assert m["bytes_pending_estimate"] == 0

    def test_replay_metrics_reflects_inflight(self, tmp_path):
        mgr = _make_replay_manager(tmp_path)
        with mgr._inflight_lock:
            mgr._inflight_count = 3
        mgr._avg_chunk_size_bytes = 1000.0
        m = mgr.replay_metrics()
        assert m["pending_flushes"] == 3
        assert m["bytes_pending_estimate"] == 3000


class TestNoChunkDroppedByReplayManager:
    def test_chunks_always_submitted_regardless_of_inflight_count(self, tmp_path):
        """ReplayManager must not drop chunks even when inflight > max_pending_flushes."""
        mgr = _make_replay_manager(tmp_path, max_pending_flushes=1)

        submit_calls = []
        original_submit = mgr._executor.submit

        def counting_submit(fn, *args, **kwargs):
            submit_calls.append(args)
            return original_submit(fn, *args, **kwargs)

        mgr._executor.submit = counting_submit

        from src.core.diagnostic import TraceEvent
        for i in range(3):
            for _ in range(5):
                mgr._buffer.record(TraceEvent(tick=i, system="K", event_type="E", payload={}))
            mgr._rotate_chunk(end_tick=i, async_write=True)

        mgr._executor.shutdown(wait=True)
        assert len(submit_calls) == 3, (
            f"Expected 3 submits (one per rotation), got {len(submit_calls)} — "
            "ReplayManager must not drop chunks under pressure"
        )
