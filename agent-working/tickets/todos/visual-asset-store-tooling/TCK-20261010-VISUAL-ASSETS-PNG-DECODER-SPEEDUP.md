---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-PNG-DECODER-SPEEDUP
phase: open
date: 2026-10-10
tags: [performance, security, testing]
---

# TCK-20261010-VISUAL-ASSETS-PNG-DECODER-SPEEDUP

## Title
A faster pure-Python PNG decoder and fewer decodes per adopt, with bounds unchanged (F3)

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
Child 2 of `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING`. budgets.md F3: the pure-Python decoder (visual_assets/store/pixels.py) limits the dimension bounds (1024 px Paeth 1.73 s; 2048 px 7.87 s; `adopt` decodes ~3 times). Owner, 2026-10-10: pure Python only, no new dependency.

## Scope
- Speed up `decode_png` row filtering (bytes/memoryview/bytearray techniques, per-filter fast paths) without changing any output: pixel hashes of every committed PNG and every test fixture stay byte-equal (a corpus equality test).
- Cut repeated decodes in `adopt`/`review` (decode once per command, pass pixels on).
- Keep every existing safety bound (decompression bound, dimension checks); malformed-input tests still refuse identically.
- Re-measure the budgets.md operation table with the same method; record before/after.

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art, no `.github/` change.
- Raising MAX_DIM / MAX_PREVIEW_DIM (a separate owner call after measurement). Any native or third-party decoder.

## Acceptance Criteria
- [ ] Pixel-hash equality over the full committed PNG corpus + fixtures.
- [ ] Malformed/oversized input tests refuse as before.
- [ ] budgets.md table re-measured, F3 updated with the new numbers (bounds unchanged).
- [ ] Security review clean (parser of untrusted input).

## Related Tickets
- Parent: `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING`
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

