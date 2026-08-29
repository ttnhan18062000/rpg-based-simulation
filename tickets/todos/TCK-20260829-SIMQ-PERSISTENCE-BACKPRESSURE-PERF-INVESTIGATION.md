---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION
phase: open
date: 2026-08-29
tags: [performance, observability, simulation-quality]
---

# TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION

## Title
Investigate Tick-Time Persistence/Telemetry I/O Overhead Causing Observability Backpressure in
Long/Heavy SimQ Calibration Runs

## Status
OPEN

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
- [ ] Real profiling data (not guessed) identifies the specific bottleneck inside the
      `persistence`/telemetry-I/O tick-phase cost.
- [ ] A concrete fix (or a documented decision not to fix, with rationale) is implemented and
      verified to reduce `persistence` phase cost meaningfully for a representative 1000-tick run.
- [ ] `tests/conftest.py`'s `--resource-budget` question is explicitly decided (fixed at the
      workload/test level, or left as-is with rationale) — not left ambiguous.
- [ ] The 6 tests named in Scope are re-run under the fix and their outcome (pass, or a now-clean
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
(blank — not yet implemented)

## Test Summary
(blank — not yet implemented)

## Files Changed
(blank — not yet implemented)

## Completion Summary
(blank — not yet implemented)
