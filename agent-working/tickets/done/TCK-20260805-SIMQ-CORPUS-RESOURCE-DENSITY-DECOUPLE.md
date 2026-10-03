---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260805-SIMQ-CORPUS-RESOURCE-DENSITY-DECOUPLE
phase: done
date: 2026-08-05
tags: [simulation-quality, world, economy, corpus, calibration]
---

# TCK-20260805-SIMQ-CORPUS-RESOURCE-DENSITY-DECOUPLE

## Title
Author a stress-tier world decoupling resource-node density from map size (small map/dense nodes, or sprawling map/sparse nodes)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
`docs/simulation_quality/corpus_tier_taxonomy.md`'s "Named scale-diversity gaps" (gap #2) notes
node-per-region density is currently roughly flat (1.3-1.75) across the entire corpus regardless of
overall map scale — no world tests either a small map with high resource-node density, or a
sprawling map with sparse resources. This ticket authors a new stress-tier world closing that gap.

Note (2026-08-05): filed as backlog, not urgent, per the same corpus-breadth-deprioritization
rationale as its sibling tickets — see
`TCK-20260805-SIMQ-CORPUS-FACTION-DENSITY-SMALL-MAP`'s Request Summary for the full caveat.

## Scope
- Author a new world with resource-node density substantially outside the corpus's current
  1.3-1.75/region band, in one of the two decoupled directions (dense nodes + small map, or sparse
  nodes + sprawling map) — the investigation phase should pick whichever direction has more
  diagnostic value for ECONOMY (e.g. does node scarcity at scale expose different failure modes
  than the content-volume ceiling already documented in `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH`?).
- Classify and register per `corpus_tier_taxonomy.md`'s decision tree (stress tier).
- Calibrate and commit anchors.
- Update `corpus_tier_taxonomy.md`'s gap #2 entry to closed, citing this ticket.

## Out of Scope
- The other 3 named scale-diversity gaps — sibling tickets, independent.
- Any ECONOMY scorer/scoring change — content-only, per the documented content-depth ceiling; this
  ticket should not be read as an attempt to move ECONOMY's grade.

## Acceptance Criteria
1. New world exists with resource-node density clearly decoupled from map size, in the direction
   chosen by the investigation phase, with the choice justified in `plan.md`.
2. World is classified and documented in `corpus_tier_taxonomy.md` as stress-tier, citing gap #2.
3. Anchors committed and `test_grade_regression.py` passes for the new world.
4. `corpus_tier_taxonomy.md`'s gap #2 entry marked closed with a citation to this ticket.

## Related Tickets
- `TCK-20260704-SIMQ-CORPUS-TIERS-EPIC` — parent epic that identified this gap.
- `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH` — prior finding that content-volume additions alone
  don't move ECONOMY's grade; relevant context for choosing this world's diagnostic angle.
- `TCK-20260805-SIMQ-CORPUS-FACTION-DENSITY-SMALL-MAP`,
  `TCK-20260805-SIMQ-CORPUS-AGENCY-REAL-ARCHETYPE`,
  `TCK-20260805-SIMQ-CORPUS-QUEST-DENSITY-DECOUPLE` — sibling tickets, mutually independent.

## Related Docs
- `docs/simulation_quality/corpus_tier_taxonomy.md` — "Named scale-diversity gaps" §, gap #2.
- `docs/simulation_quality/extension_points.md` §1 (World breadth).

## Related Stored Artifacts
None yet — standard tier, staging artifacts to be created at Scope.

## Related Code Areas
- `data/worlds/` (new world directory)
- `tests/simulation_quality/fixtures/grade_anchors.json`

## Assumptions / Open Questions
- Which of the two decoupling directions (dense/small vs. sparse/sprawling) is more diagnostically
  valuable is an open question for the investigation phase, not pre-decided here.

## Implementation Notes
Learned from the sibling gap-1 ticket's mistake (built a redundant world before checking) and
verified against real corpus data first, before authoring anything. Computed node-per-region
density across all 19 worlds' `world_compile_report.json` files — found `resource_dense_basin`
(2.33 density, 3 regions) already sits well outside the gap text's claimed "roughly flat 1.3-1.75"
range, and is already documented in the per-world table as closing this exact gap. No world
authored. Corrected `corpus_tier_taxonomy.md`'s stale gap-list section instead.

## Test Summary
`pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q`: 65 passed / 1 failed
— identical to baseline (same pre-existing, unrelated `urban_political_seed42_200t` failure),
confirming no corpus content was touched.

## Files Changed
- `docs/simulation_quality/corpus_tier_taxonomy.md` — gap #2 marked CLOSED in the "Named
  scale-diversity gaps" section

## Completion Summary
Investigated authoring a world with resource-node density decoupled from map size, per this
ticket's original scope. Verified against real corpus data before any world-authoring work began
(applying the lesson from the sibling gap-1 ticket, which built a redundant world first and caught
it late) and found the gap was already closed by `resource_dense_basin`
(`TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS`), correctly documented in the per-world table but not in
the gap-list section. Corrected the stale doc section — the real deliverable of this ticket. No
new world was needed.
