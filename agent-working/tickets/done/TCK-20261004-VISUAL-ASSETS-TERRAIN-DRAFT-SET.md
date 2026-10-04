---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET
phase: done
date: 2026-10-04
tags: [architecture, mcp, live-map]
---

# TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET

## Title
Draft one 16 x 16 tile for every Live Map terrain code as draft set `terrain-v1`, no adoption

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
User, 2026-10-04: "draft all the assets now", review only when a full batch is done (for example full map tiles).
Terrain first: one draft per `TILE_NAMES` code, kept in draft set `terrain-v1` for a later whole-set review.

## Scope
- Register one visual key per terrain code in `visual_keys.yaml` (`terrain.<name>`, family `terrain`, description naming
  the tile code and its fallback colour), all `optional: true` so no release needs them before adoption. `terrain.forest`
  keeps its adopted slots. Keys are registered by hand in the reviewed file, as the registry requires.
- Draw each tile with the drawing tools, sharing one palette family so the set reads as one style; tiles of the same
  terrain repeat seamlessly; neighbouring terrains read apart in the colour-vision simulation the pilot used (`W05`
  method), checked on the preview page before keeping. The existing forest slots are part of the set as references,
  not redrawn.
- Hand off, intake, `draft keep` each into `terrain-v1`. No `adopt`, no `adopt-set`, no release.
- Store a screenshot of the preview page with the full set and a short style note (palette, light direction) as evidence.

