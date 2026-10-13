---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261012-VISUAL-ASSETS-TERRAIN-VARIANTS-RC-AND-CLOSE
phase: done
date: 2026-10-12
tags: [architecture, documentation]
---

# TCK-20261012-VISUAL-ASSETS-TERRAIN-VARIANTS-RC-AND-CLOSE

## Title
Terrain variants: build, rc-0010 on the owner's answer, sample map re-rendered as evidence, gap report and budgets, close

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Child 4 of `TCK-20261012-EPIC-VISUAL-ASSET-TERRAIN-VARIANTS`.

## Scope
- `build` the adopted variants. **Owner-only step:** ask (blocking) to assemble rc-0010 = rc-0009's entries + the variants. Unchanged entries are byte-identical; any re-anchored slot follows child 1's design, and the guard test states it by equality.
- The red set from child 2 must turn green: re-point tests from rc-0009 to rc-0010 by exact named sets, as the real-art batch did.
- Re-run the sample map (`python -m tools.visual_assets_sample_map render --all`) on rc-0010. The EXACT view now resolves through the aliases. Update `docs/assets/sample_map/` evidence (under its 256 KiB cap) and the gap report's G1-G4 rows with the new numbers. G12 stays rpg's.
- budgets.md: real measurements for the new detail axes and aliases (fits included).
- Re-run the local Aseprite proof record once if the staleness test says it is stale.
- Both session_handoff snapshots; closure (`batch_hand_close`). `git add` everything, THEN regenerate REGISTRY and run `--check` from a clean tree (the sample-map batch's lesson). `make knowledge-index-update`.

## Out of Scope
- No `src/` or `frontend/` change: the client's colour-by-name and the V2 vocabulary dedupe are rpg's (#523). No activation.
- No new terrain KEY: V2 names reach existing art through aliases; a new key needs an owner decision outside this batch.
- No connecting tiles, no multi-tile structures, no map markers (A comes after this batch, following V2 kind names as the presenter emits them).
- No bound raise, no store or drawing-tool code change unless child 1 proves one is needed: then STOP, it is its own owner question.
- `PLAIN` vs `plain` is not resolved here: one alias covers both while rpg dedupes.

## Acceptance Criteria
- [ ] rc-0010 released on the owner's answer; `verify` ok; the red set green.
- [ ] The sample map re-rendered; gap report rows updated.
- [ ] All 5 tickets closed, done_checker PASS, REGISTRY in sync from a clean tree.

## Related Tickets
- Parent: `TCK-20261012-EPIC-VISUAL-ASSET-TERRAIN-VARIANTS`
- Needs: `TCK-20261012-VISUAL-ASSETS-REGISTRY-BUDGET-AND-DETAIL-DESIGN`, `TCK-20261012-VISUAL-ASSETS-V2-TERRAIN-ALIASES`, `TCK-20261012-VISUAL-ASSETS-TERRAIN-VARIANT-DRAFTS`

## Related Docs
- `docs/assets/sample_map/gap_report.md` (G1-G4, G12, the alias table), `docs/assets/budgets.md` (`MAX_REGISTRY_BYTES`, `MAX_DETAIL_KEYS`, `MAX_DETAIL_VALUES`), `docs/assets/store_contract.md` (registry, detail axis, known gap: a registry edit makes older candidates unexportable), `docs/assets/pixel_art_technique.md`, `docs/assets/pilot_terrain_key.md` (the forest detail axis precedent)
- GitHub #523 (V2 vocabulary, owner answer), #519

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT/`, `agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT/` (if present: the detail axis contract)

## Related Code Areas
- `visual_assets/catalog/**`, `docs/assets/{budgets,store_contract}.md`, `docs/assets/sample_map/`, `docs/assets/session_handoff/*`

## Assumptions / Open Questions


## Implementation Notes
- Built the 14 adopted variants (`build` per source, `store verify` ok). OWNER ANSWER (2026-10-13, asked directly, blocking, neutral options): "Assemble rc-0010". `release --catalog-id pilot` gave `pilot/rc-0010`, 87 entries, CANDIDATE; `verify` ok; rc-0009 byte-untouched (`cmp` against HEAD).
- Equality guard `tests/visual_assets/test_rc_0010_extends_rc_0009.py` (2): 67 rc-0009 entries byte-identical; the six keys (grassland, mountain, cave, ruins, swamp, shallow_water) re-anchored = their rc-0009 entry plus `detail: base` (same artifact and pixel hash); 14 variants new; nothing else; forest keeps plain/bush/tree.
- The 16 red tests of child 2 are green by re-pointing to rc-0010 by exact name: `test_atlas.py` (rc-0009 -> rc-0010, 87 entries), `test_release_byte_reproducibility.py` (the pinned release id), `test_sample_map_render.py` (the renderer's `RELEASE_ID`). `adopted_facts`: `GENERATED` 87, `VARIANT_*`, `RC_0010_*`, the candidate list incl. rc-0010; icon and v2-key tests accept rc-0010 beside rc-0008 and rc-0009.
- Sample map re-rendered on rc-0010 (`tools/visual_assets_sample_map_render.py` `RELEASE_ID`): the data tool no longer carries terrain proposals (they are the registry's aliases) and the exact view resolves a terrain name through `Registry.resolve` (`row["registry_alias"]`). Result, seed 42, 73,808 cells: 0 cells in the terrain gap in BOTH views (rc-0009: 12.1 % drew in the exact view). The page, README, gap report and keytable say plainly that THE LIVE CLIENT DOES NOT RESOLVE ALIASES (registry-only; no release or runtime export carries them). Evidence crops regenerated: 237,953 B of the 262,144 B cap; they went over the cap (304,812 B) because the exact view now draws terrain, so three crop boxes were shrunk (a box, not the cap). 3 sample-map tests updated for the alias resolution (data: `terrain` no longer in `PROPOSED_ALIASES`, the ruin row resolves via `registry_alias`; render: terrain gap empty in both views).
- Gap report: dated update section (G1 to G4 on rc-0010: G1-G3 resolved offline by registry aliases, G4 six axes and 14 variants, the same-offset feature limit stated), G1/G2/G3/G4 status cells, registry figure 30,943 B (6.7 %). `budgets.md`: new section "rc-0010 measured": runtime manifest 22,793 B (4.3 %), candidate 14,920 B, registry 30,943 B, crops 237,953 B. G12 left as rpg's.
- Local Aseprite proof record was stale after the guarded changes: re-run once (`make visual-assets-aseprite-local`, pytest exit 0), own commit; `test_aseprite_local_proof.py` 49 passed.
- Not done, on purpose: the registry comment wording nit ("mapped to existing art by these aliases (registry-only)"): a registry edit makes rc-0010 unexportable (`registry_mismatch`) and would force a new candidate; left for the next key-adding batch. No `src/`, `frontend/`, store or drawing code change, no bound change, no new key.

## Test Summary
`tests/visual_assets` (project venv): 2511 passed on the closing run (before the proof record refresh, 4 failed: 3 sample-map tests fixed above and the stale proof record refreshed); the 16 tests red since child 2 are green. Targeted `tests/tools`, `tests/docs`, `tests/static` and `tests/architecture` runs are listed in the closure report.

## Files Changed
`visual_assets/catalog/**` (14 adoption-built artifacts, `pilot/rc-0010.json`), `tools/visual_assets_sample_map{,_render}.py`, `tests/visual_assets/{adopted_facts,test_rc_0010_extends_rc_0009,test_sample_map_data,test_sample_map_render,test_atlas...}`, `docs/assets/{budgets.md,aseprite_local_proof.json,sample_map/**}`, the five tickets and their stored artifacts.

## Completion Summary
DONE `e772fca7c` + `3bfedffbc`. Owner answered "Assemble rc-0010": 87 entries (67 identical, 6 re-anchored to `detail: base`, 14 new), the 16 red tests green, the sample map re-rendered with registry aliases (0 terrain gap cells of 73,808; the live client does not resolve aliases), gap report and budgets updated, the local Aseprite proof record refreshed.

