---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DRAFT-PREVIEW-PAGE
phase: done
date: 2026-10-04
tags: [architecture, live-map]
---

# TCK-20261004-VISUAL-ASSETS-DRAFT-PREVIEW-PAGE

## Title
An isolated preview page that renders a whole map from a draft set, for set-level review

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
User, 2026-10-04: review art as a complete batch on a map, not tile by tile. This page shows a draft set
(`TCK-20261004-VISUAL-ASSETS-DRAFT-SETS-AND-SET-ADOPTION`) in a full map so the user can judge it as a whole before
`adopt-set`.

## Scope
- `draft export <set_id> <out_dir>`: a **draft preview manifest** (`record_type: draft_preview_manifest`, its own type,
  never parseable as a `runtime_manifest`) with the same entry and `details` shape, plus the set id and the set record
  hash. Nothing a release or the pilot page reads can load it (test both ways).
- A new isolated page next to the pilot page (`frontend/src/visualAssets/`, own entry point, not imported by the Live
  Map): loads a draft preview manifest and draws a deterministic sample map that uses every Live Map terrain code
  (`TILE_NAMES`) in realistic patches, plus a toggle to show the plain colour fills side by side. Missing drafts show the
  role fallback, labelled. Detail picks use `pickDetail`.
- The page shows, per terrain code, which draft is shown or that it is missing, and the set id and hash, so a review
  record can name exactly what was reviewed.
- How to open it is documented in `docs/assets/drawing_tools.md`.

## Out of Scope
- The normal Live Map. Real world data from the simulation or the API. Adoption.

## Acceptance Criteria
- [x] Draft preview manifests and runtime manifests are mutually unparseable (Python + TS tests).
- [x] The sample map is deterministic and covers every `TILE_NAMES` code (test).
- [x] Isolation test: nothing outside `src/visualAssets/` imports the page; the pilot page is unchanged.
- [x] A screenshot of the page with the committed draft set (or a fixture set) is stored as evidence.

## Related Tickets
- TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS (epic), TCK-20261004-VISUAL-ASSETS-DRAFT-SETS-AND-SET-ADOPTION (before)

## Related Docs
- docs/assets/store_contract.md, docs/assets/drawing_tools.md

## Related Stored Artifacts
- None.

## Related Code Areas
- frontend/src/visualAssets/, frontend/src/constants/colors.ts (read only), visual_assets/store/

## Assumptions / Open Questions
- Sample map only; a real-world-snapshot map would need world data in the client and is a later choice.

