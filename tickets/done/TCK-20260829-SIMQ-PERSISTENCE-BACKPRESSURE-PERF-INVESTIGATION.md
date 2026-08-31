---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION
phase: done
date: 2026-08-29
tags: [performance, observability, simulation-quality]
---

# TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION

## Title
Investigate Tick-Time Persistence/Telemetry I/O Overhead Causing Observability Backpressure in
Long/Heavy SimQ Calibration Runs

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Filed from `TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH`'s investigation. That
ticket found that several `tests/unit/worldassembly/test_corpus_diversity.py` grade-stability
tests (3-trial batches driving `tools/calibrate_simq.py::_run_engine` for 500-1000 real ticks)
hit `tests/conftest.py`'s default `--resource-budget medium` 60-second SIGALRM cap — confirmed
reproducible even in a fully isolated single-test run (no contention from any other concurrent
process). With the cap removed (`--resource-budget large`, 600s), the *same* scenario
(`test_urban_political_seed42_1000t_social_grade_stability`) instead completed in 84s but then
failed with `tools.calibrate_simq.CalibrationIntegrityError: ... events were lost to queue
overflow or SURVIVAL mode-shed` — a real observability-pipeline backpressure event, not a
floor-calibration issue.

Per-tick `WatchdogTrip` log evidence collected during that investigation consistently shows the
`persistence` phase dominating tick compute time by a wide margin over every other phase,
including `locomotion` (the phase most directly affected by `TCK-20260824-TOWN-CENTER-POINTER-FIX`'s
navigation change):

```
phase_costs: {..., 'locomotion': 0.565795, ..., 'persistence': 77.770284}   # tick ~20
phase_costs: {..., 'locomotion': 0.828692, ..., 'persistence': 127.477717}  # tick ~13
phase_costs: {..., 'locomotion': 0.920192, ..., 'persistence': 88.479979}   # tick ~14
```

`persistence` (telemetry/event JSONL writing) is consistently 60-120ms out of a total tick cost of
roughly 100-150ms — locomotion is under 1% of that. This suggests the resource-budget timeouts
observed in the corpus-diversity investigation are not primarily a navigation-compute regression
at all, but a pre-existing, worsening persistence/telemetry I/O bottleneck that the town_center
navigation fix's slightly-longer runs (more distance traveled, more ticks with active entities)
merely pushed over the 60s/600s edges more often than before.

## Scope
- Profile `src/simulation_quality/persistence.py`'s `QualityPersistence` write path and the
  broader event-telemetry pipeline (`src/observability/`) under the same real, unmocked
  `Kernel`-driven load these grade-stability tests exercise (`tools/calibrate_simq.py::_run_engine`,
  500-1000 real ticks) — use `/python-performance-optimization` (per CLAUDE.md's Proactive Tool
  Use table) to identify the actual I/O/serialization bottleneck inside the `persistence` phase
  cost bucket.
