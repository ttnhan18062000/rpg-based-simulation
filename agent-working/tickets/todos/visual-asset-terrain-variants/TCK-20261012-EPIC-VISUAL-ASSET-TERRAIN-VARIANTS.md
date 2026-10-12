---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261012-EPIC-VISUAL-ASSET-TERRAIN-VARIANTS
phase: open
date: 2026-10-12
tags: [architecture, planning]
---

# TCK-20261012-EPIC-VISUAL-ASSET-TERRAIN-VARIANTS

## Title
Visual asset terrain variants: V2 terrain aliases and about 14 detail variants for the terrains the sample worlds use

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Owner, 2026-10-12 (asset-planner's art-priority question after the sample map, PR #526, neutral fixed-order options): next art = **terrain variants**, and wait for #523's vocabulary answer. The owner then answered #523 (relayed by lead-planner, 2026-10-12): **V2 terrain names are canonical**. rpg publishes one deduplicated V2 vocabulary and the client colours by name (rpg's side). Asset keys follow V2 names, and existing art is reused via registry aliases (ruin -> terrain.ruins, plain/PLAIN -> terrain.grassland, river -> terrain.shallow_water); the sample-map alias table is the starting proposal. Lead's order inside the batch: (1) the `MAX_REGISTRY_BYTES` budget review first, (2) the aliases (the asset half of #523, registry only), (3) about 14 variant tiles for the terrains the sample worlds actually use. Evidence: `docs/assets/sample_map/gap_report.md` G1-G4 and G12 (grass is one tile repeated over ~60,000 cells; worlds are rectangles over one fill).

## Scope
- Child 1 `TCK-20261012-VISUAL-ASSETS-REGISTRY-BUDGET-AND-DETAIL-DESIGN`: the `MAX_REGISTRY_BYTES` budget review, and the design for adding a detail axis to keys that already have adopted art (slot identity, rc entries). **Planner gate; any store-code need -> STOP.**
- Child 2 `TCK-20261012-VISUAL-ASSETS-V2-TERRAIN-ALIASES`: the registry aliases `terrain.plain` -> `terrain.grassland`, `terrain.ruin` -> `terrain.ruins`, `terrain.river` -> `terrain.shallow_water`.
- Child 3 `TCK-20261012-VISUAL-ASSETS-TERRAIN-VARIANT-DRAFTS`: the detail axes (values approved by the owner), about 14 drawn variants, owner review folder, owner `adopt-set`.
- Child 4 `TCK-20261012-VISUAL-ASSETS-TERRAIN-VARIANTS-RC-AND-CLOSE`: build, rc-0010 on the owner's answer, sample map re-rendered as evidence, gap report and budgets updated, closure.

Planner's proposed split (14 tiles; the owner decides the values in child 3's blocking question):
  - `terrain.grassland` (60,239 sample cells via the alias): 4 new values -> `base` + 4 = 5
  - `terrain.mountain`, `terrain.cave`, `terrain.ruins`, `terrain.swamp`, `terrain.shallow_water`: 2 new values each -> `base` + 2 = 3 each
  - `terrain.forest` keeps its 3; `terrain.road` gets none (a road wants connecting tiles, gap G5, not random variants).

## Out of Scope
- No `src/` or `frontend/` change: the client's colour-by-name and the V2 vocabulary dedupe are rpg's (#523). No activation.
- No new terrain KEY: V2 names reach existing art through aliases; a new key needs an owner decision outside this batch.
- No connecting tiles, no multi-tile structures, no map markers (A comes after this batch, following V2 kind names as the presenter emits them).
- No bound raise, no store or drawing-tool code change unless child 1 proves one is needed: then STOP, it is its own owner question.
- `PLAIN` vs `plain` is not resolved here: one alias covers both while rpg dedupes.

## Acceptance Criteria
- [ ] Children 1-4 DONE, each commit reviewed and approved by `asset-planner`.
- [ ] Owner approved the detail values, adopted the variant set (`adopt-set`) and approved rc-0010.
- [ ] The re-rendered sample map shows the aliases and variants; the gap report's G1-G4 rows are updated with the new numbers.
- [ ] One PR, pushed and merged only on the user's own answer.

## Related Tickets
- Children: `TCK-20261012-VISUAL-ASSETS-REGISTRY-BUDGET-AND-DETAIL-DESIGN`, `TCK-20261012-VISUAL-ASSETS-V2-TERRAIN-ALIASES`, `TCK-20261012-VISUAL-ASSETS-TERRAIN-VARIANT-DRAFTS`, `TCK-20261012-VISUAL-ASSETS-TERRAIN-VARIANTS-RC-AND-CLOSE`
- Previous: `TCK-20261011-EPIC-VISUAL-ASSET-SAMPLE-MAP` (PR #526), `TCK-20261011-EPIC-VISUAL-ASSET-REAL-ART-PROOF` (PR #521, rc-0009)
- Next (not filed): map markers (candidate A), V2 kind names
- GitHub #523, #519

## Related Docs
- `docs/assets/sample_map/gap_report.md` (G1-G4, G12, the alias table), `docs/assets/budgets.md` (`MAX_REGISTRY_BYTES`, `MAX_DETAIL_KEYS`, `MAX_DETAIL_VALUES`), `docs/assets/store_contract.md` (registry, detail axis, known gap: a registry edit makes older candidates unexportable), `docs/assets/pixel_art_technique.md`, `docs/assets/pilot_terrain_key.md` (the forest detail axis precedent)
- GitHub #523 (V2 vocabulary, owner answer), #519

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT/`, `agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT/` (if present: the detail axis contract)

## Related Code Areas
- `visual_assets/catalog/definitions/visual_keys.yaml`, `visual_assets/catalog/**`, `visual_assets/store/catalog/registry.py` (read), `visual_assets/store/contracts/definitions.py` (read), `tools/visual_assets_sample_map*.py` (re-run)

## Assumptions / Open Questions
- Planner decisions in `SEQUENCE.md`.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

