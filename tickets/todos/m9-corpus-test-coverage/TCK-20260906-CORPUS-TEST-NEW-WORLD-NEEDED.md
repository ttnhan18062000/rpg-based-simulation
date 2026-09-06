---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260906-CORPUS-TEST-NEW-WORLD-NEEDED
phase: open
date: 2026-09-06
tags: [testing, simulation-quality, corpus]
---

# TCK-20260906-CORPUS-TEST-NEW-WORLD-NEEDED

## Title
Ideas 50 (Material-Gated Evolution) and 64 (The Empty Chair) — corpus-test authoring is blocked, mechanisms never shipped

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P3

## Request Summary
M9 epic (`TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE`) child 5 of 8. **Correction, 2026-09-06,
found while scoping this ticket, not inherited from the original M9 doc uncritically**: this item's
original framing ("new Unit-tier world needed" for corpus testing) wrongly assumed both ideas'
underlying mechanisms already exist. Direct verification found otherwise:
- **Idea 64 (The Empty Chair)**: M4's own epic doc (`rpg_m4_beyond_city_epic.md`) explicitly states
  "No code precedent anywhere for the economic-vacancy signal it needs" — confirmed still true via
  direct grep, zero real code hits for `EconomicVacancyEvent` anywhere in `src/`. M4's roadmap summary
  claims "all 12 ideas shipped," but idea 64 was evidently not actually among the ideas that landed
  in that batch — a real discrepancy between the roadmap's summary count and this specific idea's
  real state, matching the "roadmap overclaims completion" pattern found repeatedly elsewhere in this
  roadmap.
- **Idea 50 (Material-Gated Evolution)**: does not appear in any shipped milestone's epic doc at all
  (only in the atlas and M9's own speculative doc) — zero real code hits for `alt_outcome_kind`.
  Never actually ticketed into any milestone's real scope.

Both ideas are real design concepts (confirmed present in `docs/brainstorm/rpg_feature_atlas.html`),
just never built. M9 itself builds nothing (see epic's Out of Scope) — corpus-test authoring for these
two is genuinely blocked until each idea's own mechanism ships via a future milestone ticket, not
ready work today.

## Scope
- Correct the M9 epic doc's item 4 entries for ideas 50/64 to reflect this finding (mechanism not
  shipped, not merely "needs a new world").
- Flag idea 64 specifically to whoever eventually re-audits M4's completion claims — its "all 12
  ideas shipped" framing appears to not actually include this idea.
- No corpus-test authoring in this ticket — genuinely blocked, not this ticket's work to do.

## Out of Scope
- Building either idea's underlying mechanism — that belongs in a future milestone's own ticket, not
  this M9 corpus-testing epic.
- Re-auditing the rest of M4's "12 ideas shipped" claim beyond this one specific discrepancy.

## Acceptance Criteria
- [ ] M9 epic doc's item 4 entries for ideas 50/64 corrected to state the real blocker (mechanism not
      shipped) rather than "new world needed."
- [ ] The M4 "12 ideas shipped" discrepancy for idea 64 is flagged somewhere real and citable (this
      ticket, or a cross-reference from M4's own roadmap section) — not silently left uncorrected.

## Related Tickets
- `TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE` (parent epic)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md`
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` (M4 section's "12 ideas shipped" claim)

## Assumptions / Open Questions
- Whether idea 64 should be re-scoped into a real future ticket (since M4 apparently never actually
  built it despite being reviewed in that epic's own doc) is a real product decision, not resolved
  here — flag to the user/roadmap owner, don't unilaterally ticket new feature work from within this
  M9 corpus-testing epic.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