## Implementation Notes
- Planner-accepted decisions (D1-D7): the preview is copied byte for byte and drawn at 1/`scale` with smoothing off (the manifest entry adds `scale`, `source_asset_id` and `draft_id` to the runtime entry shape; `scale` is an integer that divides the preview size, refused otherwise in Python and TS); one explicit `TERRAIN_DRAFT_KEYS` table (`terrain.` + snake_case name) for all 23 `TILE_NAMES` codes (0-22, not 16), tested for full and unique coverage and named as ticket 6's contract; `size_bound` of `DraftPreviewManifest` is the existing `MAX_MANIFEST_BYTES` (a derived export, not durable state; widest at 256 entries 154837 B, noted on the budgets row); `draft export` is pure Python, verifies the set first and refuses on any finding (including a revoked intake); the page opens the committed fixture by default and a folder picker reads an exported folder in the browser (no network, no server config).
- **The hash pin.** The manifest's `draft_set_hash` is `file_hash(draft_set.json bytes)`. `test_draft_export.py` computes it three ways and requires them equal: the export's hash, the hash `adopt-set` prints in its confirmation (parsed from the notice) and the one stored in the `SetAdoptionRecord`. The page prints it verbatim (`data-testid="draft-set-hash"`, tested against the manifest's field) and the committed fixture equals a fresh export, so the displayed hash is the exported one.
- **Mutually unparseable.** The draft manifest has its own `record_type` and required `set_id`/`draft_set_hash`; both directions refuse in Python (`wrong_record_type`, and after swapping the type `unknown_field`/`missing_field`) and in TS (`parseManifest` refuses the draft manifest, `parseDraftPreview` refuses runtime manifests, with and without the swapped type).
- An entry with no `detail` on a key with a declared axis fills its default slot; both parsers refuse two entries in one effective slot, and the TS adapter keys the default slot by the declared default so the unchanged resolver and `pickDetail` find it.
- The page reuses the existing loader, resolver and `pickDetail` unchanged through an adapter (`asRuntimeSnapshot`: set id as catalog, set hash as generation); `manifest.ts` only exports helpers (the pilot page and its tests are unchanged and green). The Live Map imports nothing of it (isolation test, including the production build).
- Kept minimal per the user's decision to pause asset work after this batch: no extra options or tooling. Parked, not built: showing the recorded fallback reasons per cell in the pilot page, weights and a per-world seed (earlier), a committed Playwright capture config (the screenshot below was taken once, locally, with the installed Chromium).

- **Extension by `TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET` (planner-approved, one optional field):** a draft preview entry may carry `adopted: true` (only the literal `true`, omitted otherwise; Python and TS parsers both enforce it) for a reference to a live ADOPTED slot the set does not hold. `draft export` adds such references from the catalog artifacts; a draft always wins; they exist only in the export, never in a `DraftSet`, so `draft verify` and `adopt-set` never see one (tested). The page marks them with a small amber square and "adopted (reference)" in the status table.

## Test Summary
`tests/visual_assets`: 1512 passed (foreground, 2 GB cap); `verify`: store ok; `draft_fixture --check`: current. `vitest src/visualAssets`: 185 passed; `tsc -b` and `eslint src/visualAssets` clean; the isolation test (nothing outside `src/visualAssets/` imports any of it, and the production build contains none of it) passes with the new fixture PNGs counted (6 to 13).
- Python: `test_draft_export.py` (8: files, determinism, the three-way hash pin, a changed set changes the hash, refusals with no output left, CLI, mutually unparseable both ways, scale rules), `test_draft_fixture.py` (2), widest manifest in `test_record_bounds.py`.
- TS: `draftManifest.test.ts` (26), `terrainDrafts.test.ts` (5: the copies equal the Live Map's, full unique coverage of 23 codes, deterministic map, every code in a patch of at least 6 cells), `draftHarness.test.tsx` (10: draws at 1/scale with smoothing off, forest cells use the slot `pickDetail` names, missing codes show the flat fill with a diagonal, flat control, shown set id and hash, per-code status, toggle, refuses a runtime manifest, folder picker).
- Evidence: `agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-DRAFT-PREVIEW-PAGE/draft_page_fixture_set.png`: the page with the fixture set (the three real forest slots, four synthetic terrains, 18 codes marked as missing).

## Files Changed
- visual_assets/store/{draftexport (new),cli,config}.py, contracts/{draft,__init__}.py
- frontend/src/visualAssets/{draftManifest,terrainDrafts,DraftHarness,draftSource,draftMain}.ts(x) (new), manifest.ts (exports only), __fixtures__/draft/ (fixture export), __tests__/{draftManifest,terrainDrafts,draftHarness,isolation}.test.ts(x); frontend/rehearsal-draft.html (new)
- tests/visual_assets/{store/draft_fixture.py,test_draft_fixture.py} (new), store/unit/{test_draft_export (new),test_record_bounds,conftest}.py, test_boundaries.py; visual_assets/catalog/fixtures/contracts/draft_preview_manifest.json (new)
- docs/assets/{store_contract,drawing_tools,budgets}.md

## Completion Summary
`draft export` writes a draft preview manifest (its own record type, carrying the exact draft set hash) and the previews; an isolated dev-only page draws a deterministic whole map using every Live Map terrain code from a draft set, marks missing drafts, picks details with `pickDetail`, and prints the set id and hash the `adopt-set` confirmation prints. Nothing is adopted.

