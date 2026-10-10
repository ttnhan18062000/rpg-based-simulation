---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-RUNTIME-ATLAS-EXPORT
phase: open
date: 2026-10-10
tags: [architecture, determinism, testing]
---

# TCK-20261010-VISUAL-ASSETS-RUNTIME-ATLAS-EXPORT

## Title
Optional per-set sprite atlases in the runtime export (deterministic packing, extrude and padding), not wired

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Child 5 of `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING`. store_contract.md:204 lists atlases as not built. The client and harness draw with Canvas 2D (borderRender.ts, GameCanvas.tsx), so atlases are an export option with no consumer yet (owner chose to build it anyway, 2026-10-10).

## Scope
- An opt-in export flag producing one atlas PNG per set (terrain, icons, masks) plus an atlas JSON (key -> rect) next to the unchanged per-file runtime export; the runtime manifest stays as is.
- Deterministic packing (sorted by key, fixed shelf/grid), 1 px extrude + padding against seams; atlas PNG written by one deterministic encoder (no time/text chunks; same input -> same bytes, tested).
- Verify: each atlas rect's pixels equal the source artifact's pixels (pixel-hash check per key).
- store_contract.md section; budgets row for atlas size.

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art, no `.github/` change.
- Client loading from atlases (activation). Changing the runtime manifest schema.

## Acceptance Criteria
- [ ] Rect pixel equality for every key of rc-0008; export-twice byte equality.
- [ ] Extrude/padding tested at edges; atlas JSON schema documented.

## Related Tickets
- Parent: `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING`
- `TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING` (gap research; this batch takes items it parked)

## Related Docs
- `docs/assets/store_contract.md`, `docs/assets/budgets.md`, `docs/architecture/visual_asset_foundation_adr.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING/` (`internal_gap_audit.md`, `research_asset_pipeline.md`; moved to stored_artifacts by child 9)

## Related Code Areas


## Assumptions / Open Questions
- After child 3 (shares the determinism checks).

## Implementation Notes
See staging plan/investigation. `MAX_ATLAS_DIM` 1024 is a new bound: budgets row PROPOSED, the owner decides.


## Test Summary
17 new tests pass; store, boundaries and budgets parity 1335 passed.


## Files Changed


## Completion Summary

