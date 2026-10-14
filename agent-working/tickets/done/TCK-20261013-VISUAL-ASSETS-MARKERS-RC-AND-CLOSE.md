---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261013-VISUAL-ASSETS-MARKERS-RC-AND-CLOSE
phase: done
date: 2026-10-13
tags: [architecture, documentation]
---

# TCK-20261013-VISUAL-ASSETS-MARKERS-RC-AND-CLOSE

## Title
Map markers: build, rc-0011, sample map with markers, gap report and budgets, closure

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 4 of `TCK-20261013-EPIC-VISUAL-ASSET-MAP-MARKERS`. Closes the batch: a registry edit makes older candidates unexportable, so the batch ends with its own candidate, and the tests that export the committed one are re-pointed.

## Scope
- `build` the adopted markers. **Owner-only step:** ask (blocking) to assemble rc-0011 = rc-0010's 87 entries + the new markers. Unchanged entries are byte-identical, and the guard test states it by equality.
- The red set from children 2-3 turns green: re-point the tests from rc-0010 to rc-0011 by exact named sets.
- **Sample map:** extend `tools/visual_assets_sample_map_render.py` to draw building, place, resource-node (and entity, if child 3 shipped) markers from `world_data.json`, resolved through the registry aliases (offline only, as for terrain). Re-render on rc-0011, update `docs/assets/sample_map/` evidence (under its 256 KiB cap) and README, and the gap report's G6, G8, G9, G10 rows with the new numbers. Byte-identical on a re-run.
- budgets.md: real measurements of the committed registry and rc-0011's runtime manifest.
- Re-run the local Aseprite proof record once if the staleness test says it is stale.
- Both session_handoff snapshots; closure (`batch_hand_close`). `git add` everything, THEN regenerate REGISTRY and run `--check` from a clean tree. `make knowledge-index-update`. Close #543's cover_patch part in the gap report.

