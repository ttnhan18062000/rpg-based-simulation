---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-RENDER
phase: open
date: 2026-10-11
tags: [architecture, testing]
---

# TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-RENDER

## Title
Sample map: offline renderer from the rc-0009 runtime export, same composition rule as the client rehearsal

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 2 of `TCK-20261011-EPIC-VISUAL-ASSET-SAMPLE-MAP`.

## Scope
- `tools/visual_assets_sample_map.py render <world>`: read the rc-0009 runtime export (`export-runtime`, written to `reports/visual_assets/`, not committed) and a child-1 data file. Draw:
  - each cell's terrain tile (forest detail variants by the same rule the rehearsal uses; otherwise the default);
  - the border masks by the rule of `frontend/src/visualAssets/terrainBorders.ts` (`composeCell`, `borderOverlays`). Port the rule; do not import or edit the TS. Prove parity on a handful of cells against the rule's own test vectors in `frontend/src/visualAssets/__tests__/terrainBorders.test.ts`;
  - location glyphs on `icon.plate.location`, and building icons as town markers (scaled to one cell, stated);
  - a cell with no art in its typed fallback (the registry `fallback`: flat fill), visibly marked so gaps show in the picture.
- Output: one PNG at scale x1 plus one at x2 per world, and one static HTML page with the three maps and a legend. All under `reports/visual_assets/sample_map/`. The planner-chosen evidence copies (the x1 PNGs and the page, if small) go in child 3.
- Deterministic: two renders byte-identical. Pixel-reading uses the store's PNG decoder (`visual_assets/store/pixels.py`), with no new dependency (ask lead-planner before adding one).

## Out of Scope
- **No activation** (lead guard): no `frontend/` or `src/` edit, no change to how the Live Map draws, nothing wired into the app. `src/` is imported read-only to build a world state and call its presenters; nothing is written into `src/`, the content registries or `data/`.
- The rendered picture is evidence, not a shipped asset: never intake, adopt or put in a release candidate.
- No new art, no registry key, no store or drawing-tool code change, no bound change.
- Waiting on #519: answers correct the gap report only, with no re-render beyond that (lead).

## Acceptance Criteria
- [ ] Three worlds rendered; two runs byte-identical.
- [ ] Border composition parity proven on the TS rule's test vectors.
- [ ] Cells drawn in fallback are counted per terrain key and per marker kind (child 3's input).

## Related Tickets
- Parent: `TCK-20261011-EPIC-VISUAL-ASSET-SAMPLE-MAP`
- Needs: `TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-DATA`; rc-0009 from `TCK-20261011-VISUAL-ASSETS-REAL-ART-RELEASE-PROOF`

## Related Docs
- `docs/assets/store_contract.md` (runtime manifest, atlas), `docs/assets/pilot_terrain_key.md`, `docs/assets/surface_rehearsal_result.md`, `docs/assets/icon_style_guide.md`
- `agent-working/tickets/done/TCK-20260821-PRESENT-MAP-STATIC.md` (where `present_map` / `present_static` come from)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20260821-PRESENT-MAP-STATIC/investigation.md` (field-level drop and derive decisions of `present_static`)

## Related Code Areas
- `tools/visual_assets_sample_map.py`, `visual_assets/store/{pixels,runtime_export}.py` (used), `frontend/src/visualAssets/terrainBorders.ts` (read)

## Assumptions / Open Questions


## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

