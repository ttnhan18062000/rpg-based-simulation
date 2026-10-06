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
| 2 | `test_long_run_simulation_ph9` | Lane B (rpg-implementer-2) | assigned; ticket `TCK-20261006-TWO-WORLD-INTEGRATION-TESTS-FAIL-ON-MAIN-PH9-ASSERTS-A-BOSS-AND-TRAUMA-LONG-RUN-HITS-THE-60S-LIMIT` filed, not yet on main (same branch and PR as row 1). Cause: #356 / decision 14. That ticket also covers `test_long_run_stability`, which is NOT one of the 8: it is `skipif(CI)` and did not run in 37403688489, so it is not a ninth CI red. |
| 3 | `test_real_campaign_episode_event_stream_is_plausible_not_degenerate` | Lane A (rpg-implementer), progression-starvation chain (PANIC_RETREAT on 97% of contact evaluations) | assigned; ticket `TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS` filed on PR #366's branch; now on main (landed with #367, 'the red campaign event-stream test becomes three tests over one pinned-NORMAL run', as of 2026-10-06 per `git log origin/main`; I did not read #367's content, so whether it implements this ticket's split is not verified here). Lane A's bisect: first bad is bc00caa1a (#175, 2026-09-13; the worker-utilization sentinel). Before #175 this workers-disabled kernel was forced into DEGRADED from tick 1, and ≥3 combat_initiated was met only there, by incidental opportunity attacks; 0 deliberate attacks were dispatched even at the last good commit. A later, unisolated change took it from 1 to 0. Test-structure ruling (reviewer): split the test. Non-combat assertions stay green; the combat assertion moves to its own `xfail(strict=True)` test that asserts deliberate attacks rather than combat_initiated, with the governor mode pinned explicitly and no threshold change. Lane A implements it under that ticket; the reviewer reviews on the PR. The salience fix stays sequenced after perf's `kernel.py` slice. |
| 4 | `test_milestone_b_operational_gate` | test architecture (was routed to perf) | **Classified 2026-10-06 (test-architecture-reviewer, measured): test artefact, not a perf regression; owner: test architecture.** The test patches `time.perf_counter_ns` to advance 2 ms per CALL, so the faked tick time is a count of timing calls. Measured per tick (empty state, the test's profile): 55 calls / 126 ms / DEGRADED at `eedf7d5b47304197593365b163d8a21c913f0595` (the last green slow run, 2026-08-26) versus 67 calls / 164 ms / SURVIVAL on `origin/main` `0c89bd390462d1fadb34b07d392dd350d78a52fa`. A first-parent bisect over 260 commits shows the count creeping up 55 → 59 → 63 → 65 → 67. The first SURVIVAL commit is `a2954cfaae3dffb7f7ca643008e3207fddb7900f` (#101, 2026-09-02; added phase-cost timing calls, 59 → 63); the last DEGRADED is `32c13bd749b68626231c4146a202de36478b873b`. The #175 sentinel lead is not the cause; perf was told to drop it on #355 (correction comment). Fix (a separate test-architecture ticket, not this triage): make the test's faked clock independent of call count, e.g. advance per tick or set the pressure signal directly, so it tests the governor's thresholds rather than the kernel's instrumentation density. Lead from rpg-implementer; measurement by the reviewer. Follow-up to file in the next batch (not this one, unless the owner wants it here): `TCK-20261006-MILESTONE-B-GATE-FAKE-CLOCK-COUNTS-CALLS-NOT-TIME` (testing, P2). |
| 5–8 | four perf `TimeoutError`s | perf / test-infra | routed to perf on #355 (comment 6009521682), awaiting classification. Reviewer's read, also stated in that comment, pending perf's confirmation: the four benches each hit the 600 s large budget (about 40 of step 6's 97 min) while the whole step took ~24 min on 2026-08-26, so this looks like a hot-path regression, not a budget problem. |

## Out of Scope
Fixing any of the 8 failures, updating baselines, changing budgets or the job timeout, and the step-5 anchor drift (parked under TCK-20260822).

## Acceptance Criteria
- [ ] Each of the 8 failures is reproduced or explained, with evidence (run/job ids), and its bracket (green 2026-08-26, red 2026-10-06) narrowed where cheap (7 of 8 bracketed green 2026-08-26 → red 2026-10-06; item 3 by Lane A's bisect, first bad #175).
- [ ] Each is routed to an owner by name; any domain/rule question goes to rpg-feature-planning first, not ruled on here.
- [ ] Items 5–8 are classified perf regression vs budget, and the missing `timeout-minutes` is recorded as a finding (no change made here).
- [ ] The routed-ticket ids (or an explicit owner decision to accept) are recorded here.
- [ ] Item 4's fix is filed as `TCK-20261006-MILESTONE-B-GATE-FAKE-CLOCK-COUNTS-CALLS-NOT-TIME` (testing, P2) in the next batch (not this one, unless the owner wants it here).

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
