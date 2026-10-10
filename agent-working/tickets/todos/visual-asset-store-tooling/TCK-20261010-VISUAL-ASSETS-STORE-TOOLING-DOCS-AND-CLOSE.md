---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-STORE-TOOLING-DOCS-AND-CLOSE
phase: open
date: 2026-10-10
tags: [planning]
---

# TCK-20261010-VISUAL-ASSETS-STORE-TOOLING-DOCS-AND-CLOSE

## Title
Docs drift, handoff snapshots, the hardening epic's stranded staging artifacts, and batch close

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Child 9 of `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING`. Also: the hardening epic's research (`internal_gap_audit.md`, `research_asset_pipeline.md`) is still under `agent-working/staging_artifacts/` on main; it belongs in `agent-working/stored_artifacts/`.

## Scope
- Move the two hardening research files to `agent-working/stored_artifacts/TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING/` (git mv, status historical).
- store_contract.md "Not built" list and budgets.md updated for what this batch built; parked list re-stated (LFS, slices/9-slice, client use).
- Refresh `docs/assets/session_handoff/` snapshots from the planner's handover; close the epic.

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art, no `.github/` change.

## Acceptance Criteria
- [ ] No asset doc claims a built item is missing or vice versa (grep proof in the ticket).
- [ ] Staging folder for the hardening epic gone from main; snapshots refreshed; epic closed.

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

