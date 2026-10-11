---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261011-EPIC-VISUAL-ASSET-SAMPLE-MAP
phase: open
date: 2026-10-11
tags: [architecture, planning]
---

# TCK-20261011-EPIC-VISUAL-ASSET-SAMPLE-MAP

## Title
Visual asset sample map: render real worlds offline from the released art and list what is missing

## Status
OPEN

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


## Files Changed


## Completion Summary

