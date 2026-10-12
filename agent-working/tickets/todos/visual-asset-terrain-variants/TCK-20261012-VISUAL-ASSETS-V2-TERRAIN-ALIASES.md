---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261012-VISUAL-ASSETS-V2-TERRAIN-ALIASES
phase: open
date: 2026-10-12
tags: [architecture, testing]
---

# TCK-20261012-VISUAL-ASSETS-V2-TERRAIN-ALIASES

## Title
Terrain variants: registry aliases for the V2 terrain names (plain, ruin, river) onto existing art

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 2 of `TCK-20261012-EPIC-VISUAL-ASSET-TERRAIN-VARIANTS`. The asset half of #523: V2 names are canonical, existing art is reused through aliases.

## Scope
- Add to `visual_keys.yaml` `aliases`: `terrain.plain -> terrain.grassland`, `terrain.ruin -> terrain.ruins`, `terrain.river -> terrain.shallow_water`. Comment: owner answer on #523 (2026-10-12), V2 names canonical.
- **`PLAIN`:** an alias must match the lowercase key pattern (`visual_assets/store/identities.py:16`), so `terrain.PLAIN` cannot exist. The name -> key rule lowercases (the sample-map tool's rule), so `PLAIN` and `plain` both resolve through `terrain.plain`. Write this rule in store_contract.md as the asset side of the contract with rpg, and state that the dedupe is rpg's.
- Check what the runtime manifest / export carries for aliases. If a client could not resolve an alias from the export, record it as a finding for activation (no store-code change here).
- Tests: the three aliases resolve; no chain, no alias that is also a key (the loader's own rules); the registry content pins move to exact values.
- Registry edit -> rc-0009 becomes unexportable (known gap). Expected red until child 4's rc-0010, as in the real-art batch: list exactly which tests, nothing else may fail.

## Out of Scope
- No `src/` or `frontend/` change: the client's colour-by-name and the V2 vocabulary dedupe are rpg's (#523). No activation.
- No new terrain KEY: V2 names reach existing art through aliases; a new key needs an owner decision outside this batch.
- No connecting tiles, no multi-tile structures, no map markers (A comes after this batch, following V2 kind names as the presenter emits them).
- No bound raise, no store or drawing-tool code change unless child 1 proves one is needed: then STOP, it is its own owner question.
- `PLAIN` vs `plain` is not resolved here: one alias covers both while rpg dedupes.

## Acceptance Criteria
- [ ] Three aliases load and resolve; the name rule documented.
- [ ] The known red set listed exactly in the Test Summary; nothing else red.

## Related Tickets
- Parent: `TCK-20261012-EPIC-VISUAL-ASSET-TERRAIN-VARIANTS`
- Needs: `TCK-20261012-VISUAL-ASSETS-REGISTRY-BUDGET-AND-DETAIL-DESIGN` (design approved)

## Related Docs
- `docs/assets/sample_map/gap_report.md` (G1-G4, G12, the alias table), `docs/assets/budgets.md` (`MAX_REGISTRY_BYTES`, `MAX_DETAIL_KEYS`, `MAX_DETAIL_VALUES`), `docs/assets/store_contract.md` (registry, detail axis, known gap: a registry edit makes older candidates unexportable), `docs/assets/pixel_art_technique.md`, `docs/assets/pilot_terrain_key.md` (the forest detail axis precedent)
- GitHub #523 (V2 vocabulary, owner answer), #519

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT/`, `agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT/` (if present: the detail axis contract)

## Related Code Areas
- `visual_assets/catalog/definitions/visual_keys.yaml`, `docs/assets/store_contract.md`, `tests/visual_assets/**`

## Assumptions / Open Questions
- If rpg's dedupe later keeps `PLAIN` (uppercase), the lowercase rule still covers it; no registry change needed.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

