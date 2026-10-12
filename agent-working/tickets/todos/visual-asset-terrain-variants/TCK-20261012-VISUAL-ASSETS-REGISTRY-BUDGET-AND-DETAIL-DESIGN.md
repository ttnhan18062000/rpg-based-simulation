---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261012-VISUAL-ASSETS-REGISTRY-BUDGET-AND-DETAIL-DESIGN
phase: open
date: 2026-10-12
tags: [architecture, testing]
---

# TCK-20261012-VISUAL-ASSETS-REGISTRY-BUDGET-AND-DETAIL-DESIGN

## Title
Terrain variants: MAX_REGISTRY_BYTES budget review and the design for a detail axis on keys that already have adopted art

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Child 1 of `TCK-20261012-EPIC-VISUAL-ASSET-TERRAIN-VARIANTS`. budgets.md's standing rule: the registry's realistic maximum is about 90 % of `MAX_REGISTRY_BYTES`, and the next growth of the key schema needs a budget review first (lead: first step).

## Scope
- **Budget review:** re-measure the registry at the realistic maximum with this batch's shape (detail axes on 7 keys, 3 aliases), using the method in budgets.md's `MAX_REGISTRY_BYTES` row: bytes and load time. Also measure the worst legal case (`MAX_DETAIL_KEYS` 64 x `MAX_DETAIL_VALUES` 16 plus `MAX_ALIASES`) again on today's code. Write a dated note on the budgets.md rows; change no bound. If a measurement exceeds a bound or the 2 s line, STOP.
- **Design (planner gate, before any registry edit):** what adding a `detail` axis to a key that already has an adopted source does to:
  1. its existing adoption (no `detail_value`, so it resolves to the axis `default`): name the default `base` so the current art stays the default;
  2. its slot identity in rc-0009 and in a new candidate (key, None) vs (key, base): is rc-0009's entry for that key byte-identical in rc-0010, or does it re-anchor?
  3. `pickDetail` in the client rehearsal and the sample-map renderer (the FNV pick over the values).
  4. the runtime manifest's `details` block size.
  Write the answer as a design note with code citations; send it to asset-planner before child 2.
- If the design needs a store-code change (e.g. a detail axis cannot be added to an adopted key), STOP: that is an owner question, not part of this batch.

## Out of Scope
- No `src/` or `frontend/` change: the client's colour-by-name and the V2 vocabulary dedupe are rpg's (#523). No activation.
- No new terrain KEY: V2 names reach existing art through aliases; a new key needs an owner decision outside this batch.
- No connecting tiles, no multi-tile structures, no map markers (A comes after this batch, following V2 kind names as the presenter emits them).
- No bound raise, no store or drawing-tool code change unless child 1 proves one is needed: then STOP, it is its own owner question.
- `PLAIN` vs `plain` is not resolved here: one alias covers both while rpg dedupes.

## Acceptance Criteria
- [ ] Measurements recorded against the bounds and the 2 s line, no bound changed.
- [ ] The design note answers 1-4 with code citations; asset-planner approved it.

## Related Tickets
- Parent: `TCK-20261012-EPIC-VISUAL-ASSET-TERRAIN-VARIANTS`

## Related Docs
- `docs/assets/sample_map/gap_report.md` (G1-G4, G12, the alias table), `docs/assets/budgets.md` (`MAX_REGISTRY_BYTES`, `MAX_DETAIL_KEYS`, `MAX_DETAIL_VALUES`), `docs/assets/store_contract.md` (registry, detail axis, known gap: a registry edit makes older candidates unexportable), `docs/assets/pixel_art_technique.md`, `docs/assets/pilot_terrain_key.md` (the forest detail axis precedent)
- GitHub #523 (V2 vocabulary, owner answer), #519

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT/`, `agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT/` (if present: the detail axis contract)

## Related Code Areas
- `visual_assets/store/catalog/registry.py`, `visual_assets/store/contracts/definitions.py`, `visual_assets/store/{release,runtime_export,adoption,setadoption}.py`, `frontend/src/visualAssets/` (read only), `tools/visual_assets_sample_map_render.py`

## Assumptions / Open Questions


## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

