---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260927-SAME-TICK-DIPLOMACY-AUTHORITY-CHECK
phase: open
date: 2026-09-27
tags: [engine, faction, investigation]
---

# TCK-20260927-SAME-TICK-DIPLOMACY-AUTHORITY-CHECK

## Title
Determine whether conflicting same-tick diplomatic relation changes for one faction pair resolve
under a declared authority rule

## Status
OPEN — brief only, not started. First-wave milestone M3b. Independent of every other first-wave
milestone. Starts only after the owner reviews the first-wave scope.

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
**Semantic contract** (roadmap §3.1): the diplomatic relation between two factions has one
canonical authority. Conflicting same-tick changes resolve under a declared rule.

**Observed problem**:
- `diplomatic_relations_set` is written in the same pipeline phase and tick by two producers:
  - the autonomous transition state machine
    (`src/domains/faction/diplomatic_state_machine.py`);
  - the auto-alliance handler (`src/domains/faction/diplomatic_actions.py`).
- Their updates are concatenated before a single merge (`src/engine/pipeline.py:255-283`).
- The ordering looks intentional, but nothing asserts what happens when both target the same pair
  with different relations in one tick.
- Audit classification (roadmap §3.1, boundary 3): `UNKNOWN_WITH_REASON`.

## Scope
One representative same-pair, same-tick scenario through the real phase code, and a check for any
stated precedence rule in docs, docstrings, or the parity ledger.

## Out of Scope
- Fixing any defect found (separate ticket).
- Broader diplomacy balance or semantics.

## Acceptance Criteria
1. The result is exactly one of:
   - `CONFIRMED_FINE_WITHIN_SCOPE`, either through a passing scenario or by showing the collision
     cannot occur by construction (say which);
   - `DEFECT_CONFIRMED`, with root cause and a separate ticket;
   - `BLOCKED_WITH_REASON`, with the exact reason.
2. The report states the committed relation and whether it follows a declared rule or only
   incidental ordering.
3. A harness limitation is never reported as "fine".
4. The outcome is recorded back into roadmap §3.1's audit table as a dated addendum.

## Related Tickets
- TCK-20260927-SAME-TICK-DEATH-AUTHORITY-CHECK (M3a)
- TCK-20260927-SAME-TICK-REPUTATION-AUTHORITY-CHECK (M3c)

## Related Docs
- `docs/plans/systemic_world/roadmap.md` §3.1
- `docs/plans/systemic_world/first_wave_plan.md` M3b

## Related Stored Artifacts
None.

## Related Code Areas
`src/domains/faction/`, `src/engine/pipeline.py`. Evidence locations only.

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
