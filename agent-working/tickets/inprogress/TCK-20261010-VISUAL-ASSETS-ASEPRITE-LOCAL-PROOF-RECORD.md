---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-ASEPRITE-LOCAL-PROOF-RECORD
phase: open
date: 2026-10-10
tags: [testing, determinism]
---

# TCK-20261010-VISUAL-ASSETS-ASEPRITE-LOCAL-PROOF-RECORD

## Title
A committed local real-Aseprite proof record and a CI check that it is not stale (D10 kept)

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 4 of `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING`. ADR D10 keeps real Aseprite off CI and shared machines; CI only states the skip count (tools/ci_aseprite_skip_line.py). Owner, 2026-10-10: keep D10; add a committed local proof record that CI checks.

## Scope
- **Design first (planner approves the guarded-path list and record shape).** `make visual-assets-aseprite-local` (strict, refuses to skip) writes a committed proof record: Aseprite version, commit, a content hash over the guarded paths (the code the `needs_aseprite` tests exercise: drawing tools, store build/exporter, those tests), pass/skip/fail counts, child 3's rc rebuild verdict.
- A CI-run test (no Aseprite) recomputes the guarded-path hash and fails when it differs from the record (message names the make target). The proof record excludes itself from the hash.
- `ci_aseprite_skip_line.py` summary line also states the proof record's commit and freshness.
- ADR: a D10 addendum (owner approves text) describing the proof record; D10's decision is unchanged.

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art, no `.github/` change.
- A self-hosted runner (owner declined, 2026-10-10).

## Acceptance Criteria
- [ ] Guarded-path list and record shape approved by the planner; D10 addendum text by the owner.
- [ ] CI test fails on a changed guarded file and passes after a fresh local run (mutation proof).
- [ ] First record committed from a real local run.

## Related Tickets
- Parent: `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING`
- `TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING` (gap research; this batch takes items it parked)

## Related Docs
- `docs/assets/store_contract.md`, `docs/assets/budgets.md`, `docs/architecture/visual_asset_foundation_adr.md`

## Related Stored Artifacts
- `agent-working/staging_artifacts/TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING/` (`internal_gap_audit.md`, `research_asset_pipeline.md`; moved to stored_artifacts by child 9)

## Related Code Areas


## Assumptions / Open Questions
- Depends on child 3 (rebuild verdict field).

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