- Determine whether the `QueueDrainWorker` backpressure mechanism's `SURVIVAL` mode-shed threshold
  (`src/observability/`'s `EventRecorder` backpressure modes) is tuned appropriately for this
  workload, or whether the root fix belongs in reducing write volume/frequency, batching, or
  changing the serialization format.
- Decide whether `tests/conftest.py`'s default `--resource-budget medium` (60s) is simply
  under-provisioned for these specific 3-trial x 500-1000-tick test scenarios (a test-invocation
  fix — e.g. marking them to always run with `--resource-budget large`) as a *separate*, narrower
  question from the backpressure/perf root cause itself — both may need addressing, but they are
  not the same fix.
- Once a root cause and fix are identified, re-run the 5 tests `TCK-20260828-CORPUS-DIVERSITY-
  TOWN-CENTER-BASELINE-REFRESH` deferred here for this exact reason
  (`test_simq_routing_test_seed42_1000t_cognition_grade_stability`,
  `test_hero_guild_routing_seed42_1000t_cognition_grade_stability`,
  `test_unit_selfmodel_pilot_seed42_1000t_cognition_economy_narrative_grade_stability`,
  `test_urban_political_seed42_1000t_social_grade_stability`,
  `test_urban_political_seed123_1000t_social_economy_grade_stability`), plus
  `test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability` (not one of
  `TCK-20260828`'s 13 named tests, but independently observed in this same investigation to show
  the identical `CalibrationIntegrityError` failure mode — additional corroborating evidence, not
  a formally-deferred test), to determine whether they then reveal a genuine, calibratable floor/
  tolerance drift (the outcome `TCK-20260828`'s own ticket originally assumed for all 13) — that
  re-baseline work, if still needed once these tests can actually complete, belongs in its own
  follow-up ticket, not this one (this ticket is scoped to root-causing and fixing the
  backpressure/timeout problem itself).

## Out of Scope
- Re-baselining `test_corpus_diversity.py`'s floor/tolerance values directly — that is either
  already done (`TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH`'s 3 re-baselined
  tests) or explicitly deferred pending this ticket's own fix (a follow-up ticket, not this one).
- `TCK-20260824-TOWN-CENTER-POINTER-FIX`'s navigation logic — already complete, correct, and out
  of scope; this ticket investigates a pre-existing perf characteristic the navigation fix merely
  made more visible, not a defect in the navigation fix itself.
- The already-known, already-deferred `Kernel` wall-clock mid-tick throttle nondeterminism finding
  (see Related Docs / Assumptions below) — related (same "determinism/timing under load" class of
  issue) but a distinct, separately-tracked decision the user has already chosen to let sit; do
  not fold a fix for it into this ticket's own scope without a fresh, separate decision.
- `TCK-20260829-LIFECYCLE-HEIRLOOM-INVENTORY-TUPLE-TYPEERROR`'s bug fix — unrelated (a pure
  type-normalization bug in death/heir succession, already fixed separately).

## Acceptance Criteria
- [x] Real profiling data (not guessed) identifies the specific bottleneck inside the
      `persistence`/telemetry-I/O tick-phase cost.
- [x] A concrete fix (or a documented decision not to fix, with rationale) is implemented and
      verified to reduce `persistence` phase cost meaningfully for a representative 1000-tick run.
- [x] `tests/conftest.py`'s `--resource-budget` question is explicitly decided (fixed at the
      workload/test level, or left as-is with rationale) — not left ambiguous.
- [x] The 6 tests named in Scope are re-run under the fix and their outcome (pass, or a now-clean
      floor/tolerance drift needing its own re-baseline ticket) is reported.

## Related Tickets
- TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH (discovered and investigated this
  finding; deferred these 6 tests here rather than force-fitting a floor edit onto a timeout/
  backpressure failure)
- TCK-20260824-TOWN-CENTER-POINTER-FIX (the navigation fix whose slightly-longer runs made this
  pre-existing perf characteristic newly visible as test timeouts)

## Related Docs
- `docs/engine/performance_contract.md` (Hardware Classes A/B/C, scaling limits — the natural
  home for any new perf-budget documentation this investigation produces)
- `docs/testing/regression_policy.md` §3 (Soft Monitors — `tests/unit/worldassembly/` is already
  a soft monitor, not a hard gate; this investigation does not change that classification)

## Related Stored Artifacts
None yet — to be created at Investigate phase (standard tier).

## Related Code Areas
- `src/simulation_quality/persistence.py` (`QualityPersistence` write path)
- `src/observability/` (`EventRecorder` backpressure modes, `QueueDrainWorker`)
- `tools/calibrate_simq.py` (`_run_engine`, the harness these tests drive)
- `tests/conftest.py` (`--resource-budget` time-limit enforcement)

## Assumptions / Open Questions
- Whether this is the same root mechanism as the already-known, already-deferred finding that
  `Kernel`'s wall-clock mid-tick throttle breaks strict determinism under `audit_mode=False`
  (both are "timing/determinism sensitivity under system load" issues) is an open question for
  Investigate to assess — they may be related symptoms of the same underlying architecture
  decision (wall-clock-based budgets/throttles rather than deterministic tick-count budgets), or
  genuinely separate. Do not assume either way; the prior finding stays tracked separately and
  the user has already chosen to let it sit — this ticket's Investigate phase should surface the
  relationship, not silently merge or silently ignore it.
- Whether the fix belongs in `persistence.py`'s write strategy (batching, async flush, format),
  the `EventRecorder` backpressure thresholds, or `tests/conftest.py`'s resource budget itself
  (or some combination) is left to Investigate/Plan to determine from real profiling data.