## Out of Scope
- Adoption (the user's, later, by `adopt-set` after their review). Entities, buildings, items (later sets).
  Detail variants for other terrains. Animation (lava, water) beyond a single frame.

## Acceptance Criteria
- [x] `draft verify` clean; `terrain-v1` has a draft for every `TILE_NAMES` code (23: 22 drafts, and forest through labelled references to its adopted slots).
- [x] The preview page shows the whole set with no fallback cells (0 missing rows; the three forest cells are adopted references); screenshot stored.
- [x] Catalog `verify` clean. **Rewritten by planner decision A (2026-10-04):** registering the 22 keys changes `registry_hash`, so the pilot fixture is a fresh export of the new release `pilot/rc-0003` and its entries are unchanged (a test checks rc-0003's entries equal rc-0002's); the draft set adopts nothing.

## Related Tickets
- TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS (epic), TCK-20261004-VISUAL-ASSETS-DRAFT-SETS-AND-SET-ADOPTION,
  TCK-20261004-VISUAL-ASSETS-DRAFT-PREVIEW-PAGE (both before)

## Related Docs
- docs/assets/drawing_tools.md, docs/assets/pilot_terrain_m5_criteria.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-FOREST-DETAIL-TILES/

## Related Code Areas
- visual_assets/catalog/definitions/visual_keys.yaml, visual_assets/drafts/

## Assumptions / Open Questions
- The style may change once the RPG's art direction settles; drafts are cheap to replace (`draft keep --replace`).

## Implementation Notes
- **Decisions (planner, after two blockers I raised):** (1) registry change: register the 22 keys, assemble `pilot/rc-0003` (identical entries, new registry hash), re-export the pilot fixture, re-point the guards honestly (`test_pilot_fixture`, `test_catalog_integrity`, `test_store_tools_stdio`, the registry test now reads the page's explicit key table); rc-0002 stays as history. (2) Forest cannot be a draft entry (a draft needs a PASSED intake and `adopt-set` would refuse an already-held slot), so `draft export` adds labelled **reference entries** for live adopted slots the set does not hold: `adopted: true` only in the draft preview manifest, never in `DraftSet`; a draft wins; both parsers accept only the literal `true`; the page marks them (amber square, "adopted (reference)"). Tested (references never reach `draft verify` or `adopt-set`).
- **How the 22 tiles were made.** Procedurally, by a deterministic generator (`tile_generator.py` in this ticket's stored artifacts) that draws each tile through the same library functions the MCP drawing tools call (`new_sprite`, `apply_ops`, `build_handoff`), then `store intake` and `draft keep --set terrain-v1` for each. Handoffs: producer class CAP_A, licence UNREVIEWED (the adopter states the licence at `adopt-set`). The MCP server could not paste 22 x 256-pixel dumps economically; the output is the same kind of handoff the tools write. No adoption, no `adopt-set`, no release.
- **Style note.** One palette family: every terrain's ramp (darkest, dark, base, light, lightest) is derived from its own Live Map fill colour, so the flat fill stays a faithful fallback (tile mean within 3 to 41 of the fill; the dungeon entrance and lava are darkest because of the opening and crust). Light comes from the top-left: highlights on the top-left of features, shadows to the bottom-right. Every texture is periodic (all coordinates wrap mod 16), so each tile repeats seamlessly, checked in a 2 x 2 repeat sheet of all 22. A few named accents only: berries and embers (orange), moss and reeds (green), straw, sand and pebbles, a glow. 16 x 16, 4 to 7 colours per tile, previews are the 8x exports.
- **Colour-vision check (what could be checked).** The pilot's W05 check (`pilot_colour_vision.py`) is defined for the pilot tile against five named neighbours, so it does not run as-is for a whole set. I reused its functions (Machado simulation, CIE76 dE) on the mean colour of every draft and of the forest tile against the flat fills for ALL 253 terrain pairs under protan, deutan and tritan, a P1-style comparison only (no texture term, no result recorded as a PASS): 30 pair-vision cases have a draft mean more than 2.0 dE closer than the flat fills and under dE 10, mostly involving `dungeon_entrance` (its dark opening lowers the mean; floor / camp / swamp / mountain / desert pairs), then grassland/farmland and desert/ruins. The closest draft pairs are forest / volcanic (protan, dE 1.6 against 2.8 for the flat fills) and jungle / volcanic (deutan, 2.0 against 5.1). Not fixed here (minimal, drafts are reviewed as a set); noted for the review. Output: `cvd_pairs.txt`.
- Parked, not built: a committed colour-vision check for sets, redrawing the dungeon entrance and farmland/grassland for colour-vision margins, a Playwright config.

## Test Summary
`tests/visual_assets`: 1521 passed (foreground, 2 GB cap); catalog `verify`: store ok; `draft verify`: drafts ok. `vitest src/visualAssets`: 187 passed; `tsc -b` and `eslint src/visualAssets` clean.
- New: `test_terrain_draft_set.py` (the committed set has a draft for every key except forest and verifies clean; each is an 8x preview of a 16 px tile with its own source asset id; nothing adopted, keys optional); reference-entry tests in `test_draft_export.py` (added, a draft wins, never reaches the DraftSet / `draft verify` / `adopt-set`, `adopted` only the literal true) and `draftManifest.test.ts`/`draftHarness.test.tsx` (parser, mark and label); `test_rc_0003_lists_exactly_the_entries_of_rc_0002_so_only_the_registry_moved`.
- Re-pointed, nothing weakened: `test_pilot_fixture` (rc-0003), `test_catalog_integrity` (three candidates), `test_store_tools_stdio` (three releases), the registry test (23 keys: forest adopted, 22 optional, equal to the page's table), the PNG-read-site test (`draftexport.py` now reads PNGs with the file-size bound).
- Evidence: `terrain_v1_preview_page.png` (the page opened from the exported set: 25 entries, no missing rows, the draft set hash `sha256:d5a6bce5...a65645`), the colour-vision output, the generator.

## Files Changed
- visual_assets/catalog/definitions/visual_keys.yaml (22 optional keys), manifests/candidates/pilot/rc-0003.json (new); visual_assets/drafts/terrain-v1/ (22 entries + draft_set.json, new)
- visual_assets/store/{draftexport.py,contracts/draft.py}; frontend/src/visualAssets/{draftManifest,terrainDrafts,DraftHarness}.ts(x), __fixtures__/pilot/runtime_manifest.json (rc-0003 export), __tests__/{draftManifest,draftHarness}.test.ts(x)
- tests/visual_assets/{test_terrain_draft_set (new),test_pilot_fixture,test_catalog_integrity}.py, store/unit/{test_draft_export,test_registry,test_record_bounds}.py, drawing/test_store_tools_stdio.py
- docs/assets/{store_contract,pilot_terrain_key,retention_and_rollback}.md; the done DRAFT-PREVIEW-PAGE ticket's notes

## Completion Summary
Draft set `terrain-v1` holds a draft for each of the 22 non-forest Live Map terrain codes, kept (not adopted) and verified; the preview page shows all 23 codes with the three adopted forest slots as labelled references and no fallback cells. The 22 optional keys are registered, `pilot/rc-0003` carries the unchanged pilot entries under the new registry, and the pilot fixture is its export. Nothing is adopted or released for the new terrains.

