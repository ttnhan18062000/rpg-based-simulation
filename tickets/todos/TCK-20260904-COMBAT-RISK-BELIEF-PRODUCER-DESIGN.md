---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN
phase: open
date: 2026-09-04
tags: [content]
---

# TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN

## Title
Design and wire a real producer for entity.strategic.beliefs["combat_risk"] -- a tested consumer with
no production writer

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`TCK-20260904-COMBAT-RISK-BELIEF-DEAD-READ` investigated `src/domains/cooperation/evaluators.py:47`'s
`entity.strategic.beliefs.get("combat_risk")` read and found it is **not dead code** — it's a real,
deliberately designed, tested consumer with no production producer. Confirmed via direct grep: 5 test
files (`tests/unit/domains/cooperation/test_phase7_help_need_evaluator.py`,
`tests/integration/domains/cooperation/test_phase7_cooperation_phase.py`,
`tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py` (x2),
`tests/perf/test_phase7_social_cooperation_budget.py`) manually construct
`entity.strategic.beliefs["combat_risk"] = {"level": RiskLevel.HIGH}` to exercise
`HelpNeedEvaluator.evaluate()`'s HIGH/EXTREME-risk branch — proving the consumer contract is real and
intentional, not leftover cruft. No code anywhere in `src/` writes this key in a live gameplay path;
only tests construct it artificially.

Checked the two most obvious candidate existing signals as a possible reused producer — neither fits
directly:
- `src/systems/strategic_systems/belief.py::estimate_threat()` — also has zero real callers anywhere,
  and models **regional** danger (concerns/leads about a region), not an entity's own personal
  in-combat risk. A different concept, not a drop-in producer.
- No other existing "combat danger assessment" computation was found.

## Scope
- Design what should actually determine an entity's `combat_risk` level (`LOW`/`NORMAL`/`HIGH`/
  `EXTREME`) — candidate signals include recent HP loss/trend, nearby hostile entity count/strength,
  active combat engagement duration, or some combination. This needs real design-authority input, not
  an invented formula — deliberately not decided in this ticket.
- Once designed, implement the producer and wire it into whichever phase should compute it (likely
  strategic cognition or combat-adjacent, given `HelpNeedEvaluator` already runs in Phase 7
  cooperation).
- Confirm the 5 existing tests' manually-constructed `combat_risk` dict shape (`{"level": RiskLevel}`)
  matches whatever the real producer emits — do not silently change the consumer contract without
  updating those tests in the same ticket.

## Out of Scope
- `src/systems/strategic_systems/belief.py::estimate_threat()`'s own separate zero-caller status — a
  distinct finding (regional threat, not personal combat risk), not part of this ticket unless design
  review decides to actually reuse/extend it.
- Any other `StrategicComponent.beliefs` key or the `BeliefEntry`/`KnowledgeFact` reconciliation
  question — already decided separately (`TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION`).

## Acceptance Criteria
- [ ] Real combat-risk-assessment design confirmed with design-authority input, not invented
      unilaterally.
- [ ] A real producer writes `entity.strategic.beliefs["combat_risk"]` in a live gameplay path.
- [ ] All 5 existing tests that manually construct this belief still pass (or are updated in step with
      a confirmed, deliberate contract change).
- [ ] `HelpNeedEvaluator.evaluate()`'s combat-support-need logic is verified to actually fire in a real
      simulation run at least once, not just in hand-constructed unit tests.

## Related Tickets
- TCK-20260904-COMBAT-RISK-BELIEF-DEAD-READ (the investigation that found this gap)

## Related Docs
None yet.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/domains/cooperation/evaluators.py` (`HelpNeedEvaluator.evaluate()`)
- `src/core/strategic.py` (`RiskLevel`)
- `src/systems/strategic_systems/belief.py` (`estimate_threat()`, checked but not a direct fit)

## Assumptions / Open Questions
- What real signal(s) should determine `combat_risk` level is the central open design question this
  ticket must resolve before implementation — deliberately not decided here.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
