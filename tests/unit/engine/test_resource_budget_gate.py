"""
Unit tests for per-subsystem resource budget gates (TCK-20260614-RESOURCE-BUDGET-GATE).

Compliance IDs: INFRA-194, INFRA-195, INFRA-196

Covers:
  - SubsystemBudget / SubsystemPressureReport dataclasses
  - DEFAULT_SUBSYSTEM_BUDGETS sanity (7 subsystems, non-None defaults)
  - DEBUG_REFERENCE all-None budgets
  - EventRecorder.pressure_report() at varying queue occupancies
  - ReplayManager.pressure_report() existence and basic contract

All tests are fast (< 100 ms) and do not touch real disk I/O except via tmp_path.
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.config.optimization_profiles import (
    DEFAULT_SUBSYSTEM_BUDGETS,
    DEBUG_REFERENCE,
    DEFAULT_PROFILE,
    SubsystemBudget,
    SubsystemPressureReport,
    DEFAULT_HASHING_BUDGET,
    DEFAULT_OBSERVABILITY_BUDGET,
    DEFAULT_REPLAY_BUDGET,
)
from src.observability.event_recorder import EventRecorder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_recorder(queue_size: int, max_queue_items: int | None) -> EventRecorder:
    """
    Construct an EventRecorder with a mocked queue whose get_size() returns
    *queue_size*, and inject an explicit SubsystemBudget.
    """
    budget = SubsystemBudget(subsystem="observability", max_queue_items=max_queue_items)
    recorder = EventRecorder.__new__(EventRecorder)
    recorder.enabled = True
    recorder.max_events = 5000
    recorder.run_dir = None
    recorder.events = []
    recorder.dropped_event_count = 0
    recorder.event_count_by_type = {}
    recorder._file_handle = None
    recorder.filepath = None
    recorder._subsystem_budget = budget

    mock_queue = MagicMock()
    mock_queue.get_size.return_value = queue_size
    recorder.queue = mock_queue
    return recorder


def _make_replay_manager(tmp_path: Path, max_inflight_chunks: int | None = 3) -> Any:
    """
    Construct a ReplayManager with a SubsystemBudget injected at pressure_report() call.
    Uses tmp_path so no real filesystem state leaks between tests.
    """
    from src.engine.replay_manager import ReplayManager
    from src.core.replay_modes import ReplayMode

    mgr = ReplayManager(
        run_dir=tmp_path,
        profile_name="TEST",
        buffer_capacity_kb=64,
        chunk_tick_limit=100,
        replay_mode=ReplayMode.DEBUG_WINDOWED,
    )
    return mgr, SubsystemBudget(subsystem="replay", max_inflight_chunks=max_inflight_chunks)


# ---------------------------------------------------------------------------
# STEP 2: Default budget sanity
# ---------------------------------------------------------------------------

class TestSubsystemBudgetDefaults:
    EXPECTED_SUBSYSTEMS = {
        "certification",
        "replay",
        "observability",
        "cognition",
        "hashing",
        "worker",
        "content",
    }

    def test_subsystem_budget_defaults_are_sane(self):
        """All 7 default subsystem budgets exist and have at least one non-None field."""
        assert set(DEFAULT_SUBSYSTEM_BUDGETS.keys()) == self.EXPECTED_SUBSYSTEMS, (
            f"Missing subsystems: {self.EXPECTED_SUBSYSTEMS - set(DEFAULT_SUBSYSTEM_BUDGETS.keys())}"
        )
        for name, budget in DEFAULT_SUBSYSTEM_BUDGETS.items():
            assert budget.subsystem == name
            non_none = [
                f
                for f in (
                    budget.max_artifact_mb,
                    budget.max_pending_flushes,
                    budget.max_queue_items,
                    budget.max_tracked_entities,
                    budget.max_full_hashes_per_100_ticks,
                    budget.max_inflight_chunks,
                    budget.max_hot_path_loads,
                )
                if f is not None
            ]
            assert non_none, (
                f"DEFAULT_SUBSYSTEM_BUDGETS['{name}'] has all-None fields — "
                "production defaults must enforce at least one limit"
            )

    def test_debug_reference_budgets_are_all_none(self):
        """DEBUG_REFERENCE profile has all-None subsystem budgets (unlimited)."""
        assert set(DEBUG_REFERENCE.subsystem_budgets.keys()) == self.EXPECTED_SUBSYSTEMS
        for name, budget in DEBUG_REFERENCE.subsystem_budgets.items():
            assert budget.max_artifact_mb is None, f"{name}.max_artifact_mb should be None"
            assert budget.max_pending_flushes is None, f"{name}.max_pending_flushes should be None"
            assert budget.max_queue_items is None, f"{name}.max_queue_items should be None"
            assert budget.max_tracked_entities is None, f"{name}.max_tracked_entities should be None"
            assert budget.max_full_hashes_per_100_ticks is None, (
                f"{name}.max_full_hashes_per_100_ticks should be None"
            )
            assert budget.max_inflight_chunks is None, f"{name}.max_inflight_chunks should be None"
            assert budget.max_hot_path_loads is None, f"{name}.max_hot_path_loads should be None"

    def test_default_profile_has_all_7_subsystems(self):
        """DEFAULT_PROFILE carries all 7 subsystem budgets."""
        assert set(DEFAULT_PROFILE.subsystem_budgets.keys()) == self.EXPECTED_SUBSYSTEMS


# ---------------------------------------------------------------------------
# STEP 5: EventRecorder.pressure_report()
# ---------------------------------------------------------------------------

class TestEventRecorderPressureReport:

    def test_event_recorder_reports_ok_below_threshold(self):
        """Queue < 80% of cap → OK."""
        # cap=10, size=7 → 70% → OK
        recorder = _make_recorder(queue_size=7, max_queue_items=10)
        report = recorder.pressure_report()
        assert report.subsystem == "observability"
        assert report.pressure_state == "OK"
        assert report.degradation_action is None
        assert report.budget == 10.0
        assert report.current_usage == 7.0

    def test_event_recorder_reports_warn_at_80pct_capacity(self):
        """Queue at exactly 80% of cap → WARN."""
        # cap=10, size=8 → 80% → WARN
        recorder = _make_recorder(queue_size=8, max_queue_items=10)
        report = recorder.pressure_report()
        assert report.pressure_state == "WARN"
        assert report.degradation_action is not None

    def test_event_recorder_reports_degraded_at_full_capacity(self):
        """Queue at 100% of cap → DEGRADED."""
        # cap=5, size=5 → 100% → DEGRADED
        recorder = _make_recorder(queue_size=5, max_queue_items=5)
        report = recorder.pressure_report()
        assert report.pressure_state == "DEGRADED"
        assert report.degradation_action is not None

    def test_event_recorder_reports_degraded_over_full_capacity(self):
        """Queue exceeds cap → DEGRADED (not a crash)."""
        recorder = _make_recorder(queue_size=12, max_queue_items=10)
        report = recorder.pressure_report()
        assert report.pressure_state == "DEGRADED"

    def test_event_recorder_none_budget_always_ok(self):
        """None max_queue_items → always OK regardless of queue size."""
        recorder = _make_recorder(queue_size=999999, max_queue_items=None)
        report = recorder.pressure_report()
        assert report.pressure_state == "OK"
        assert report.budget is None
        assert report.degradation_action is None

    def test_event_recorder_pressure_report_returns_correct_type(self):
        """pressure_report() returns a SubsystemPressureReport instance."""
        recorder = _make_recorder(queue_size=0, max_queue_items=100)
        report = recorder.pressure_report()
        assert isinstance(report, SubsystemPressureReport)


# ---------------------------------------------------------------------------
# STEP 3: ReplayManager.pressure_report()
# ---------------------------------------------------------------------------

class TestReplayManagerPressureReport:

    def test_replay_pressure_report_exists(self, tmp_path):
        """ReplayManager.pressure_report() returns a SubsystemPressureReport."""
        mgr, budget = _make_replay_manager(tmp_path, max_inflight_chunks=5)
        try:
            report = mgr.pressure_report(budget=budget)
            assert isinstance(report, SubsystemPressureReport)
            assert report.subsystem == "replay"
            assert report.budget == 5.0
            assert report.pressure_state == "OK"
        finally:
            mgr._executor.shutdown(wait=False)

    def test_replay_pressure_report_none_budget(self, tmp_path):
        """None max_inflight_chunks → OK with budget=None."""
        mgr, _ = _make_replay_manager(tmp_path, max_inflight_chunks=None)
        try:
            report = mgr.pressure_report(budget=SubsystemBudget(subsystem="replay"))
            assert report.budget is None
            assert report.pressure_state == "OK"
        finally:
            mgr._executor.shutdown(wait=False)

    def test_replay_pressure_report_default_budget_used_when_none_passed(self, tmp_path):
        """pressure_report() with no args uses DEFAULT_REPLAY_BUDGET."""
        mgr, _ = _make_replay_manager(tmp_path)
        try:
            report = mgr.pressure_report()
            assert isinstance(report, SubsystemPressureReport)
            assert report.subsystem == "replay"
            # DEFAULT_REPLAY_BUDGET.max_inflight_chunks == 3
            assert report.budget == float(DEFAULT_REPLAY_BUDGET.max_inflight_chunks)
        finally:
            mgr._executor.shutdown(wait=False)
