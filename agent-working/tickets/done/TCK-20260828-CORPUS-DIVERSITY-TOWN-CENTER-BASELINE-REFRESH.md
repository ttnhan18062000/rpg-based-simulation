---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH
phase: done
date: 2026-08-28
tags: [testing, world, corpus, calibration]
---

# TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH

## Title
Re-baseline test_corpus_diversity.py's Population/Grade-Stability Floors After the town_center Navigation Fix

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
`TCK-20260824-TOWN-CENTER-POINTER-FIX` fixed a real navigation bug: `WorldCompiler.compile()` now
derives a real `AuthoritativeState.town_center` from the compiled town-type region(s) instead of
leaving it at the default `(0.0, 0.0)`, and `FlowFieldService.get_flow_direction(target_kind='TOWN')`
now navigates to that real value instead of two hardcoded fake waypoints (`(100,100)`/`(200,50)`).
As a direct, git-bisected consequence, entities now correctly navigate to the real compiled town
location — which changes their combat/hazard exposure along the way in several corpus world
compositions enough to trip `tests/unit/worldassembly/test_corpus_diversity.py`'s hardcoded
population-stability and simulation-quality-grade-stability floors. This was reproduced independently
in the town_center ticket's own Test-gate re-verification (13 failed + 1 error out of 235 tests in
that file, re-run via `pytest tests/unit/worldbuilding/test_world_compiler.py
tests/unit/worldgeneration/ tests/unit/worldassembly/ -q`).

The human product decision on `TCK-20260824-TOWN-CENTER-POINTER-FIX` (2026-08-28) was to **accept**
this as the fix's correct, intended consequence — the pre-fix "passing" state of these 13 tests was
itself an artifact of the pointer bug being fixed (entities never actually reaching the real town
before), not evidence of genuine balance under correct navigation — and to file this separate
follow-up ticket to re-baseline the affected floors/thresholds using the now-correct navigation
behavior as fresh ground truth, per `docs/testing/regression_policy.md`'s documented pattern for "a
hardcoded test baseline that this session's own legitimate change caused to drift."

## Scope
- Re-baseline `tests/unit/worldassembly/test_corpus_diversity.py`'s population-stability and
  simulation-quality-grade-stability floor/threshold values for exactly the 13 named failing tests
  below, using fresh evidence collected under the current (fixed) code — i.e. actual observed
  population/grade outcomes with `town_center` correctly set and `FlowFieldService` correctly
  navigating to it, not the old buggy values.
- The 13 failing tests (from `TCK-20260824-TOWN-CENTER-POINTER-FIX`'s Test-gate re-verification,
  scoped run `pytest tests/unit/worldbuilding/test_world_compiler.py tests/unit/worldgeneration/
  tests/unit/worldassembly/ -q`):
  - `test_population_stability[frontier_living_world]`
  - `test_population_stability[highland_traverse]`
  - `test_population_stability[generated_frontier_3_42]`
  - `test_generated_frontier_3_42_extended_population_stability`
  - `test_simq_routing_test_seed42_500t_cognition_grade_stability`
  - `test_simq_routing_test_seed42_1000t_cognition_grade_stability`
  - `test_hero_guild_routing_seed42_1000t_cognition_grade_stability`
  - `test_unit_selfmodel_pilot_seed42_1000t_cognition_economy_narrative_grade_stability`
  - `test_urban_political_seed42_1000t_social_grade_stability`
  - `test_urban_political_seed123_1000t_social_economy_grade_stability`
  - `test_frontier_extended_seed42_200t_narrative_grade_stability`
  - `test_frontier_living_world_seed42_200t_social_grade_stability`
  - `test_frontier_marches_seed42_200t_narrative_grade_stability`
- Investigate and resolve the 1 associated ERROR (observed at different test names across different
  runs — `test_resolver.py::test_resolve_module_contribution_rejects_raw_spec` in one run,
  `test_trading_company_hub_composed[swamp_border_world]` in another — both already flagged as a
  likely test-ordering/shared-state teardown artifact of whichever test runs last in the batch, not
  a floor-value problem; confirm this diagnosis or find the real cause).
