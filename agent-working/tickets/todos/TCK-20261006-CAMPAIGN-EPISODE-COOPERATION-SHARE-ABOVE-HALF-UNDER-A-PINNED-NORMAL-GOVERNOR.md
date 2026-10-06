---
status: active
layer: testing
authority: P3
audience: agent
ticket_id: TCK-20261006-CAMPAIGN-EPISODE-COOPERATION-SHARE-ABOVE-HALF-UNDER-A-PINNED-NORMAL-GOVERNOR
phase: open
date: 2026-10-06
tags: [engine, combat]
---

# TCK-20261006-CAMPAIGN-EPISODE-COOPERATION-SHARE-ABOVE-HALF-UNDER-A-PINNED-NORMAL-GOVERNOR

## Title
In the campaign episode, `cooperation_event` is 56% of the event stream under a pinned NORMAL governor (0.5629, 0.5828 pinned DEGRADED), above the test's 0.5 limit; it was 0.404 at `24920f912`; cause not isolated

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Found while splitting `test_real_campaign_episode_event_stream_is_plausible_not_degenerate` (`TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS`): the cooperation-share assertion (< 0.5) had been hidden behind the combat assertion, which failed first, and is itself red. The test now carries it as `xfail(strict=True)` on this ticket, threshold unchanged, so a fix flips it loudly.

**Values** (seed 42, 70 ticks, the test's own manifest; values, the pinned runs identical twice):
| tree / mode | cooperation_event | total events | share |
|---|---|---|---|
| `24920f912` (last good for the old test), forced DEGRADED by the pre-#175 sentinel | 459 | 1135 | 0.404 |
| `4311e7fc5`, unpinned (already NORMAL) | 926 | 1645 | 0.5629 |
| `4311e7fc5`, pinned NORMAL (two runs) | 926 | 1645 | 0.5629 |
| `4311e7fc5`, pinned DEGRADED | 1091 | 1872 | 0.5828 |

**What this does and does not say.** The mode is not the explanation: the current tree is above 0.5 under both modes. The cause between `24920f912` and now is not isolated. Planner's domain hypothesis, **not verified**: fewer combat events raise cooperation's share. A caution against it as the whole story: the cooperation COUNT itself roughly doubled (459 to 926), which a smaller denominator cannot produce; combat events fell, but cooperation grew in absolute terms. The test's original concern was co-located entities inflating the share to ~79%; `InvariantViolation` is 0 and the scatter test passes, so this does not look like co-location.

## Scope
1. Isolate where the share crossed 0.5 (a bisect over the commits between `24920f912` and `main` with the NORMAL pin, as in `TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS`'s investigation), and what emits the extra `cooperation_event`s.
2. Decide whether 56% is a defect (then fix it) or a legitimate change in the stream (then the threshold is wrong, and that is a decision for the test owner, not a quiet edit).

## Out of Scope
- Changing the 0.5 threshold without that decision.
- The attack chain itself (`TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE`, `TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK`).

## Acceptance Criteria
- [ ] The commit range where the share crossed 0.5 is identified and what changed is stated.
- [ ] Defect or legitimate drift is decided by its owner; if a defect, fixed, and the strict xfail flips (XPASS) in the same change.

## Related Tickets
- `TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS` (the campaign test; the possible-symptom link: fewer combat events and the attack chain)
- `TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE`
- `TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK`

## Related Docs
- None yet.

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS/probes/coop_share.py`, `pinned_measure.py`.

## Related Code Areas
- `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py` (`test_real_campaign_episode_event_mix_is_not_dominated_by_cooperation`); the source of `cooperation_event` (not yet located).

## Assumptions / Open Questions
- One seed (42), one 70-tick episode.
- Which system emits the extra cooperation events is not yet known.

## Implementation Notes
(not started)

## Test Summary
(not started)

## Files Changed
(not started)

## Completion Summary
(not started)
