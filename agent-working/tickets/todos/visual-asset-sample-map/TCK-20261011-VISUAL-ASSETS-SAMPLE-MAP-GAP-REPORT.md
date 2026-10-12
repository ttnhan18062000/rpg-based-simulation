---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT
phase: open
date: 2026-10-11
tags: [architecture, documentation]
---

# TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT

## Title
Sample map: gap report with sizes and needed-by, evidence copies, docs, close

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Child 3 of `TCK-20261011-EPIC-VISUAL-ASSET-SAMPLE-MAP`.

## Scope
- `docs/assets/sample_map/README.md` (new): what was rendered, the commands, and the x1 PNGs as committed evidence, with a note that they are evidence and not assets. Plus the gap report, one row per gap: what (e.g. `terrain.grassland` variants, road/coast connecting tiles, multi-tile town structures, a unit marker per entity kind), evidence (cell or object counts from the renders), a size/count estimate (tiles to draw, dimensions), and needed by (A markers / terrain variants / connecting tiles / multi-tile structures).
- End with the owner's art-priority question, drafted (asset-planner asks it), and the input list for candidate A.
- If #519 has answered by then, reconcile: correct rows and do not re-render (lead). If not, say "unconfirmed by rpg-planner (#519)".
- Both `docs/assets/session_handoff/*` snapshots; `make knowledge-index-update`; closure (`batch_hand_close`), REGISTRY regenerated after the final stored-artifact move and before push.

## Out of Scope
- **No activation** (lead guard): no `frontend/` or `src/` edit, no change to how the Live Map draws, nothing wired into the app. `src/` is imported read-only to build a world state and call its presenters; nothing is written into `src/`, the content registries or `data/`.
- The rendered picture is evidence, not a shipped asset: never intake, adopt or put in a release candidate.
- No new art, no registry key, no store or drawing-tool code change, no bound change.
- Waiting on #519: answers correct the gap report only, with no re-render beyond that (lead).

## Acceptance Criteria
- [ ] Every gap has a size/count estimate and a needed-by.
- [ ] Evidence PNGs committed under `docs/assets/sample_map/` only, under a stated size cap (planner: 256 KiB total).
- [ ] All 4 tickets closed, done_checker PASS.

## Related Tickets
- Parent: `TCK-20261011-EPIC-VISUAL-ASSET-SAMPLE-MAP`
- Needs: `TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-DATA`, `TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-RENDER`

## Related Docs
- `docs/assets/store_contract.md` (runtime manifest, atlas), `docs/assets/pilot_terrain_key.md`, `docs/assets/surface_rehearsal_result.md`, `docs/assets/icon_style_guide.md`
- `agent-working/tickets/done/TCK-20260821-PRESENT-MAP-STATIC.md` (where `present_map` / `present_static` come from)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20260821-PRESENT-MAP-STATIC/investigation.md` (field-level drop and derive decisions of `present_static`)

## Related Code Areas
- `docs/assets/sample_map/`, `docs/assets/session_handoff/*`

## Assumptions / Open Questions


## Implementation Notes
- `docs/assets/sample_map/README.md` (what was rendered, the three worlds and why, how the data is made read-only, the two labelled views, the commands, the port's three proofs, the committed crops) and `docs/assets/sample_map/gap_report.md` (11 gaps G1-G11, each with evidence by view, a tile or sprite estimate and a needed-by; the cells-per-terrain-name table for #523; the proposed-alias table; the reconciliation with #519 and #523; the owner's art-priority question drafted with five options in a fixed order and none recommended; the input list for candidate A). Evidence: ten x1 crops (five per view) under `docs/assets/sample_map/`, 137,376 B in all against the 256 KiB cap (the whole folder is 156,566 B), reproduced by `python -m tools.visual_assets_sample_map evidence` and checked equal by a test; the full-world sheets stay in the gitignored `reports/`.
- Reconciliation (lead: correct, do not re-render): #519 HAS answered (rpg-planner, 2026-10-11) and nothing contradicts a number; the report cites it and notes that rpg's counts over all worlds (buildings shop 24, inn 24, healer_hut 21, blacksmith 20, town_hall 19, mine_entrance 7, watchtower 4; places CITY 20, CAMP 11, NEST 10, RUIN 9, LAIR 2) were not re-measured here and that rpg's suggested sample worlds were not rendered. #523 (the client colours terrain by a per-world sorted index into a fixed table; the V2 vocabulary) is linked as the evidence target: the report carries the per-world cell counts per exact terrain name with `PLAIN` and `plain` separate and the alias table, as lead asked, and does not resolve the vocabulary mismatch or the `PLAIN`/`plain` duplicate (rpg's).
- The estimates are counts of tiles or sprites at the sizes the store already holds (terrain 16x16, building icons 24x24, markers 16x16): terrain variants about 14 tiles; connecting tiles about 48; multi-tile structures about 7 sprites at 32x32; markers about 18 to 24 icons (4 building, 9 resource node, 1 place, 4 to 10 entity); name decisions 0 tiles. They are inputs to the owner's question, not commitments.
- Refreshed both `docs/assets/session_handoff/*` snapshots at close; `make knowledge-index-update`; closure by hand (`batch_hand_close`).

## Test Summary
`tests/visual_assets/test_sample_map_render.py` and `test_sample_map_data.py`: 46 passed, including the committed crops equal what the tool produces and the 256 KiB cap. The full `tests/visual_assets` run and the tools, docs and architecture subsets are in the epic's Completion Summary.

## Files Changed
- `docs/assets/sample_map/README.md`, `docs/assets/sample_map/gap_report.md`, ten `docs/assets/sample_map/*_x1.png` crops (new), `tools/visual_assets_sample_map.py` and `tools/visual_assets_sample_map_render.py` (the `evidence` command), `tests/visual_assets/test_sample_map_render.py`

## Completion Summary

