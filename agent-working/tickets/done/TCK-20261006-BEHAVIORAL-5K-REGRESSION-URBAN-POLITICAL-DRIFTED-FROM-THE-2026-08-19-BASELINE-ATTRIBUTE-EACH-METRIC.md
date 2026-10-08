---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261006-BEHAVIORAL-5K-REGRESSION-URBAN-POLITICAL-DRIFTED-FROM-THE-2026-08-19-BASELINE-ATTRIBUTE-EACH-METRIC
phase: done
date: 2026-10-06
tags: [testing, world, investigation]
---

# TCK-20261006-BEHAVIORAL-5K-REGRESSION-URBAN-POLITICAL-DRIFTED-FROM-THE-2026-08-19-BASELINE-ATTRIBUTE-EACH-METRIC

## Title
`tests/regression/test_behavioral_5k.py::test_behavioral_5k_regression` (urban_political, seed 42, 5,000 ticks) is red on `main`: attribute each metric's move to a change and explain gold reaching exactly 0

## Status
DONE

## Tier
standard

## Type
investigation

## Priority
P2

## Request Summary
Found by `test-architecture-reviewer` in the step-6 slow job (run 37403688489, main `9299891a9`), visible since #360. Measured vs the baseline (`tests/regression/baseline_5k.json`, `generated_at` 2026-08-17T08:42:13Z, committed 2026-08-19 in d2816ab6c): `alive_avg` 5.46 vs 13.30, `gold_avg` 0.00 vs 584.16, `quest_active_count` 1.02 vs 0. Filed by `rpg-implementer-2` on the planner's instruction. **Do not start until the spawn-faction batch (DEV-015) has landed.**

## Date bracket (from `test-architecture-reviewer`, via the planner)
Step 6 was fully green on `main` on 2026-08-26 (run 32937991342) and red by 2026-10-06 (#362). Bisect across that window (the baseline itself is from 2026-08-17), starting from the intentional world changes.

## Datapoints
Test-arch at #362: alive_avg 5.46. Lane A on clean `main` `0c89bd390` (after #366), urban_political, seed 42, 5,000 ticks: alive_avg 5.52, gold_avg 0.0, quest_active_count 1.02; identical with and without Lane A's social-contract change, deterministic. So #366 barely moved it, and the drift predates it.

## Scope
1. Reproduce under `audit_mode` with `max_tick_budget_ms=1e9`, seed 42, 5,000 ticks, on a base immediately before each candidate change and after it, so each metric's move is attributed to one change: owner decision 12 (open-ended hazard growth, DEV-013), violent-only trauma (DEV-011), LOC-08 region precedence (DEV-012), inert world bosses (DEV-010), and the spawn-faction/occupancy batch (DEV-015). Compare series, not endpoints.
2. Explain why `gold_avg` is exactly 0.00 (a floor, a sink, an economy that stopped, or an average over zero entities?).
3. Say which moves are intended gameplay changes and which are defects.

## Out of Scope
Running `make regression-baseline`. Nobody regenerates the baseline until the owner accepts the explanation.

## Acceptance Criteria
- [x] Each of the three metrics attributed to a change, with before/after values.
- [x] Exact-zero gold explained.
- [x] A recommendation to the owner (accept and rebaseline, or fix); baseline untouched.

## Related Tickets
- `TCK-20261006-TWO-WORLD-INTEGRATION-TESTS-FAIL-ON-MAIN-PH9-ASSERTS-A-BOSS-AND-TRAUMA-LONG-RUN-HITS-THE-60S-LIMIT`
- `TCK-20261005-SPAWN-MONSTER-STRIPS-CATALOG-FACTION-FROM-EVERY-RUNTIME-SPAWNED-MONSTER`
- `TCK-20261005-SLOW-REGRESSION-GATE-SKIPS-ITS-ONLY-TEST-STEP-ON-MAIN`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261006-BEHAVIORAL-5K-REGRESSION-URBAN-POLITICAL-DRIFTED-FROM-THE-2026-08-19-BASELINE-ATTRIBUTE-EACH-METRIC/` (investigation.md, plan.md, test_plan.md, probes/)

## Related Code Areas
`tests/regression/test_behavioral_5k.py`, the 2026-08-19 baseline file it reads, `data/worlds/urban_political`.

## Assumptions / Open Questions
Lane B (world), measurement only. The 2026-08-19 baseline predates every candidate change above.

## Implementation Notes
Measurement only; no src changes. See investigation.md for the full table. Summary: alive_avg and gold_avg both moved at #303 (1a40d22d1), which retired the global world-clock raid whose goblin raiders were the baseline's only survivors of a synchronised starvation collapse at t~1000 (present in baseline AND main, zero eat/sleep events in both). quest_active_count 0 -> 1.02 moved in small steps at #182, #291 and #333. Recommendation: do not rebaseline until the biology (SURV-05/06) and capacity-gate fixes land.

## Test Summary
No code changed. Positive control: d2816ab6c reproduces 13.30 / 584.16 / 0.0 exactly. Audit and plain runs on main are identical.

## Files Changed
Ticket and stored artifacts only.

## Completion Summary
Each metric attributed with before/after values; exact-zero gold explained (sum over entities, no gold-holder left alive); baseline untouched; recommendation: do not rebaseline now.
