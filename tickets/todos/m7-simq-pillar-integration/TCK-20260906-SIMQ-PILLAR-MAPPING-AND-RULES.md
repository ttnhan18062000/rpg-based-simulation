---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES
phase: open
date: 2026-09-06
tags: [simulation-quality, content]
---

# TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES

## Title
M7 step 1-3: name pillars for all 65 ideas, inventory real event types, author missing SimQ signal rules

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
M7 epic (`TCK-20260823-EPIC-RPG-M7-SIMQ-INTEGRATION`) child 1 of 2. Implements the epic doc's Scope
items 1-3: expand the Merit Scorecard's Pillar Reach axis from a count (e.g. "5/10") into named
pillars per idea; for each shipped idea (M1-M6, all confirmed DONE), confirm its real event types
exist and are named; and author a signal rule (following the exact shape already used by the 10
pillars' existing rules in `docs/simulation_quality/quality_scoring_contract.md` §5) for every named
event type that doesn't already have one.

**Confirmed real, not assumed, before this ticket's own Investigate phase re-confirms at
implementation time:**
- The 10 real pillars are: COGNITION, AGENCY & ACTION, COMBAT, FACTION & MILITARY, ECONOMY,
  PROGRESSION, SOCIAL, INFORMATION & BELIEF, WORLD DYNAMICS, NARRATIVE
  (`docs/simulation_quality/quality_scoring_contract.md` §5).
- **A real, concrete complication, not a hypothetical**: at least 3 of the 65 ideas are disclosed as
  "built, not yet visible in play" — idea 57 (`FameDeriver`/`LegendFact`, zero live Perception/
  Motivation pipeline call sites), idea 62 (`FidelityDeriver`, no live consumer), idea 56
  (`LoyaltyDriftService`, the one live per-tick call site never passes its signal). This ticket's own
  event-type inventory (Scope item 2) must check each of these 3 for whether they actually emit any
  real, observable event today — if none do, that is not this ticket's bug to fix, but it must be
  recorded as an explicit "no live event type yet" disposition, not silently mapped to a pillar it
  can't actually signal for, and not silently dropped from the list either.

## Scope
- For all 65 ideas (`docs/brainstorm/design_merit_scorecard.html`'s Pillar Reach axis), name the
  specific pillar(s) each should register with, replacing the current count-only representation.
- For each shipped idea (M1-M6), confirm its real event type(s) exist in code and are named — a
  direct read of what got built, not a redesign.
- Cross-check every named event type against `quality_scoring_contract.md` §5's existing per-pillar
  signal tables. For each event type with no existing rule, author one (a signal, a delta, a tag)
  following the exact existing pattern.
- Explicitly disposition the 3 flagged dormant ideas (57, 62, 56) per the Request Summary above.

## Out of Scope
- Re-running SimQ's calibration workflow or the final completeness cross-check —
  `TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS`, sequenced after this ticket.
- Building any new mechanism to make the 3 dormant ideas' event types live — that is each idea's own
  future follow-up ticket, not this one.
- Designing a signal rule for any event type that doesn't actually exist in shipped code.

## Acceptance Criteria
- [ ] All 65 ideas have a named-pillar mapping recorded (not just a count).
- [ ] Every real event type introduced by M1-M6 either has a traceable SimQ signal rule, or an
      explicit, written reason it's intentionally excluded (including the 3 flagged dormant ideas).
- [ ] New signal rules follow the exact existing shape/pattern in `quality_scoring_contract.md` §5 —
      no new rule-authoring convention invented.
- [ ] `docs/simulation_quality/quality_scoring_contract.md` and/or
      `docs/brainstorm/design_merit_scorecard.html` updated to reflect the named-pillar mapping.

## Related Tickets
- `TCK-20260823-EPIC-RPG-M7-SIMQ-INTEGRATION` (parent epic)
- `TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS` (sequenced after this ticket)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_m7_simq_pillar_integration_epic.md`
- `docs/simulation_quality/quality_scoring_contract.md`
- `docs/brainstorm/design_merit_scorecard.html`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/simulation_quality/` (`scorers/`, `pillar_accumulator.py`, `quality_report.py`)
- `src/domains/fame/`, `src/domains/fidelity/`, `src/systems/social_systems/loyalty_drift.py`

## Assumptions / Open Questions
- Whether a dormant idea with no live event type gets its own placeholder rule (inert until the
  event exists) or a pure documentation exclusion is left to this ticket's own Investigate/Plan
  phases — not decided here.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
