---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261006-SLOW-STEP-6-REDS-UNMASKED-BY-GATE-FIX
phase: open
date: 2026-10-06
tags: [testing, investigation]
---

# TCK-20261006-SLOW-STEP-6-REDS-UNMASKED-BY-GATE-FIX

## Title
Triage and route the 8 `Slow regression` step-6 failures unmasked by the `!cancelled()` gate fix

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`TCK-20261005-SLOW-REGRESSION-GATE-SKIPS-ITS-ONLY-TEST-STEP-ON-MAIN` made step 6 (`slow or extra_slow`) run after a step-5 failure. First completed `main` run after #360: **37403688489**, head 9299891a9 (#362), job `Slow regression` 112078415756. Step 6: 8 failed, 112 passed, 57 skipped, 1 xfailed, 1 xpassed in 5829 s (1:37:09). Reds were hidden by the old gating. Last `main` run where step 6 executed: 32937991342 (push, 2026-08-26), green in ~24 min (06:47:41→07:11:33Z; also 32882484878 and 32862075313 on 2026-08-25, green in ~24–25 min). For 7 of the 8 reds, the red appeared after 2026-08-26 (step 6 skipped on main ~6 weeks since): those 7 tests existed unchanged and slow-marked at the green run 32937991342 (head eedf7d5b47304197593365b163d8a21c913f0595). The bracket does NOT apply to the campaign test (item 3): it was added 2026-09-09 (#150), and Lane A's bisect puts its first bad commit at #175 (bc00caa1a, 2026-09-13).

Source: relayed by hand from `test-architecture-reviewer` (REST jobs API and job log). Not re-measured by the implementer.

## Scope
Test architecture owns the triage and the routing, NOT the fixes. Per failure: confirm it reproduces or is explained, bisect within the 2026-08-26 → 2026-10-06 bracket where cheap, and route to the owning seat with evidence. Routing proposed by the reviewer:

