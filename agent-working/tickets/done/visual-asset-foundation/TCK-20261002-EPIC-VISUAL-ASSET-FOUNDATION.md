---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION
phase: done
date: 2026-10-02
tags: [mcp, architecture, documentation]
---

# TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION

## Title
Visual asset foundation: in-project drawing tools and asset store under `visual_assets/`

## Status
DONE

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
- [x] Every child ticket in `SEQUENCE.md` is closed (all six; see Related Tickets).
- [x] `docs/plans/visual-asset-foundation/README.md` matches what was built, or records each deviation (its "As built: deviations" section).
- [x] No `src/` import of `visual_assets` and no `visual_assets` import of `src/` (boundary test green; also nothing under `visual_assets/` may import the human-gated layers from the drawing code).

## Related Tickets
- TCK-20261002-ASEPRITE-MCP-SPIKE-HARDENING, TCK-20261002-ASEPRITE-MCP-HIGHLEVEL-PIXEL-ART-TOOLS (done; the code being moved)
- TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT (child 1, done; merged in PR #286)
- TCK-20261002-VISUAL-ASSETS-STORE-CONTRACTS, -STORE-INTAKE, -STORE-ADOPTION, -STORE-BUILD-RELEASE, -STORE-MCP-TOOLS (children 2-6, done on branch `visual-assets-store`)

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
Epic: see children. Built: the drawing tools in `visual_assets/drawing/` (19 MCP tools), the store in `visual_assets/store/` (records and identities, intake with an independent validator and the store's own render check, human-gated adoption and revocation, sandboxed pixel-hashed build, release candidates, `verify`, `gc`, read-only MCP store tools), the managed catalog `visual_assets/catalog/` (still zero keys, sources, adoptions and artifacts), and the boundary test that keeps drawing code away from every writer. Planner follow-ups R1-R4, H1, B1 and the `ops.lua` summary change are recorded in the children.

### What stays open (stated, not ticked)
- `U-02` Aseprite licence/provenance review; `U-05` numeric budgets (every bound is provisional); `U-14` CI with Aseprite (the real-Aseprite tests run locally only; CI runs everything that needs no Aseprite).
- `AM1-W01` deployment profile, signing/trust channel (`AM1-W08`), retention numbers, and `AM-M5`..`M7` (activation, resolver, Live Map/HUD): out of scope by design (D6).
- Known limits: the human gate does not authenticate the person; a consistent forgery of two linked records is caught only by git history; a local intake revocation covers only one machine; animation metadata beyond frame and tag counts is not checked; one visual key maps to one artifact (one scale class); an untouched first revision with a default palette is quarantined (`PALETTE_UNVERIFIABLE`).
- The branch has not been pushed and no PR is open; that decision is the user's.

## Test Summary
Epic: see children.

## Files Changed
Epic: see children.

## Completion Summary
All six children are closed. An agent can draw, hand a revision off, submit it for intake and read the store through the MCP server; only a human-run command can adopt or revoke; the store builds pixel-hashed artifacts and immutable release candidates and checks itself in pure Python; nothing activates at runtime. The committed catalog holds zero keys, sources, adoptions and artifacts. What stays open and the known limits are listed under Implementation Notes.
