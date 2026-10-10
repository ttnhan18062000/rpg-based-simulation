---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING
phase: open
date: 2026-10-10
tags: [architecture, planning]
---

# TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING

## Title
Visual asset store tooling: lock and deletion log, faster decoder, byte-reproducible releases, local Aseprite proof, atlases, palettes, animation metadata, bundle evidence

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Owner, 2026-10-10 (blocking questions): next asset batch is store tooling only, and ALL four groups: release safety, evidence capture, palette as data, and the previously parked no-consumer items (real-Aseprite CI, atlases, faster decoder, animation fields). Then: reverse D18 (new D24: lock + deletion log), keep D10 with a committed local proof record, decoder stays pure Python.

## Scope
- Children, in order (see SEQUENCE.md):
  1. `TCK-20261010-VISUAL-ASSETS-STORE-LOCK-AND-DELETION-LOG`
  2. `TCK-20261010-VISUAL-ASSETS-PNG-DECODER-SPEEDUP`
  3. `TCK-20261010-VISUAL-ASSETS-RELEASE-BYTE-REPRODUCIBILITY`
  4. `TCK-20261010-VISUAL-ASSETS-ASEPRITE-LOCAL-PROOF-RECORD`
  5. `TCK-20261010-VISUAL-ASSETS-RUNTIME-ATLAS-EXPORT`
  6. `TCK-20261010-VISUAL-ASSETS-PALETTE-AS-DATA`
  7. `TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS`
  8. `TCK-20261010-VISUAL-ASSETS-EVIDENCE-CAPTURE-REAL-BUNDLE`
  9. `TCK-20261010-VISUAL-ASSETS-STORE-TOOLING-DOCS-AND-CLOSE`

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art, no `.github/` change.
- Parked still: Git LFS, slices/9-slice/pivots, client use of atlases or animation, raising bounds, self-hosted runner.

## Acceptance Criteria
- [ ] All nine children DONE and merged in one PR (user authorizes push/PR/merge).

## Related Tickets
- `TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING` (gap research; this batch takes items it parked)

## Related Docs
- `docs/assets/store_contract.md`, `docs/assets/budgets.md`, `docs/architecture/visual_asset_foundation_adr.md`

## Related Stored Artifacts
- `agent-working/staging_artifacts/TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING/` (`internal_gap_audit.md`, `research_asset_pipeline.md`; moved to stored_artifacts by child 9)

## Related Code Areas


## Assumptions / Open Questions


## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

