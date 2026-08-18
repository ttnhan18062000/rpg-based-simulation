---
status: active
layer: performance
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-WARNING
tags: [performance, testing, calibration]
---

# Plan — TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-WARNING

## Step 1 — Shared mechanism
Create `tests/tools/perf_assertions.py`:
- `PerformanceThresholdWarning(UserWarning)` — purpose-built warning class, module
  docstring records the stopgap rationale and revisit condition (per CLAUDE.md's
  Authoritative Mechanics Rule spirit: divergent/temporary behavior must carry a trail back
  to why).
- `perf_check(ok: bool, message: str, *, hard: bool = False) -> bool` — the low-level
  primitive. `ok=True` → no-op. `ok=False` and `hard=False` (default) → `warnings.warn(...,
  PerformanceThresholdWarning)`, returns `False`, does not raise. `ok=False` and
  `hard=True` → raises `AssertionError`.
- `assert_perf_threshold(actual, limit, message, *, op="<=", hard=False) -> bool` — numeric
  convenience wrapper over `perf_check`, supports `<`, `<=`, `>`, `>=`. Message includes
  actual value, limit, operator, and a best-effort test identity (read from
  `PYTEST_CURRENT_TEST` env var pytest sets during test execution — no fixture required, so
  it works in both fixture-based and plain-function test files).

## Step 2 — Extend existing PerfBudget infra
`tests/perf/conftest.py::PerfBudget.assert_within_budget()` gets a `hard: bool = False`
parameter; its two internal `assert` statements route through
`tests.tools.perf_assertions.perf_check` instead of a bare `assert`. Preserves the existing
message format. No behavior change for any currently-passing caller other than
hard→soft on breach (and there are currently no real callers — `perf_baselines.json` is
empty — so this is forward-looking consistency, verified via the dedicated
`tests/unit/perf/test_perf_guard.py` file... which is out of scope, so this file is
verified instead by a scratch script in test_plan.md Step 2).

## Step 3 — Convert every genuine perf-threshold assert
Per investigation.md's per-file table. Import line added to each converted file:
`from tests.tools.perf_assertions import assert_perf_threshold` (and `perf_check` where a
raw boolean flag, not a numeric comparison, is being asserted — e.g. the
`test_cert_long_run_stability.py` `report.rss_bounded`-style flags).

Pattern for a numeric bound, e.g. `test_perf_movement.py`:
```python
# before
assert result["p95_tick_compute_ms"] < threshold

# after
assert_perf_threshold(
    result["p95_tick_compute_ms"], threshold,
    f"[{entity_count}] p95 tick compute time",
    op="<",
)
```

Pattern for a pre-computed boolean flag, e.g. `test_cert_long_run_stability.py`:
```python
# before
assert report.rss_bounded, f"RSS growth unbounded: ..."

# after
perf_check(report.rss_bounded, f"RSS growth unbounded: ...")
```

Existing `f"...{...}"` message bodies are preserved verbatim inside the `message` argument
wherever practical, so no diagnostic detail is lost — only the hard/soft behavior changes.

## Step 4 — Doc parity
Add a row/note to `docs/testing/regression_policy.md` §3 (Soft Monitors — Alert Only)
naming `tests/tools/perf_assertions.py` as the mechanism backing perf-threshold soft
status in `tests/perf/`, `tests/arena/`, and `tests/certification/`'s performance-only
assertions, with a pointer to this ticket for the "temporary stopgap" framing. This keeps
the doc and code in the parity CLAUDE.md's Authoritative Mechanics Rule requires whenever
test-classification behavior changes.

## Step 5 — Verification
See test_plan.md. Key point: since the 5 precedent-ticket thresholds are already
calibrated with real headroom, a normal local/CI run will NOT breach them — so "does the
warning actually fire with real content" must be verified with a deliberate, temporary,
reverted-before-commit threshold tightening (forced-breach smoke test), not just code
review of the diff.

## Step 6 — Ticket closeout
Standard `tickets/done/` migration, `stored_artifacts/` migration, `working_log.csv`
append, agent-monitoring run+event records, `docs/REGISTRY.yaml` regeneration (since
`docs/testing/regression_policy.md` was modified), `data/runs/`/`reports/release_proof/`
cleanup, frontmatter validation.
