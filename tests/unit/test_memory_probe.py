"""
Smoke tests for tests/tools/memory_probe.py helpers.

Verifies:
- The module is importable without memray.
- A clean EventRecorder lifecycle produces worker_count_delta == 0.
- assert_no_worker_leak raises AssertionError with a clear message when a leak is detected.
"""
from __future__ import annotations

import pytest

from tests.tools.memory_probe import (
    assert_no_worker_leak,
    count_drain_workers,
    snapshot_end,
    snapshot_start,
)


class TestCleanLifecycleNoWorkerLeak:
    def test_clean_recorder_no_worker_leak(self) -> None:
        """
        Creating an EventRecorder with enabled=True starts a QueueDrainWorker thread.
        Calling shutdown() must stop that thread. Worker count delta must be zero.
        """
        from src.observability.event_recorder import EventRecorder

        start = snapshot_start()
        recorder = EventRecorder(enabled=True)
        recorder.shutdown()
        report = snapshot_end(start)

        assert report.worker_count_delta == 0, (
            f"Expected 0 worker thread delta after clean shutdown, got {report.worker_count_delta}. "
            "QueueDrainWorker thread was not stopped properly."
        )


class TestAssertNoWorkerLeakHelper:
    def test_no_raise_when_equal(self) -> None:
        """assert_no_worker_leak must not raise when before == after."""
        assert_no_worker_leak(0, 0)
        assert_no_worker_leak(3, 3)

    def test_raises_when_after_greater(self) -> None:
        """assert_no_worker_leak must raise AssertionError with count info when after > before."""
        with pytest.raises(AssertionError) as exc_info:
            assert_no_worker_leak(0, 1)
        msg = str(exc_info.value)
        assert "1" in msg, f"Expected '1' in AssertionError message, got: {msg}"
        assert "0" in msg, f"Expected '0' (before) in AssertionError message, got: {msg}"

    def test_raises_with_larger_delta(self) -> None:
        """Error message must include the actual after-count for multi-leak scenarios."""
        with pytest.raises(AssertionError) as exc_info:
            assert_no_worker_leak(1, 4)
        msg = str(exc_info.value)
        assert "4" in msg
        assert "1" in msg
