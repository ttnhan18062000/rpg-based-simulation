---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS
phase: open
date: 2026-09-06
tags: [simulation-quality, calibration]
---

# TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS

## Title
M7 step 4-5: re-run SimQ calibration against the new rule set, final completeness cross-check

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
M7 epic (`TCK-20260823-EPIC-RPG-M7-SIMQ-INTEGRATION`) child 2 of 2, depends on
`TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES` landing first. Implements the epic doc's Scope items 4-5:
re-run SimQ's own calibration workflow (real precedent: `TCK-20260628-SIMQ-E7-CALIBRATE`, confirmed
real and closed) against at least one corpus profile exercising the new content, to confirm the new
signal rules produce a meaningful grade signal rather than a flat, uninformative score; then a final,
explicit completeness check — cross-referencing the finished rule set against the prior ticket's
named-pillar list for all 65 ideas, so every idea that should touch a pillar has a traceable rule or
an explicit, written reason it doesn't.

## Scope
- Re-run SimQ's calibration workflow (`tools/calibrate_simq.py`, matching
  `TCK-20260628-SIMQ-E7-CALIBRATE`'s own precedent) against at least one real corpus profile that
  exercises the M1-M6 content the prior ticket added rules for.
- Confirm the new signal rules produce a meaningful, non-flat grade signal — not just "rules were
  written," a real recorded calibration result.
- Cross-reference the final rule set against the prior ticket's named-pillar list for all 65 ideas —
  a checklist against a known-complete list, not an open-ended scan. Every idea Pillar Reach says
  should touch a pillar needs a traceable rule or an explicit, written reason it doesn't (e.g. a pure
  governance/investigation idea legitimately has nothing to register).
- Record the completeness check's own results (pass/gap list) somewhere real and citable.

## Out of Scope
- Authoring any new signal rule or naming any new pillar mapping —
  `TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES`'s own scope, this ticket only calibrates and checks it.
- Closing M9's `CampaignScorecardEvaluator` field gap — a related but distinct SimQ gap, out of this
  epic's scope entirely.
- Fixing any gap the completeness check finds — record it, ticket it separately if real follow-up
  work is needed; this ticket verifies, it does not extend the rule set further.

## Acceptance Criteria
- [ ] A real calibration run against at least one corpus profile is completed and its results
      (grades/scores before and after the new rules) are recorded, not just asserted.
- [ ] The new signal rules are confirmed to produce a meaningful grade signal (a real change in score
      attributable to the new rules, not a flat/uninformative result).
- [ ] The completeness cross-check is recorded with an explicit pass/gap list against all 65 ideas —
      no idea silently unaccounted for.
- [ ] Any real gap the completeness check finds is either fixed in this same ticket (if small) or
      explicitly ticketed as separate follow-up work (if not) — never silently left unstated.

## Related Tickets
- `TCK-20260823-EPIC-RPG-M7-SIMQ-INTEGRATION` (parent epic)
- `TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES` (must land first)
- `TCK-20260628-SIMQ-E7-CALIBRATE` (`tickets/done/`, the real precedent this ticket's own calibration
  re-run follows)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_m7_simq_pillar_integration_epic.md`
- `docs/simulation_quality/quality_scoring_contract.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `tools/calibrate_simq.py`
- `src/simulation_quality/`
- `config/simulation_quality/profiles/`

## Assumptions / Open Questions
- Which corpus profile(s) to calibrate against is left to this ticket's own Investigate/Plan phases —
  not decided here; should exercise real M1-M6 content, not an unrelated older profile.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
