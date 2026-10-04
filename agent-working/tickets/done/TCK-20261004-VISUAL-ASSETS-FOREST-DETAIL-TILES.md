---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-FOREST-DETAIL-TILES
phase: done
date: 2026-10-04
tags: [architecture, mcp, live-map]
---

# TCK-20261004-VISUAL-ASSETS-FOREST-DETAIL-TILES

## Title
Two forest detail tiles (bush, tree) drawn, adopted by the user per slot, released as `pilot/rc-0002`

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Third child of `TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS`. Real art for the detail slots of
`terrain.forest`: the pilot tile stays `plain`; add `bush` and `tree`.

## Scope
- Draw two 16 x 16 tiles with the aseprite-pixel-art drawing tools, starting from the pilot tile's palette and ground so
  any mix of `plain` / `bush` / `tree` tiles seamlessly (edges match the plain tile; the detail sits inside the tile).
  Check with a preview of a mixed 4 x 4 arrangement before handing off. A third value is optional; if drawn, it is declared in
  the same registry change below.
- Declare the axis on `terrain.forest` in `visual_assets/catalog/definitions/visual_keys.yaml`
  (`detail: {values: [plain, bush, tree], default: plain}`, in that order: the pick indexes the declared order, and the spread the user approved on 2026-10-04 — plain 1354, bush 1397, tree 1345 over 64 x 64, seed 1 — was computed for it), moved here from ticket 1: it changes `registry_hash`, so it lands
  together with `pilot/rc-0002`, and before the adoptions (`adopt --detail` needs it). rc-0001 stays valid (`verify`
  tolerates its axis-less entry); its export now refuses on `registry_hash`, so any test that re-exports rc-0001 (the
  fixture-equality test, the rollback drill's retained release) must be re-pointed honestly, with the change named in
  the commit; if a guard can only pass by weakening it, stop and tell the planner.
- Hand off and pass intake per tile (`export_handoff`, `submit_candidate`).
- **Adoption is the user's**, one blocking question per tile, run by the user in their own terminal:
  `adopt <intake_id> --visual-key terrain.forest --detail bush|tree ...`. Never run `adopt` or `revoke` yourself. The
  ticket ends `BLOCKED` on the user if an adoption is not given.
- Build, assemble release `pilot/rc-0002` (rc-0001 stays as the retained previous release for the rollback drill),
  export the runtime manifest, and replace the committed pilot runtime fixture by a fresh export (the equality test
  stays the guard). `verify` clean.
- `docs/assets/pilot_terrain_key.md`: the three slots, their source assets and adoptions.

## Out of Scope
- Variants for other terrains; animation; other scales. Weights. Any `src/` change.

## Acceptance Criteria
- [x] Each new tile adopted by the user (adoption ids recorded); `verify` clean.
- [x] `pilot/rc-0002` lists `plain`, `bush`, `tree` for `terrain.forest`; runtime manifest lists every value and the declared `details`.
- [x] Runtime fixture equals a fresh export; the rollback drill still runs against rc-0001.
- [x] A mixed-tile preview is attached to the ticket's evidence (stored artifact), showing no seams.

## Related Tickets
- TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS (epic), TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT,
  TCK-20261004-VISUAL-ASSETS-DETAIL-PICK-CLIENT, TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE

## Related Docs
- docs/assets/drawing_tools.md, docs/assets/pilot_terrain_key.md, docs/assets/retention_and_rollback.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE/

## Related Code Areas
- visual_assets/catalog/, frontend/src/visualAssets/__fixtures__/pilot/

## Assumptions / Open Questions
- The user may reject a tile at the adoption question; redraw and re-submit, never edit store records.

## Implementation Notes
- Order followed: axis declared on `terrain.forest` first (`values: [plain, bush, tree]`, default `plain`), then art, intake, the user's adoptions, `build`, `release --catalog-id pilot` (rc-0002), `export-runtime`, fresh fixture.
- **Art, and the redraw.** First drafts (bush `in-1f3ef37e2cc9156b`, tree `in-990026dd005070e8`) changed one canopy over the plain palette; the user asked why they looked like the pilot tile (the edge ring and bottom band must match the plain tile for seamless mixes, and the palette was reused). Redrawn: about 120 pixels differ from plain, same edge ring and bottom band, two added colours (`#3a6e32`, `#9a3b3b`). The first drafts stay PASSED, reviewed and **un-adopted**, local and uncommitted (gitignored quarantine); they are not in the catalog.
- **Adoptions are the user's.** Bush `ad-5615d03ed5a98f0a` (intake `in-0bb0ef9116d72ee2`), tree `ad-34303489f1e5db70` (intake `in-3cafac684023adbc`), both `nhan` / owner, 2026-10-04, run in the user's own terminal; the agent never ran `adopt`.
- **First adopt failure:** my hand-out used `.venv/bin/python`, which does not exist in the worktree (the venv is the main checkout's), so the first "adopted it" answer had no records behind it (found by checking `list`, `audit` and the catalog before building). Future command hand-outs use `/home/vboxuser/Work/rpg-based-simulation/.venv/bin/python` by absolute path.
- The MCP drawing server may root elsewhere, so intake and review ran through the CLI in this worktree.
- Re-pointed honestly (nothing weakened): `test_pilot_fixture.py` (rc-0002, three slots, declared order), exact-catalog tests (3 sources, 3 adoptions, 6 intake files, 3 artifacts, 2 candidates: `test_adoption`, `test_registry`, `test_catalog_integrity`, `test_store_tools_stdio`, `test_server_stdio`), the isolation PNG count (4 to 6), and `test_detail_axis`'s committed-catalog test (each slot held once; the pilot adoption still names no detail value). `rc-0001` cannot be re-exported any more (`registry_mismatch`); `verify` tolerates its axis-less entry and the committed fixture is the rc-0002 export.
- The rollback drill's "previous release" is the rehearsal export, not rc-0001, so nothing there needed rc-0001; it is re-pointed to the new release's three slots (below).

## Test Summary
`tests/visual_assets`: 1261 passed (foreground, 2 GB cap); `verify`: store ok; `audit`: chain ok; `vitest src/visualAssets`: 144 passed; `tsc -b`, `eslint src/visualAssets` clean.
- **Why the rollback drill is not weaker.** Before, the "mixed snapshot" test asserted every forest cell drew the single pilot URL. The release now has three images, so it asserts, per forest cell in the scene's row-major order, the exact URL of the slot `pickDetail` names for that cell (`expectedPerCell`), and separately that every drawn image is one of the new release's three and none is the previous release's. That is stricter per cell than "any of the three": a wrong pick, a wrong order or a stale image from the old release fails. Checked with a mutant (swapping x and y in the resolver's pick call): the drill fails.
- Mixed 4 x 4 preview (no seams) and a plain | bush | tree strip at 16x: `agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-FOREST-DETAIL-TILES/`.

## Files Changed
- visual_assets/catalog/: definitions/visual_keys.yaml (axis), sources/terrain_forest_{bush,tree}/, provenance/{adoptions,intake}/ (2 adoptions, 2 intakes + review checks), generated/terrain_forest_{bush,tree}--x1/, manifests/candidates/pilot/rc-0002.json
- frontend/src/visualAssets/__fixtures__/pilot/ (rc-0002 export), __tests__/{isolation,pilotScene,manifest,detail,rollbackDrill}.test.ts
- tests/visual_assets/{test_pilot_fixture,test_catalog_integrity}.py, store/unit/{test_adoption,test_registry,test_detail_axis}.py, drawing/{test_store_tools_stdio.py,integration/test_server_stdio.py}
- docs/assets/{pilot_terrain_key,retention_and_rollback}.md

## Completion Summary
`terrain.forest` now has three adopted slots (plain, bush, tree) in release candidate `pilot/rc-0002`, exported to the committed pilot runtime fixture; the user adopted both new tiles after rejecting the first drafts. Nothing activates it.

