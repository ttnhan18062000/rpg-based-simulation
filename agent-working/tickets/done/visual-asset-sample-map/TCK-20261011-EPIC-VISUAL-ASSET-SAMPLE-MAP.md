---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261011-EPIC-VISUAL-ASSET-SAMPLE-MAP
phase: done
date: 2026-10-11
tags: [architecture, planning]
---

# TCK-20261011-EPIC-VISUAL-ASSET-SAMPLE-MAP

## Title
Visual asset sample map: render real worlds offline from the released art and list what is missing

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Owner, 2026-10-11, asked whether the current art is enough for an example full Live Map with several terrains and structures, then: "yes, you can open an PR to ask RPG for information or issue (ask lead to decide)". asset-planner opened #519 (for:rpg-planner: terrain grid, location and entity kinds, how the Live Map draws today). lead-planner decided 2026-10-11 the order B (real-art proof) -> D (this batch) -> A (entity markers). D does NOT wait for #519: it reads the data read-only from the repo's own tooling, and #519's answers only confirm or correct the gap report.

## Scope
- Child 1 `TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-DATA`: read 3 real worlds' terrain grid and static objects read-only through the repo's own tooling into a sample-map data file per world.
- Child 2 `TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-RENDER`: an offline renderer (`tools/visual_assets_sample_map.py`) that draws each world from the rc-0009 runtime export with the same composition rule as the isolated client rehearsal, into a PNG and a static page.
- Child 3 `TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT`: the gap report (each gap sized and given a "needed by"), docs, closure.

## Out of Scope
- **No activation** (lead guard): no `frontend/` or `src/` edit, no change to how the Live Map draws, nothing wired into the app. `src/` is imported read-only to build a world state and call its presenters; nothing is written into `src/`, the content registries or `data/`.
- The rendered picture is evidence, not a shipped asset: never intake, adopt or put in a release candidate.
- No new art, no registry key, no store or drawing-tool code change, no bound change.
- Waiting on #519: answers correct the gap report only, with no re-render beyond that (lead).

## Acceptance Criteria
- [ ] Children 1-3 DONE, each commit reviewed and approved by `asset-planner`.
- [ ] The gap report gives every gap a size/count estimate and a "needed by" (A markers, terrain variants, connecting tiles, multi-tile structures): A's input and the owner's art-priority question.
- [ ] One PR, pushed and merged only on the user's own answer.

## Related Tickets
- Children: `TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-DATA`, `TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-RENDER`, `TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT`
- Depends on: `TCK-20261011-EPIC-VISUAL-ASSET-REAL-ART-PROOF` (rc-0009; dispatch only after it closes, lead)
- Feeds: candidate A, entity markers (not filed; starts with the `MAX_REGISTRY_BYTES` budget review)
- GitHub #519 (for:rpg-planner)

## Related Docs
- `docs/assets/store_contract.md` (runtime manifest, atlas), `docs/assets/pilot_terrain_key.md`, `docs/assets/surface_rehearsal_result.md`, `docs/assets/icon_style_guide.md`
- `agent-working/tickets/done/TCK-20260821-PRESENT-MAP-STATIC.md` (where `present_map` / `present_static` come from)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20260821-PRESENT-MAP-STATIC/investigation.md` (field-level drop and derive decisions of `present_static`)

## Related Code Areas
- `src/worldbuilding/cli.py`, `src/api/presenters/state_presenter.py` (read-only), `frontend/src/visualAssets/terrainBorders.ts` (the composition rule, read-only), `tools/visual_assets_sample_map.py` (new), `docs/assets/sample_map/` (new)

## Assumptions / Open Questions
- Planner decisions in `SEQUENCE.md`.

## Implementation Notes


## Test Summary
`tests/visual_assets` 2489 passed, 0 red at the batch head; sample-map tests 46 (the differential test against the real TS rule skips without node and esbuild). See the Completion Summary for the targeted subset and the one environmental failure (`complexipy` not installed in this venv).

## Files Changed


## Completion Summary
All three children are DONE on `visual-asset-sample-map` (off origin/main `5951fdb71`, which holds rc-0009), each approved by the planner (asset-planner session, now named `rpg-based-simulation-0b`): DATA `8ca3eabea`, RENDER `8a001d17a`, GAP-REPORT `d9189ff7e` and the closing commit. `tests/visual_assets`: 2489 passed, 0 red. Targeted `tests/tools` + `tests/docs` + `tests/architecture` (`-m "not slow"`, `-k` registry/frontmatter/stored/paths/working_log/ticket/layer/tag/visual/asset/knowledge/sample): 1409 passed, 8 skipped, 1 xfailed, and one registry-drift test red until the closing commit regenerated `docs/REGISTRY.yaml` (in sync now). The full `tests/tools` was not run locally (CI's Tools lane covers it). `tests/codebase/test_codebase_health_snapshot.py::test_make_target_runs_successfully_end_to_end` fails in this venv with "complexipy not found" (environmental, not caused by this batch; CI's Code health lane covers it). The differential test against the real TS rule skips without node and esbuild, so CI may not run it; its evidence is the run here (node v20.19.4, esbuild 0.27.3). No `src/`, `frontend/`, `data/` or `.github/` file changed, no store or drawing code, no key, no bound; nothing was written outside `reports/` (gitignored) and `docs/assets/sample_map/` (137,376 B of crops, 256 KiB cap).

**What it found (read-only, seed 42, three worlds, 73,808 cells):** in the exact view only 12.1 % of cells draw with art (8,936); 87.9 % (64,872) have no key: `PLAIN` 54,661, `plain` 5,578, `ruin` 3,362, `river` 1,271. `PLAIN` and `plain` coexist in one world. In the labelled alias view (UNCONFIRMED: asset-planner's proposal for rpg-planner, #519) every cell can draw, because all 23 terrain keys have art in rc-0009. Objects with no art: building kinds healer_hut, town_hall, mine_entrance, watchtower (and `shop` exactly), 9 resource-node kinds, place kinds CITY and NEST, 10 entity kinds. The sample worlds are a few rectangles over one default fill (G12, rpg's to judge).

**Gaps (12, each sized, in `docs/assets/sample_map/gap_report.md`):** terrain variants about 14 tiles; connecting tiles about 48; multi-tile structures about 7 sprites at 32x32; markers about 18 to 24 icons; name decisions 0 tiles; G12 0 art (rpg world generation). The owner's art-priority question is drafted with five options in a fixed order and none recommended; asset-planner asks it.

**rpg's side:** #519 answered (nothing contradicted a number; its all-worlds counts were not re-measured). #523 (the Live Map colours terrain by a per-world sorted index into a fixed table; the V2 vocabulary) is the evidence target of this report and rpg's to decide; the renderer draws by name and does not work around it.

**Next asset batch:** candidate A, entity and object markers: it starts with the `MAX_REGISTRY_BYTES` budget review and waits for rpg's vocabulary answer (#523); dispatched by the planner after this merges.
