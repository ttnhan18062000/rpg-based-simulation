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
INPROGRESS

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
- `agent-working/stored_artifacts/TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING/` (`internal_gap_audit.md`, `research_asset_pipeline.md`; moved to stored_artifacts by child 9)

## Related Code Areas


## Assumptions / Open Questions


## Implementation Notes
Per-channel slice unfilter plus a 4-entry decode memo in `visual_assets/store/pixels.py`; bounds unchanged; budgets.md F3 re-measured (2x on the worst filter). See staging `plan.md`, `investigation.md`, `test_plan.md`.


## Test Summary
`tests/visual_assets` full tree 2133 passed before the final memo hardening; store + boundaries + budgets parity 1314 after it. New `test_pixels_unfilter.py` (reference-equality over random rows and every committed PNG, memo). 6 mutants: 5 killed, 1 equivalent (Paeth tie). Security review: CLEAN; applied bytes() coercion, no caching above the decoded-size bound, autouse memo reset.


## Files Changed
- `docs/architecture/visual_asset_foundation_adr.md`
- `docs/assets/budgets.md`
- `tests/visual_assets/store/unit/conftest.py`
- `tests/visual_assets/store/unit/test_pixels.py`
- `tests/visual_assets/store/unit/test_pixels_unfilter.py`
- `tests/visual_assets/test_no_ignored_files.py`
- `visual_assets/store/pixels.py`

## Completion Summary
The pure-Python PNG decoder unfilters rows per channel and decodes a preview once (a bounded memo), with every bound unchanged and no new dependency. Pixel hashes are identical to a reference over random rows and every committed PNG; malformed and oversized input is refused as before; `budgets.md` F3 is re-measured. The security review was CLEAN (bytes() coercion, no caching above the decoded-size bound, test-reset of the memo).
