---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261020-BEHAVIORAL-5K-BUILDS-ITS-WORLD-WITHOUT-THE-CONTENT-CONTEXT
phase: open
date: 2026-10-20
tags: []
---

# TCK-20261020-BEHAVIORAL-5K-BUILDS-ITS-WORLD-WITHOUT-THE-CONTENT-CONTEXT

## Title
tests/regression/test_behavioral_5k.py compiles its world without the content context, so the bodies hold no starting coin and gold_avg reads 0.0

## Status
INPROGRESS

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
The v1 dry run measured behavioral_5k gold_avg 0.0 against a baseline of 584.16. The metric (mean of `MetricsService.total_gold`, the sum of `inventory.gold` over all entities, sampled every 100 ticks) is correct; the world is wrong. The test used `WorldRepository.load_world` and `WorldCompiler.compile(spec, seed)` with no `CompileContext`; without it (`compiler.py` `profile is None or not profile.starting_gold`) bodies get no starting inventory, so no entity holds coin at tick 1. The gate builds with `load_world_with_context` and `compile(spec, seed, context=context)`; urban_political then holds 950 coin at tick 0. At 1000 ticks the same function with the context reads gold_avg 938.0 (alive_avg 19.7, quest_active_count 7.4) against 0.0, alive 25.5, quest 6.6 without it.

## Scope
- `tests/helpers/world_build.py`: one `compile_world_with_context(world_id, seed)` helper; the 5k test builds its world through it.
- A guard in the test: on a world that declares starting gold (`WORLDS_WITH_STARTING_GOLD`), the compiled tick-0 state must hold coin, or the test fails loudly.
- `tests/unit/test_world_build_helper_matches_the_gate.py`: the helper's tick-0 state hash equals the gate kernel's (`rpg_gate_run.build_kernel`), the bodies hold coin, and a context-less compile holds none.
- Stability proof: two 5000-tick runs of the fixed harness agree.

## Out of Scope
- Rebaselining `baseline_5k.json`: that happens on the v1 commit as part of the record.
- Other callers that compile without the context (listed to rpg-planner for triage).

## Acceptance Criteria
- The fixed harness gives identical values in two 5000-tick runs; the guard and the helper-vs-gate test pass.

## Related Tickets
- TCK-20261019-RECORD-BASELINE-V1
- TCK-20261007-BEHAVIORAL-5K-REBASELINE-AFTER-THE-STARVATION-CHAIN-LANDS

## Related Docs
- docs/testing/regression_policy.md

## Related Stored Artifacts
- none

## Related Code Areas
- tests/regression/test_behavioral_5k.py, tests/helpers/world_build.py

## Assumptions / Open Questions
- The alive_avg and quest_active_count moves attributed earlier to newer worlds are re-measured with the fixed harness before the rebaseline attributes them.

## Implementation Notes
The gate's own build (`tools/test_architecture/rpg_gate_run.build_kernel`) is untouched; the drift guard is the unit test comparing the two tick-0 hashes.

## Test Summary
Fixed harness, urban_political seed 42, 5000 ticks, audit_mode + pinned NORMAL governor, PYTHONHASHSEED=0, two independent runs (run in parallel): both alive_avg 18.34, gold_avg 909.4, quest_active_count 7.08 (identical; 336 s each, 144 MB). Before the fix the same function gave 24.64 / 0.0 / 6.12 at 5000t. tests/unit/test_world_build_helper_matches_the_gate.py: 2 passed (the helper's tick-0 state hash equals the gate kernel's; the bodies hold coin; a context-less compile holds none). baseline_5k.json is NOT rewritten here: the rebaseline happens on the v1 commit.

## Files Changed
tests/regression/test_behavioral_5k.py, tests/helpers/world_build.py, tests/unit/test_world_build_helper_matches_the_gate.py

## Completion Summary
TBD
