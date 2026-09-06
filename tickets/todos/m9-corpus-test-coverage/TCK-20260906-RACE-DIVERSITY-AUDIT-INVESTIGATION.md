---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260906-RACE-DIVERSITY-AUDIT-INVESTIGATION
phase: open
date: 2026-09-06
tags: [testing, simulation-quality, corpus]
---

# TCK-20260906-RACE-DIVERSITY-AUDIT-INVESTIGATION

## Title
Idea 37 (Species Relations) — scope a race-diversity dimension for the corpus registry

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
M9 epic (`TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE`) child 8 of 8, investigative. The original
epic doc confirmed a real gap that remains real, 2026-09-06: `config/simulation_quality/
corpus_registry.yaml` has no race-diversity dimension at all, so a test world for idea 37 (Species
Relations) can't be designed without first answering the epic doc's own Open Question: is this a
small addition to the existing corpus registry's scale metrics, or a wholly new registry dimension?

## Scope
- Investigate `config/simulation_quality/corpus_registry.yaml`'s real current schema and the 21 real
  worlds' actual race/species composition (reuse `data/content/living/races.yaml`'s 13 real entries,
  confirmed from earlier M8 work).
- Answer the epic doc's own Open Question with a real recommendation, grounded in the registry's
  actual current shape — not assumed here.
- Once answered, name a concrete world spec for idea 37's own corpus test (per this epic's own
  pattern — real world names, real entity/region counts, real assertable checks), following on from
  whichever registry-shape decision this investigation reaches. If a genuinely new world is needed,
  scope it; if an existing world already has sufficient race diversity, name it directly instead.

## Out of Scope
- Building idea 37's own species-relations mechanism (`Faction`-level race-relations matrix or
  equivalent) — confirm during Investigate whether this idea has even been ticketed into any
  milestone yet; if not, that's a real finding to report to the roadmap owner, not something to
  build inside this M9 corpus-testing epic.
- Any other item from M9's scope.

## Acceptance Criteria
- [ ] The registry-shape question (extend existing scale metrics vs. new dimension) has a concrete,
      evidenced recommendation.
- [ ] A named, concrete world spec exists for idea 37's corpus test (or an explicit written reason
      none can be specified yet, matching idea 63's own honest-deferral precedent elsewhere in this
      epic).
- [ ] If idea 37's own underlying mechanism is confirmed not yet built, that finding is reported
      clearly rather than a corpus test being fabricated against a mechanism that doesn't exist.

## Related Tickets
- `TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE` (parent epic)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `config/simulation_quality/corpus_registry.yaml`
- `data/content/living/races.yaml`

## Assumptions / Open Questions
- Whether idea 37 (Species Relations) has ever actually been ticketed into any shipped milestone is
  not confirmed here — real work for this ticket's own Investigate phase, given this session's own
  repeated finding pattern of ideas referenced in planning docs without ever landing in real code
  (see sibling ticket `TCK-20260906-CORPUS-TEST-NEW-WORLD-NEEDED`'s idea 50/64 finding).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
