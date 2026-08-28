---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH
phase: open
date: 2026-08-28
tags: [testing, world, corpus, calibration]
---

# TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH

## Title
Re-baseline test_corpus_diversity.py's Population/Grade-Stability Floors After the town_center Navigation Fix

## Status
OPEN

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
- [ ] All 13 named tests in `tests/unit/worldassembly/test_corpus_diversity.py` pass against
      freshly-collected, evidence-backed floor/threshold values (not reverse-engineered from a single
      run without sanity-checking against expected simulation-quality ranges)
- [ ] The associated ERROR is diagnosed and either fixed or confirmed as an unrelated pre-existing
      test-ordering artifact with a documented rationale (not silently ignored)
- [ ] `docs/testing/regression_policy.md` (or the relevant test file's own docstring/comments) records
      that these floors were re-baselined as a result of `TCK-20260824-TOWN-CENTER-POINTER-FIX`, with
      a pointer back to that ticket for context
- [ ] Full `tests/unit/worldassembly/` suite passes cleanly after the update (no other test regresses
      as a side effect of the re-baselining)

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
(blank — not yet implemented)

## Test Summary
(blank — not yet implemented)

## Files Changed
(blank — not yet implemented)

## Completion Summary
(blank — not yet implemented)
