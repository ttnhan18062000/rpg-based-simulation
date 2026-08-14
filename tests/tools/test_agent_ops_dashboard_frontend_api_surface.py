"""
Architecture guard: dashboard-frontend/ must never reference the simulation
engine's own API surface.

The dashboard's real backend is the standalone
`src/api/agent_ops_dashboard/{main,ingest,models}.py` (TCK-20260716-AGENTOPS-
DASHBOARD-BACKEND), consumed read-only over HTTP via `GET /api/runs`. It is
not mounted on `src/api/server.py`, does not share `src/api/read_model_cache.py`,
and has nothing to do with `src/api/routes/history.py` or `src/api/ws/stream.py`
— those are the simulation engine's own API surface. The ticket's own Related
Code Areas boilerplate listed those four stale paths as reuse-source
references; this guard makes sure no frontend code, mock, or fetch client ever
actually couples to them (see
staging_artifacts/TCK-20260716-AGENTOPS-ACTIVITY-GANTT/plan.md's Anti-Drift
Notes, "Stale backend references").
"""
from __future__ import annotations

from pathlib import Path

_FRONTEND_ROOT = Path(__file__).parent.parent.parent / "dashboard-frontend" / "src"

_FORBIDDEN_PATHS = [
    "src/api/server.py",
    "src/api/read_model_cache.py",
    "src/api/routes/history.py",
    "src/api/ws/stream.py",
]


def _frontend_source_files() -> list[Path]:
    if not _FRONTEND_ROOT.is_dir():
        return []
    return sorted(
        p for p in _FRONTEND_ROOT.rglob("*") if p.suffix in (".ts", ".tsx")
    )


def test_dashboard_frontend_never_references_simulation_api_surface() -> None:
    violations: list[str] = []

    for path in _frontend_source_files():
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(_FRONTEND_ROOT.parent.parent)
        for forbidden in _FORBIDDEN_PATHS:
            if forbidden in text:
                line_no = text[: text.index(forbidden)].count("\n") + 1
                violations.append(f"{rel}:{line_no} references forbidden path {forbidden!r}")

    assert not violations, (
        "dashboard-frontend/ must never reference the simulation engine's own "
        "API surface (src/api/server.py, src/api/read_model_cache.py, "
        "src/api/routes/history.py, src/api/ws/stream.py). The dashboard's real "
        "backend is src/api/agent_ops_dashboard/{main,ingest,models}.py, "
        "consumed only via GET /api/runs.\n\n" + "\n".join(f"  {v}" for v in violations)
    )


def test_echarts_dependencies_declared_in_package_json() -> None:
    import json
    pkg_path = _FRONTEND_ROOT.parent / "package.json"
    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    deps = pkg.get("dependencies", {})
    assert "echarts" in deps, "package.json must declare 'echarts' under dependencies"
    assert "echarts-for-react" in deps, (
        "package.json must declare 'echarts-for-react' under dependencies"
    )


def test_no_source_file_imports_full_echarts_bundle() -> None:
    import re
    # Matches a bare `from 'echarts'` / `require('echarts')` — NOT 'echarts/core',
    # any 'echarts/...' submodule path, or the distinct 'echarts-for-react' package.
    bare_echarts_import = re.compile(r"""(from\s+['"]echarts['"]|require\(\s*['"]echarts['"]\s*\))""")
    violations: list[str] = []
    for path in _frontend_source_files():
        text = path.read_text(encoding="utf-8")
        if bare_echarts_import.search(text):
            rel = path.relative_to(_FRONTEND_ROOT.parent.parent)
            violations.append(str(rel))
    assert not violations, (
        "no dashboard-frontend/src file may import the full 'echarts' bundle — only "
        "'echarts/core' plus tree-shaken submodule imports are allowed. Violations: "
        + ", ".join(violations)
    )


def test_gantt_components_fully_retired() -> None:
    import re

    retired_component_paths = [
        "dashboard-frontend/src/components/GanttBar.tsx",
        "dashboard-frontend/src/components/TimeAxis.tsx",
        "dashboard-frontend/src/components/Legend.tsx",
        "dashboard-frontend/src/views/RecentActivityGantt.tsx",
    ]
    for rel_path in retired_component_paths:
        assert not (_FRONTEND_ROOT.parent.parent / rel_path).exists(), (
            f"{rel_path} must be deleted — retired by TCK-20260720-PROGRESS-TIMELINE-VIEW"
        )

    forbidden_import = re.compile(
        r"""from\s+['"]@/(components/(GanttBar|TimeAxis|Legend)|views/RecentActivityGantt)['"]"""
    )
    to_percent_call = re.compile(r"\btoPercent\(")
    violations: list[str] = []
    for path in _frontend_source_files():
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(_FRONTEND_ROOT.parent.parent)
        if forbidden_import.search(text):
            violations.append(f"{rel} imports a retired Gantt component")
        if to_percent_call.search(text):
            violations.append(f"{rel} still calls toPercent(), which was deleted with GanttBar.tsx")
    assert not violations, "\n".join(violations)
