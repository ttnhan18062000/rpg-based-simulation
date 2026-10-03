---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260904-COMBAT-RISK-BELIEF-DEAD-READ
phase: done
date: 2026-09-04
tags: [content]
---

# TCK-20260904-COMBAT-RISK-BELIEF-DEAD-READ

## Title
entity.strategic.beliefs.get("combat_risk") is NOT dead code -- it's a real, tested consumer with a
missing production producer

## Status
DONE

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
- [x] Real disposition (feature gap vs. dead code) determined with evidence, not assumed. **Feature
      gap, confirmed via 5 real test files** (`tests/unit/domains/cooperation/
      test_phase7_help_need_evaluator.py`, `tests/integration/domains/cooperation/
      test_phase7_cooperation_phase.py`, `tests/integration/scenarios/
      test_phase7_social_cooperation_scenarios.py` (x2), `tests/perf/
      test_phase7_social_cooperation_budget.py`) that manually construct
      `entity.strategic.beliefs["combat_risk"] = {"level": RiskLevel.HIGH}` to exercise the consumer's
      HIGH/EXTREME branch — a real, deliberate, tested contract, not leftover cruft.
- [x] Either a real producer is added, or the dead read/branch is removed — not left as-is. **Neither
      done inline here** — building the actual producer needs real combat-risk-assessment design
      (HP trend? nearby threat? none specified anywhere found), which this hotfix-tier ticket cannot
      invent unilaterally without misrepresenting the intended mechanic. Filed as its own standard-tier
      design ticket, `TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN`, per this repo's own
      Clarification Rule (don't guess when uncertainty affects behavior/architecture).
- [x] Existing `src/domains/cooperation/` tests pass unchanged (or updated if the fix changes real
      behavior). Unchanged — no code was modified, only investigated.

## Related Tickets
- TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION (where this was found)
- TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN (the follow-up filed to actually build the producer)

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
Read `src/domains/cooperation/evaluators.py:47`'s full context: `combat_belief.get("level", ...)`
expects a dict shape (`{"level": RiskLevel}`), not a `BeliefEntry` dataclass — confirming this key was
always meant to hold a different shape than the real `BeliefEntry` objects also stored in the same
`Dict[str, Any]` field. Grepped all `RiskLevel` usages repo-wide to check for an obvious existing
producer to wire in — found none. Checked `belief.py::estimate_threat()` as the most plausible existing
candidate: also zero real callers, and models regional danger (concerns/leads about a region), not an
entity's own personal combat risk — a different concept, not a drop-in fix.

Grepped `tests/` for `combat_risk` (not just `src/`) and found the real evidence that changed this
ticket's disposition: 5 test files manually construct the belief to test a real, intentional consumer
branch. Concluded this is confirmed a genuine feature gap, not dead code — implementing a producer
requires real design input (what determines combat risk?) that this ticket cannot invent, so filed
`TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN` rather than guessing a formula.

## Test Summary
No code changed — investigation only, per the confirmed disposition (a design decision is needed before
any implementation, not this ticket's own call to make).

## Files Changed
- `tickets/todos/TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN.md` — new, filed as the real follow-up.

## Completion Summary
Investigated whether `entity.strategic.beliefs.get("combat_risk")` was dead code or a feature gap.
Confirmed feature gap, not dead code: 5 real test files manually construct this belief to test a real,
intentional `HelpNeedEvaluator` consumer branch, but no production code anywhere writes it. Did not
implement a producer inline — the actual combat-risk-assessment design (which signals should determine
risk level) is a real design decision this ticket cannot invent unilaterally without misrepresenting the
intended mechanic. Filed `TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN` as the properly-scoped
standard-tier follow-up for whoever has the design authority to specify it.
