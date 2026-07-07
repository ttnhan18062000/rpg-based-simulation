---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP
phase: open
date: 2026-07-07
tags: [simulation-quality, world, corpus, calibration]
---

# TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP

## Title
`test_population_stability`/`test_hazard_kind_completeness` don't parametrize `dungeon_crawl`, `sandbox_world`, or `generated_frontier_3_42`

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`'s Verify phase (done-checker gate).
`tests/unit/worldassembly/test_corpus_diversity.py`'s `POPULATION_STABILITY_WORLDS` list is built from
`ANCHORED_WORLD_BANDS.keys()` (`frontier_extended`, `frontier_living_world`, `wilderness_survival`,
`highland_traverse`, `swamp_border_world` — the 5 worlds `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`
anchored) plus the unit-tier isolation worlds added by later tickets
(`unit_faction_tension`/`unit_information_source`/`unit_selfmodel_pilot`/`hero_guild_routing`). It
never included `dungeon_crawl`, `sandbox_world`, `generated_frontier_3_42` (or `urban_political`,
though that one may have separate coverage — verify during investigation), so the >=60%-alive-floor
population-collapse regression guard and the hazard-kind-completeness guard do not run against them
at all. This predates `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` (which added FACTION/
INFORMATION content to `dungeon_crawl` and `sandbox_world`, and content-only to
`generated_frontier_3_42`) — that ticket did not introduce the gap, it surfaced it.

## Scope
1. Confirm which of the corpus's 10+ compiled worlds currently have `test_population_stability`/
   `test_hazard_kind_completeness` coverage vs. not (re-derive from `POPULATION_STABILITY_WORLDS`
   and any other coverage list in `test_corpus_diversity.py`, don't assume the 3 named above are the
   only gaps — verify `urban_political`'s status too).
2. Add `dungeon_crawl`, `sandbox_world`, and `generated_frontier_3_42` (and `urban_political`, if
   confirmed missing) to `POPULATION_STABILITY_WORLDS`.
3. Run each newly-added world through `test_population_stability` and `test_hazard_kind_completeness`
   to confirm they actually pass — if any fails, that is a genuine pre-existing defect this ticket
   must then decide whether to fix (content/hazard-tag gap) or escalate, not silently paper over.

## Out of Scope
- Adding any of these worlds to `ANCHORED_WORLD_BANDS` (a separate, larger concern — entity-count-band
  anchoring, not just population-stability/hazard-kind coverage)
- Any FACTION/INFORMATION/AGENCY content changes — this is a test-coverage-only ticket

## Acceptance Criteria
- [ ] Full audit of which corpus worlds have `test_population_stability`/`test_hazard_kind_completeness`
      coverage, documented in this ticket's investigation
- [ ] `dungeon_crawl`, `sandbox_world`, `generated_frontier_3_42` added to `POPULATION_STABILITY_WORLDS`
      (plus `urban_political` if confirmed missing)
- [ ] All newly-covered worlds pass both tests, or any genuine failure is documented and escalated
      (not silently fixed as an undocumented side effect)

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION — the ticket whose done-checker gate surfaced this
  pre-existing gap
- TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS — originally added `test_population_stability` and the 5-world
  `ANCHORED_WORLD_BANDS` list this ticket's `POPULATION_STABILITY_WORLDS` builds on

## Related Docs
- None beyond the code itself (`tests/unit/worldassembly/test_corpus_diversity.py`'s own module
  docstring documents `test_population_stability`'s purpose)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION/` — where this gap was found

## Related Code Areas
- `tests/unit/worldassembly/test_corpus_diversity.py` — `POPULATION_STABILITY_WORLDS`,
  `test_population_stability`, `test_hazard_kind_completeness`

## Assumptions / Open Questions
- Assumes adding these worlds to the list is purely additive and low-risk (matching the precedent of
  every prior ticket that added a world to this same list) — but a genuine population-collapse or
  hazard-kind failure surfacing for one of them is a real possibility this ticket must handle
  honestly, not assume away.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
