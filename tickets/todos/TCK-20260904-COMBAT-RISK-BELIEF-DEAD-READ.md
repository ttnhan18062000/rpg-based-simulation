---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260904-COMBAT-RISK-BELIEF-DEAD-READ
phase: open
date: 2026-09-04
tags: [content]
---

# TCK-20260904-COMBAT-RISK-BELIEF-DEAD-READ

## Title
entity.strategic.beliefs.get("combat_risk") is dead code -- the key is never written anywhere

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION`'s investigation, out of that
ticket's own scope. `src/domains/cooperation/evaluators.py:47`:
`combat_belief = entity.strategic.beliefs.get("combat_risk")`. Confirmed via repo-wide grep:
`"combat_risk"` is never written as a key into `strategic.beliefs` anywhere in `src/` — this read
always returns `None`, and the `if combat_belief:` branch that follows it is unreachable dead code.

`StrategicComponent.beliefs` is typed `Dict[str, Any]` (not `Dict[str, BeliefEntry]`) and, separately
from this dead key, genuinely holds real `BeliefEntry` objects keyed by belief id (from
`process_rumor`/`process_observation`, `src/systems/strategic_systems/belief.py`) — this ticket is
scoped to the dead `"combat_risk"` key specifically, not a review of the field's typing.

## Scope
- Decide whether `"combat_risk"` was meant to be a real, still-unimplemented producer (a feature gap —
  something should write this key) or whether the read itself is stale leftover code from a removed or
  never-finished feature (a cleanup — delete the dead read/branch).
- Check git history / related tickets for `evaluators.py`'s cooperation risk-assessment logic to
  determine which disposition is correct before acting — do not guess.
- Implement whichever disposition the investigation confirms.

## Out of Scope
- Any other field/key in `StrategicComponent.beliefs` — this ticket is scoped to `"combat_risk"` only.
- The `BeliefEntry`/`KnowledgeFact` reconciliation question — already decided separately
  (`TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION`).

## Acceptance Criteria
- [ ] Real disposition (feature gap vs. dead code) determined with evidence, not assumed.
- [ ] Either a real producer is added, or the dead read/branch is removed — not left as-is.
- [ ] Existing `src/domains/cooperation/` tests pass unchanged (or updated if the fix changes real
      behavior).

## Related Tickets
- TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION (where this was found)

## Related Docs
None.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/domains/cooperation/evaluators.py`

## Assumptions / Open Questions
- Whether this was ever a real feature (a producer exists somewhere not yet found, or existed and was
  removed) is not yet confirmed.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
