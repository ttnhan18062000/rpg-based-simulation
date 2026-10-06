---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS
phase: open
date: 2026-10-06
tags: [engine, combat]
---

# TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS

## Title
The slow test `test_real_campaign_episode_event_stream_is_plausible_not_degenerate` is red on `main` (`combat_initiated` 0, needs 3) because the campaign episode contains no deliberate attack at all: its only combat has always been incidental opportunity attacks, and their count collapsed

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Reported by `rpg-feature-planning` from `test-architecture-reviewer`: `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py::test_real_campaign_episode_event_stream_is_plausible_not_degenerate` fails on `main` with `combat_initiated` 0 (needs >= 3), stream dominated by `cooperation_event` 909 and `gold_sink_fired` 359; visible since #360 started running slow tests. Investigated by `rpg-implementer` (values below; the runs are deterministic, `main` reproduces the reported 909/359 exactly).

**Findings**
1. **The counter reads the right event.** `combat_initiated` is emitted by `observability/event_shapers.py` (push path) and mirrored in `event_extractor.py` when a full-HP entity takes real combat damage. The test listens on the kernel's own event stream.
2. **First bad commit: `bc00caa1a` (#175, 2026-09-13), the batch "worker-utilization sentinel, survivor progression, ...".** Last good `24920f912` (its parent, test passes), first bad `bc00caa1a` (`combat_initiated` 1). Both ends were run directly; the test file is unchanged since 2026-09-11. A bisect over the 190 commits to `main` agrees. (The test did not exist in August, so the "green on 2026-08-26" bracket does not apply to it.)
3. **The cause inside #175 is the worker-utilization sentinel.** Restoring `governor.py`, `worker_manager.py` and `kernel.py` to their pre-#175 versions makes the test pass; restoring `candidate_selector.py`, the contract files or the campaign files does not. The change is one line: `worker_utilization` returns 0.0 instead of 1.0 when `max_workers <= 0`. This test's kernel runs with workers disabled, so before #175 it ran **forced into DEGRADED mode from tick 1** and the test's expectation was met in that mode. Fixed, the run is NORMAL and the count fell to 1.
4. **Not the whole story on `main`:** with the sentinel put back to 1.0 on `origin/main` the count is **1**, not >= 3, so something between #175 and now lowered it further (1 to 0).
5. **The combat in this campaign is only opportunity attacks.** Over 70 ticks (seed 42, same manifest, 49 entities): `ActionRouter` dispatches: **0 of any kind** on both arms; `resolve_attack` (deliberate attacks): **0**; `resolve_multi_attack` with `is_opportunity_attack=True`: **15** on the last-good commit and **1** on `#366`'s head. So the test's "multiple distinct combat engagements" has only ever been satisfied by incidental opportunity attacks during movement, never by an entity choosing to attack. Opportunity-attack volume is chaotic on this corpus (gate 4 measured 38 to 644 and 488 to 283 in two worlds, unexplained), so a count of 15 was never a stable property.
6. **#366 does not restore it:** `main` (`9299891a9`) `combat_initiated` 0, `cooperation_event` 909; #366 head (`27a72b70b`) `combat_initiated` 0, `cooperation_event` 926.

**Not verified:** whether this campaign's lack of deliberate attacks is the same chain as `TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK` and the PANIC_RETREAT finding (`TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE`). That chain was measured on the four standard worlds, not on this campaign; here no action is dispatched at all, which is consistent with it but is not proof. The salience fix (`TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING`, parked behind perf's `kernel.py` slice) is the candidate remedy and is untested against this campaign.

## Scope
1. Decide what the combat assertion is meant to certify: "a spread-out episode produces several deliberate engagements" (then it is correctly red until entities attack) or "some combat happens" (then it is certifying an accident).
2. Do **not** weaken the assertion to make it pass. Options for the owner of the decision (`rpg-feature-planning` / `test-architecture-reviewer`), recommendation first:
   - **A (recommended):** split the test. Keep the `InvariantViolation == 0` and `cooperation_event` share assertions running (they still guard real regressions), and move the combat assertion to its own test, red or `xfail(strict=True, reason=<this ticket>)` so it flips when deliberate attacks return.
   - B: keep the single test red until the attack chain is fixed. Cheapest, but it hides the two other guards behind a known failure.
   - C: assert on deliberate attacks (`resolve_attack` calls or `ATTACK` dispatches) instead of `combat_initiated`, which removes the dependence on opportunity-attack volume.
