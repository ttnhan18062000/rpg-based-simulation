---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-PERF-REGRESSION-GATE
phase: done
date: 2026-08-06
tags: [observability, performance, simulation-quality]
---

# TCK-20260806-PUSH-SHAPER-PERF-REGRESSION-GATE

## Title
Build a standing, committed performance regression gate for the push-shaper registry's cumulative
cost

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 1 (build first) of `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC`. Phase 1's
own performance validation (`TCK-20260806-PUSH-SHADOW-VALIDATION-PERF`, DONE) confirmed no
measurable overhead from 3 domains' worth of shapers, but did so via an uncommitted, reduced-scope
scratch script (`perf_compare.py`, warmup=30/sample=150 vs. the standard doc's 100/1000) — a real
one-off measurement, not a standing gate. `tests/perf/test_simq_isolation_overhead.py` (the
existing, committed harness with locked regression-guard thresholds) currently has **zero**
knowledge of `ENABLE_PUSH_EVENT_SHAPERS` — it was never extended to measure the shaper path at all.

Phase 2 adds 4-5x more shapers (STRATEGY, PROGRESSION, WORLD DYNAMICS, SOCIAL, plus deferred
instrumentation) on top of Phase 1's 3. Re-running an ad-hoc script by hand once per phase does
not catch gradual overhead accumulation across children, and each phase's implementer would need
to re-derive the measurement methodology from scratch. This ticket builds the standing gate once,
so every subsequent Phase 2 child (and any future phase) is measured against a real, enforced,
committed threshold automatically.

## Scope
1. Read `tests/perf/test_simq_isolation_overhead.py` in full — its existing `ModeResult` dataclass,
   the 3 existing tests (`test_three_mode_engine_overhead_benchmark`,
   `test_inprocess_simq_overhead_within_regression_band`,
   `test_broker_mode_engine_cpu_within_disabled_band`), and how it structures its 3-mode
   comparison (whatever those 3 modes currently are — confirm by reading, don't assume).
2. Add a 4th dimension to the harness (or a parallel, sibling test file if the existing one's
   structure doesn't cleanly extend) that measures `ENABLE_PUSH_EVENT_SHAPERS=ON` vs `OFF` CPU
   time delta, using the harness's own existing `BenchHarness`/measurement machinery (not a new
   one) at the doc's standard warmup=100/sample=1000 scale (not the reduced scale Phase 1's
   scratch script used for speed — this is a committed gate, not a one-off check, so use the real
   scale from the start).
3. Establish a locked regression-guard threshold (mirroring the existing tests' pattern —
   `test_inprocess_simq_overhead_within_regression_band`'s style) based on real measured data from
   this ticket's own run, not a guessed number.
4. Wire the new test into whatever CI/Makefile target already runs
   `test_simq_isolation_overhead.py`, so it's exercised automatically going forward — confirm via
   `grep -rn "test_simq_isolation_overhead" Makefile .github/` where it's currently invoked from.
5. Document the new gate's existence and how to interpret a failure in
   `docs/performance/simq_isolation_overhead.md` (the existing doc `event_shapers.py`'s own module
   docstring already cross-references).

## Out of Scope
- Re-measuring Phase 1's already-validated COMBAT/ECONOMY/FACTION overhead — that's done, this
  ticket's baseline should include it as already-active (flag defaults `ON`), not re-litigate it.
- Any change to the shaper registry itself — this is a test-infrastructure-only ticket.
- Performance work for the shapers built in children 2-6 — this ticket builds the *gate*, not the
  shapers; those children's own Test phases run against this gate once it exists, and child 7
  re-runs it with the full registry active.

## Acceptance Criteria
- [ ] `test_simq_isolation_overhead.py` (or a clearly-named sibling file) has a real, running test
      comparing `ENABLE_PUSH_EVENT_SHAPERS=ON` vs `OFF` CPU overhead at standard doc scale
      (warmup=100/sample=1000)
- [ ] A locked regression-guard threshold exists, derived from real measured data, not guessed
- [ ] The new test is wired into the same CI/Makefile invocation path as the existing 3 tests in
      this file
- [ ] `docs/performance/simq_isolation_overhead.md` documents the new gate
- [ ] Scoped pytest run (`tests/perf/`) passes

## Related Tickets
- TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC (parent epic)
- TCK-20260806-PUSH-SHADOW-VALIDATION-PERF (DONE — Phase 1's one-off measurement methodology this
  ticket formalizes into a standing gate)

## Related Docs
- `docs/performance/simq_isolation_overhead.md`
- `docs/simulation_quality/quality_scoring_contract.md` §3 (Performance Contract, §3.1 Zero
  Simulation Impact)

## Related Stored Artifacts
None yet — will be created at
`staging_artifacts/TCK-20260806-PUSH-SHAPER-PERF-REGRESSION-GATE/` during implementation.

## Related Code Areas
- `tests/perf/test_simq_isolation_overhead.py`
- `src/observability/event_shapers.py`
- `src/domains/optimization/feature_flags.py` (`ENABLE_PUSH_EVENT_SHAPERS`)

## Assumptions / Open Questions
- Whether the existing harness's 3-mode structure extends cleanly to a 4th flag dimension, or
  needs a sibling file, is genuinely open until this ticket's own Investigate phase reads the file
  — not assumed here.

## Implementation Notes
- Confirmed the existing 3-mode harness's structure extends cleanly — no sibling file needed.
  Added `_run_mode_inprocess_with_shaper_flag(monkeypatch, shapers_on: bool)`, reusing
  `_build_state()` + `dataclasses.replace(state, feature_flags={...})` to pin
  `ENABLE_PUSH_EVENT_SHAPERS` explicitly under the `inprocess` SimQ mode (orthogonal to the
  existing `QUALITY_FEED_MODE` dimension).
- Added `test_push_shaper_registry_overhead_benchmark` and
  `test_push_shaper_registry_overhead_within_regression_band` (`@pytest.mark.slow`), mirroring the
  existing 3 tests' `ModeResult`/band-tolerance pattern exactly.
- Ran both new tests twice for a real convergence check (same discipline as this file's own
  existing doc): Run 1 overhead -3.75%, Run 2 -2.35%, OFF-leg convergence 1.7% (well within the
  doc's existing 10% threshold). Locked the regression band at 25% — margin above measured noise,
  not the raw (negative) overhead, same philosophy as the existing in-process-vs-disabled
  threshold, since a threshold locked near 0% would flake on noisy hardware for a genuinely
  near-zero-cost change.
- Confirmed no new CI/Makefile wiring is needed: this file's existing 3 tests were never invoked by
  a dedicated Makefile target either — they're already covered only by
  `.github/workflows/test.yml`'s broad `pytest tests/ -m "slow or extra_slow"` sweep (the `slow`
  job), which automatically picks up the 2 new `@pytest.mark.slow` tests in the same file.
- Documented the new gate in `docs/performance/simq_isolation_overhead.md`'s new "Push-Shaper
  Registry Overhead" section (method, committed 2-run table, locked threshold, CI-wiring note).

## Test Summary
- `pytest tests/perf/test_simq_isolation_overhead.py -m slow -s -q`: 5 tests total (3 pre-existing,
  unmodified; 2 new), all passing. New tests individually confirmed: benchmark test passed twice
  (convergence check), regression-band test passed with -2.37% vs. the 25% band.

## Files Changed
- `tests/perf/test_simq_isolation_overhead.py` — new helper + 2 new `@pytest.mark.slow` tests
- `docs/performance/simq_isolation_overhead.md` — new "Push-Shaper Registry Overhead" section

## Completion Summary
Built a standing, committed performance regression gate for the push-shaper registry's cumulative
CPU cost, extending the existing `test_simq_isolation_overhead.py` harness (which previously had
zero knowledge of `ENABLE_PUSH_EVENT_SHAPERS`) rather than building new tooling from scratch.
Locked a 25% overhead band from 2 real, convergence-checked measurement runs on this session's
hardware (measured actual overhead: -3.75% and -2.35% — the shaper path is measurably faster, not
slower, at this scale, plausibly because it reads typed update-record fields directly instead of
the old extractor's full-state diffing). No new CI/Makefile wiring was needed — confirmed the
existing broad `slow`-marker sweep already covers the new tests. This ticket is Child 1 of
`TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC`, built first so children 2-6 (the
new shaper-registry builds) are each measured against a real, enforced baseline as they land,
rather than a one-off check discovered retroactively.
