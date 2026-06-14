"""Tests for diagnostics resources CLI (RESOURCE-DASHBOARD).

Covers: table format, JSON format, exit code on DEGRADED, offline mode,
kernel resource_snapshot() integration.
"""
from __future__ import annotations

import io
import json
import pytest
from unittest.mock import MagicMock


def _make_report(subsystem: str, current: float, budget: float | None, state: str):
    from src.config.optimization_profiles import SubsystemPressureReport
    return SubsystemPressureReport(
        subsystem=subsystem,
        current_usage=current,
        budget=budget,
        pressure_state=state,
        degradation_action=None if state == "OK" else f"reduce_{subsystem}",
    )


class TestFormatTable:
    def test_table_contains_subsystem_names(self):
        from src.cli.diagnostics import format_table
        reports = [
            _make_report("observability", 400, 500, "WARN"),
            _make_report("replay", 1, 2, "OK"),
        ]
        out = format_table(reports)
        assert "observability" in out
        assert "replay" in out

    def test_table_contains_state(self):
        from src.cli.diagnostics import format_table
        reports = [_make_report("replay", 2, 2, "DEGRADED")]
        out = format_table(reports)
        assert "DEGRADED" in out

    def test_table_shows_usage_fraction_when_budget_set(self):
        from src.cli.diagnostics import format_table
        reports = [_make_report("observability", 80, 100, "WARN")]
        out = format_table(reports)
        assert "80%" in out or "80" in out

    def test_table_empty_reports_shows_notice(self):
        from src.cli.diagnostics import format_table
        out = format_table([])
        assert "no subsystem data" in out.lower()

    def test_table_has_header(self):
        from src.cli.diagnostics import format_table
        out = format_table([_make_report("replay", 0, 5, "OK")])
        assert "Subsystem" in out
        assert "State" in out


class TestFormatJson:
    def test_json_is_valid(self):
        from src.cli.diagnostics import format_json
        reports = [
            _make_report("observability", 400, 500, "WARN"),
            _make_report("replay", 1, 2, "OK"),
        ]
        data = json.loads(format_json(reports))
        assert isinstance(data, list)
        assert len(data) == 2

    def test_json_contains_required_keys(self):
        from src.cli.diagnostics import format_json
        reports = [_make_report("replay", 1, 2, "OK")]
        data = json.loads(format_json(reports))
        assert "subsystem" in data[0]
        assert "pressure_state" in data[0]
        assert "current_usage" in data[0]

    def test_json_empty_is_empty_array(self):
        from src.cli.diagnostics import format_json
        data = json.loads(format_json([]))
        assert data == []


class TestHasDegraded:
    def test_no_degraded_returns_false(self):
        from src.cli.diagnostics import has_degraded
        reports = [_make_report("obs", 0, 100, "OK"), _make_report("rep", 1, 2, "WARN")]
        assert not has_degraded(reports)

    def test_one_degraded_returns_true(self):
        from src.cli.diagnostics import has_degraded
        reports = [_make_report("obs", 100, 100, "DEGRADED")]
        assert has_degraded(reports)

    def test_empty_returns_false(self):
        from src.cli.diagnostics import has_degraded
        assert not has_degraded([])


class TestRunDiagnosticsResources:
    def test_exit_code_0_when_all_ok(self):
        from src.cli.diagnostics import run_diagnostics_resources
        kernel = MagicMock()
        kernel.resource_snapshot.return_value = [
            _make_report("observability", 10, 100, "OK"),
        ]
        code = run_diagnostics_resources(fmt="table", kernel=kernel, out=io.StringIO())
        assert code == 0

    def test_exit_code_1_on_degraded(self):
        from src.cli.diagnostics import run_diagnostics_resources
        kernel = MagicMock()
        kernel.resource_snapshot.return_value = [
            _make_report("replay", 5, 5, "DEGRADED"),
        ]
        code = run_diagnostics_resources(fmt="table", kernel=kernel, out=io.StringIO())
        assert code == 1

    def test_table_output_written(self):
        from src.cli.diagnostics import run_diagnostics_resources
        kernel = MagicMock()
        kernel.resource_snapshot.return_value = [
            _make_report("observability", 50, 100, "WARN"),
        ]
        buf = io.StringIO()
        run_diagnostics_resources(fmt="table", kernel=kernel, out=buf)
        assert "observability" in buf.getvalue()

    def test_json_output_valid(self):
        from src.cli.diagnostics import run_diagnostics_resources
        kernel = MagicMock()
        kernel.resource_snapshot.return_value = [
            _make_report("replay", 0, 2, "OK"),
        ]
        buf = io.StringIO()
        run_diagnostics_resources(fmt="json", kernel=kernel, out=buf)
        data = json.loads(buf.getvalue())
        assert isinstance(data, list)
        assert data[0]["subsystem"] == "replay"

    def test_offline_mode_no_kernel(self):
        from src.cli.diagnostics import run_diagnostics_resources
        buf = io.StringIO()
        code = run_diagnostics_resources(fmt="table", kernel=None, run_id=None, out=buf)
        assert isinstance(code, int)


class TestKernelResourceSnapshot:
    def test_resource_snapshot_returns_list(self):
        from src.engine.kernel import Kernel
        from src.core.state import AuthoritativeState
        from src.config.profiles import RuntimeProfile, HardwareClass
        from unittest.mock import MagicMock
        profile = RuntimeProfile(
            name="TEST", hardware_class=HardwareClass.CLASS_B,
            max_ram_mb=512, max_cpu_percent=50.0, max_worker_count=1,
            max_queue_depth=100, max_work_debt=100, max_replay_buffer_kb=64,
            max_observability_budget_percent=5.0, max_tick_budget_ms=10.0,
        )
        k = Kernel(state=AuthoritativeState(tick=0, seed=42), profile=profile,
                   rng=MagicMock(), flags={"no_replay": True})
        try:
            reports = k.resource_snapshot()
            assert isinstance(reports, list)
            for r in reports:
                assert hasattr(r, "subsystem")
                assert hasattr(r, "pressure_state")
        finally:
            k.shutdown()

    def test_resource_snapshot_includes_observability(self):
        from src.engine.kernel import Kernel
        from src.core.state import AuthoritativeState
        from src.config.profiles import RuntimeProfile, HardwareClass
        from unittest.mock import MagicMock
        profile = RuntimeProfile(
            name="TEST", hardware_class=HardwareClass.CLASS_B,
            max_ram_mb=512, max_cpu_percent=50.0, max_worker_count=1,
            max_queue_depth=100, max_work_debt=100, max_replay_buffer_kb=64,
            max_observability_budget_percent=5.0, max_tick_budget_ms=10.0,
        )
        k = Kernel(state=AuthoritativeState(tick=0, seed=42), profile=profile,
                   rng=MagicMock(), flags={"no_replay": True})
        try:
            reports = k.resource_snapshot()
            subsystems = [r.subsystem for r in reports]
            assert "observability" in subsystems
        finally:
            k.shutdown()