3. When the salience fix or the attack chain lands, re-run this campaign and record the count.

## Out of Scope
- The worker-utilization fix itself (correct; it only exposed this).
- The salience fix and the PANIC_RETREAT chain (their own tickets).

## Acceptance Criteria
- [x] The decision is recorded by its owners: test-architecture-reviewer ruled a three-test split pinned to NORMAL (2026-10-06, with `rpg-feature-planning`'s domain support); implemented by the campaign-test split PR (branch `campaign-test-split-pinned-governor`).
- [x] The non-combat guards keep running: the `InvariantViolation == 0` test is green and unmarked; the cooperation-share test runs as a strict xfail on `TCK-20261006-CAMPAIGN-EPISODE-COOPERATION-SHARE-ABOVE-HALF-UNDER-A-PINNED-NORMAL-GOVERNOR` (threshold 0.5 unchanged).
- [ ] The PR that lands the attack-chain fix re-measures this test's attempts, K (decisions that perceived a hostile) and in-reach, and records them here (revisit trigger below).
- [ ] **Moved here 2026-10-06 from `TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE`** (that ticket is not the attack-starvation fix; its re-measure showed decision-path attacks of 30-41 per run before it, and this ticket still owns the remaining starvation, SAFETY_PRESSURE retreat at full HP). A deliberate-attack test (a tactical decision that sets an offensive ENTITY_ACT) on a world or seed with MEASURED hostile contact, i.e. an in-reach count K > 0 stated in the test, shows >= N deliberate attacks after the fix and fewer before (control arm). N is left for this ticket's investigation to set from the measured contact. K in reach must come from approach, not spawn adjacency (checked by the first in-reach decision's tick relative to spawn), or the test would skip the very gate under suspicion. The campaign episode test (`TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS`) is NOT this signal; its XPASS is a bonus. The landing PR also re-measures that test's attempts, K and in-reach and records them in the campaign ticket (its revisit trigger).

## Related Tickets
- `TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK`
- `TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE`
- `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING`

