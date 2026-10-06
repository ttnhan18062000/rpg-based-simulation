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
- [ ] The decision on A/B/C is recorded by its owner.
- [ ] The two non-combat guards keep running while the combat guard is red.
- [ ] The count is re-measured after the attack-chain or salience fix.

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

## Implementation Notes
(not started)

## Test Summary
(not started)

## Files Changed
(not started)

## Completion Summary
(not started)
