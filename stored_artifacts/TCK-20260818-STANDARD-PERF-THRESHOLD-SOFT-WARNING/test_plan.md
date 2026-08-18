---
status: active
layer: performance
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-WARNING
tags: [performance, testing, calibration]
---

# Test Plan — TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-WARNING

## Normal flow
1. `pytest tests/tools/ -k perf_assertions -q` (once test coverage for the new module
   exists, or a direct `python3 -c` smoke import) — `assert_perf_threshold`/`perf_check`
   behave correctly for both `hard=True` and `hard=False`, both breach and non-breach.
2. `pytest tests/perf tests/certification tests/arena -m "not slow and not extra_slow" --tb=short -q`
   — the real fast-lane CI command. Must show the same pass/fail/collected counts as
   before this ticket's changes (no test starts failing for a new reason; no collection
   count change).
3. `pytest tests/perf tests/certification tests/arena -m "slow or extra_slow" --resource-budget large --tb=short -q`
   — the slow-lane subset scoped to these 3 directories (full `tests/` slow lane is
   out of scope/too broad for this ticket's verification budget; the modified files are a
   subset of what the real `slow` job runs). Must show all previously-passing tests still
   passing, and previously-recalibrated-but-fragile tests (the 5 precedent files) passing
   normally (their thresholds already carry real headroom, so no warning is expected in a
   normal run).

## Edge cases
- Forced-breach smoke test (temporary, reverted before commit): tighten one already-passing
  threshold in a scratch copy (or via monkeypatch in an ad-hoc script) enough to guarantee
  breach, run under `-W default::tests.tools.perf_assertions.PerformanceThresholdWarning`
  (or `-W always`) with `-rw`, and confirm: (a) the test PASSES (does not fail), (b) pytest's
  warnings summary shows a real `PerformanceThresholdWarning` with actual value, limit, and
  test id in the message.
- `hard=True` path: a converted assertion using `hard=True` (e.g. if any correctness check
  were mistakenly routed through the helper) must still raise `AssertionError`, not warn —
  verified via the same ad-hoc script targeting `perf_check(False, "msg", hard=True)`.

## Failure modes
- Confirm a genuinely broken engine (not a hardware-calibration miss) does not get masked
  silently forever: `PerformanceThresholdWarning` must appear in pytest's `-rw` warnings
  summary (not swallowed), so CI logs still surface it even though the job no longer fails.
- Confirm `tests/certification/test_cert_long_run_stability.py::test_long_run_determinism_parity`
  and the hash-equality assertions are byte-for-byte unmodified (diff review) — regression
  in scope-discipline would be a Hard Rule violation (CLAUDE.md's explicit instruction not
  to touch this).

## Regression-prone paths
- `tests/perf/conftest.py::PerfBudget` — confirm the `hard` parameter default (`False`)
  does not change existing collection-time behavior (`pytest.fail` on missing baseline
  entry is untouched; only the post-lookup comparison behavior changes).
- Fast-lane collection count for `tests/perf tests/certification tests/arena` — compare
  `--collect-only -q` counts before/after (should be identical; only assertion bodies
  change, no test added/removed/marker-changed).

## Commands actually run and results
(filled in during Verify phase, copied into the ticket's Test Summary / Completion Summary)