## Out of Scope
- No `src/` or `frontend/` change, no activation. The live client draws none of this (#519). The client-side kind -> key resolution belongs to rpg (#523: option (a) build-time registry read, or (b) an asset alias export with its own owner D-record).
- No item icons: `grass_cover`/`raw_meat` are a later item-icon ticket (#543 decision).
- No multi-tile structures (G7), connecting tiles (G5) or chests (G11, no data). No new terrain.
- No bound raise, and no store or drawing-tool code change unless child 1 proves one is needed. If it does, STOP: that is its own owner question.
- No animation. `TCK-20261011-VISUAL-ASSETS-BUILD-EXPORTS-FRAME-ONE-ONLY` stays in the backlog unless a marker is animated.

## Acceptance Criteria
- [x] rc-0011 assembled on the owner's answer; the guard states unchanged entries by equality.
- [x] No red test left; the renderer draws the markers and re-runs byte-identical.
- [x] Gap report, README, budgets updated; all five tickets closed; REGISTRY in sync from a clean tree.

## Related Tickets
- Parent: `TCK-20261013-EPIC-VISUAL-ASSET-MAP-MARKERS`; needs `TCK-20261013-VISUAL-ASSETS-MARKER-BUDGET-AND-KEY-DESIGN`, `TCK-20261013-VISUAL-ASSETS-OBJECT-MARKER-DRAFTS` (and `TCK-20261013-VISUAL-ASSETS-ENTITY-MARKER-DRAFTS` unless the owner moved it out)
- Precedent: `TCK-20261012-VISUAL-ASSETS-TERRAIN-VARIANTS-RC-AND-CLOSE`

## Related Docs
- `docs/assets/sample_map/gap_report.md` (G6, G8, G9, G10, G11; "Input list for candidate A"), `docs/assets/budgets.md` (`MAX_REGISTRY_BYTES`, the 2026-10-12 re-measurement, ~450 B per real icon key), `docs/assets/store_contract.md` (registry-only aliases Known gap; a registry edit makes older candidates unexportable), `docs/assets/icon_style_guide.md` (family conventions, per-icon specs, the recognisability process rule), `docs/assets/fallback_safety.md` (`safety_class`, `fallback`), `docs/assets/icon_criteria.md`
- GitHub #523 (owner: V2 names canonical; markers follow V2 kind names as the presenter emits them), #519 (rpg's kinds and counts), #543 (cover_patch nodes in A)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT/`, `agent-working/stored_artifacts/TCK-20261012-VISUAL-ASSETS-REGISTRY-BUDGET-AND-DETAIL-DESIGN/` (the last budget review), `agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS/` (if present)

## Related Code Areas
- `visual_assets/catalog/manifests/candidates/pilot/`, `tools/visual_assets_sample_map*.py`, `docs/assets/sample_map/**`, `docs/assets/budgets.md`, `tests/visual_assets/**`

## Assumptions / Open Questions


## Implementation Notes
- rc-0011 assembled on the owner's answer of 2026-10-14 ("Assemble rc-0011 (105)"): `store release --catalog-id pilot` after `store build` of the 18 adopted sources; 87 entries byte-identical to rc-0010 + 18 new, no alias entries (`tests/visual_assets/test_rc_0011_extends_rc_0010.py`, by equality).
- Re-pointed: `adopted_facts.py` (the 18 sources, set adoption, 112 adoptions, 224 intake files, 105 generated, `RC_0011_ENTRIES`, terrain and object aliases), `test_atlas.py`, `test_release_byte_reproducibility.py` (rc-0011), the registry pins (83 keys, 54 icon keys, 53 labels, 8 aliases), the spec and recognition pins (54), `test_icon_set_adoption.py`, `test_icon_v2_keys.py`, `test_icon_draft_set.py`, `test_icon_release_candidate.py`, `test_key_usage.py`, `test_sample_map_data.py`, `test_v2_terrain_aliases.py`; new `test_object_marker_adoption.py`.
- Sample map: `tools/visual_assets_sample_map.py` maps nodes to `icon.node.<kind>`, resolves `shop`, `CAMP`, `RUIN` through the registry aliases and marks a CITY `plate_only`; the renderer draws it (CITY = plate alone) on rc-0011; 0 object gaps in the three worlds; the alias view equals the exact view, so only exact crops are committed (120,273 B).
- Gap report (G6, G8, G9 closed; G10 moved to the entity-marker batch; the 16 px building map glyph recorded as a later owner choice), README, `budgets.md` (rc-0011 measured).
- Child 3 moved out on the owner's answer to `agent-working/tickets/todos/visual-asset-entity-markers/`.
- The Aseprite local proof record was refreshed once at the end (guarded files `adoption.py`, `revoke.py`, `test_release_byte_reproducibility.py` changed).

## Test Summary
Run under `systemd-run --user --scope -p MemoryMax=3G`, one at a time: the 28 ids of the red set from child 2 (all green now), the new rc-0011 and object-adoption tests, the sample-map data (17) and render tests, the atlas and byte-reproducibility tests (27), the store unit tests for the placeholder guard. The full `tests/visual_assets` run (2026-10-15, MemoryMax=3G, 625 s) ended 4 failed, 2538 passed; all four were fixed and re-run as targeted files: `test_boundaries.py` (the placeholder guard moved from `adoption.py` into `identities.py`, because `revoke` may not import `adoption`), `test_detail_axis.py` and `test_icon_owner_fixes_adoption.py` (pins now include the 18 object sources and 112 adoptions), `test_store_tools_stdio.py` (the response-size ceiling for a listing went from 20,000 to 30,000 characters: 105 artifacts are 20,333; a listing stays capped by `limit`).

## Files Changed
`visual_assets/catalog/manifests/candidates/pilot/rc-0011.json`, `visual_assets/catalog/generated/*--x1/` (18), `tools/visual_assets_sample_map.py`, `tools/visual_assets_sample_map_render.py`, `tests/visual_assets/**` (pins, new tests), `docs/assets/sample_map/**`, `docs/assets/budgets.md`, `docs/assets/aseprite_local_proof.json`, the session-handoff snapshots, the ticket folders.

## Completion Summary
rc-0011 (105 entries) is a candidate; the sample map draws every building, place and resource node of the three worlds with 0 gaps; the red set is green; gap report, README and budgets are updated. Entities moved to their own batch on the owner's answer.