- Before re-baselining any value, confirm with fresh evidence that the new population/grade outcomes
  under correct navigation are themselves reasonable per the Mechanics Bible / simulation-quality
  pillars (not just "whatever number makes the test pass") — a floor should reflect genuine expected
  behavior, not be reverse-engineered from one observed run.
- Note: this session also observed that running `test_corpus_diversity.py` standalone (outside the
  file's usual test_plan.md-scoped bundling with the rest of `tests/unit/worldassembly/`) produces a
  *different* failure set (16 failed vs. 13, with some seed123-variant tests failing only in
  isolation) — investigate whether this is genuine test-order/shared-state sensitivity worth hardening
  separately, or purely an artifact of this specific re-baselining work; note findings either way.

## Out of Scope
- Any further change to `src/worldbuilding/compiler.py`, `src/systems/world_systems/navigation.py`,
  `src/systems/strategic_systems/{redirection,intelligence,town_targeting}.py`,
  `src/core/worker_protocol.py`, or `src/engine/executor.py` — the navigation fix itself is complete
  and correct; this ticket only re-calibrates test expectations to match it.
- Re-litigating whether the `town_center` fix (`TCK-20260824-TOWN-CENTER-POINTER-FIX`) was the right
  call — that product decision has already been made and is final.
- `tests/regression/test_behavioral_5k.py` / `tests/integration/kernel/test_long_run_determinism.py`
  — both fail in this environment on a pre-existing, separately-documented resource-time-limit
  `TimeoutError` under CPU contention, unrelated to this ticket.
- Any change to `tests/simulation_quality/test_grade_regression.py` or its
  `grade_anchors.json`/`baseline_5k.json` fixtures — those were spot-checked during
  `TCK-20260824-TOWN-CENTER-POINTER-FIX` and found clean; not implicated here.

## Acceptance Criteria

**Revised 2026-08-29, after Implement-phase investigation and an explicit human decision (Option A
of 3 presented options — see Completion Summary).** Fresh evidence showed the original assumption
below ("all 13 are floor-value drift") held for only 3 of the 13. The other 10 fail for reasons a
floor edit cannot fix (a real, unrelated `src/` bug; a test-invocation resource-budget cap; a real
observability-backpressure issue) and are explicitly deferred to two new follow-up tickets rather
than force-fit. See Implementation Notes for the full per-test classification.

- [x] The 3 tests confirmed as genuine floor/tolerance drift —
      `test_population_stability[highland_traverse]`,
      `test_frontier_extended_seed42_200t_narrative_grade_stability`,
      `test_frontier_living_world_seed42_200t_social_grade_stability` — now pass against
      freshly-collected, evidence-backed floor/threshold values (2 independent 3-trial batches per
      grade-stability test, 4 independent runs for the population-stability test; not
      reverse-engineered from a single run; sanity-checked as mechanically plausible — see
      Implementation Notes).
- [~] The other 10 named tests are **explicitly NOT re-baselined here** — each fails for a
      confirmed reason other than a calibratable floor value: real pre-existing `src/` bug (3:
      `test_population_stability[frontier_living_world]`,
      `test_generated_frontier_3_42_extended_population_stability`,
      `test_frontier_marches_seed42_200t_narrative_grade_stability`); test-invocation
      resource-budget cap / observability backpressure (5:
      `test_simq_routing_test_seed42_1000t_cognition_grade_stability`,
      `test_hero_guild_routing_seed42_1000t_cognition_grade_stability`,
      `test_unit_selfmodel_pilot_seed42_1000t_cognition_economy_narrative_grade_stability`,
      `test_urban_political_seed42_1000t_social_grade_stability`,
      `test_urban_political_seed123_1000t_social_economy_grade_stability`); already passing
      cleanly with no action needed (2: `test_population_stability[generated_frontier_3_42]`,
      `test_simq_routing_test_seed42_500t_cognition_grade_stability`). 3+5+2=10. Filed as two
      separate follow-up tickets (bug fix already implemented; backpressure investigation filed)
      rather than force-fitting floor edits onto crashes/timeouts. This was an explicit,
      human-approved scope decision (Option A), not a silent gap.
- [x] The associated ERROR is diagnosed and confirmed as an unrelated pre-existing test-ordering/
      teardown artifact with a documented, evidence-backed root-cause chain (not silently ignored):
      a `QueueDrainWorker` thread-leak sentinel firing at whichever test the pytest session happens
      to be tearing down when it checks, directly caused by an earlier test's `TimeoutError`/
      `CalibrationIntegrityError` skipping its own `kernel.shutdown()` cleanup — see Completion
      Summary. Explained by, not needing its own ticket beyond, the new backpressure ticket.
- [x] `tests/unit/worldassembly/test_corpus_diversity.py`'s own module docstring records that
      these 3 floors were re-baselined as a result of `TCK-20260824-TOWN-CENTER-POINTER-FIX`, with
      a pointer back to that ticket, and explicitly documents why the other 10 were NOT touched
      here, with pointers to the two new follow-up tickets.
- [~] Full `tests/unit/worldassembly/` suite: the 3 re-baselined tests plus every test unaffected by
      this investigation's 3 failure categories pass cleanly. The 10 deferred tests are expected to
      still fail/error for their own already-diagnosed, already-ticketed reasons — this is the
      accepted, disclosed state of this AC, not a regression introduced by this ticket's own work.

## Related Tickets
- TCK-20260824-TOWN-CENTER-POINTER-FIX (root cause; this ticket's entire reason for existing)

## Related Docs
- docs/testing/regression_policy.md
- docs/testing/test_taxonomy.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260824-TOWN-CENTER-POINTER-FIX/ (once migrated — investigation.md/plan.md
  contain the git-bisection evidence and the exact disclosed failure list this ticket must resolve)

## Related Code Areas
- tests/unit/worldassembly/test_corpus_diversity.py
- src/worldbuilding/compiler.py (read-only reference — the now-correct derivation this re-baseline
  must calibrate against, do not modify)
- src/systems/world_systems/navigation.py (read-only reference, do not modify)

## Assumptions / Open Questions
- Whether the correct fix is new hardcoded floor constants, or a more principled tolerance-band/
  percentile approach, is left to the Investigate/Plan phase to determine from the actual observed
  population/grade distributions under the fixed code — not decided here.
- Whether the 16-vs-13-failure test-ordering sensitivity noted in Scope is in-scope to harden or just
  worth noting is left open for Investigate to assess.

## Implementation Notes

**Methodology**: real, unmocked `Kernel`/`WorldCompiler`-driven simulation runs only — no
guessed/invented values. Standalone `pytest tests/unit/worldassembly/test_corpus_diversity.py -v
--tb=short` (~11 min, 14 failed/76 passed/1 error) surfaced full per-test evidence, followed by
targeted clean isolated re-runs (single-test invocations, no concurrent activity) to separate
genuine signal from resource contention. Per-test classification of all 13 named tests:

| Test | Real cause | Action |
|---|---|---|
| `test_population_stability[highland_traverse]` | Genuine floor drift (stable 55.6%/10 of 18, confirmed via 4 independent runs incl. a full 300-tick trajectory probe) | **Re-baselined here** |
| `test_frontier_extended_seed42_200t_narrative_grade_stability` | Genuine tolerance drift (NARRATIVE) | **Re-baselined here** |
| `test_frontier_living_world_seed42_200t_social_grade_stability` | Genuine tolerance drift (SOCIAL) | **Re-baselined here** |
| `test_population_stability[generated_frontier_3_42]` | Did not reproduce as a failure in a clean run | No action needed |
| `test_simq_routing_test_seed42_500t_cognition_grade_stability` | Did not reproduce as a failure in a clean run | No action needed |
| `test_population_stability[frontier_living_world]` | `TypeError` in `src/systems/lifecycle_systems/lifecycle.py:122` (pre-existing, unrelated, commit `56211688` 2026-05-18) | Deferred → `TCK-20260829-LIFECYCLE-HEIRLOOM-INVENTORY-TUPLE-TYPEERROR` (fixed) |
| `test_generated_frontier_3_42_extended_population_stability` | Same `TypeError` | Deferred → same ticket (fixed) |
| `test_frontier_marches_seed42_200t_narrative_grade_stability` | Same `TypeError` | Deferred → same ticket (fixed) |
| `test_simq_routing_test_seed42_1000t_cognition_grade_stability` | `tests/conftest.py`'s 60s `--resource-budget medium` cap; with cap lifted, `CalibrationIntegrityError` (observability backpressure) | Deferred → `TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION` |
| `test_hero_guild_routing_seed42_1000t_cognition_grade_stability` | Same class | Deferred → same ticket |
| `test_unit_selfmodel_pilot_seed42_1000t_cognition_economy_narrative_grade_stability` | Same class | Deferred → same ticket |
| `test_urban_political_seed42_1000t_social_grade_stability` | Same class (directly confirmed: 60s timeout in isolation; 84s + `CalibrationIntegrityError` with `--resource-budget large`) | Deferred → same ticket |
| `test_urban_political_seed123_1000t_social_economy_grade_stability` | Same class | Deferred → same ticket |

**Re-baseline evidence and sanity-check for the 3 re-baselined tests**:
- `test_population_stability[highland_traverse]`: floor lowered 60%→50% of starting (18 entities).
  4 independent same-seed(42) runs (1 in the original standalone batch, 2 more pytest reruns, 1
  full 300-tick trajectory probe outside pytest's early-exit) all landed on the identical stable
  value: 10/18 (55.6%) alive from tick 150 through tick 300 — a plateau, not a runaway collapse
  toward extinction. New floor (50%, 9 entities) sits comfortably below the observed stable point
  with ~1 entity of margin, remaining a real regression guard. Sanity check: plausible and
  consistent with the navigation fix's own accepted, disclosed consequence — entities now travel
  real (previously never-reached) hazardous distance to town, and this world's 300-tick trajectory
  shows losses stabilizing rather than compounding, which is the expected shape for "more real
  hazard exposure once" rather than "the fix broke survival mechanics."
- `test_frontier_extended_seed42_200t_narrative_grade_stability` (NARRATIVE) and
  `test_frontier_living_world_seed42_200t_social_grade_stability` (SOCIAL): both required **two**
  independent batches of 3 fresh trials each (a first batch's evidence-derived tolerance, once
  written, promptly proved insufficient against an independent second batch — confirming this
  file's own real, pre-existing non-determinism under system load, not a mistake in the first
  batch). Both anchors were re-calibrated from the **combined 6-draw pool** (not either batch
  alone), matching this file's own established precedent for exactly this situation
  (`urban_political_seed123_1000t`/SOCIAL: "derived from 11 independent fresh draws combined
  across two sessions... not this latter session's 8 draws alone"). Final values: NARRATIVE
  score=0.1039 (from 0.0), abs_floor=0.1688 (from 0.05); SOCIAL score=22.3133 (from 33.7),
  abs_floor=13.2817 (from 5.382). Verified with a **third**, independent fresh batch (plus
  highland_traverse together) — all 3 re-baselined tests passed cleanly. Sanity check: SOCIAL's
  large drop is mechanically plausible (SOCIAL correlates with live entities interacting
  in/around town; this world's population is also down from real hazard exposure along the now-
  real route, so fewer live entities produce fewer SOCIAL events); NARRATIVE's shift from exactly
  0 to a small but real nonzero value is plausible (entities now genuinely travel and can trigger
  real narrative-eligible events — arrival/hazard encounters — en route that never fired when
  navigation was a no-op).

**The 1 associated ERROR — confirmed, root cause traced**: `QueueDrainWorker thread leak
detected` fires at pytest session-teardown, attributed to whichever test happens to be
running/torn-down at that moment (`test_resolver.py::test_resolve_module_contribution_rejects_raw_spec`
in one run, `test_trading_company_hub_composed[swamp_border_world]` in another — reproduced
directly in this session's own standalone run). Root cause: a `TimeoutError`/
`CalibrationIntegrityError` mid-`_run_engine()` (the resource-budget/backpressure class above)
skips whatever `kernel.shutdown()` cleanup would normally run, leaking that run's
`QueueDrainWorker` background thread; a later, unrelated test's session-teardown sentinel then
reports the leak against itself. Independently reproduced (2 threads leaked) in an isolated
single-test run that itself hit the resource-budget timeout — confirming the causal chain, not
just correlation. Confirmed as a pre-existing test-ordering/teardown artifact, not a floor-value
problem, per this ticket's own AC #2 "confirmed" branch — fully explained by, and not needing its
own ticket beyond, `TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION`.

**16-vs-13 standalone-vs-bundled — confirmed genuine, not an artifact of this ticket's own work**:
the standalone run in this session produced 14 failed (neither a stable 16 nor 13), and the *same
test* (`test_urban_political_seed42_1000t_social_grade_stability`) showed a *different* failure
mode (`TimeoutError` vs. `CalibrationIntegrityError`) across two of this session's own isolated
runs. This matches the already-known, already-deferred finding that `Kernel`'s wall-clock
mid-tick throttle breaks strict determinism under variable system load (`audit_mode=False`) —
tracked separately (the user has already chosen to let it sit); no new ticket filed for it, per
the coordinator's explicit direction.

**Scope decision (2026-08-29)**: presented 3 options for handling the 10 non-floor-drift tests;
coordinator selected Option A — re-baseline only the 3 genuine floor-drift tests here, file
separate tickets for the bug and the backpressure investigation, leave the other tests' assertions
as-is pending those tickets.

## Test Summary
- `tests/unit/worldassembly/test_corpus_diversity.py::test_population_stability[highland_traverse]`,
  `::test_frontier_extended_seed42_200t_narrative_grade_stability`,
  `::test_frontier_living_world_seed42_200t_social_grade_stability` — 3 passed (verified twice:
  once immediately after the re-baseline edit with a fresh third-batch draw, confirming the
  widened tolerance holds against genuinely new evidence, not just the two batches used to derive
  it).
- Full `tests/unit/worldassembly/` suite run separately (see Verify phase) — the 10 deferred tests
  are expected to still fail/error for their own already-diagnosed, already-ticketed reasons; this
  is the accepted, disclosed state per the revised Acceptance Criteria, not a regression.

**Verify-phase re-run (2026-08-29, after the ENOSPC disk-full interruption cleared)**: full
`pytest tests/unit/worldassembly/ -q`, real run, cwd-verified — **7 failed, 147 passed in 938.45s**
(0 errors this time — the 1 associated ERROR did not recur, consistent with its diagnosed
session-teardown/test-ordering root cause rather than a stable failure). All 3 re-baselined tests
passed cleanly (not in the failure list). `test_population_stability[frontier_living_world]`
(one of the 3 lifecycle.py-TypeError-unblocked tests) now passes cleanly. Of the 10 deferred
tests: 3 of the 5 backpressure-class tests (`test_simq_routing_test_seed42_1000t_...`,
`test_hero_guild_routing_seed42_1000t_...`, `test_unit_selfmodel_pilot_seed42_1000t_...`) passed
cleanly this run (resource contention is inherently load-dependent — this is consistent with, not
contradicting, the backpressure diagnosis); 2 (`test_urban_political_seed42_1000t_social_...`,
`test_urban_political_seed123_1000t_social_economy_...`) still failed, as expected. Of the 2
remaining lifecycle.py-unblocked tests (`test_generated_frontier_3_42_extended_population_stability`,
`test_frontier_marches_seed42_200t_narrative_grade_stability`): both still failed, but now for
their own genuine floor/grade-drift reasons (no more `TypeError`) — exactly the open,
undecided-here question the lifecycle ticket's own Completion Summary flagged ("whether their own
floor/tolerance assertions now pass is a separate, already-tracked concern for a future session").

**3 additional failures observed, not among the originally-named 13**:
`test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability`,
`test_frontier_extended_seed123_200t_combat_progression_narrative_grade_stability`,
`test_frontier_living_world_seed123_200t_combat_narrative_grade_stability`. None are touched by
this ticket's own diff (confirmed via `git diff tests/unit/worldassembly/test_corpus_diversity.py`
— only `test_population_stability`, `test_frontier_extended_seed42_200t_narrative_grade_stability`,
and `test_frontier_living_world_seed42_200t_social_grade_stability` were edited). Re-ran all 3 in
isolation immediately after: 2 of 3 (`test_urban_political_selfmodel_probe_...`,
`test_frontier_living_world_seed123_...`) passed cleanly; 1
(`test_frontier_extended_seed123_200t_combat_progression_narrative_grade_stability`) failed again,
with wildly divergent per-trial COMBAT scores across its 3 trials (0.237, 0.834, 1.251) — and this
exact test's own docstring already documents this exact pillar/scenario as genuinely
load-variable, citing the pre-existing, unrelated `TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP`
finding. Both the full-suite run and the isolated re-run showed heavy `WatchdogTrip`/mid-tick
emergency-throttle warnings throughout (this machine was concurrently running 4+ other active
Claude/Codex sessions during Verify, `load average: 0.57, 1.92, 3.09` on 4 cores at the time of
the isolated re-run), consistent with the already-known, already-deferred finding that `Kernel`'s
wall-clock mid-tick throttle breaks strict determinism under variable system load (see
Implementation Notes' "16-vs-13" discussion above; the user has already chosen to let that sit).
Conclusion: these 3 are load-driven pre-existing test flakiness in an already-known class, not a
regression introduced by this ticket's own (narrowly-scoped, verified-by-diff) changes. Recorded
here for traceability; no new ticket filed — already covered by the existing, accepted
non-determinism finding and by `TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION`'s
adjacent observability-backpressure scope.

## Files Changed
- `tests/unit/worldassembly/test_corpus_diversity.py` — re-baselined 3 tests'
  floors/anchors (`POPULATION_STABILITY_FLOOR_OVERRIDES` dict added; `test_population_stability`
  reads the per-world override instead of a hardcoded 60%; the 2 grade-stability tests' `anchors`
  dicts updated), plus a new module-docstring section (§5) documenting the re-baseline event, what
  was/wasn't touched, the ERROR diagnosis, and the 16-vs-13 pointer.
- `docs/testing/regression_policy.md` — added a note cross-referencing this re-baseline event as a
  concrete example of the documented "hardcoded test baseline drift" pattern.
- (Separately, in sibling ticket `TCK-20260829-LIFECYCLE-HEIRLOOM-INVENTORY-TUPLE-TYPEERROR`, not
  this ticket's own commit: `src/systems/lifecycle_systems/lifecycle.py`,
  `docs/simulation/lifecycle_systems_contract.md`, `docs/parity_ledger/social_narrative.yaml`.)

## Completion Summary
Re-baselined 3 of the 13 named `test_corpus_diversity.py` tests
(`test_population_stability[highland_traverse]`,
`test_frontier_extended_seed42_200t_narrative_grade_stability`,
`test_frontier_living_world_seed42_200t_social_grade_stability`) using fresh, multi-batch
evidence collected under the current (fixed) navigation code, per this file's own established
tolerance-band methodology. The other 10 named tests were investigated with the same rigor but
found to fail for reasons other than floor drift — a real, pre-existing, unrelated `src/` bug
(fixed separately in `TCK-20260829-LIFECYCLE-HEIRLOOM-INVENTORY-TUPLE-TYPEERROR`) and a
test-invocation resource-budget cap masking a real observability-backpressure issue (filed as
`TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION`) — and were explicitly deferred
rather than force-fitting floor edits onto crashes/timeouts, per an explicit human scope decision
(Option A of 3 presented). The 1 associated ERROR was diagnosed to a precise root-cause chain
(session-teardown thread-leak sentinel, caused by the same resource-budget/backpressure class of
failure skipping cleanup) and confirmed as an unrelated test-infrastructure artifact, fully
explained by the new backpressure ticket rather than needing its own. The 16-vs-13 standalone-
vs-bundled variance was confirmed as genuine run-to-run non-determinism matching the already-known,
already-deferred `Kernel` wall-clock throttle finding — left tracked there, per the coordinator's
explicit direction, not spawned as a new ticket.
