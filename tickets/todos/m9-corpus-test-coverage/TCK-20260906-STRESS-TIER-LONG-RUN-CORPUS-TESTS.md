---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260906-STRESS-TIER-LONG-RUN-CORPUS-TESTS
phase: open
date: 2026-09-06
tags: [testing, simulation-quality, corpus]
---

# TCK-20260906-STRESS-TIER-LONG-RUN-CORPUS-TESTS

## Title
Idea 48 stress-tier corpus test (ready); idea 57 corpus test blocked on already-known dormant-wiring gap

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
M9 epic (`TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE`) child 6 of 8. Both ideas need longer-run/
stress-tier corpus extensions per the original epic doc, but re-verification, 2026-09-06, found their
readiness differs:
- **Idea 48 (Place-Type Transitions)** — confirmed shipped (M2's epic doc,
  `rpg_m2_foundational_systems_epic.md`), and its `region_transformed` event confirmed real and live
  (`src/observability/event_extractor.py`, `event_shapers.py`,
  `src/simulation_quality/scorers/world_dynamics.py`). Ready to test.
- **Idea 57 (Living Legend Feedback Loop)** — `heroism_score` is real (`src/core/models/social.py`),
  but the corpus test's own required mechanism (a Townsperson's Motivation & Doctrine route bias
  shifting after a fame-perception event) is NOT live: zero hits for any Perception/Motivation
  call site consuming `heroism_score`/`LegendFact` output anywhere in `src/systems/
  strategic_systems/` or `src/domains/fame/`. This matches the already-known, already-disclosed gap
  from idea 57's own M5 ticket and M7's own scoping pass (`PerceptionUpdatePhase`/
  `MotivationBiasService` have zero live pipeline call sites for this signal) — not a new finding,
  but confirmed still blocking this specific corpus test.

## Scope
- **Idea 48**: extend `lifecycle_full_coverage_world` (41 entities, 8 regions, stress tier, 7
  factions). Author a `faction_tension_overrides` entry driving sustained conflict against the
  `frontier_village_core` region; since this world's only committed run_key is 200t, a siege reaching
  completion needs a separate, longer manual run via the long-run tooling, outside
  `grade_anchors.json`. Assert `Place.kind` flips CITY->RUIN and `region_transformed` fires. **Real
  risk to carry into the assertion design**: this world's own prior investigation found sustained
  COMBAT pressure starves SOCIAL/GUILD goal-selection for the whole run — tolerate SOCIAL/GUILD
  dropping in this specific test, don't treat it as a false regression.
- **Idea 57**: do NOT author this corpus test yet — it cannot currently produce a real, non-vacuous
  assertion. Document the blocker in the M9 epic doc (already partially done via the dormant-idea
  cross-references elsewhere this session) and leave a forward pointer to whichever future ticket
  builds the Perception/Motivation live wiring.

## Out of Scope
- Building idea 57's missing Perception/Motivation wiring — that is real, separate future work
  (already disclosed by idea 57's own M5 ticket as out of that ticket's scope too).
- Any other item from M9's scope.

## Acceptance Criteria
- [ ] Idea 48's corpus test is authored and passing, with the SOCIAL/GUILD-drop caveat explicitly
      documented in the test itself (a comment or assertion tolerance), not silently ignored.
- [ ] Idea 57's corpus test is explicitly deferred with a written reason (dormant wiring gap), not
      silently dropped or fabricated against a mechanism that doesn't fire.

## Related Tickets
- `TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE` (parent epic)
- `TCK-20260905-FAME-DERIVER-LEGEND-FACT` (idea 57's own ticket, already disclosed this same gap)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/simulation_quality/scorers/world_dynamics.py`
- `data/content/world_modules/` (`lifecycle_full_coverage_world`)

## Assumptions / Open Questions
- None beyond the idea-57 deferral already stated above.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
