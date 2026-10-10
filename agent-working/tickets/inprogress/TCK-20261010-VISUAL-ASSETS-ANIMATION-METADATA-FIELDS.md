---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS
phase: open
date: 2026-10-10
tags: [architecture, testing]
---

# TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS

## Title
Animation metadata in the handoff and artifact records, after a registry budget review

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Child 7 of `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING`. store_contract.md:226: per-frame durations, tag ranges and loop modes are not in the handoff package nor checked by intake. budgets.md standing rule: any new per-key registry field needs a `MAX_REGISTRY_BYTES` review first (realistic max 414942 B = 90%).

## Scope
- **Design first (planner approves where the fields live).** Default: per-artifact/handoff fields (frame durations ms, tags with from/to/direction, loop mode), validated at intake against Aseprite's own data; **no** per-key registry field. If the design needs a registry field, the budget review comes first and the owner approves any new bound.
- Intake checks (durations > 0, tag ranges inside frame_count, bounded counts), contract records, export carries them through to the runtime export.
- store_contract.md, budgets.md.

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art, no `.github/` change.
- Raising MAX_SOURCE_BYTES / MAX_FRAMES (reopened only when real animated art exceeds them, budgets.md:46). Slices, 9-slice, pivots. Client playback.

## Acceptance Criteria
- [ ] Placement approved by the planner; budget review recorded if any registry growth.
- [ ] Intake refuses each planted bad case; a 4-frame fixture round-trips to the runtime export.

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

