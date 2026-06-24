---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260624-PERF-GUARD-INFRA
phase: done
date: 2026-06-24
tags: [performance, infrastructure, baseline, perf-guard, memory, fixture]
---

# TCK-20260624-PERF-GUARD-INFRA

## Title
Implement dynamic performance guard infrastructure (perf_baselines.json + perf_budget fixture + perf_guard CLI)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
All current perf tests hardcode thresholds as ad-hoc literals with no warmup, no sampling, no memory tracking, and no mechanism to distinguish intentional cost increases from regressions. This ticket introduces a three-component system:

1. **`perf_baselines.json`** (repo root) — committed, reviewed, annotated source of truth for expected time and memory budgets per test
2. **`perf_budget` pytest fixture** (`tests/perf/conftest.py`) — measures wall-clock time and RSS memory delta, compares against the baseline with per-test tolerance, fails with an actionable message pointing to `make perf-measure`
3. **`tools/perf_guard.py`** + **`make perf-measure`** target — CLI that re-runs perf tests with instrumentation and outputs a proposed `perf_baselines.json` diff for human review

This is the prerequisite for `TCK-20260624-FIX-PERF-BUDGETS`, which migrates existing perf tests to the new system.

## Scope

### `perf_baselines.json`
Schema:
```json
{
  "version": 1,
  "hardware_class_default": "B",
  "entries": {
    "<pytest node ID>": {
      "time_ms": <float>,
      "memory_kb": <float | null>,
      "tolerance_pct": <int>,
      "hardware_class": "A" | "B" | "C",
      "rationale": "<string>",
      "updated_by": "<ticket ID>",
      "updated_at": "<YYYY-MM-DD>"
    }
  }
}
```
- `memory_kb: null` — skip memory assertion for inherently noisy tests
- `tolerance_pct` — per-test band; typical values: 20% (stable), 50% (moderate noise), 100% (intentionally wide for VM-sensitive tests)
- Hardware classes per `docs/engine/performance_contract.md`: A = dedicated CI, B = shared VM, C = laptop/dev

### `perf_budget` fixture (`tests/perf/conftest.py`)
- Loads `perf_baselines.json` at session start (cached, not re-read per test)
- Resolves test entry by `request.node.nodeid`
- **Missing entry → `pytest.fail`** (strict — author must add an entry before the test runs)
- Provides `snapshot_rss() -> float` (reads `/proc/self/statm`, page_size × RSS pages in KB; Linux-only, no extra deps)
- Provides `assert_within_budget(measured_ms, measured_kb=None)`:
  - Compares against `time_ms * (1 + tolerance_pct/100)`
  - Compares against `memory_kb * (1 + tolerance_pct/100)` if both are non-null
  - Failure message includes: measured value, budget, tolerance, rationale from baseline, and instruction to run `make perf-measure`
- Hardware class override via env var `PERF_HARDWARE_CLASS` (default: value from baseline entry, fallback: `"B"`). Hardware class is informational only in first pass — it does not yet modify the tolerance band (that can follow when CI hardware is classified).

### `tools/perf_guard.py`
Two subcommands:

**`measure`** — run each test in `tests/perf/` with instrumentation, output proposed baseline diff:
```
python3 tools/perf_guard.py measure [--test <node_id>]
```
Output:
- UNCHANGED (within tolerance)
- REGRESSION (>tolerance above current baseline)
- OVERSPEND (above tolerance, no existing baseline or baseline too low)
- NEW (no entry in perf_baselines.json)
- For each non-UNCHANGED: proposed new JSON entry with `time_ms`/`memory_kb` set to measured values, `rationale`/`updated_by`/`updated_at` left as `"TODO"` placeholders

**`show`** — pretty-print current baseline with pass/fail status for last-run measurements (reads from a `.perf_last_run.json` scratch file written by the fixture):
```
python3 tools/perf_guard.py show
```

### `Makefile` target
```makefile
perf-measure:
    python3 tools/perf_guard.py measure
```

### Developer workflow (doc update)
Add a section to `docs/testing/v2_test_taxonomy.md` (or `docs/engine/performance_contract.md`) documenting:
1. How to add a new perf test (must add baseline entry first, or test will `pytest.fail`)
2. How to update after an intentional performance change (`make perf-measure` → edit rationale → commit with code change)
3. How to interpret wide tolerance bands vs narrow ones

## Out of Scope
- Migrating existing perf tests to use the fixture (that is `TCK-20260624-FIX-PERF-BUDGETS`)
- CPU time tracking (`psutil` dependency — defer to follow-up)
- Auto-detecting hardware class at runtime (env var override is sufficient for now)
- Modifying tolerance based on hardware class (defer until CI hardware is classified)

## Acceptance Criteria
- `perf_baselines.json` exists at repo root with a valid schema (validate with a unit test)
- `perf_budget` fixture is importable from `tests/perf/conftest.py`
- A test with a baseline entry and a budget of 10ms ± 20%:
  - passes when measured value is 9ms
  - fails with an actionable message when measured value is 13ms
  - fails (not skips) when no baseline entry exists
