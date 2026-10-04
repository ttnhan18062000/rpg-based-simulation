---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE
phase: open
date: 2026-10-04
tags: [mcp, live-map, testing]
---

# TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE

## Title
One real terrain tile through the whole store: draw, hand off, intake, user adoption, build, release candidate, runtime manifest

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`AM-M6` needs "one exact noncritical role, source and artifact separately reviewed and adopted under named human
authority". The user chose a terrain cell (2026-10-04). The committed catalog has zero real keys today. Child 2 of
`TCK-20261004-EPIC-VISUAL-ASSET-PILOT-READINESS`.

## Scope
- The terrain: **Forest** (Live Map tile code 6, `TILE_NAMES[6]`), unless the user named another before this ticket starts.
  It replaces a flat fill (`TILE_COLORS[6]` `#1b3a1b`, `frontend/src/hooks/useCanvas.ts:70`) at `CELL_SIZE` 16, x1.
- Register one visual key in the catalog for it (family `terrain`), following `docs/assets/store_contract.md` and the
  catalog's own rules (no tool write path into the catalog: a hand-edited, reviewed change).
- Draw it with the drawing tools (MCP) at 16 x 16. It must tile (edges meet when repeated) and stay readable at 1:1 next
  to the other terrain fills; keep its average colour close to `#1b3a1b` so the colour fill stays an honest fallback.
  Up to three candidates; show each to the user with `preview` at scale 8 and as a 4 x 4 tiled patch.
- `export_handoff` + `submit_candidate` for the one the user picks; intake must pass with no `PALETTE_UNVERIFIABLE`.
- **Stop and ask the user** (blocking question) to adopt it through the CLI gate. The agent never adopts.
- After adoption: build (pixels-v1), cut a release candidate, `export-runtime`, `verify` clean.
- Record which revision, intake id, adoption record, artifact hash, release id and manifest hash belong together, in the
  ticket's `investigation.md` and as a short "Pilot key" section in `docs/assets/store_contract.md` or a new
  `docs/assets/pilot_terrain_key.md` (planner prefers the new doc).

## Out of Scope
- Any change to the normal Live Map, `GameCanvas.tsx`, `useCanvas.ts`, `TILE_COLORS`, or `src/`.
- More than one key, animation, variants (no axes beyond what the key format requires), other scales.
- The harness changes (ticket 3).

## Acceptance Criteria
- [ ] The catalog has exactly one real key (terrain/forest or the user's choice) plus the existing fixtures.
- [ ] Its adoption record names the user as the adopting human and was made through the CLI gate, not by the agent.
- [ ] `verify` passes; the release candidate and runtime manifest contain the key with matching hashes.
- [ ] The tile tiles cleanly: a 4 x 4 repeat has no visible seam (shown to the user, user's call recorded).
- [ ] Boundary tests and `tests/visual_assets/` pass (scoped, under the 2 GB cap); real-Aseprite steps run locally (D10).
- [ ] If the user declines every candidate or has not adopted, the ticket ends `BLOCKED` with that stated, not `DONE`.

## Related Tickets
- TCK-20261003-VISUAL-ASSETS-RUNTIME-MANIFEST (done), TCK-20261003-VISUAL-ASSETS-LOCAL-ASEPRITE-EVIDENCE (done)

## Related Docs
- docs/assets/store_contract.md, docs/assets/drawing_tools.md, docs/assets/pixel_art_technique.md
- docs/plans/visual-asset-management-runtime-integration/06_bounded_activation_pilot_plan.md (prerequisites)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261003-VISUAL-ASSETS-RUNTIME-MANIFEST/

## Related Code Areas
- visual_assets/catalog/, visual_assets/store/, visual_assets/drawing/

## Assumptions / Open Questions
- Adopt needs Aseprite: runs on the licence holder's machine only (D10).
- Whether a 16 px tile looks right at 1:1 is a human call; the agent proposes, the user decides.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
