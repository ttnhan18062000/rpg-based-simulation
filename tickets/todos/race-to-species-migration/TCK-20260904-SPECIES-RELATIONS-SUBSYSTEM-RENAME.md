---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260904-SPECIES-RELATIONS-SUBSYSTEM-RENAME
phase: open
date: 2026-09-04
tags: [content, combat, social]
---

# TCK-20260904-SPECIES-RELATIONS-SUBSYSTEM-RENAME

## Title
Rename idea 37's "Race Relations" subsystem to "Species Relations"

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Child 2/4 of `TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY`. Depends on
`TCK-20260904-SPECIES-CORE-SCHEMA-RENAME` (reads `species_id`/the renamed base catalog). Renames idea
37 of the canonical 65-idea design roadmap — "Race Relations," the pairwise diplomacy/legality/
tactical-modifier matrix between creature kinds — to "Species Relations," along with its content
catalog and every consumer.

## Scope
- `data/content/social/race_relations.yaml` -> `species_relations.yaml`, every path reference updated.
- `src/content_semantics/faction.py`, `src/content_semantics/relation.py` — matrix lookups and
  helper function renames (e.g. `get_race_id_str` -> a species-named equivalent).
- `src/engine/tactical.py` — `source_race`/`target_race` parameter renames.
- `src/world/perception/gate.py`, `src/world/motivation/pressure_resolver.py`,
  `src/strategy/role_model_imitation.py` — consumer renames.
- 6 dedicated test files, renamed to match (file name and contents):
  `tests/unit/combat/test_race_relations_legality_wiring.py`,
  `tests/unit/combat/test_race_relations_tactical_wiring.py`,
  `tests/unit/content/test_race_relations_catalog.py`,
  `tests/unit/content/test_race_relations_coverage.py`,
  `tests/unit/content_semantics/test_relation_race_projection.py`,
  `tests/integration/lab/test_race_relations_metamorphic_validation.py`.

## Out of Scope
- Any change to the actual legality/diplomacy/tactical-modifier values or matrix semantics — pure
  rename only.
- Idea 37's own name in the frozen brainstorm HTML sources — see the parent epic's Out of Scope; a
  reconciliation note lives in `rpg_design_roadmap.md` instead.

## Acceptance Criteria
- [ ] `race_relations.yaml` renamed with every consumer path updated.
- [ ] All listed `src/` consumers renamed (function/parameter names, not just imports).
- [ ] All 6 dedicated test files renamed (file name + contents) and pass unchanged.
- [ ] No change to any legality/diplomacy/tactical-modifier value — verified by test parity, not
      assumed.

## Related Tickets
- TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY (parent epic)
- TCK-20260904-SPECIES-CORE-SCHEMA-RENAME (dependency)

## Related Docs
- `docs/brainstorm/rpg_expected_schemas.html#schema-37` (frozen source, not edited — see epic)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/content_semantics/faction.py`, `src/content_semantics/relation.py`
- `src/engine/tactical.py`
- `src/world/perception/gate.py`, `src/world/motivation/pressure_resolver.py`,
  `src/strategy/role_model_imitation.py`
- `data/content/social/race_relations.yaml`

## Assumptions / Open Questions
None beyond what the parent epic already tracks.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
