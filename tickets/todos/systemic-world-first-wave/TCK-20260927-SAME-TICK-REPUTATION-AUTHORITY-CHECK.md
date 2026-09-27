---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260927-SAME-TICK-REPUTATION-AUTHORITY-CHECK
phase: open
date: 2026-09-27
tags: [engine, social, investigation]
---

# TCK-20260927-SAME-TICK-REPUTATION-AUTHORITY-CHECK

## Title
Determine whether the two producers of an entity's reputation value can collide in one tick, and
if so whether a declared rule resolves it

## Status
OPEN — brief only, not started. First-wave milestone M3c. Independent of every other first-wave
milestone. Starts only after the owner reviews the first-wave scope.

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
**Semantic contract** (roadmap §3.1): a persistent value has one canonical authority, and
concurrent writes resolve under a declared rule. This is a **mechanical authority/order check
only**. It does not decide, and must not presume, what `public_reputation` means in the world;
that stays an open owner-level semantic question (roadmap §10, item 3).

**Observed problem**:
- `SocialComponent.reputation` (`reputation_set`) has two producers:
  - `src/domains/campaigns/social_memory.py:528`;
  - `src/domains/campaigns/orchestrator.py:928`.
- Their phase ordering, reachability, and same-tick, same-entity collision behaviour were not
  checked.
- Audit classification (roadmap §3.1, boundary 5): `UNKNOWN_WITH_REASON`.

## Scope
Establish the callers and phases of both producers and whether a same-tick, same-entity collision is
reachable. If it is, run one representative scenario through the real code path and state how two
values merge.

## Out of Scope
- Fixing any defect found (separate ticket).
- Any decision about reputation's meaning, provenance, or retention.

## Acceptance Criteria
1. The result is exactly one of:
   - `CONFIRMED_FINE_WITHIN_SCOPE`, either through a passing scenario or by showing the collision
     is unreachable by construction (say which);
   - `DEFECT_CONFIRMED`, with root cause and a separate ticket;
   - `BLOCKED_WITH_REASON`, for example flag or campaign-mode gating that prevents staging, with the
     exact reason.
2. The report states the committed value and the merge rule that produced it.
3. A harness limitation is never reported as "fine".
4. The outcome is recorded back into roadmap §3.1's audit table as a dated addendum.

## Related Tickets
- TCK-20260927-SAME-TICK-DEATH-AUTHORITY-CHECK (M3a)
- TCK-20260927-SAME-TICK-DIPLOMACY-AUTHORITY-CHECK (M3b)

## Related Docs
- `docs/plans/systemic_world/roadmap.md` §3.1, §10
- `docs/plans/systemic_world/first_wave_plan.md` M3c

## Related Stored Artifacts
None.

## Related Code Areas
`src/domains/campaigns/social_memory.py`, `src/domains/campaigns/orchestrator.py`. Evidence
locations only.

## Assumptions / Open Questions
An incomplete, unverified scenario draft from a stopped exploratory agent exists on the local branch
`natural-aging-old-age-dispatch-fix-unreviewed`. It is not evidence.

## Implementation Notes
_Not started — owned by the implementation agent._

## Test Summary
_Not started._

## Files Changed
_Not started._

## Completion Summary
_Not started._
