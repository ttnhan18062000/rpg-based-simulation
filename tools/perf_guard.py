"""tools/perf_guard.py — Performance guard CLI.

Subcommands
-----------
measure [--test <node_id>]
    Discover perf tests (those using the ``perf_budget`` fixture), run them
    with instrumentation, and print a proposed diff for ``perf_baselines.json``.
    Does NOT write the baseline file — a human must review and commit changes.

show
    Pretty-print ``perf_baselines.json`` entries side-by-side with the last
    measured values from ``.perf_last_run.json``.

Usage
-----
    python3 tools/perf_guard.py measure
    python3 tools/perf_guard.py measure --test tests/perf/test_foo.py::test_bar
    python3 tools/perf_guard.py show
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import time
from typing import Any

_BASELINE_PATH = pathlib.Path("perf_baselines.json")
_LAST_RUN_PATH = pathlib.Path(".perf_last_run.json")
_PERF_DIR = pathlib.Path("tests/perf")
_HARDWARE_CLASS = os.environ.get("PERF_HARDWARE_CLASS", "B")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_baseline() -> dict[str, Any]:
    """Return the full baseline document (not just entries)."""
    if not _BASELINE_PATH.exists():
        return {"version": 1, "hardware_class_default": "B", "entries": {}}
    return json.loads(_BASELINE_PATH.read_text())


def _load_last_run() -> dict[str, Any]:
    if not _LAST_RUN_PATH.exists():
        return {}
    return json.loads(_LAST_RUN_PATH.read_text())


def _snapshot_rss_kb() -> float:
    rss_pages = int(pathlib.Path("/proc/self/statm").read_text().split()[1])
    return rss_pages * 4.0


# ── Test discovery ─────────────────────────────────────────────────────────────

def _discover_perf_tests(filter_test: str | None = None) -> list[str]:
    """Return pytest node IDs for all tests that reference the perf_budget fixture.

    Searches ``tests/perf/`` recursively for function definitions that include
    ``perf_budget`` in their parameter list.
    """
    if filter_test:
        return [filter_test]

    node_ids: list[str] = []
    for py_file in sorted(_PERF_DIR.rglob("test_*.py")):
        rel = str(py_file)
        # Quick grep: does this file use perf_budget?
        content = py_file.read_text(errors="replace")
        if "perf_budget" not in content:
            continue
        # Ask pytest to collect the file and extract node IDs for matching tests
        result = subprocess.run(
            [
                sys.executable, "-m", "pytest",
                rel,
                "--collect-only", "-q",
                "--no-header",
                "--tb=no",
            ],
            capture_output=True,
            text=True,
        )
        for line in result.stdout.splitlines():
            line = line.strip()
            if "::" in line and not line.startswith("<"):
                # Check that this specific test function uses the fixture
                func_name = line.split("::")[-1]
                if _test_uses_fixture(py_file, func_name, "perf_budget"):
                    node_ids.append(line)
    return node_ids


def _test_uses_fixture(py_file: pathlib.Path, func_name: str, fixture: str) -> bool:
    """Return True if ``func_name`` in ``py_file`` declares ``fixture`` as a parameter."""
    content = py_file.read_text(errors="replace")
    import re
    pattern = rf"def\s+{re.escape(func_name)}\s*\([^)]*\b{re.escape(fixture)}\b"
    return bool(re.search(pattern, content))


# ── PerfMeasurePlugin ─────────────────────────────────────────────────────────

class PerfMeasurePlugin:
    """Pytest plugin that records wall-clock time and RSS delta per test call."""

    def __init__(self) -> None:
        self.results: dict[str, dict[str, float]] = {}
        self._rss_before: float = 0.0
        self._t0: float = 0.0
        self._current_id: str = ""

    def pytest_runtest_call(self, item: Any) -> None:  # noqa: ANN401
        self._current_id = item.nodeid
        self._rss_before = _snapshot_rss_kb()
        self._t0 = time.perf_counter()

    def pytest_runtest_logreport(self, report: Any) -> None:  # noqa: ANN401
        if report.when != "call":
            return
        elapsed_ms = (time.perf_counter() - self._t0) * 1000.0
        rss_after = _snapshot_rss_kb()
        rss_delta = max(0.0, rss_after - self._rss_before)
        self.results[self._current_id] = {
            "time_ms": round(elapsed_ms, 3),
            "memory_kb": round(rss_delta, 1),
            "passed": report.passed,
        }


# ── measure subcommand ────────────────────────────────────────────────────────

def measure(extra_args: list[str]) -> None:
    """Discover perf tests, run them in-process via pytest, and print a proposed diff."""
    filter_test: str | None = None
    args = list(extra_args)
    while args:
        arg = args.pop(0)
        if arg in ("--test", "-t") and args:
            filter_test = args.pop(0)
        else:
            print(f"Unknown argument: {arg}", file=sys.stderr)
            sys.exit(1)

    baseline_doc = _load_baseline()
    current_entries: dict[str, Any] = baseline_doc.get("entries", {})

    node_ids = _discover_perf_tests(filter_test)
    if not node_ids:
        print("No perf tests using perf_budget found.", file=sys.stderr)
        return

    print(f"Measuring {len(node_ids)} perf test(s) with hardware class {_HARDWARE_CLASS} ...\n")

    plugin = PerfMeasurePlugin()

    # Import pytest here so the module is importable without pytest installed
    import pytest as _pytest
    _pytest.main(
        [
            *node_ids,
            "-p", "no:timeout",
            "--tb=no",
            "-q",
            "--no-header",
            "-p", "no:cacheprovider",
        ],
        plugins=[plugin],
    )

    # Write last-run scratch file
    _LAST_RUN_PATH.write_text(json.dumps(plugin.results, indent=2))

    # Classify and build proposed diff
    today = time.strftime("%Y-%m-%d")
    proposed: dict[str, Any] = {}
    statuses: dict[str, str] = {}

    for node_id, measured in plugin.results.items():
        existing = current_entries.get(node_id)
        measured_ms = measured["time_ms"]
        measured_kb = measured.get("memory_kb")

        if existing is None:
            status = "NEW"
        else:
            tol = existing.get("tolerance_pct", 20) / 100.0
            limit_ms = existing["time_ms"] * (1 + tol)
            if measured_ms > limit_ms:
                status = "REGRESSION"
            elif measured_ms < existing["time_ms"] * (1 - tol):
                status = "OVERSPEND"  # significantly faster — baseline is stale
            else:
                status = "UNCHANGED"

        statuses[node_id] = status

        if status != "UNCHANGED":
            proposed[node_id] = {
                "time_ms": measured_ms,
                "memory_kb": measured_kb if measured_kb and measured_kb > 0 else None,
                "tolerance_pct": (existing or {}).get("tolerance_pct", 20),
                "hardware_class": _HARDWARE_CLASS,
                "rationale": "TODO",
                "updated_by": "TODO",
                "updated_at": today,
            }

    # Print summary
    width = max((len(n) for n in plugin.results), default=40)
    print(f"{'NODE ID':<{width}}  {'STATUS':<12}  {'TIME_MS':>10}  {'MEM_KB':>10}")
    print("-" * (width + 38))
    for node_id, measured in plugin.results.items():
        status = statuses.get(node_id, "?")
        print(
            f"{node_id:<{width}}  {status:<12}  {measured['time_ms']:>10.2f}  "
            f"{measured.get('memory_kb', 0.0):>10.1f}"
        )

    if proposed:
        print("\n── Proposed perf_baselines.json diff (non-UNCHANGED entries) ──")
        print(json.dumps(proposed, indent=2))
        print("\nReview the values above, fill in rationale/updated_by, and update perf_baselines.json.")
    else:
        print("\nAll tests within tolerance — no baseline updates needed.")


# ── show subcommand ───────────────────────────────────────────────────────────

def show() -> None:
    """Pretty-print baseline vs last-measured values."""
    baseline_doc = _load_baseline()
    entries = baseline_doc.get("entries", {})
    last_run = _load_last_run()

    if not entries and not last_run:
        print("No baseline entries and no last-run data. Run `make perf-measure` first.")
        return

    all_ids = sorted(set(entries) | set(last_run))
    width = max((len(n) for n in all_ids), default=40)

    print(f"{'NODE ID':<{width}}  {'BUDGET_MS':>10}  {'LAST_MS':>10}  {'STATUS':<12}")
    print("-" * (width + 40))

    for node_id in all_ids:
        entry = entries.get(node_id)
        run = last_run.get(node_id)

        budget_ms = entry["time_ms"] if entry else None
        last_ms = run["time_ms"] if run else None

        if budget_ms is None:
            status = "NO_BASELINE"
        elif last_ms is None:
            status = "NOT_RUN"
        else:
            tol = entry.get("tolerance_pct", 20) / 100.0  # type: ignore[union-attr]
            limit_ms = budget_ms * (1 + tol)
            status = "PASS" if last_ms <= limit_ms else "FAIL"

        budget_str = f"{budget_ms:.2f}" if budget_ms is not None else "—"
        last_str = f"{last_ms:.2f}" if last_ms is not None else "—"
        print(f"{node_id:<{width}}  {budget_str:>10}  {last_str:>10}  {status:<12}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "show":
        show()
    elif sys.argv[1] == "measure":
        measure(sys.argv[2:])
    else:
        print(f"Usage: perf_guard.py [measure|show]", file=sys.stderr)
        sys.exit(1)