## Implementation Notes

Implemented `staging_artifacts/.../plan.md` Steps 1-9 exactly, with the execution-detail
deviations recorded in that file's own new "Deviations" section (test-design corrections found
while actually running the tests — no change to the plan's substance).

**Step 1 — `src/engine/replay_manager.py`.** Deleted `_rotate_chunk()`'s synchronous
budget-check pre-check block (the `_to_dict`/`json.dumps`/`get_default_registry().check(...)`
sequence that used to run on the main tick thread before `executor.submit()`). Relocated the
budget check into `_execute_persistence()` (the background-thread method), reusing the
`chunk_bytes` value that method already computes for `_avg_chunk_size_bytes` — zero new
serialization work, one full redundant `json.dumps` walk per chunk rotation removed. The
`# INFRA-193:` tag moved with the check. `async_write=False` (the shutdown/finalize path) is
unaffected — it still calls `_execute_persistence()` directly and therefore still runs the check
synchronously in that one legitimately-synchronous case.

**Step 2 — `src/simulation_quality/persistence.py`.** `QualityPersistence` now has a class
constant `_FLUSH_INTERVAL = 50` and an instance counter `_pending_writes`. `write()` increments
the counter and flushes only every 50th record, resetting the counter. `shutdown()` was already
unconditional (`flush()` then `close()`) — no change needed there; it correctly flushes any
remainder below the threshold.

**Step 3 — `src/observability/event_recorder.py`.** Same batch-of-50 pattern applied to
`EventRecorder._write_envelope_to_file()` via a new `_FLUSH_INTERVAL = 50` class constant and
`_pending_envelope_writes` instance counter. Additionally added an explicit `flush()` call in
`shutdown()` immediately before `close()` (belt-and-suspenders — `close()` already flushes
internally — added so both non-authoritative writer classes in this ticket read the same way as
`QualityPersistence.shutdown()`'s already-explicit flush-then-close).

**Step 4 — `CanonicalStateHasher` cadence: explicit decision NOT to change it.**
`CanonicalStateHasher.get_hash()`'s every-tick cadence in NORMAL/CONSTRAINED mode
(`src/engine/checkpoint.py:38-107`, `Kernel._phase_persistence()` at
`src/engine/kernel.py:1158-1172`) is deliberately NOT changed by this ticket. Rationale: it is a
`verified`, P2 parity-ledger contract (`INFRA-223`, `docs/parity_ledger/infrastructure.yaml`),
documented identically in `docs/engine/known_limitations.md` §2.4 and `docs/engine/kernel.md`,
that exists specifically to give replay/determinism verification a fresh canonical hash every
tick in the common case. Routing it through the already-present but currently-bypassed
`BudgetedCanonicalHasher` (`checkpoint.py:110-155`) would reduce persistence cost but would also
measurably reduce per-tick determinism-verification coverage — a real product/architecture
trade-off, not a pure efficiency win like Steps 1-3. This ticket's own scope explicitly allows
closing AC2 via "a concrete fix (or a documented decision not to fix, with rationale)" — this is
that documented decision. Changing this cadence remains available as a future ticket, gated on a
fresh, explicit `docs/guidelines/intentional_divergences.md` entry and user sign-off, not a
default assumed here.

**Step 5 — resource-budget decision: Option A (marker mechanism).** Added a
`resource_budget_large` pytest marker read inside `tests/conftest.py`'s `pytest_runtest_setup(item)`
hook: when present, it forces the effective `--resource-budget` to `"large"` (600s/8GB) unless
the CLI value is `"off"` (the profiler escape hatch, which always wins). Registered in
`pyproject.toml`'s `[tool.pytest.ini_options] markers` list. Option A was selected over Option B
(directory-wide default change) because it is scoped exactly to the tests that need it, with no
blast radius on the rest of `tests/unit/worldassembly/`.

**Step 6 — applied the marker.** Added `@pytest.mark.resource_budget_large` (alongside the
existing `@pytest.mark.slow`) to exactly the 6 named tests in
`tests/unit/worldassembly/test_corpus_diversity.py`. Confirmed via
`pytest --collect-only -m resource_budget_large` that exactly these 6 collect, no more, no fewer.

**Step 7 — before/after measurement + regression guard.** Real measured numbers (500-tick clean
`urban_political`/seed=42 Kernel-driven run, same methodology as `investigation.md`'s own
baseline):
- Pre-fix (investigation.md): mean=8.891ms, sum=4445.7ms, 29.3% share, **max=243.150ms**.
- Post-fix (this ticket): mean=8.817ms, sum=4408.6ms, 30.3% share, **max=83.507ms**.

The mean/sum barely move because the `persistence` tick-phase's steady-state cost is dominated by
`CanonicalStateHasher.get_hash()` (deliberately untouched, Step 4) — Root cause #1's fix instead
eliminates the ~100-tick-periodic redundant-serialization *spikes* specifically (max dropped from
243ms to 83ms, a real ~66% cut in worst-case single-tick persistence cost). Root cause #2's fix
(flush batching) targets a separate pipeline (`QualityPersistence`/`EventRecorder`'s background
drain-worker thread) not reflected in `_phase_costs["persistence"]` at all — its real effect shows
up in Step 8's outcome instead (all 6 named tests now complete without `CalibrationIntegrityError`
or `TimeoutError`, where they previously did not).

