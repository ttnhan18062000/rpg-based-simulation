---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261014-THE-PRESENTER-EMITS-SPECIES-AND-SIZE-FOR-MAP-MARKERS
phase: open
date: 2026-10-14
tags: []
---

# TCK-20261014-THE-PRESENTER-EMITS-SPECIES-AND-SIZE-FOR-MAP-MARKERS

## Title
The entity presenter emits species and size, so map markers can vary by them (#548, designer application of D46/D50/D69/D74).

## Status
INPROGRESS (presentation only; built on cefce1664)

## Tier
hotfix

## Type
feature

## Priority
P2

## Request Summary
Asset (#548) keys entity map markers on the presented `kind` (the role id). The designer answered #548 Q3: the presenter should also emit `species` (the species id, an open content catalog) and `size` (the species' power band: small, medium or large). It does not emit diet. Today StatePresenter emits only `kind` (state_presenter.py:70 and :174).

## Scope
- Add `species` (str or null) and `size` (small | medium | large, or null) to both entity shapes in src/api/presenters/state_presenter.py, and to their API schemas.
- `size` presents the species' declared `power` field from species.yaml (small | medium | large). Never derive it in code.
- A body with no species presents null for both. Under R3/D74 none should exist; a test asserts that the sample worlds present no null.
- Presentation only: prove it hash-neutral (the sim state hashes are unchanged on one paired seed per sample world).

## Out of Scope
- diet in the presenter.
- Any marker art (asset's work).
- Folding away wild_creature (M1, D46).

## Acceptance Criteria
- Both entity shapes carry species and size; the schema and API tests are updated.
- A test: a known species presents its id and declared band.
- Sim hashes are unchanged.
- Comment on #548 when it merges so asset can key on the new fields.

## Related Tickets
- #548 (asset map markers), #523 (lower-case unique names)

## Related Docs
- docs/api presenter docs, if any; the designer's answer at https://github.com/ttnhan18062000/rpg-based-simulation/issues/548#issuecomment-6160399247

## Related Stored Artifacts
- none

## Related Code Areas
- src/api/presenters/state_presenter.py, src/api/schemas, data/content/living/species.yaml

## Assumptions / Open Questions
- Species content already declares `power: small | medium | large` (species.yaml; 4 small, 7 medium, 3 large on rpg-next 003aa051e). `size` presents that value.

## Implementation Notes

## Test Summary

`tests/unit/api/test_presenter_species_and_size.py` (both shapes: a known species presents its id and declared band for human, wolf and small_plant_eater; no species presents null for both; an unknown species keeps its id and has no size). `tests/unit/api` and the API projection perf test pass; code-health and import contracts clean. Hash-neutral: 5000 ticks, rpg-next `cefce1664` vs branch, one seed per sample world: frontier_living_world s42 `4d08dd15f19e45a4` identical, urban_political s42 `8ad52f2d8c7e8c58` identical.

Not done here: the acceptance line that sample worlds present no null species. On `cefce1664` the 51 hero, merchant and scout bodies still have no species (the diet step, D74, is not folded yet), so that test would fail today; it belongs with the diet step.

## Files Changed

`src/api/presenters/state_presenter.py` (`_species_and_size`, both entity shapes) and the test above. There are no entity schemas under `src/api/schemas.py` to update.

## Completion Summary