## Related Docs
- `docs/engine/kernel.md` (Sticky-Task Law); `docs/guidelines/intentional_divergences.md` (2.70 notes incidental opportunity-attack volume as unexplained).

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS/` (probes and bisect log).

## Related Code Areas
- `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py`; `src/engine/worker_manager.py` (the sentinel); `src/engine/governor.py`; `src/engine/movement.py:241` (opportunity attacks); `src/observability/event_shapers.py`.

## Assumptions / Open Questions
- One seed (42), one 70-tick episode; deterministic, but one world only.
- Why `main` falls from 1 to 0 after #175 is not isolated.
- **This test is NOT the attack fix's acceptance signal** (test-architecture-reviewer's ruling); its XPASS would be a bonus. The acceptance signal is a deliberate-attack test on a world or seed with measured contact (see `TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE`). A correct fix might yield fewer than 3 attacks from only ~11 encounters.
- **Revisit trigger:** the PR that lands the attack-chain fix re-measures this test's attempts, K (perceived) and in-reach. If attempts are < 3: do NOT lengthen the episode (on seed 42, perceived plateaus at 13 from tick 200 to 400 with 0 in reach; grid measured on `4311e7fc5`, single run per config) and do NOT lower the threshold. Move the deliberate-attack assertion to a seed or scenario with measured in-reach contact (seed 1337 had the grid's only in-reach decision), chosen by measurement.
- **Open question, not chased (planner):** 10 of the 11 decisions that perceived a hostile chose `SAFETY_PRESSURE_RETREAT` at full HP (`tactical.py:268`, `if hostiles and entity_pressures.safety_pressure > 0.75`). Discriminator: if the `safety_pressure` INPUT is wrong (biased sample, wrong set, mis-signed) it is a hard bug and `rpg-implementer`'s; if the input is right and the 0.75 threshold produces this, it is tuning, parked under owner decision 7. Linked to `TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE` (the PANIC_RETREAT chain).
- **Hypothesis (n=1, one seed, `4311e7fc5`):** in seed 1337 the only in-reach decision (entity 18, tick 32, hp 1.0) chose `SAFETY_PRESSURE_RETREAT`; the only ATTACK decision (entity 47, tick 33) was made from outside combat range; contact came at ticks 32 to 33, from approach, not spawn adjacency. So the defect in this campaign looks like "entities do not close to reach because they retreat at full HP", not "entities in reach do not attack". Consistent with, but not proof of, the flee-gate finding on the standard worlds.
- Not isolated: why the count fell from 1 (at `bc00caa1a`) to 0 between #175 and `main` (the cause inside #175 is the worker-utilization sentinel).

## Implementation Notes
Landed by the campaign-test split PR (the old single test is replaced by three tests over ONE episode run, module-scoped fixture, governor pinned to NORMAL through the new optional `governor=` argument on `ScenarioRuntimeService`):
1. `test_real_campaign_episode_has_no_hard_law_violation`: unmarked, green.
2. `test_real_campaign_episode_event_mix_is_not_dominated_by_cooperation`: `xfail(strict=True)` on `TCK-20261006-CAMPAIGN-EPISODE-COOPERATION-SHARE-ABOVE-HALF-UNDER-A-PINNED-NORMAL-GOVERNOR`; threshold < 0.5.
3. `test_real_campaign_episode_makes_deliberate_attacks`: `xfail(strict=True)` on this ticket; threshold >= 3 deliberate attacks (decisions that set an ENTITY_ACT of ATTACK, AOE_ATTACK or SKILL; SKILL counts as offensive by origin, guarded by a static single-writer test). Router dispatches of those kinds are a separate diagnostic in the message, never added.
Fixture hard preconditions (they fail the fixture, so the xfails cannot outlive the contact): ticks == 70, router-phase calls == ticks, decisions > 0, decisions that perceived a hostile (K) > 0. K is computed from the public perception API at decision entry; on this episode it is **11, equal to the frame-based count used in the investigation**, so the two definitions of "perceived" agree here. Positive controls (non-slow): router ATTACK dispatch counted; a healthy hero beside a monster decides ATTACK and is counted, with K >= 1; the wrapper restores the entry points; tactical.py has exactly one SKILL writer. The controls were shown to fail when the instrument is broken (3 mutations, 2, 1 and 1 failures).

Measured values (seed 42, 70 ticks, `4311e7fc5`, values; two pinned runs identical): InvariantViolation 0; cooperation 926 of 1645 = 0.5629; deliberate attacks 0 among 250 decisions; K 11, in reach 0; router-phase calls 70 of 70 ticks; router dispatches 0 of any kind. DEGRADED pin (control that the pin works): cooperation 1091 of 1872 = 0.5828, combat_initiated 1.

Where the episode's time goes (trace, `probes/trace_episode.py`; values): #366 head: 250 decisions, 236 change nothing (the function returns an EntityUpdate with no task, so the entity KEEPS its current task: idle ENTITY_ACT; `tactical.py:418`), 14 set an ENTITY_MOVE (SAFETY_PRESSURE_RETREAT 10, REGROUP 2, PANIC_RETREAT 1, plain 1), 0 set an ENTITY_ACT; idle 2404 of 2899 entity-ticks. Last good `24920f912`: 52 decisions, 24 PANIC_RETREAT before the hostile scan, 28 no change; 737 entity-ticks fleeing; the 15 opportunity attacks behind the old pass were drawn while fleeing.

Discriminator (`probes/decision_opportunity.py`; "hostile perceived" is the decision's own scan; "in reach" = Manhattan <= combat range), #366 head: 250 decisions by 47 entities (7 each); hostile perceived and in reach 0; hostile perceived, not in reach 11 (4.4%): SAFETY_PRESSURE_RETREAT 10, pursue 1, all at hp 1.0; no hostile 238: no task change 236, REGROUP 2; returned before the scan 1: PANIC_RETREAT.

Grid (frame-based K, single run per config, `4311e7fc5`):
| config | decisions | hostile perceived | in reach | attack decisions |
|---|---|---|---|---|
| seed 42, 70 ticks | 250 | 11 | 0 | 0 |
| seed 42, 200 ticks | 585 | 13 | 0 | 0 |
| seed 42, 400 ticks | 1085 | 13 | 0 | 0 |
| seed 7, 70 ticks | 253 | 14 | 0 | 0 |
| seed 2024, 70 ticks | 250 | 11 | 0 | 0 |
| seed 1337, 70 ticks | 254 | 10 | 1 | 1 |

## Test Summary
(not started)

## Files Changed
(not started)

## Completion Summary
(not started)
