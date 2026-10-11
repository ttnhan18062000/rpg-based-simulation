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
OPEN

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


## Test Summary


## Files Changed


## Completion Summary

