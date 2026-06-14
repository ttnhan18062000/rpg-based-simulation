"""Tests for ObservabilityController and EventRecorder dynamic mode switching (OBS-BACKPRESSURE).

Covers: mode enum, controller.evaluate() thresholds, record() behavior per mode,
observability_status() accuracy, and reset_mode() cleanup.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, PropertyMock


def _make_event(severity: str = "INFO", event_type: str = "test_event"):
    from src.observability.events import SimulationEvent
    return SimulationEvent(
        event_id="evt-1",
        run_id="run-1",
        tick=1,
        entity_id=1,
        event_type=event_type,
        event_category="combat",
        severity=severity,
        source_system="TEST",
        message="test message",
        payload={},
        related_entity_ids=[],
    )


def _make_recorder(max_events: int = 100, enabled: bool = True):
    from src.observability.event_recorder import EventRecorder
    rec = EventRecorder(run_dir=None, max_events=max_events, enabled=enabled)
    rec._worker.stop()
    return rec


def _set_queue_fill(recorder, ratio: float) -> None:
    """Force queue fill ratio by manipulating mock queue state."""
    max_q = recorder.queue.max_size
    target_size = int(ratio * max_q)
    recorder.queue.get_size = lambda: target_size


class TestObservabilityMode:
    def test_mode_enum_values(self):
        from src.observability.event_recorder import ObservabilityMode
        assert ObservabilityMode.NORMAL.value == "NORMAL"
        assert ObservabilityMode.PRESSURE.value == "PRESSURE"
        assert ObservabilityMode.DEGRADED.value == "DEGRADED"
        assert ObservabilityMode.SURVIVAL.value == "SURVIVAL"

    def test_mode_is_str_enum(self):
        from src.observability.event_recorder import ObservabilityMode
        assert isinstance(ObservabilityMode.NORMAL, str)


class TestObservabilityController:
    def setup_method(self):
        from src.observability.event_recorder import ObservabilityController
        self.ctrl = ObservabilityController()

    def test_normal_below_70pct(self):
        from src.observability.event_recorder import ObservabilityMode
        assert self.ctrl.evaluate(0.0) is ObservabilityMode.NORMAL
        assert self.ctrl.evaluate(0.69) is ObservabilityMode.NORMAL

    def test_pressure_at_70pct(self):
        from src.observability.event_recorder import ObservabilityMode
        assert self.ctrl.evaluate(0.70) is ObservabilityMode.PRESSURE

    def test_pressure_between_70_and_90(self):
        from src.observability.event_recorder import ObservabilityMode
        assert self.ctrl.evaluate(0.85) is ObservabilityMode.PRESSURE

    def test_degraded_at_90pct(self):
        from src.observability.event_recorder import ObservabilityMode
        assert self.ctrl.evaluate(0.90) is ObservabilityMode.DEGRADED

    def test_degraded_between_90_and_100(self):
        from src.observability.event_recorder import ObservabilityMode
        assert self.ctrl.evaluate(0.95) is ObservabilityMode.DEGRADED

    def test_survival_at_100pct(self):
        from src.observability.event_recorder import ObservabilityMode
        assert self.ctrl.evaluate(1.00) is ObservabilityMode.SURVIVAL

    def test_survival_above_100pct(self):
        from src.observability.event_recorder import ObservabilityMode
        assert self.ctrl.evaluate(1.10) is ObservabilityMode.SURVIVAL

    def test_evaluate_ignores_event_rate(self):
        from src.observability.event_recorder import ObservabilityMode
        assert self.ctrl.evaluate(0.0, event_rate_per_tick=99999) is ObservabilityMode.NORMAL


class TestNormalMode:
    def test_normal_mode_records_all_events(self):
        rec = _make_recorder()
        _set_queue_fill(rec, 0.0)
        before = len(rec.events)
        for sev in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            rec.record(_make_event(severity=sev, event_type=f"ev_{sev}"))
        assert len(rec.events) == before + 5
        assert rec._events_dropped_by_mode == 0

    def test_normal_mode_does_not_drop(self):
        rec = _make_recorder()
        _set_queue_fill(rec, 0.5)
        rec.record(_make_event("INFO"))
        assert rec._events_dropped_by_mode == 0


class TestPressureMode:
    def _force_pressure(self, rec):
        _set_queue_fill(rec, 0.75)
        from src.observability.event_recorder import ObservabilityMode
        rec._obs_mode = ObservabilityMode.PRESSURE

    def test_pressure_mode_samples_info_events(self):
        rec = _make_recorder()
        self._force_pressure(rec)
        # With sample rate 5, only the 5th INFO event should pass
        passed = 0
        for i in range(10):
            before = len(rec.events)
            rec.record(_make_event("INFO"))
            if len(rec.events) > before:
                passed += 1
        # Exactly 2 events passed (5th and 10th of 10 total)
        assert passed == 2

    def test_pressure_mode_keeps_warning_events(self):
        rec = _make_recorder()
        self._force_pressure(rec)
        before = len(rec.events)
        for _ in range(5):
            rec.record(_make_event("WARNING"))
        assert len(rec.events) == before + 5

    def test_pressure_mode_keeps_error_events(self):
        rec = _make_recorder()
        self._force_pressure(rec)
        before = len(rec.events)
        rec.record(_make_event("ERROR"))
        assert len(rec.events) == before + 1

    def test_pressure_mode_increments_drop_count(self):
        rec = _make_recorder()
        self._force_pressure(rec)
        # Send 4 INFO events — all should be dropped (counter not divisible by 5 yet)
        for _ in range(4):
            rec.record(_make_event("INFO"))
        assert rec._events_dropped_by_mode == 4


class TestDegradedMode:
    def _force_degraded(self, rec):
        _set_queue_fill(rec, 0.92)
        from src.observability.event_recorder import ObservabilityMode
        rec._obs_mode = ObservabilityMode.DEGRADED

    def test_degraded_mode_drops_info_events(self):
        rec = _make_recorder()
        self._force_degraded(rec)
        before = len(rec.events)
        rec.record(_make_event("INFO"))
        rec.record(_make_event("DEBUG"))
        assert len(rec.events) == before
        assert rec._events_dropped_by_mode == 2

    def test_degraded_mode_keeps_warning_events(self):
        rec = _make_recorder()
        self._force_degraded(rec)
        before = len(rec.events)
        rec.record(_make_event("WARNING"))
        assert len(rec.events) == before + 1

    def test_degraded_mode_keeps_critical_events(self):
        rec = _make_recorder()
        self._force_degraded(rec)
        before = len(rec.events)
        rec.record(_make_event("CRITICAL"))
        assert len(rec.events) == before + 1


class TestSurvivalMode:
    def _force_survival(self, rec):
        _set_queue_fill(rec, 1.0)
        from src.observability.event_recorder import ObservabilityMode
        rec._obs_mode = ObservabilityMode.SURVIVAL

    def test_survival_mode_no_queue_enqueue(self):
        rec = _make_recorder()
        self._force_survival(rec)
        pushes = []
        original_push = rec.queue.try_push
        rec.queue.try_push = lambda e: pushes.append(e)
        rec.record(_make_event("WARNING"))
        rec.record(_make_event("INFO"))
        assert len(pushes) == 0

    def test_survival_mode_no_buffer_append(self):
        rec = _make_recorder()
        self._force_survival(rec)
        before = len(rec.events)
        rec.record(_make_event("ERROR"))
        assert len(rec.events) == before

    def test_survival_mode_increments_counters(self):
        rec = _make_recorder()
        self._force_survival(rec)
        rec.record(_make_event("INFO", event_type="combat_damage"))
        rec.record(_make_event("WARNING", event_type="combat_damage"))
        rec.record(_make_event("INFO", event_type="movement"))
        assert rec._survival_event_counts.get("combat_damage") == 2
        assert rec._survival_event_counts.get("movement") == 1

    def test_survival_mode_counts_all_severities(self):
        rec = _make_recorder()
        self._force_survival(rec)
        for sev in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            rec.record(_make_event(sev))
        total = sum(rec._survival_event_counts.values())
        assert total == 5
        assert rec._events_dropped_by_mode == 5


class TestObservabilityStatus:
    def test_status_initial_state(self):
        rec = _make_recorder()
        status = rec.observability_status()
        assert status["mode"] == "NORMAL"
        assert status["events_dropped"] == 0
        assert status["survival_counts"] == {}
        assert isinstance(status["queue_fill_ratio"], float)

    def test_status_reflects_current_mode(self):
        rec = _make_recorder()
        from src.observability.event_recorder import ObservabilityMode
        rec._obs_mode = ObservabilityMode.DEGRADED
        status = rec.observability_status()
        assert status["mode"] == "DEGRADED"

    def test_status_events_dropped_accumulates(self):
        rec = _make_recorder()
        from src.observability.event_recorder import ObservabilityMode
        rec._obs_mode = ObservabilityMode.DEGRADED
        _set_queue_fill(rec, 0.92)
        rec.record(_make_event("INFO"))
        rec.record(_make_event("DEBUG"))
        status = rec.observability_status()
        assert status["events_dropped"] == 2

    def test_status_survival_counts_exposed(self):
        rec = _make_recorder()
        from src.observability.event_recorder import ObservabilityMode
        rec._obs_mode = ObservabilityMode.SURVIVAL
        _set_queue_fill(rec, 1.0)
        rec.record(_make_event("INFO", event_type="gold_transaction"))
        status = rec.observability_status()
        assert status["survival_counts"]["gold_transaction"] == 1


class TestResetMode:
    def test_reset_mode_clears_state(self):
        rec = _make_recorder()
        from src.observability.event_recorder import ObservabilityMode
        rec._obs_mode = ObservabilityMode.SURVIVAL
        rec._press_event_counter = 42
        rec._survival_event_counts["foo"] = 10
        rec._events_dropped_by_mode = 99
        rec.reset_mode()
        assert rec._obs_mode is ObservabilityMode.NORMAL
        assert rec._press_event_counter == 0
        assert rec._survival_event_counts == {}
        assert rec._events_dropped_by_mode == 0
