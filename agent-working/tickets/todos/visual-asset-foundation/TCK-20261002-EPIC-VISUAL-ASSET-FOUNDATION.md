---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION
phase: open
date: 2026-10-02
tags: [mcp, architecture, documentation]
---

# TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION

## Title
Visual asset foundation: in-project drawing tools and asset store under `visual_assets/`

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
The user wants the Aseprite drawing tools to live in the project proper, not as an experiment, together
with a complete asset store, before PR #286 merges. The approved structure is
`docs/plans/visual-asset-foundation/README.md`: one root folder `visual_assets/` holding `drawing/` (tools
and MCP server), `store/` (store logic and CLI) and `catalog/` (managed data), with the lifecycle gates of the
asset-management proposal preserved (an agent can draw and hand off; only a human-run command adopts; nothing
activates at runtime).

## Scope
Tracks the child tickets in `SEQUENCE.md`. No direct implementation.

## Out of Scope
- Runtime activation, resolver, Live Map/HUD consumption, any `frontend/` or `src/` change (`AM-M5`..`M7`).
- Deployment profile selection (`AM1-W01`), signing/trust channel, retention numbers.
- Any art decision or real asset; the catalog ships empty apart from synthetic fixtures.
- Closing `U-02` (Aseprite licence/provenance), `U-05` (budgets), `U-14` (CI with Aseprite).

## Acceptance Criteria
- [ ] Every child ticket in `SEQUENCE.md` is closed.
- [ ] `docs/plans/visual-asset-foundation/README.md` matches what was built, or records each deviation.
- [ ] No `src/` import of `visual_assets` and no `visual_assets` import of `src/` (boundary test green).

## Related Tickets
- TCK-20261002-ASEPRITE-MCP-SPIKE-HARDENING, TCK-20261002-ASEPRITE-MCP-HIGHLEVEL-PIXEL-ART-TOOLS (done; the code being moved)
- TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT (child 1, done; merged in PR #286)

## Related Docs
- docs/plans/visual-asset-foundation/README.md
- docs/plans/visual-asset-management-runtime-integration/README.md
- docs/plans/aseprite-mcp-pixel-art/README.md
- docs/brainstorm/render-and-art/asset_management_and_runtime_integration_proposal.md

## Related Stored Artifacts
- None (epic).

## Related Code Areas
- experiments/aseprite_mcp/ (source of the move), visual_assets/ (target), tests/visual_assets/

## Assumptions / Open Questions
- The user approved the structure and the root-folder name `visual_assets/` on 2026-10-02.
- D3 decided by the user on 2026-10-02: commit generated PNGs only for adopted assets; candidates and anything
  under review stay local in the gitignored `visual_assets/catalog/.review/` area.
- D2 (no LFS for sources) and D4 (canonical pixel hash) were proposed by the planner and confirmed by the user on
  2026-10-02.

## Implementation Notes
Epic: see children.

## Test Summary
Epic: see children.

## Files Changed
Epic: see children.

## Completion Summary
(open)
