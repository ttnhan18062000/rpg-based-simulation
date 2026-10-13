---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-RENDER
phase: done
date: 2026-10-11
tags: [architecture, testing]
---

# TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-RENDER

## Title
Sample map: offline renderer from the rc-0009 runtime export, same composition rule as the client rehearsal

## Status
DONE

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
- Tool: `tools/visual_assets_sample_map_render.py` (the renderer; a sibling module so the data tool stays small), reached as `python -m tools.visual_assets_sample_map render <world>` or `render --all` (which also writes the page). It exports rc-0009 once with the store's own `export-runtime` into `reports/visual_assets/sample_map/rc-0009-runtime/` and reads the PNGs with the store's decoder (`visual_assets/store/pixels.py`); the PNG writer is stdlib `zlib`/`struct`. No dependency added. Output per world: `exact_x1.png`, `exact_x2.png`, `alias_x1.png`, `alias_x2.png`, `render_stats.json`; plus `index.html` with the three maps, both views, a legend and the numbers of each view. Everything under the gitignored `reports/visual_assets/sample_map/`.
- Two views, labelled wherever a number or picture is quoted (asset-planner's addition): EXACT (primary evidence: only exact keys draw; a terrain name with no key is a plum diagonal-striped gap cell) and ALIAS ("unconfirmed: asset-planner proposal for rpg-planner (#519)": a name with no exact key draws with its proposed alias). The picture draws by terrain NAME from the presenter's own code table, never by `present_map`'s per-world integer code; the client's fixed-code-table colour bug is rpg's (#523) and is not worked around.
- The ported rule (cited): `frontend/src/visualAssets/terrainBorders.ts` (`borderOverlays`, `composeCell`, `rotate`, `TERRAIN_PRIORITY`, `CRISP_TERRAINS`, `BORDER_DEPTH`), `pickDetail.ts` (32-bit FNV-1a, seed 1) and `resolver.ts` (picked value, then the default, then the role fallback = flat fill with a diagonal, `terrainDrafts.ts drawDraftCell`). The TS is neither imported nor edited. Drift guard: a test reads the TS text and asserts every ported constant (priority list, crisp set, depth, mask keys, seed, FNV offset and prime, the 23-code key table, the 23 fallback colours) equals it.
- PARITY PROVEN three ways: (1) the rule's own test vectors ported one for one (`terrainBorders.test.ts`: equal codes, higher onto lower only, crisp, rotations N/E/S/W, four sides -> two inner corners, outer corners, adjacent edges -> one inner corner or two edges without the mask, three sides, draw order by rank, off-map/unknown/no mask, determinism; rotate; the 4 px cap in every rotation and kind; neighbour pixels where the mask is opaque; skipped overlay) and `pickDetail.test.ts`'s golden FNV vectors (10 key/x/y/seed/n rows and the published FNV-1a values); (2) a DIFFERENTIAL test that bundles the real `terrainBorders.ts` with the frontend's own esbuild (read-only, output in a temp directory) and runs the TS `borderOverlays` on six seeded random maps (over 20 fringing cells), asserting equal overlays (skipped, with a stated reason, where node or esbuild is missing; it ran here, node v20.19.4, esbuild 0.27.3); (3) the render of a real world is checked cell by cell by the data tests. Not run: the TS's own vitest suite (it is the TS's own gate).
- Numbers per world (cells; exact view / alias view): `frontier_living_world` 161x106 = 17,066 cells: art 4,458 / 17,066, gap 12,608 / 0, cells with a border fringe 264 / 627 (440 / 846 pieces), objects drawn 3 / 7, objects in the gap 21 / 17. `highland_traverse` 211x211 = 44,521: art 3,362 / 44,521, gap 41,159 / 0, fringed cells 0 / 433, objects drawn 2 / 3, gap 7 / 6. `dungeon_crawl` 101x121 = 12,221: art 1,116 / 12,221, gap 11,105 / 0, fringed cells 0 / 138, objects drawn 0 / 1, gap 1 / 0. Gap objects per kind (exact view) are in each `render_stats.json` (`objects_gap`: e.g. frontier: healer_hut 1, mine_entrance 1, shop 2, town_hall 1, CAMP 1, CITY 1, NEST 1, RUIN 1 and eight resource-node kinds, 12 nodes); no terrain key lacks art in rc-0009 (all 23 terrain keys are released), so `terrain_key_without_art` is empty and the flat-fill-with-diagonal fallback is exercised by a test only. Buildings are drawn from their 24x24 icon scaled to one 16x16 cell (nearest neighbour, stated in the legend and the page); places are the `icon.plate.location` plate with their marker glyph; entities are counted in the data, not drawn.
- Determinism: `render --all` twice, every PNG, `render_stats.json` and `index.html` byte-identical (`sha256sum` lists equal); 9.4 s and 635 MB peak under a 4 GB cap. File sizes: x1 59,603 to 231,054 B, x2 189,952 to 785,159 B. The store's PNG decoder refuses images over `MAX_DECODED_BYTES` (a bound, not changed), so the test checks the big sheets through the IHDR and the inflated size instead of decoding them.
- Not claimed: the picture is evidence of how far the adopted art goes on the V2 world vocabulary, not a visual-quality verdict; the alias view is a proposal's effect, not a decision.

## Test Summary
`tests/visual_assets/test_sample_map_render.py`: 28 tests: ported constants equal the TS text, pick vectors, every `borderOverlays`/`rotate`/`composeCell` vector, the differential test against the real TS rule, the views and their labelled alias, gap marking and counting per terrain name / key / object kind, the detail fallback order, object drawing, border composition, PNG encoder, two real renders byte-identical, the page. With `test_sample_map_data.py` (16): 44 passed. Not guarded files.

## Files Changed
- `tools/visual_assets_sample_map_render.py` (new), `tools/visual_assets_sample_map.py` (render subcommand), `tests/visual_assets/test_sample_map_render.py` (new)

## Completion Summary
`tools/visual_assets_sample_map_render.py`: the border rule, the detail pick and the resolver order ported from the TS (not imported), proven on the TS vectors, against the TS text and differentially against the real TS rule (skips without node and esbuild); exact and labelled alias views per world, gaps marked and counted, two renders byte-identical, a static page. Commit `8a001d17a`.
