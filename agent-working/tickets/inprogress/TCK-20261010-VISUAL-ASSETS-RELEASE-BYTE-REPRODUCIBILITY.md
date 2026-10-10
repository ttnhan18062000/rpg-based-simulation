---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-RELEASE-BYTE-REPRODUCIBILITY
phase: open
date: 2026-10-10
tags: [determinism, testing]
---

# TCK-20261010-VISUAL-ASSETS-RELEASE-BYTE-REPRODUCIBILITY

## Title
Prove a release candidate rebuilds to identical bytes (local real-Aseprite test + CI export test)

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 3 of `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING`. Today a rebuild with different pixels is refused (exporter.py:131) but file bytes are never compared; artifact identity is the pixel hash, `png_hash` is informational (contracts/artifact.py:34). No test rebuilds a real rc.

## Scope
- A `needs_aseprite` test (local strict target only, D10) that rebuilds every artifact of the current release candidate (`pilot/rc-0008`, 70 entries) from its stored source in a temp store and compares file bytes **and** pixel hash with the stored artifact; reports per-entry diffs.
- A CI-runnable test: runtime export of the stored rc twice into two dirs gives identical bytes (directory hash), and no exported PNG carries tIME/tEXt/iTXt/zTXt chunks (chunk allowlist: IHDR, PLTE, tRNS, sRGB, gAMA, IDAT, IEND).
- If bytes differ while pixels match, record it (Aseprite version drift) rather than fail silently; the design of that verdict is approved by the planner.

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art, no `.github/` change.
- Re-encoding stored artifacts. Aligning the review/test encoders' zlib levels (not shipped bytes).

## Acceptance Criteria
- [ ] Local rebuild test passes on rc-0008 (run recorded in the ticket with Aseprite version).
- [ ] CI export-twice + chunk-allowlist test passes and fails on a planted tIME chunk.

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
Test-only: `tests/visual_assets/test_release_byte_reproducibility.py` plus a store_contract.md section. Local run recorded 2026-10-10T05:27Z at 11ace7957, Aseprite 1.3.18.6: rc-0008 70 of 70 IDENTICAL, 10 passed under strict mode. Byte-drift verdict: pass with a warning naming entries and the Aseprite version (planner to confirm).


## Test Summary
10 passed (2 needs_aseprite, 8 CI-runnable); fails on planted tIME/tEXt/iTXt/zTXt.


## Files Changed


## Completion Summary

