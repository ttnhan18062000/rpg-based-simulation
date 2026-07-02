import json
import logging
import pathlib
import pytest
from pathlib import Path
from typing import Dict, Any

from src.perf.bench_harness import BenchHarness
from src.perf.profiles import PERF_PROFILES

logger = logging.getLogger(__name__)

# ── Performance budget fixture ────────────────────────────────────────────────

_BASELINE_PATH = pathlib.Path("perf_baselines.json")


def _snapshot_rss_kb() -> float:
    """Read current RSS from /proc/self/statm (Linux only, no extra deps).

    /proc/self/statm fields: <vsize> <rss> <shared> ...  (all in pages)
    Page size is 4 KB on x86-64.
    """
    rss_pages = int(pathlib.Path("/proc/self/statm").read_text().split()[1])
    return rss_pages * 4.0


class PerfBudget:
    """Holds a single baseline entry and validates measured performance against it."""

    def __init__(self, entry: dict, test_id: str) -> None:
        self._entry = entry
        self._test_id = test_id

    def snapshot_rss(self) -> float:
        """Return current RSS in KB."""
        return _snapshot_rss_kb()

    def assert_within_budget(
        self,
        measured_ms: float,
        measured_kb: "float | None" = None,
    ) -> None:
        """Assert time and (optionally) memory are within tolerance.

        Args:
            measured_ms: Elapsed wall-clock time in milliseconds.
            measured_kb: RSS delta in KB.  Pass None (or omit) to skip memory
                check even if the baseline has a ``memory_kb`` value.
                If the baseline entry has ``memory_kb: null`` the check is also
                skipped regardless of what is passed here.
        """
        tol = self._entry.get("tolerance_pct", 20) / 100.0
        budget_ms = self._entry["time_ms"]
        limit_ms = budget_ms * (1 + tol)
        assert measured_ms <= limit_ms, (
            f"\nPerformance gate failed: {self._test_id}\n"
            f"  time: {measured_ms:.2f}ms > {limit_ms:.2f}ms"
            f" (budget={budget_ms}ms ±{tol * 100:.0f}%)\n"
            f"  rationale: {self._entry.get('rationale', 'N/A')}\n"
            f"  → If intentional, run: make perf-measure  then update perf_baselines.json"
        )
        if measured_kb is not None and self._entry.get("memory_kb") is not None:
            budget_kb = self._entry["memory_kb"]
            limit_kb = budget_kb * (1 + tol)
            assert measured_kb <= limit_kb, (
                f"\nMemory gate failed: {self._test_id}\n"
                f"  rss delta: {measured_kb:.0f}KB > {limit_kb:.0f}KB"
                f" (budget={budget_kb}KB ±{tol * 100:.0f}%)\n"
                f"  → If intentional, run: make perf-measure  then update perf_baselines.json"
            )


@pytest.fixture(scope="session")
def _perf_baselines() -> dict:
    """Load perf_baselines.json once per session and return the entries dict."""
    if not _BASELINE_PATH.exists():
        return {}
    return json.loads(_BASELINE_PATH.read_text()).get("entries", {})


@pytest.fixture
def perf_budget(request, _perf_baselines) -> PerfBudget:
    """Resolve the baseline entry for the current test and return a PerfBudget.

    Fails immediately (``pytest.fail``) if no entry exists for this test ID.
    Authors must add an entry to ``perf_baselines.json`` before the test will run.
    Use ``make perf-measure`` to obtain a proposed entry.
    """
    test_id = request.node.nodeid
    entry = _perf_baselines.get(test_id)
    if entry is None:
        pytest.fail(
            f"No perf baseline entry for:\n  {test_id}\n"
            f"Run `make perf-measure` and add an entry to perf_baselines.json."
        )
    return PerfBudget(entry, test_id)


@pytest.fixture
def perf_harness():
    """Returns a factory for BenchHarness with a specific profile."""
    def _make_harness(profile_name: str = "PERF_512MB_LOCAL"):
        profile = PERF_PROFILES[profile_name]
        return BenchHarness(profile)
    return _make_harness


@pytest.fixture(autouse=True)
def perf_reporter(request):
    """Automatically logs performance results to a JSON file if the test is marked 'perf'."""
    yield
    
    # After test execution
    if "perf" in request.keywords:
        results = getattr(request.node, "perf_results", None)
        if results:
            report_dir = Path("reports/perf")
            report_dir.mkdir(parents=True, exist_ok=True)
            
            report_path = report_dir / f"{request.node.name}.json"
            with open(report_path, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Performance report saved to {report_path}")

@pytest.fixture
def perf_report_dir():
    """Directory for performance reports."""
    path = Path("reports/perf")
    path.mkdir(parents=True, exist_ok=True)
    return path