- `python3 tools/perf_guard.py measure` runs without error and produces output on stdout
- `make perf-measure` invokes the tool
- `tests/unit/perf/test_perf_guard.py` covers: schema validation, fixture pass/fail/missing-entry, RSS snapshot, proposed diff output
- `docs/testing/v2_test_taxonomy.md` updated with perf-test authoring section

## Related Tickets
- `TCK-20260624-FIX-PERF-BUDGETS` — depends on this ticket; migrates existing tests to new system
- `docs/engine/performance_contract.md` — measurement methodology (§3.2 warmup/sample requirements)

## Related Docs
- `docs/engine/performance_contract.md` — Hardware Class A/B/C definitions, §3.2 measurement protocol, §4.2 instrumentation ceiling, §5 regression flag rule
- `docs/testing/v2_test_taxonomy.md` — test classification
- `docs/architecture/adr-005 performance`

## Related Stored Artifacts
None

## Related Code Areas
- `tests/perf/conftest.py` — new fixture (create or extend)
- `tests/perf/` — all files (read-only in this ticket; migrated in FIX-PERF-BUDGETS)
- `tools/perf_guard.py` — new CLI
- `Makefile` — new `perf-measure` target
- `perf_baselines.json` — new file at repo root

## Assumptions / Open Questions
- `/proc/self/statm` is Linux-only — confirm that is acceptable (this project is Linux-only per environment)
- The `perf_budget` fixture should live in `tests/perf/conftest.py`, not the root `tests/conftest.py`, so it does not add overhead to non-perf test collection
- `perf_guard.py measure` does NOT auto-commit or auto-modify `perf_baselines.json` — it only prints a proposed diff. Human reviews and commits.
- Initial `perf_baselines.json` entries will be empty (or contain only placeholder entries) — `FIX-PERF-BUDGETS` populates them after measuring the post-fix values

## Implementation Notes

### RSS snapshot (no psutil required)
```python
import pathlib

def snapshot_rss_kb() -> float:
    # /proc/self/statm: <vsize> <rss> <shared> ...  (all in pages)
    rss_pages = int(pathlib.Path("/proc/self/statm").read_text().split()[1])
    return rss_pages * 4.0   # 4KB per page on x86-64
```

### Fixture skeleton
```python
@pytest.fixture(scope="session")
def _perf_baselines():
    path = pathlib.Path("perf_baselines.json")
    if not path.exists():
        return {}
    return json.loads(path.read_text())["entries"]

@pytest.fixture
def perf_budget(request, _perf_baselines):
    test_id = request.node.nodeid
    entry = _perf_baselines.get(test_id)
    if entry is None:
        pytest.fail(
            f"No perf baseline entry for:\n  {test_id}\n"
            f"Run `make perf-measure` and add an entry to perf_baselines.json."
        )
    return PerfBudget(entry, test_id)
```

### `perf_guard.py measure` approach
For each test in `tests/perf/`:
1. Import and call the test function directly (not via subprocess) to avoid pytest overhead
2. Or: run `pytest <test_id> --tb=no -q` and parse timing from a custom pytest plugin hook that the guard injects
3. The simplest: use `subprocess.run(["python3", "-m", "pytest", test_id, "-p", "no:timeout", "--tb=no", "-q"])` and measure elapsed from outside — but this loses per-test granularity

Recommended: small pytest plugin class (`PerfMeasurePlugin`) that hooks `pytest_runtest_call` to record timing and RSS delta per test, then writes `.perf_last_run.json`.

### Schema validation unit test
```python
# tests/unit/perf/test_perf_guard.py
def test_baseline_schema_is_valid():
    data = json.loads(pathlib.Path("perf_baselines.json").read_text())
    assert data["version"] == 1
    for key, entry in data["entries"].items():
        assert "time_ms" in entry
        assert "tolerance_pct" in entry
        assert "rationale" in entry
        assert entry.get("memory_kb") is None or isinstance(entry["memory_kb"], (int, float))
```

## Test Summary
Run: `pytest tests/unit/perf/test_perf_guard.py -v`
Run: `python3 tools/perf_guard.py measure --test tests/perf/test_phase3_adventure_decision_budget.py::test_phase3_adventure_decision_perf_budget`

## Files Changed
- `perf_baselines.json` (new) — repo root, schema v1, empty entries
- `tests/perf/conftest.py` (extended) — added `_snapshot_rss_kb`, `PerfBudget`, `_perf_baselines`, `perf_budget` fixtures; existing `perf_harness`/`perf_reporter`/`perf_report_dir` unchanged
- `tests/unit/perf/test_perf_guard.py` (new) — 6 unit tests; all pass
- `tools/perf_guard.py` (new) — `measure` + `show` subcommands with `PerfMeasurePlugin`
- `Makefile` (modified) — added `perf-measure` target + `.PHONY` entry
- `docs/testing/test_taxonomy.md` (extended) — added Section 4 "Performance Test Authoring"

## Completion Summary
All six components delivered. 6/6 unit tests pass. Existing perf test collection unaffected (60/71 collected, 11 deselected by markers). `perf_baselines.json` starts empty — TCK-20260624-FIX-PERF-BUDGETS will populate entries after measuring migrated tests. Staging artifacts moved to `stored_artifacts/`.