A separate 1000-tick clean run (the representative length AC2 asks for) measured **23.3%**
persistence-phase share of total tick cost. Added
`tests/perf/test_persistence_phase_cost.py::test_persistence_phase_cost_regression_guard_1000t`
— a soft-monitor (warn, never fail) guard using `tests/tools/perf_assertions.py`'s
`assert_perf_threshold` pattern, ceiling locked at 33.3% (23.3% measured + 10 percentage points
headroom). Re-running the test standalone reproduced 22.9%, confirming the measurement is stable.

**Step 8 — 6 named tests re-run under the fix.** 5 of 6 pass. The 6th,
`test_urban_political_seed42_1000t_social_grade_stability`, now completes (no
`CalibrationIntegrityError`, no `TimeoutError` — confirming the backpressure/timeout root cause is
fixed) but fails on a genuine floor/tolerance drift: `SOCIAL: mean_score=36.8373` vs.
`anchor_score=15.45` (tolerance `abs_floor=6.5052`), per-trial values `[32.3, 34.424, 43.788]`.
Per the plan's explicit "Do NOT touch" instruction, this assertion/floor was left unmodified.
**This is a now-clean floor/tolerance drift that needs its own re-baseline follow-up ticket** —
out of this ticket's scope, reported here per AC4.

**Step 9 — parity ledger confirmation.** Re-read `INFRA-193`, `INFRA-223`, `INFRA-194`,
`INFRA-198`, `INFRA-199`, `INFRA-320` in `docs/parity_ledger/infrastructure.yaml` against the
actual final diff. All six still accurately describe current behavior: `INFRA-193`'s `text`
describes only `ArtifactBudgetRegistry.check()`'s own size/action/logging semantics, not caller
timing (Step 1 only relocated the call site); `INFRA-194`/`INFRA-198`/`INFRA-199` describe
threshold math, inflight-count bookkeeping, and mode-transition logic, none of which Steps 1-3
touched; `INFRA-223` describes the canonical-hash cadence, explicitly untouched per Step 4;
`INFRA-320` (status `verified`, priority `P0`) describes the queue-overflow/SURVIVAL guard itself,
unchanged — its four listed `test_path` tests
(`tests/simulation_quality/test_calibrate_simq.py::TestQueueOverflowGuard::*`, `::TestSurvivalModeGuard::*`,
`tests/simulation_quality/test_evaluate_harness.py::TestQueueOverflowGuardIntegration::*`) were
run as part of the Step 1-3 regression suite and pass. None of these six required editing.

**Post-Implement update (Parity phase):** the Parity phase (run after this Implementation Notes
section was originally written) added a new entry, `INFRA-397`, to
`docs/parity_ledger/infrastructure.yaml` — status `verified`, priority `P2` — documenting the
`QualityPersistence.write()`/`EventRecorder._write_envelope_to_file()` batch-of-50 flush cadence
introduced by Steps 2-3 as new, real, operationally-significant behavior (up to 49 unflushed
records can now be lost on an unclean crash, vs. ~0 before), with `test_path` covering
`tests/simulation_quality/test_persistence.py::test_quality_persistence_write_does_not_flush_every_record`
and `tests/unit/observability/test_event_recorder.py::test_event_recorder_write_envelope_does_not_flush_every_record`.
The cross-reference gate confirmed this is the only `docs/parity_ledger/` edit required.

