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
DONE

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
- [x] `race_relations.yaml` renamed with every consumer path updated.
- [x] All listed `src/` consumers renamed (function/parameter names, not just imports).
- [x] All 6 dedicated test files renamed (file name + contents) and pass unchanged.
- [x] No change to any legality/diplomacy/tactical-modifier value — verified by test parity, not
      assumed.

## Related Tickets
- TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY (parent epic)
- TCK-20260904-SPECIES-CORE-SCHEMA-RENAME (dependency)

## Related Docs
- `docs/brainstorm/rpg_expected_schemas.html#schema-37` (frozen source, not edited — see epic)

## Related Stored Artifacts
- stored_artifacts/TCK-20260904-SPECIES-RELATIONS-SUBSYSTEM-RENAME/{investigation,plan,test_plan}.md

## Related Code Areas
- `src/content_semantics/faction.py`, `src/content_semantics/relation.py`
- `src/engine/tactical.py`
- `src/world/perception/gate.py`, `src/world/motivation/pressure_resolver.py`,
  `src/strategy/role_model_imitation.py`
- `data/content/social/race_relations.yaml`

## Assumptions / Open Questions
None beyond what the parent epic already tracks. One real gap found in this ticket's own scoping
(not an open question, resolved during implementation): `src/content/schema.py`
(`RaceRelationRecord`), `src/content/repository.py`, and `src/content/matrix.py` were not in the
ticket's own file list despite being the actual data-model layer for the "race_relations" subsystem
this ticket renames — fixed here, see investigation.md.

## Implementation Notes
Found and fixed 2 hard-coupling gaps beyond the ticket's own file list, confirmed via grep not
assumed: `src/content/{schema,repository,matrix}.py` (the `RaceRelationRecord`/`race_relations`
data-model layer itself — the ticket's title covers the full subsystem but its own scope list
missed the model definition) and `src/engine/legality.py` (a second `get_race_id_str()`/
`source_race`/`target_race` consumer alongside `tactical.py`, which the ticket did list). Confirmed
`gate.py`/`pressure_resolver.py`/`role_model_imitation.py` (listed in this ticket's own scope as
"consumer renames") were already fully handled by child 1's hard-coupling fixes — no further work
needed. Confirmed `FactionDefinition.common_races` stays out of scope (belongs to child 3).
Rewrote all 6 dedicated test files (file name + contents) plus fixed one more test file broken by
this rename found via full-sweep collection error
(`tests/integration/combat/test_relation_combat_integration.py`). No legality/diplomacy/
tactical-modifier value changed — pure rename, verified by unchanged test assertions.

## Test Summary
34 passed (scoped run) + 539/625/129 passed across content/combat/engine/world/strategic/lab
sweeps + 24 passed for `docs/mechanics/content_usage_matrix.md`'s auto-regeneration. Full
non-slow `tests/unit/ tests/integration/` sweep: 6008 passed, 9 skipped, 84 deselected, 2 failed
(both the identical `tests/conftest.py` resource-time-limit `TimeoutError` diagnosed as
environment-load noise, unrelated to this rename — see test_plan.md). Full details in
stored_artifacts/TCK-20260904-SPECIES-RELATIONS-SUBSYSTEM-RENAME/test_plan.md.

## Files Changed
- `src/content/{schema,repository,matrix}.py` (beyond original scope — hard coupling)
- `src/content_semantics/{faction,relation}.py`
- `src/engine/tactical.py`, `src/engine/legality.py` (latter beyond original scope — hard coupling)
- `data/content/social/race_relations.yaml` → `species_relations.yaml` (git mv, 24 entries)
- 6 dedicated test files renamed (file + contents), plus
  `tests/integration/combat/test_relation_combat_integration.py` (hard-coupling fix)
- `docs/mechanics/content_usage_matrix.md` (auto-regenerated)
- `docs/parity_ledger/combat_movement.yaml` (COMB-321)

## Completion Summary
Renamed the "Race Relations" subsystem (idea 37) to "Species Relations" throughout: content
catalog file, Pydantic model + fields, repository/matrix wiring, `RelationContext` fields, helper
function, and both real-code consumers (tactical.py, legality.py — the latter a hard-coupling
discovery beyond the ticket's own scope). Found and closed a real gap in the ticket's own scoping
(the model-definition layer itself wasn't listed). Confirmed zero legality/diplomacy/
tactical-modifier value changes — pure rename. All 6 dedicated test files rewritten and passing;
full repo-wide grep confirms no remaining old symbol references outside historical citations and
unrelated concurrency terminology.
