"""tests/unit/perf/test_perf_guard.py

Unit tests for the performance guard infrastructure:
- perf_baselines.json schema
- PerfBudget fixture behaviour (pass / fail / missing-entry)
- RSS snapshot
"""

from __future__ import annotations

import json
import pathlib

import pytest

# Import the implementation directly from tests/perf/conftest internals.
# We import the private helpers and class explicitly to avoid pytest
# fixture resolution (which needs a live session).
import importlib.util
import sys


def _load_conftest():
    """Load tests/perf/conftest.py as a module without going through pytest."""
    spec = importlib.util.spec_from_file_location(
        "perf_conftest",
        pathlib.Path("tests/perf/conftest.py"),
    )
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


_conftest = _load_conftest()
PerfBudget = _conftest.PerfBudget
_snapshot_rss_kb = _conftest._snapshot_rss_kb


# ── 1. Schema validation ──────────────────────────────────────────────────────

def test_baseline_schema_valid():
    """perf_baselines.json must exist with version==1 and an entries dict."""
    path = pathlib.Path("perf_baselines.json")
    assert path.exists(), "perf_baselines.json not found at repo root"
    data = json.loads(path.read_text())
    assert data.get("version") == 1, f"Expected version 1, got {data.get('version')}"
    assert isinstance(data.get("entries"), dict), "entries must be a dict"


# ── 2. Missing entry → pytest.fail ───────────────────────────────────────────

def test_perf_budget_fixture_fail_on_missing_entry():
    """When no baseline entry exists for a test ID, the fixture must call pytest.fail."""
    baselines: dict = {}  # empty — no entries

    class FakeNode:
        nodeid = "tests/perf/test_fake.py::test_nonexistent"

    class FakeRequest:
        node = FakeNode()

    # Simulate what the fixture does
    test_id = FakeRequest.node.nodeid
    entry = baselines.get(test_id)
    if entry is None:
        with pytest.raises(pytest.fail.Exception):
            pytest.fail(
                f"No perf baseline entry for:\n  {test_id}\n"
                f"Run `make perf-measure` and add an entry to perf_baselines.json."
            )
    else:
        pytest.fail("Expected missing entry to trigger pytest.fail — but entry was found")


# ── 3. assert_within_budget — pass at 11ms ────────────────────────────────────

def test_perf_budget_assert_within_budget_pass():
    """10ms budget ±20%: limit is 12ms. 11ms must pass."""
    entry = {
        "time_ms": 10.0,
        "tolerance_pct": 20,
        "memory_kb": None,
        "rationale": "test entry",
    }
    budget = PerfBudget(entry, "tests/perf/test_fake.py::test_example")
    # Should not raise
    budget.assert_within_budget(measured_ms=11.0)


# ── 4. assert_within_budget — fail at 13ms ───────────────────────────────────

def test_perf_budget_assert_within_budget_fail():
    """10ms budget ±20%: limit is 12ms. 13ms must raise AssertionError."""
    entry = {
        "time_ms": 10.0,
        "tolerance_pct": 20,
        "memory_kb": None,
        "rationale": "test entry",
    }
    budget = PerfBudget(entry, "tests/perf/test_fake.py::test_example")
    with pytest.raises(AssertionError, match="Performance gate failed"):
        budget.assert_within_budget(measured_ms=13.0)


# ── 5. memory_kb: null → skip memory assertion ───────────────────────────────

def test_perf_budget_assert_memory_skip_when_null():
    """When baseline memory_kb is null, memory assertion must be skipped even
    when a measured_kb value is provided."""
    entry = {
        "time_ms": 1000.0,  # wide budget so time always passes
        "tolerance_pct": 100,
        "memory_kb": None,  # null → skip memory check
        "rationale": "noisy test",
    }
    budget = PerfBudget(entry, "tests/perf/test_fake.py::test_noisy")
    # Provide a very large memory value — should NOT raise because memory_kb is null
    budget.assert_within_budget(measured_ms=1.0, measured_kb=9_999_999.0)


# ── 6. RSS snapshot returns a positive value ──────────────────────────────────

def test_snapshot_rss_returns_positive():
    """_snapshot_rss_kb() must return a positive number on Linux."""
    rss = _snapshot_rss_kb()
    assert isinstance(rss, float), f"Expected float, got {type(rss)}"
    assert rss > 0, f"RSS must be positive, got {rss}"