1. `tests/regression/test_behavioral_5k.py::test_behavioral_5k_regression` — urban_political seed 42, 5000 ticks: alive_avg 5.46 vs baseline 13.30 (−58.9%, allowed 10%), gold_avg 0.00 vs 584.16, quest_active_count 1.02 vs 0. `tests/regression/baseline_5k.json` last changed 2026-08-19. → rpg-feature-planning (domain) (proposed; superseded by Routing Status): real degradation, or accept via `make regression-baseline`.
2. `tests/integration/world/test_living_world_ph9.py::test_long_run_simulation_ph9` — "Boss should have spawned during 1000 ticks" (−1). Cause identified: #356 (501933066, owner decision 14) made world-boss spawn default-OFF (`ENABLE_WORLD_BOSS_SPAWN`); the slow test was never updated. → rpg-feature-planning / world (proposed; superseded by Routing Status): flag ON in the test, or an inverted assertion.
3. `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py::test_real_campaign_episode_event_stream_is_plausible_not_degenerate` — combat_initiated 0 (expects ≥3). → rpg-feature-planning (domain) (proposed; superseded by Routing Status).
4. `tests/integration/kernel/test_milestone_b_closure.py::test_milestone_b_operational_gate` — governor reaches SURVIVAL, expected DEGRADED. → perf (governor; via #355) (proposed; superseded by Routing Status: classified a test artefact, owner test architecture).
5–8. `TimeoutError` at the large budget: `tests/perf/test_perf_combat.py[500]`, `test_perf_movement.py[5000]`, `test_perf_passive_scaling.py[5000]`, `test_perf_strategic.py[1000]`. → perf / test-infra boundary: perf regression or budget? The `Slow regression` job has no `timeout-minutes` (step 6 alone took 1h37m; the workflow comment says "~45-90min" for the whole job).

## Routing Status (2026-10-06, relayed by hand from `test-architecture-reviewer` for rpg-feature-planning)
Each is "assigned, ticket pending" until the owning lane sends its ticket id.

| # | Failure | Owner | State |
|---|---|---|---|
| 1 | `test_behavioral_5k_regression` | Lane B (rpg-implementer-2) | assigned; ticket `TCK-20261006-BEHAVIORAL-5K-REGRESSION-URBAN-POLITICAL-DRIFTED-FROM-THE-2026-08-19-BASELINE-ATTRIBUTE-EACH-METRIC` (P2, investigation, baseline untouched) filed, not yet on main (on branch `spawn-monster-catalog-faction`, lands with Lane B's spawn-batch PR, not pushed yet). **Do not rebaseline.** Lane B's investigation ticket (sequenced after its spawn-faction batch) must attribute each moved metric to a change (decision 12 open-ended hazard, violent-only trauma, LOC-08, inert bosses, the spawn-faction fix) before anyone touches `baseline_5k.json`. Accepting the result as new behaviour is the owner's call. gold → exactly 0 is flagged as not drift. |
| 2 | `test_long_run_simulation_ph9` | Lane B (rpg-implementer-2) | assigned; ticket `TCK-20261006-TWO-WORLD-INTEGRATION-TESTS-FAIL-ON-MAIN-PH9-ASSERTS-A-BOSS-AND-TRAUMA-LONG-RUN-HITS-THE-60S-LIMIT` filed, not yet on main (same branch and PR as row 1). Cause: #356 / decision 14. That ticket also covers `test_long_run_stability`, which is NOT one of the 8: it is `skipif(CI)` and did not run in 37403688489, so it is not a ninth CI red. Lane B (2026-10-06, relayed by rpg-feature-planning) re-ran test_long_run_stability at --resource-budget large on its spawn branch: it passed in 434 s, so the earlier failure was the medium (60 s) budget. Lane B dropped that half of its ticket (the ID keeps its old wording); only the ph9 boss half stands. |
| 3 | `test_real_campaign_episode_event_stream_is_plausible_not_degenerate` | Lane A (rpg-implementer), progression-starvation chain (PANIC_RETREAT on 97% of contact evaluations) | assigned; ticket `TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS` filed on PR #366's branch; now on main. #367 merged as 37a020b6e3dc62390c588f66c8e60af20f031f55; the split was verified by test-architecture-reviewer (PR review comments 6010041129 and 6010187674). Main slow-run confirmation pending (the run on the merge, 37425900959, was cancelled by a newer push). Lane A's bisect: first bad is bc00caa1a (#175, 2026-09-13; the worker-utilization sentinel). Before #175 this workers-disabled kernel was forced into DEGRADED from tick 1, and ≥3 combat_initiated was met only there, by incidental opportunity attacks; 0 deliberate attacks were dispatched even at the last good commit. A later, unisolated change took it from 1 to 0. Test-structure ruling (reviewer): split the test. Non-combat assertions stay green; the combat assertion moves to its own `xfail(strict=True)` test that asserts deliberate attacks rather than combat_initiated, with the governor mode pinned explicitly and no threshold change. Lane A implements it under that ticket; the reviewer reviews on the PR. The salience fix stays sequenced after perf's `kernel.py` slice. |
| 4 | `test_milestone_b_operational_gate` | test architecture (was routed to perf) | **Fixed by #373 (7daef8075); first slow-run confirmation pending.** The two gate tests are no longer `slow`, so the PR lanes on #373 already ran them green (run 37444005971). Earlier classification (test-architecture-reviewer, measured): test artefact, not a perf regression: the old test faked `time.perf_counter_ns` at 2 ms per CALL, and the call count crept up 55 → 67 per tick, first SURVIVAL commit `a2954cfaae3dffb7f7ca643008e3207fddb7900f` (#101). The #175 sentinel lead was not the cause; correction posted to perf on #355, comment 6010733923. Fix ticket `TCK-20261006-MILESTONE-B-GATE-FAKE-CLOCK-COUNTS-CALLS-NOT-TIME`. |
| 5–8 | four perf `TimeoutError`s | Lane A (cooperation) and Lane B (combat_engagement), routed by rpg-feature-planning | **Classified 2026-10-06 (test-architecture-reviewer, measured): a real engine regression, not a budget problem.** movement[5000]: 0.51 s per tick at eedf7d5b (08-26) versus 17.2 s on main d135dd6be; the same with the 08-26 scenario builder. Bisected to #172 (589c9045294540a7d4c74d57e69b69800b0dcea1; cooperation `find_pending_incoming_offer`, O(N² log N) per tick) → TCK-20261006-COOPERATION-PENDING-OFFER-SCAN-IS-QUADRATIC-PER-TICK (Lane A, P2, after the salience fix). A second step, combat_engagement +3.3 s per tick between c84352465 and 132bf09ca → TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP (Lane B). Routing by rpg-feature-planning; perf informed on #381 (comment 6018086519). |

## Out of Scope
Fixing any of the 8 failures, updating baselines, changing budgets or the job timeout, and the step-5 anchor drift (parked under TCK-20260822).

## Acceptance Criteria
- [ ] Each of the 8 failures is reproduced or explained, with evidence (run/job ids), and its bracket (green 2026-08-26, red 2026-10-06) narrowed where cheap (7 of 8 bracketed green 2026-08-26 → red 2026-10-06; item 3 by Lane A's bisect, first bad #175).
- [ ] Each is routed to an owner by name; any domain/rule question goes to rpg-feature-planning first, not ruled on here.
- [ ] Items 5–8 are classified perf regression vs budget, and the missing `timeout-minutes` is recorded as a finding (no change made here).
- [ ] The routed-ticket ids (or an explicit owner decision to accept) are recorded here.
- [x] Item 4's fix is filed as `TCK-20261006-MILESTONE-B-GATE-FAKE-CLOCK-COUNTS-CALLS-NOT-TIME` (testing, P2) in the next batch (not this one, unless the owner wants it here).

## Related Tickets
- TCK-20261005-SLOW-REGRESSION-GATE-SKIPS-ITS-ONLY-TEST-STEP-ON-MAIN (done; this ticket is its AC 6 "a red result files its own ticket")
- TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED (inprogress; testing adopted its reporting/triage scope 2026-10-06, and its reporting path must cover steps 5-7)
- TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2 (parked step-5 cause)

## Related Docs
- `.github/workflows/test.yml` (`slow` job)

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `tests/regression/`, `tests/integration/world/`, `tests/integration/campaigns/`, `tests/integration/kernel/`, `tests/perf/`

## Assumptions / Open Questions
- Whether the perf timeouts are a real regression or the budget is unknown.
- Whether the owner wants the job to keep running a 1h37m red step 6 on every main push.

## Implementation Notes
None yet.

## Test Summary
None yet.

## Files Changed
None yet.

## Completion Summary
None yet.
