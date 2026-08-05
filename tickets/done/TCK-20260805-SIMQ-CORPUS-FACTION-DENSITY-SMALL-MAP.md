---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260805-SIMQ-CORPUS-FACTION-DENSITY-SMALL-MAP
phase: done
date: 2026-08-05
tags: [simulation-quality, world, faction, corpus, calibration]
---

# TCK-20260805-SIMQ-CORPUS-FACTION-DENSITY-SMALL-MAP

## Title
Author a stress-tier world combining a high distinct-faction count (6-9) with a small entity/region footprint

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
`docs/simulation_quality/corpus_tier_taxonomy.md`'s "Named scale-diversity gaps" section (gap #1,
sourced from `TCK-20260704-SIMQ-CORPUS-TIERS-EPIC`'s own investigation) identifies that no world in
the current 18-world corpus combines a high distinct-faction count (6-9) with a small map — faction
density and world size currently move together across every existing world. This ticket authors a
new stress-tier world closing that specific gap.

Note (2026-08-05): corpus-breadth expansion was explicitly deprioritized relative to fixing
currently-wrong signals (see `docs/audits/D20_simq_quality_status_review.md`), and
`TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH` demonstrated content/scale additions don't reliably move
a pillar's grade when the real blocker is upstream logic, not corpus volume. This ticket is filed
as backlog, not urgent — it adds structural test-matrix coverage, not a fix for a known-wrong score.

## Scope
- Author a new world (`world.yaml` + compiled content) with 6-9 distinct factions in a small
  entity/region footprint (small relative to the corpus's existing faction-heavy worlds).
- Classify and register it per `corpus_tier_taxonomy.md`'s decision tree (fills a named
  scale-diversity gap → stress tier).
- Calibrate and commit anchors (`calibrate_simq.py`, `grade_anchors.json`) for the new world.
- Update `corpus_tier_taxonomy.md`'s "Named scale-diversity gaps" list to mark gap #1 closed,
  citing this ticket.

## Out of Scope
- The other 3 named scale-diversity gaps (resource density, AGENCY-active real archetype, quest
  density decoupling) — each tracked as its own sibling ticket in this folder.
- Any scoring/scorer change — this ticket only adds corpus content, consistent with the
  content-depth ceiling already documented; do not assume this will move FACTION's grade.

## Acceptance Criteria
1. New world exists with 6-9 distinct factions and a small entity/region footprint, distinguishable
   from existing faction-heavy worlds by this combination specifically.
2. World is classified and documented in `corpus_tier_taxonomy.md` as stress-tier, with its
   justification citing gap #1.
3. Anchors committed to `grade_anchors.json` and `test_grade_regression.py` passes for the new world.
4. `corpus_tier_taxonomy.md`'s gap #1 entry is marked closed with a citation to this ticket.

## Related Tickets
- `TCK-20260704-SIMQ-CORPUS-TIERS-EPIC` — parent epic that identified this gap.
- `TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS` — precedent stress-tier world-authoring ticket, same
  pattern.
- `TCK-20260805-SIMQ-CORPUS-RESOURCE-DENSITY-DECOUPLE`,
  `TCK-20260805-SIMQ-CORPUS-AGENCY-REAL-ARCHETYPE`,
  `TCK-20260805-SIMQ-CORPUS-QUEST-DENSITY-DECOUPLE` — sibling tickets for the other 3 gaps;
  mutually independent, no ordering constraint between them.

## Related Docs
- `docs/simulation_quality/corpus_tier_taxonomy.md` — "Named scale-diversity gaps" §, gap #1.
- `docs/simulation_quality/extension_points.md` §1 (World breadth).

## Related Stored Artifacts
None yet — standard tier, staging artifacts to be created at Scope.

## Related Code Areas
- `data/worlds/` (new world directory)
- `tests/simulation_quality/fixtures/grade_anchors.json`

## Assumptions / Open Questions
- The exact faction count within the 6-9 range and the exact "small" footprint threshold are left
  to the investigation phase to pin down against the existing corpus's actual distribution, not
  assumed here.

## Implementation Notes
Authored a draft world (`faction_dense_frontier`: frontier_village_core + goblin_camp_conflict +
moon_cult_ruins + sunken_swamp_border + old_mine_resource_loop + orc_clan_territory), resolved and
compiled it, verified via direct `WorldCompiler.compile()` inspection that it produced 7 genuinely
populated distinct factions on a 44-entity/6-region map. Before calibrating anchors, compared
against the existing corpus and found `crowded_frontier` (6 factions/4 regions, already documented
in `corpus_tier_taxonomy.md`'s per-world table as closing this exact gap) and
`generated_frontier_3_42` (7 factions/6 regions — an identical footprint to the draft world) both
already satisfy the gap's own stated 6-9-faction/small-map criteria. The doc's "Named
scale-diversity gaps" list section had simply never been updated to reflect this, even though the
per-world table a few dozen lines earlier already recorded it. Reverted all draft-world artifacts
(`data/worlds/faction_dense_frontier/`, 3 calibration directories, 3 `grade_anchors.json` entries,
`test_grade_regression.py`'s `FAST_ANCHOR_KEYS`/count edits) rather than ship redundant corpus
content, and corrected the stale doc section instead.

## Test Summary
`pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q`: 65 passed / 1 failed
— identical to the pre-ticket baseline (same pre-existing, unrelated
`urban_political_seed42_200t` failure documented in prior tickets this session), confirming the
revert left no trace.

## Files Changed
- `docs/simulation_quality/corpus_tier_taxonomy.md` — gap #1 marked CLOSED in the "Named
  scale-diversity gaps" section, with the staleness and correction explained

## Completion Summary
Investigated authoring a stress-tier world combining a high distinct-faction count (6-9) with a
small map, per the ticket's original scope. Found — via direct compilation and comparison, not
just re-reading the ticket's own premise — that this gap was already closed twice over before the
ticket was even filed, by `crowded_frontier` and `generated_frontier_3_42`. A draft world was
built and found to have an identical footprint to `generated_frontier_3_42`'s; shipping it would
have been redundant corpus padding, not real coverage, so it was reverted. The actual, real
deliverable of this ticket is the correction to `corpus_tier_taxonomy.md`'s stale gap-list
section, which had disagreed with its own per-world table. No new world was needed.