**Post-Implement update (Document-Update phase):** the Document-Update phase also independently
verified this ticket's diff against `docs/engine/kernel.md`, `known_limitations.md` §2.4,
`performance_contract.md`, and `docs/testing/test_taxonomy.md` (all confirmed to need no change —
none describe per-write flush cadence or budget-check timing as contractual) and additionally
found and fixed one real, unrelated staleness item: `docs/testing/regression_policy.md` §6's
worked example still forward-referenced this ticket as "filed for investigation" for one of the
10 deferred `test_corpus_diversity.py` tests; that line was updated to cite the actual resolution
(the two code fixes plus the `resource_budget_large` marker) and the real 5-pass/1-genuine-drift
outcome, and the file's `last_verified` frontmatter date was bumped.

**Regression suite run (Steps 1-3, before Step 7/8):** 178 passed, 4 skipped (0 failed) across
`tests/unit/kernel/test_replay_chunk_rotation.py`, `test_replay_contract.py`,
`test_replay_overflow.py`, `test_replay_pressure.py`, `test_replay_shutdown_budget.py`,
`tests/unit/engine/test_replay_backpressure.py`, `tests/unit/engine/test_resource_budget_gate.py`,
`tests/certification/test_artifact_budget.py`, `tests/simulation_quality/test_persistence.py`,
`test_evaluate_harness.py`, `test_quality_hub_integration.py`, `test_calibrate_simq.py`,
`test_broker_feed_integration.py`, `test_performance.py`, `tests/perf/test_simq_isolation_overhead.py`,
`tests/unit/observability/test_event_recorder.py`, `test_event_recorder_quality_fn.py`,
`test_obs_backpressure.py`, `tests/unit/observability/stream/test_phase21_bounded_observability_queue.py`,
`tests/unit/test_queue_worker_singleton.py`, `tests/unit/engine/test_lifecycle_supervisor.py`.
Skips are pre-existing (Redis-dependent broker-mode tests), unrelated to this diff.

## Test Summary

New/extended tests, all passing:
- `tests/unit/kernel/test_replay_chunk_rotation.py::test_rotate_chunk_does_not_serialize_synchronously_on_main_thread`
- `tests/simulation_quality/test_persistence.py::test_quality_persistence_write_does_not_flush_every_record`
- `tests/simulation_quality/test_persistence.py::test_quality_persistence_shutdown_flushes_remaining_records`
- `tests/unit/observability/test_event_recorder.py::test_event_recorder_write_envelope_does_not_flush_every_record`
- `tests/unit/observability/test_event_recorder.py::test_event_recorder_shutdown_flushes_remaining_writes`
- `tests/tools/test_conftest_resource_budget.py` (new file, 3 tests: marker applies large,
  unmarked test unaffected, `--resource-budget off` short-circuits regardless of marker)
- `tests/perf/test_persistence_phase_cost.py::test_persistence_phase_cost_regression_guard_1000t`
  (new file; soft-monitor, warn-not-fail)

Existing tests updated (behavioral timing fix, not assertion-value changes — see plan.md
Deviations #2/#3): `test_write_appends_jsonl_line`, `test_write_multiple_appends_multiple_lines`,
in `tests/simulation_quality/test_persistence.py`.

Regression suite (Steps 1-3 scope, 21 files): 178 passed, 4 skipped, 0 failed.

Test-phase gate (orchestrator-run, full pipeline): the structural `test_scope_coverage_static`
backstop initially FAILED — the first Test-phase pytest_command listed individual files inside
`tests/unit/observability/` instead of the bare directory token, so the ~90 other pre-existing
tests in that directory (unrelated event-extractor/shaper/analytics-pipeline tests) were never
actually run to confirm nothing broke. Re-scoped and re-ran the full bare `tests/unit/observability/`
directory: **1056 passed, 1 skipped, 0 failed** (independently verified twice). Structural coverage
gate re-checked: PASS. Combined with `tests/unit/perf/`/`tests/perf/ -m "not slow"` (93 passed, 47
deselected, one non-blocking `PerformanceThresholdWarning` soft-monitor) and the original 21-file
regression suite above, this ticket's own real regression surface (everything except the 6
AC4-reporting-only tests below) is **1327 passed, 0 failed, 51 skipped/deselected** — fully clean.

