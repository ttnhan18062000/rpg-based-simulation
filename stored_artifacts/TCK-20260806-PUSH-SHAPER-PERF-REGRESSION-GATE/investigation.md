---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-PERF-REGRESSION-GATE
artifact_type: investigation
tags: [observability, performance, simulation-quality]
---

# investigation.md — TCK-20260806-PUSH-SHAPER-PERF-REGRESSION-GATE

## Current Behavior

`tests/perf/test_simq_isolation_overhead.py` (333 lines pre-ticket) has 3 existing tests
(`test_three_mode_engine_overhead_benchmark`, `test_inprocess_simq_overhead_within_regression_band`,
`test_broker_mode_engine_cpu_within_disabled_band`), all comparing SimQ *delivery* mode
(`QUALITY_SCORING_DISABLED`/`QUALITY_FEED_MODE=inprocess`/`QUALITY_FEED_MODE=broker`) — none vary
`ENABLE_PUSH_EVENT_SHAPERS`. Confirmed via grep: zero references to that flag anywhere in the file
before this ticket. `src/observability/event_shapers.py`'s Phase 1 performance validation
(`TCK-20260806-PUSH-SHADOW-VALIDATION-PERF`, DONE) used an uncommitted scratch script
(`/tmp/.../perf_compare.py`, warmup=30/sample=150, reduced scale) — real, but not a standing,
committed gate.

`BenchHarness.run_benchmark()` (`src/perf/bench_harness.py:38`) takes `initial_state:
AuthoritativeState` and `flags: Dict[str, bool]` (for `no_replay`/`no_frame_pacing` — a *different*
mechanism from `AuthoritativeState.feature_flags`, which is where `ENABLE_PUSH_EVENT_SHAPERS`
lives, per `kernel.py`'s `_phase_observability`: `state.feature_flags.get("ENABLE_PUSH_EVENT_SHAPERS",
"ON")`). `_build_state()` (test file, calls `tools.calibrate_simq._load_world_state`) returns a
state with `feature_flags={}` (empty dict, confirmed this session), so the existing 3 tests
implicitly run with the shaper path at its default `"ON"` — but never explicitly test the `OFF`
(old-extractor) comparison, and never isolate the shaper's own cost from the SimQ-scoring-pipeline
cost the existing 3 tests measure.

## Mechanics/Engine Constraints

None — this is a test-infrastructure-only change, no simulation-law or engine-contract surface
touched. `docs/simulation_quality/quality_scoring_contract.md` §3 (Performance Contract, §3.1 Zero
Simulation Impact) is the relevant contract this gate protects, not one it changes.

## Docs Requiring Update

- `docs/performance/simq_isolation_overhead.md`: new "Push-Shaper Registry Overhead" section
  documenting the method, committed 2-run measurement, and locked threshold — this file is the
  authoritative source doc for everything `test_simq_isolation_overhead.py` measures, per its own
  existing convention ("this doc summarizes, it does not duplicate, that test's own measurement
  code").

## Parity Ledger Overlap

None. This ticket adds test infrastructure only — no behavior change to any simulation-law-bearing
code, so no `docs/parity_ledger/*.yaml` entry is affected (confirmed: `implementation.files_changed`
below contains no `src/` path, only `tests/` and `docs/`).

## Prior Work

- `TCK-20260806-PUSH-SHADOW-VALIDATION-PERF` (DONE) — the one-off scratch-script measurement this
  ticket formalizes into a standing, committed gate.
- `TCK-20260702-OBSISO-ISOLATION-PROOF` (the ticket that built the existing 3-mode harness this
  ticket extends, per this file's own module docstring).

## Risks and Open Questions

None found to be genuinely open. The existing harness's structure extended cleanly — no sibling
file was needed; a new helper (`_run_mode_inprocess_with_shaper_flag`) plus 2 new
`@pytest.mark.slow` tests, following the exact same pattern (`ModeResult`, band-tolerance
threshold, print + assert) as the 3 existing tests.

## Anti-Drift Hazards

- The new tests pin `QUALITY_FEED_MODE=inprocess` explicitly (not left to default) so a future
  change to the harness's own default mode can't silently change what this gate is measuring.
- `dataclasses.replace(state, feature_flags={**(state.feature_flags or {}), "ENABLE_PUSH_EVENT_SHAPERS": ...})`
  merges into whatever `feature_flags` `_build_state()` already returns, rather than overwriting it
  wholesale — protects against a future `_build_state()` change that starts returning non-empty
  `feature_flags` (e.g. a world-specific override) from being silently clobbered by this test.
