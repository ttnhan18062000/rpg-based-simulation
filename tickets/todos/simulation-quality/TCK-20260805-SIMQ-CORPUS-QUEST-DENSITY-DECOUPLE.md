---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260805-SIMQ-CORPUS-QUEST-DENSITY-DECOUPLE
phase: open
date: 2026-08-05
tags: [simulation-quality, world, progression, corpus, calibration]
---

# TCK-20260805-SIMQ-CORPUS-QUEST-DENSITY-DECOUPLE

## Title
Author a stress-tier world decoupling quest-definition density from entity count

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
`docs/simulation_quality/corpus_tier_taxonomy.md`'s "Named scale-diversity gaps" (gap #5) notes
quest-def count currently scales almost linearly with entity count across the corpus — no world
deliberately decouples these two axes (e.g. few entities with many quests, or many entities with
few quests). This ticket authors a new stress-tier world closing that gap.

Note (2026-08-05): filed as backlog, not urgent, per the same corpus-breadth-deprioritization
rationale as its sibling tickets — see
`TCK-20260805-SIMQ-CORPUS-FACTION-DENSITY-SMALL-MAP`'s Request Summary for the full caveat.

## Scope
- Author a new world with quest-def density clearly decoupled from entity count, in one of the two
  directions (quest-dense/entity-sparse, or quest-sparse/entity-dense) — investigation phase picks
  the direction with more diagnostic value for PROGRESSION/NARRATIVE.
- Classify and register per `corpus_tier_taxonomy.md`'s decision tree (stress tier).
- Calibrate and commit anchors.
- Update `corpus_tier_taxonomy.md`'s gap #5 entry to closed, citing this ticket.

## Out of Scope
- The other 3 named scale-diversity gaps — sibling tickets, independent.
- Any PROGRESSION/NARRATIVE scorer change — content-only.

## Acceptance Criteria
1. New world exists with quest-def density clearly decoupled from entity count, in the direction
   chosen by the investigation phase, justified in `plan.md`.
2. World is classified and documented in `corpus_tier_taxonomy.md` as stress-tier, citing gap #5.
3. Anchors committed and `test_grade_regression.py` passes for the new world.
4. `corpus_tier_taxonomy.md`'s gap #5 entry marked closed with a citation to this ticket.

## Related Tickets
- `TCK-20260704-SIMQ-CORPUS-TIERS-EPIC` — parent epic that identified this gap.
- `TCK-20260805-SIMQ-CORPUS-FACTION-DENSITY-SMALL-MAP`,
  `TCK-20260805-SIMQ-CORPUS-RESOURCE-DENSITY-DECOUPLE`,
  `TCK-20260805-SIMQ-CORPUS-AGENCY-REAL-ARCHETYPE` — sibling tickets, mutually independent.

## Related Docs
- `docs/simulation_quality/corpus_tier_taxonomy.md` — "Named scale-diversity gaps" §, gap #5.
- `docs/simulation_quality/extension_points.md` §1 (World breadth).

## Related Stored Artifacts
None yet — standard tier, staging artifacts to be created at Scope.

## Related Code Areas
- `data/worlds/` (new world directory)
- `tests/simulation_quality/fixtures/grade_anchors.json`

## Assumptions / Open Questions
- Which decoupling direction is more diagnostically valuable is left to the investigation phase.

## Implementation Notes
(fill during implementation)

## Test Summary
(fill during implementation)

## Files Changed
(fill during implementation)

## Completion Summary
(fill during implementation)
