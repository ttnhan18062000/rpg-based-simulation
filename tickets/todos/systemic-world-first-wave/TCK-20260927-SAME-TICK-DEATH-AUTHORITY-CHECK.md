---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260927-SAME-TICK-DEATH-AUTHORITY-CHECK
phase: open
date: 2026-09-27
tags: [engine, combat, investigation]
---

# TCK-20260927-SAME-TICK-DEATH-AUTHORITY-CHECK

## Title
Determine whether a same-tick combat kill and lethal hazard damage on one entity resolve under a
declared authority rule

## Status
OPEN — brief only, not started. First-wave milestone M3a. Independent of every other first-wave
milestone. Starts only after the owner reviews the first-wave scope.

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
**Semantic contract** (roadmap §3.1): a persistent fact (here, whether an entity is alive, and
the recorded cause of death) has one canonical authority, and concurrent world effects resolve
under a declared rule, not by accident of ordering.

**Observed problem**:
- `alive_set` is written from combat resolution (`src/engine/combat.py`, 5 sites) and from
  world-dynamics hazard damage (`src/engine/world_dynamics.py:39`).
- Comments at `src/systems/world_systems/groups.py:99` and
  `src/engine/pipeline_phases/clan_lifecycle.py:19` suggest a deliberate precedence.
- No scenario exercises the same-tick collision, so the rule is asserted by comment, not verified.
- Audit classification (roadmap §3.1, boundary 2): `UNKNOWN_WITH_REASON`.

## Scope
One representative same-tick collision scenario through the real pipeline, with a bounded
statement of what it covers.

## Out of Scope
- Fixing any defect found; route it to a separate ticket.
- Other death causes.
- The natural-aging defect (M1).
- The region-ownership issue (FAC-010), which is tracked independently.

## Acceptance Criteria
1. The result is exactly one of:
   - `CONFIRMED_FINE_WITHIN_SCOPE`;
   - `DEFECT_CONFIRMED`, with root cause and a separate ticket;
   - `BLOCKED_WITH_REASON`, naming the exact harness or reachability limitation.
2. The report states the final alive/active state and the recorded cause. It says whether the death
   is processed exactly once and whether the commented precedence holds.
3. A harness limitation is never reported as "fine".
4. The outcome is recorded back into roadmap §3.1's audit table as a dated addendum.

## Related Tickets
- TCK-20260927-SAME-TICK-DIPLOMACY-AUTHORITY-CHECK (M3b)
- TCK-20260927-SAME-TICK-REPUTATION-AUTHORITY-CHECK (M3c)

## Related Docs
- `docs/plans/systemic_world/roadmap.md` §3.1
- `docs/plans/systemic_world/first_wave_plan.md` M3a

## Related Stored Artifacts
None.

## Related Code Areas
`src/engine/combat.py`, `src/engine/world_dynamics.py`, `src/systems/world_systems/groups.py`,
`src/engine/pipeline_phases/clan_lifecycle.py`. Evidence locations only.

## Assumptions / Open Questions
An incomplete, unverified scenario draft from a stopped exploratory agent exists on the local branch
`natural-aging-old-age-dispatch-fix-unreviewed` (`tests/integration/authority/`). It is not
evidence. The implementer may consult or discard it.

## Implementation Notes
_Not started — owned by the implementation agent._

## Test Summary
_Not started._

## Files Changed
_Not started._

## Completion Summary
_Not started._
