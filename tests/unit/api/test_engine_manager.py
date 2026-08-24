"""
Unit tests for V2EngineManager's engine-liveness accessors and health computation
(TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC), plus total_spawned/total_deaths counters
(TCK-20260821-REST-MAP-STATIC-STATS).

Covers:
- `is_thread_alive` reflecting the real background thread's lifecycle.
- `get_health_status()`'s three states: unhealthy (dead thread), degraded (stale tick while
  alive and not paused), ok (healthy, or paused-but-stale which must NOT be degraded).
- `total_spawned`/`total_deaths` incremented once per tick via a new_ids/dead_ids set-diff on
  `state.entities.keys()`, and zeroed by `reset()`.
"""
import dataclasses
import time
from unittest.mock import patch

from src.api.engine_manager import V2EngineManager
from src.config.profiles import PROD_DEFAULT
from src.core.builder import V2EntityBuilder
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


def _make_entity(eid: int):
    return (
        V2EntityBuilder(eid)
        .kind("goblin")
        .location(0.0, 0.0)
        .combat(hp=10, max_hp=10, atk=1, def_stat=1, attack_range=1, alive=True, readiness=100.0)
        .inventory(gold=0)
        .build()
    )


def test_engine_manager_total_spawned_incremented_on_new_entity():
    """Kernel.tick_once must be patched at the class level, not the instance -- Kernel uses
    __slots__ (see test_get_health_status_killed_thread_reports_unhealthy_realistic above)."""
    manager = V2EngineManager(PROD_DEFAULT, seed=42, entities_count=3)
    spawned = {"done": False}

    def _side_effect():
        old = manager._kernel._state
        if not spawned["done"]:
            spawned["done"] = True
            entities = dict(old.entities)
            entities[999901] = _make_entity(999901)
            manager._kernel._state = dataclasses.replace(old, entities=entities, tick=old.tick + 1)
        else:
            manager._kernel._state = dataclasses.replace(old, tick=old.tick + 1)

    try:
        with patch.object(Kernel, "tick_once", side_effect=_side_effect):
            manager.start()
            assert _poll_until(lambda: manager.total_spawned >= 1)
            assert manager.total_spawned == 1
            assert manager.total_deaths == 0
    finally:
        manager.stop()


def test_engine_manager_total_deaths_incremented_on_removed_entity():
    manager = V2EngineManager(PROD_DEFAULT, seed=42, entities_count=3)
    removed = {"done": False}

    def _side_effect():
        old = manager._kernel._state
        if not removed["done"]:
            removed["done"] = True
            removed_id = next(iter(old.entities))
            entities = {k: v for k, v in old.entities.items() if k != removed_id}
            manager._kernel._state = dataclasses.replace(old, entities=entities, tick=old.tick + 1)
        else:
            manager._kernel._state = dataclasses.replace(old, tick=old.tick + 1)

    try:
        with patch.object(Kernel, "tick_once", side_effect=_side_effect):
            manager.start()
            assert _poll_until(lambda: manager.total_deaths >= 1)
            assert manager.total_deaths == 1
            assert manager.total_spawned == 0
    finally:
        manager.stop()


def test_engine_manager_reset_zeroes_spawn_death_counters():
    manager = V2EngineManager(PROD_DEFAULT, seed=42, entities_count=3)
    spawned = {"done": False}

    def _side_effect():
        old = manager._kernel._state
        if not spawned["done"]:
            spawned["done"] = True
            entities = dict(old.entities)
            entities[999902] = _make_entity(999902)
            manager._kernel._state = dataclasses.replace(old, entities=entities, tick=old.tick + 1)
        else:
            manager._kernel._state = dataclasses.replace(old, tick=old.tick + 1)

    try:
        with patch.object(Kernel, "tick_once", side_effect=_side_effect):
            manager.start()
            assert _poll_until(lambda: manager.total_spawned >= 1)

        manager.reset()
        assert manager.total_spawned == 0
        assert manager.total_deaths == 0
    finally:
        # reset()'s _build() constructs a fresh Kernel (new QueueDrainWorker threads) --
        # must stop() again or those threads leak past this test.
        manager.stop()


def test_stats_counters_non_decreasing_across_ticks():
    manager = V2EngineManager(PROD_DEFAULT, seed=42, entities_count=3)
    remaining_ids = iter([999903, 999904, 999905])

    def _side_effect():
        old = manager._kernel._state
        new_id = next(remaining_ids, None)
        if new_id is None:
            manager._kernel._state = dataclasses.replace(old, tick=old.tick + 1)
            return
        entities = dict(old.entities)
        entities[new_id] = _make_entity(new_id)
        manager._kernel._state = dataclasses.replace(old, entities=entities, tick=old.tick + 1)

    try:
        with patch.object(Kernel, "tick_once", side_effect=_side_effect):
            manager.start()
            samples = []
            for _ in range(3):
                last = samples[-1] if samples else -1
                assert _poll_until(lambda: manager.total_spawned > last)
                samples.append(manager.total_spawned)
            assert samples == sorted(samples)
            assert samples[-1] == 3
    finally:
        manager.stop()