Step 8 (6 named grade-stability tests, run under the fix, no CLI flag needed — the marker forces
`large`): 5 passed, 1 failed on a genuine floor/tolerance drift (not a timeout/backpressure
failure) — see Implementation Notes above; needs its own re-baseline follow-up ticket, not fixed
here per plan scope. Per AC4's own wording ("their outcome — pass, or a now-clean floor/tolerance
drift needing its own re-baseline ticket — is reported"), this disclosed, out-of-scope,
pre-existing floor drift is a reported, accepted outcome for this ticket's closure, not a Test-gate
blocker — it is not caused by this ticket's diff (the backpressure/timeout failure mode it used to
hit is confirmed fixed; what remains is an unrelated, pre-existing scoring-anchor mismatch this
ticket's Out of Scope section explicitly forbids touching).

## Files Changed
- `src/engine/replay_manager.py`
- `src/simulation_quality/persistence.py`
- `src/observability/event_recorder.py`
- `tests/unit/kernel/test_replay_chunk_rotation.py`
- `tests/simulation_quality/test_persistence.py`
- `tests/unit/observability/test_event_recorder.py`
- `tests/conftest.py`
- `pyproject.toml`
- `tests/tools/test_conftest_resource_budget.py` (new)
- `tests/unit/worldassembly/test_corpus_diversity.py` (marker only, 6 named tests)
- `tests/perf/test_persistence_phase_cost.py` (new)
- `docs/parity_ledger/infrastructure.yaml` (new entry `INFRA-397` added by the Parity phase —
  documents the `QualityPersistence`/`EventRecorder` batch-of-50 flush cadence and its
  data-loss-window change; see Implementation Notes Step 9 below)
- `docs/testing/regression_policy.md` (Document-Update phase corrected a stale forward-reference
  in §6's worked example — see Implementation Notes Step 9 below)
- `tickets/inprogress/TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION.md` (this file)
- `staging_artifacts/TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION/plan.md`
  (Deviations section added)

## Completion Summary
Implemented plan.md Steps 1-9. Removed `ReplayManager._rotate_chunk()`'s redundant synchronous
full-chunk JSON re-serialization (Root cause #1) by relocating the budget check into the
already-async `_execute_persistence()`, reusing its already-computed byte count — eliminated the
~100-tick-periodic spikes (max single-tick persistence cost dropped from 243ms to 83ms in a
500-tick measured comparison). Batched `QualityPersistence.write()`'s and
`EventRecorder._write_envelope_to_file()`'s unconditional per-record `flush()` to every 50 records
(Root cause #2, a deterministic counter trigger, not wall-clock), which is what actually fixed the
`CalibrationIntegrityError` backpressure failure — all 6 previously-deferred grade-stability tests
now complete within budget (5 pass; 1 surfaces a genuine, separately-scoped floor/tolerance drift
needing its own re-baseline ticket). Documented an explicit decision not to change
`CanonicalStateHasher`'s every-tick hash cadence (a verified INFRA-223 contract). Added a
`resource_budget_large` pytest marker mechanism (Option A) and applied it to the 6 named tests so
they always run under `--resource-budget large` without requiring callers to remember the CLI
flag. Added a soft-monitor persistence-phase-cost regression guard
(`tests/perf/test_persistence_phase_cost.py`) with a ceiling locked from a real measured
1000-tick post-fix number (23.3% + 10pp headroom = 33.3%). Confirmed all 6 pre-existing touched
parity-ledger entries (INFRA-193/194/198/199/223/320) still accurately describe current behavior
unchanged — but the Parity phase did add one new entry, `INFRA-397` (P2, verified), documenting
the flush-batching cadence itself as new, real, operationally-significant telemetry behavior; the
Document-Update phase also fixed a stale forward-reference in `docs/testing/regression_policy.md`
§6. All new/extended tests pass; this ticket's own real regression surface (everything outside
the 6 AC4-reporting-only grade-stability tests) is 1327 passed, 0 failed, 51 skipped/deselected —
see Test Summary for the full breakdown including the mid-Test-phase structural re-scope.
