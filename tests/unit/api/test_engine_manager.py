"""
Unit tests for V2EngineManager's engine-liveness accessors and health computation
(TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC).

Covers:
- `is_thread_alive` reflecting the real background thread's lifecycle.
- `get_health_status()`'s three states: unhealthy (dead thread), degraded (stale tick while
  alive and not paused), ok (healthy, or paused-but-stale which must NOT be degraded).
"""
import time
from unittest.mock import patch

from src.api.engine_manager import V2EngineManager
from src.config.profiles import PROD_DEFAULT
from src.engine.kernel import Kernel


def _poll_until(predicate, timeout=2.0, interval=0.01):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


def test_is_thread_alive_reflects_real_thread_state():
    manager = V2EngineManager(PROD_DEFAULT, seed=42, entities_count=3)
    try:
        assert manager.is_thread_alive is False
        manager.start()
        assert manager.is_thread_alive is True
    finally:
        manager.stop()
    assert manager.is_thread_alive is False


def test_last_tick_age_seconds_uses_tick_times_then_started_at_fallback():
    manager = V2EngineManager(PROD_DEFAULT, seed=42, entities_count=3)
    try:
        assert manager.last_tick_age_seconds is None

        manager.start()
        # Before the first tick completes, falls back to started_at.
        assert manager.last_tick_age_seconds is not None

        assert _poll_until(lambda: len(manager._tick_times) > 0)
        age_from_tick = manager.last_tick_age_seconds
        assert age_from_tick is not None
        assert age_from_tick < 2.0
    finally:
        manager.stop()


def test_get_health_status_killed_thread_reports_unhealthy_synthetic():
    manager = V2EngineManager(PROD_DEFAULT, seed=42, entities_count=3)
    real_thread = None
    try:
        manager.start()
        assert _poll_until(lambda: len(manager._tick_times) > 0)
        real_thread = manager._thread

        class _DeadThread:
            def is_alive(self):
                return False

        manager._thread = _DeadThread()
        status = manager.get_health_status()
        assert status["status"] == "unhealthy"
        assert status["engine"]["thread_alive"] is False
    finally:
        manager._thread = real_thread
        manager.stop()


def test_get_health_status_killed_thread_reports_unhealthy_realistic():
    manager = V2EngineManager(PROD_DEFAULT, seed=42, entities_count=3)
    try:
        manager.start()
        assert _poll_until(lambda: len(manager._tick_times) > 0)

        # Kernel uses __slots__, so tick_once must be patched at the class level,
        # not reassigned on the instance.
        with patch.object(Kernel, "tick_once", side_effect=RuntimeError("simulated kernel failure")):
            assert _poll_until(lambda: not manager._thread.is_alive())
            status = manager.get_health_status()
            assert status["status"] == "unhealthy"
            assert manager.errors_total >= 1
    finally:
        manager.stop()


def test_get_health_status_stale_tick_reports_degraded():
    manager = V2EngineManager(PROD_DEFAULT, seed=42, entities_count=3)
    try:
        manager.start()
        assert _poll_until(lambda: len(manager._tick_times) > 0)

        with manager._state_lock:
            manager._tick_times.append(time.time() - 10.0)

        status = manager.get_health_status()
        assert status["status"] == "degraded"
        assert status["engine"]["thread_alive"] is True
        assert status["engine"]["paused"] is False
    finally:
        manager.stop()


def test_get_health_status_paused_stays_ok():
    manager = V2EngineManager(PROD_DEFAULT, seed=42, entities_count=3)
    try:
        manager.start()
        assert _poll_until(lambda: len(manager._tick_times) > 0)
        manager.pause()

        with manager._state_lock:
            manager._tick_times.append(time.time() - 10.0)

        status = manager.get_health_status()
        assert status["status"] == "ok"
        assert status["engine"]["paused"] is True
    finally:
        manager.stop()
