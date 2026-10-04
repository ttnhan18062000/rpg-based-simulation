---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DRAFT-PREVIEW-PAGE
phase: open
date: 2026-10-04
tags: [architecture, live-map]
---

# TCK-20261004-VISUAL-ASSETS-DRAFT-PREVIEW-PAGE

## Title
An isolated preview page that renders a whole map from a draft set, for set-level review

## Status
OPEN

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
- [ ] Draft preview manifests and runtime manifests are mutually unparseable (Python + TS tests).
- [ ] The sample map is deterministic and covers every `TILE_NAMES` code (test).
- [ ] Isolation test: nothing outside `src/visualAssets/` imports the page; the pilot page is unchanged.
- [ ] A screenshot of the page with the committed draft set (or a fixture set) is stored as evidence.

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

## Test Summary

## Files Changed

## Completion Summary
