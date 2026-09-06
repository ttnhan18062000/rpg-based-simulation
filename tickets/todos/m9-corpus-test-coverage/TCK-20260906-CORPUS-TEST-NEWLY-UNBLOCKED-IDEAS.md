---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260906-CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS
phase: open
date: 2026-09-06
tags: [testing, simulation-quality, corpus]
---

# TCK-20260906-CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS

## Title
Author corpus tests for ideas 32+43, 51/52, 54, 60, 65 — blockers cleared since M9's original scoping

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
M9 epic (`TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE`) child 3 of 8. Each of these ideas was
flagged "blocked" in the original M9 scoping (2026-08-24), but re-verified against real code,
2026-09-06: every blocker has since shipped.

- **Idea 60 (Reputations Are Local)** — "hard-blocked... determinism-aware pass" cleared:
  `src/replay/fingerprint.py:72` already includes `regional_reputation` in the fingerprint string
  (landed with M5).
- **Ideas 32 (Reproduction) + 43 (population_cohorts seeding)** — "blocked on idea 43" cleared:
  `TCK-20260831-POPULATION-COHORT-SEEDING` (DONE) and M3's Reproduction epic (DONE) have both shipped.
- **Ideas 51/52 (Country EXPAND + population-driven expansion)** — "blocked on idea 43" cleared, same
  as above.
- **Idea 54 (Guilt by Association)** — "gated on Clan" cleared: Clan (idea 36) shipped in M2.
- **Idea 65 (Named Refugee Threads)** — "blocked on 43+59" cleared: idea 59
  (`TCK-20260905-HOME-EXILE-REFUGEE-THREADS`) is DONE alongside idea 43.

## Scope
Author the following corpus tests, per the epic doc's own concrete specs (re-confirm each against
real shipped code during Investigate, not just this ticket's citations):
- **Idea 60**: `frontier_extended` world — read the same entity's `public_reputation`-equivalent
  (confirm real field name, likely `regional_reputation`) from 3 different regions, assert 3 distinct
  values rather than one global float.
- **Idea 32+43**: `frontier_living_world`, past the existing 200-tick calibration window — assert
  `demographic_birth` fires at least once, `population_pressure_gate` reads `migration_threshold=0.7`
  correctly, and `genetic_inheritance_weight` (0.8-1.3) is applied to at least one child vs. parent
  average.
- **Ideas 51/52**: `frontier_marches` — assert `EXPAND_TERRITORY` fires for the faction with the
  highest population-scarcity signal, targeting an adjacent unclaimed region.
- **Idea 54**: new world needed, 2 Clans of 4 members each; one member of Clan A commits a witnessed
  betrayal; assert a stranger's trust delta toward an unmet Clan A member is measurably lower than
  baseline.
- **Idea 65**: `crowded_frontier` (6 factions, 4 regions) — trigger a hostile-pressure event in one
  region, assert a civilian's home-region field is set to the fled-from region and a displacement
  tick is recorded.

## Out of Scope
- Building any of these 5 ideas' underlying mechanisms — all confirmed already shipped; this ticket
  only authors the corpus tests exercising them.
- Any other item from M9's scope.

## Acceptance Criteria
- [ ] All 5 corpus tests above are authored and passing against real compiled worlds.
- [ ] Each test asserts the specific named outcome (not a generic smoke test) and would fail if the
      underlying mechanism regressed.

## Related Tickets
- `TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE` (parent epic)
- `TCK-20260831-POPULATION-COHORT-SEEDING`, `TCK-20260905-HOME-EXILE-REFUGEE-THREADS`,
  `TCK-20260904-CLAN-REPUTATION-ASSOCIATION` (the shipped prerequisites this ticket's tests target)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/replay/fingerprint.py`
- `src/domains/demographics/cohort.py`
- `config/simulation_quality/corpus_registry.yaml`

## Assumptions / Open Questions
- Idea 54's test needs a genuinely new corpus world (2 Clans of 4) — confirm no existing world already
  fits this shape before authoring one, during Investigate.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
