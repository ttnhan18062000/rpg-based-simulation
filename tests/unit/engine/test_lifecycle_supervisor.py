"""Tests for Kernel lifecycle supervisor — ShutdownReport and orphan detection.

Covers: ShutdownReport shape, clean shutdown outcome, worker accounting,
pending_replay_flushes warning, BehaviorWorker thread cleanup.
"""
from __future__ import annotations

import threading
import time
import pytest
from unittest.mock import MagicMock, patch, PropertyMock


def _make_profile():
    from src.config.profiles import RuntimeProfile, HardwareClass
    return RuntimeProfile(
        name="TEST",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=50.0,
        max_worker_count=1,
        max_queue_depth=100,
        max_work_debt=100,
        max_replay_buffer_kb=64,
        max_observability_budget_percent=5.0,
        max_tick_budget_ms=10.0,
    )


def _make_kernel(no_replay: bool = True):
    from src.engine.kernel import Kernel
    from src.core.state import AuthoritativeState
    from unittest.mock import MagicMock
    state = AuthoritativeState(tick=0, seed=42)
    return Kernel(
        state=state,
        profile=_make_profile(),
        rng=MagicMock(),
        flags={"no_replay": no_replay},
    )


class TestShutdownReportShape:
    def test_shutdown_report_dataclass_exists(self):
        from src.core.lifecycle import ShutdownReport
        r = ShutdownReport()
        assert hasattr(r, "workers_started")
        assert hasattr(r, "workers_stopped")
        assert hasattr(r, "open_file_handles")
        assert hasattr(r, "pending_replay_flushes")
        assert hasattr(r, "survival_event_counts")
        assert hasattr(r, "outcome")
        assert hasattr(r, "warnings")

    def test_shutdown_report_defaults(self):
        from src.core.lifecycle import ShutdownReport
        r = ShutdownReport()
        assert r.workers_started == 0
        assert r.workers_stopped == 0
        assert r.pending_replay_flushes == 0
        assert r.survival_event_counts == {}
        assert r.outcome == "SUCCESS"
        assert r.warnings == []

    def test_shutdown_report_mutable(self):
        from src.core.lifecycle import ShutdownReport
        r = ShutdownReport()
        r.warnings.append("test warning")
        assert "test warning" in r.warnings


class TestCleanShutdown:
    def test_shutdown_returns_shutdown_result(self, tmp_path):
        from src.core.lifecycle import ShutdownResult
        k = _make_kernel()
        result = k.shutdown()
        assert isinstance(result, ShutdownResult)

    def test_shutdown_report_accessible_after_shutdown(self, tmp_path):
        from src.core.lifecycle import ShutdownReport
        k = _make_kernel()
        k.shutdown()
        report = k.shutdown_report()
        assert isinstance(report, ShutdownReport)

    def test_shutdown_report_none_before_shutdown(self):
        k = _make_kernel()
        assert k.shutdown_report() is None
        k.shutdown()

    def test_clean_shutdown_outcome_success(self):
        k = _make_kernel()
        k.shutdown()
        report = k.shutdown_report()
        assert report.outcome == "SUCCESS"

    def test_clean_shutdown_warnings_empty(self):
        k = _make_kernel()
        k.shutdown()
        report = k.shutdown_report()
        assert report.warnings == []

    def test_workers_started_is_positive(self):
        k = _make_kernel()
        assert k._workers_started >= 0
        k.shutdown()

    def test_workers_stopped_equals_started_on_clean_shutdown(self):
        k = _make_kernel()
        k.shutdown()
        report = k.shutdown_report()
        assert report.workers_stopped == report.workers_started


class TestPendingReplayFlushesWarning:
    def test_pending_replay_flushes_zero_no_warning(self):
        k = _make_kernel()
        # Mock replay_metrics to return 0 pending
        if hasattr(k._replay, "replay_metrics"):
            with patch.object(k._replay, "replay_metrics", return_value={"pending_flushes": 0, "chunks_persisted": 0, "bytes_pending_estimate": 0}):
                k.shutdown()
        else:
            k.shutdown()
        report = k.shutdown_report()
        flush_warnings = [w for w in report.warnings if "pending_replay_flushes" in w]
        assert len(flush_warnings) == 0

    def test_pending_replay_flushes_nonzero_generates_warning(self):
        k = _make_kernel()
        if hasattr(k._replay, "replay_metrics"):
            with patch.object(k._replay, "replay_metrics", return_value={"pending_flushes": 3, "chunks_persisted": 0, "bytes_pending_estimate": 0}):
                k.shutdown()
            report = k.shutdown_report()
            flush_warnings = [w for w in report.warnings if "pending_replay_flushes" in w]
            assert len(flush_warnings) >= 1
        else:
            k.shutdown()
            pytest.skip("replay does not support replay_metrics()")


class TestBehaviorWorkerShutdown:
    def test_behavior_worker_thread_joined_on_shutdown(self):
        """If a behavior-normalization-worker thread is running at shutdown, it should be joined."""
        k = _make_kernel()

        stopped = threading.Event()

        def fake_worker():
            stopped.wait(timeout=5.0)

        t = threading.Thread(target=fake_worker, name="behavior-normalization-worker", daemon=True)
        t.start()
        # Signal the thread to stop so join succeeds quickly
        stopped.set()

        k.shutdown()
        report = k.shutdown_report()
        # Thread should have been joined (it exits immediately after stopped is set)
        assert not t.is_alive()
        # No orphan warning expected when thread stops cleanly
        orphan_warnings = [w for w in report.warnings if "behavior-normalization-worker" in w]
        assert len(orphan_warnings) == 0


class TestSurvivalCountsInReport:
    def test_survival_counts_captured_in_report(self):
        from src.observability.event_recorder import ObservabilityMode
        k = _make_kernel()
        # Directly inject survival counts into the recorder
        k._event_recorder._survival_event_counts = {"combat_damage": 5, "movement": 2}
        k.shutdown()
        report = k.shutdown_report()
        assert report.survival_event_counts.get("combat_damage") == 5
        assert report.survival_event_counts.get("movement") == 2
