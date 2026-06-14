"""diagnostics resources — runtime resource dashboard CLI.

Usage:
    python -m src diagnostics resources [--format table|json] [--run-id <id>]

Exit codes:
    0  all subsystems OK or WARN
    1  at least one DEGRADED subsystem
"""
from __future__ import annotations

import json
import sys
from typing import Any, List, Optional


def _collect_from_kernel(kernel: Any) -> List[Any]:
    """Collect pressure reports from a live Kernel instance."""
    if hasattr(kernel, "resource_snapshot"):
        return kernel.resource_snapshot()
    return []


def _collect_offline(run_id: Optional[str] = None) -> List[Any]:
    """Best-effort collection from persisted artifacts (offline mode).

    Returns empty list if no artifacts are readable; callers display a notice.
    """
    from src.config.optimization_profiles import SubsystemPressureReport
    reports = []
    try:
        from src.observability.reporting.artifact_repository import RunArtifactRepository
        repo = RunArtifactRepository()
        target_run = run_id
        if target_run is None:
            runs = repo.list_runs()
            if runs:
                target_run = sorted(runs, key=lambda r: r.get("started_at", ""))[-1].get("run_id")
        if target_run:
            manifest = repo.get_manifest(target_run)
            if manifest:
                replay_flushes = 0
                reports.append(SubsystemPressureReport(
                    subsystem="replay",
                    current_usage=float(replay_flushes),
                    budget=None,
                    pressure_state="OK",
                    degradation_action=None,
                ))
    except Exception:
        pass
    return reports


def format_table(reports: List[Any]) -> str:
    """Render a fixed-width table of pressure reports."""
    col_sub = 18
    col_usage = 18
    col_state = 10

    header = (
        f"{'Subsystem':<{col_sub}} {'Usage':<{col_usage}} {'State':<{col_state}}"
    )
    sep = "-" * (col_sub + col_usage + col_state + 2)
    rows = [header, sep]

    for r in reports:
        usage_str = _usage_str(r)
        rows.append(
            f"{r.subsystem:<{col_sub}} {usage_str:<{col_usage}} {r.pressure_state:<{col_state}}"
        )

    if not reports:
        rows.append("  (no subsystem data available)")

    return "\n".join(rows)


def _usage_str(r: Any) -> str:
    if r.budget is not None and r.budget > 0:
        pct = int(100 * r.current_usage / r.budget)
        return f"{r.current_usage:.0f}/{r.budget:.0f} ({pct}%)"
    return f"{r.current_usage:.0f}"


def format_json(reports: List[Any]) -> str:
    data = [
        {
            "subsystem": r.subsystem,
            "current_usage": r.current_usage,
            "budget": r.budget,
            "pressure_state": r.pressure_state,
            "degradation_action": r.degradation_action,
        }
        for r in reports
    ]
    return json.dumps(data, indent=2)


def has_degraded(reports: List[Any]) -> bool:
    return any(r.pressure_state == "DEGRADED" for r in reports)


def run_diagnostics_resources(
    fmt: str = "table",
    run_id: Optional[str] = None,
    kernel: Optional[Any] = None,
    out=None,
) -> int:
    """Main entry point for `diagnostics resources`.

    Returns exit code (0 = ok, 1 = degraded).
    """
    if out is None:
        out = sys.stdout

    if kernel is not None:
        reports = _collect_from_kernel(kernel)
    else:
        reports = _collect_offline(run_id)
        if not reports:
            print("No live kernel and no readable run artifacts found.", file=out)
            print("Pass --run-id <id> or run with a live kernel.", file=out)

    if fmt == "json":
        print(format_json(reports), file=out)
    else:
        print(format_table(reports), file=out)

    return 1 if has_degraded(reports) else 0
