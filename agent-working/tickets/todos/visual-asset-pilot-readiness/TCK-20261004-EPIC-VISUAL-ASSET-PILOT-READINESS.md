---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261004-EPIC-VISUAL-ASSET-PILOT-READINESS
phase: open
date: 2026-10-04
tags: [architecture, mcp, testing, live-map, planning]
---

# TCK-20261004-EPIC-VISUAL-ASSET-PILOT-READINESS

## Title
Visual assets toward an `AM-M6` pilot: close U-05 doc drift, adopt one real terrain tile, close the `AM-M5` gaps, retention and rollback, rerun M5 and draft the M6 charter

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
The user asked (2026-10-04) to scope U-05 and to plan `AM-M6`/`AM-M7`. Found: U-05 is already decided (every row of
`docs/assets/budgets.md` `APPROVED 2026-10-04`, PR #309); three docs still say "proposed, awaiting owner approval", and
the retention row is deliberately unset. `AM-M6` cannot start: its plan requires `AM-M5` `PASS`, and the isolated M5
rehearsal is `INCONCLUSIVE` (`W03`, `W05`, `W07` `INCONCLUSIVE`; `W09`, `AM-C06`, `AM-C09` `BLOCKED`), and there is no
adopted art and no chosen role. Decided by the user the same day, through a blocking question each: file this batch
(doc drift, real art for one role, M5 gap closure, retention/rollback, M5 rerun and an M6 charter draft); the pilot role
is **a terrain cell**. `AM-M7` stays dormant.

This batch makes `AM-M6` *ready to authorize*. It authorizes no activation, no deployment and no change to the normal
Live Map: activation needs a separate, signed charter (`AM6-W01`) and a new explicit authorization.

## Scope
Tracks the child tickets in `SEQUENCE.md`. No direct implementation.

## Out of Scope
- Executing `AM-M6` (any activation, deployment or change to `GameCanvas.tsx` / `useCanvas.ts`), and all of `AM-M7`.
- Any change to `src/` or simulation truth.
- More than one pilot role or more than one visual key; animation; scale classes other than x1.
- Reopening D2 (`MAX_SOURCE_BYTES`), D8-D10, or any approved budget row other than retention.

## Acceptance Criteria
- [ ] Every child in `SEQUENCE.md` is closed.
- [ ] No doc says U-05 numbers are awaiting approval; retention has an owner-approved value or a stated reason to stay unset.
- [ ] Exactly one real visual key (a terrain tile) is adopted by the user through the CLI gate, built, in a release candidate and in the runtime manifest.
- [ ] The rerun M5 result record classifies every `AM5-W*` deliverable and gate with evidence, never a pass by default.
- [ ] An `AM6-W01` charter draft exists for the user to sign, with every field that needs a human named as such; `AM-M6` and `AM-M7` plan docs carry a dated status note.
- [ ] Boundary tests stay green: no `src/` <-> `visual_assets` import; the normal frontend path does not import `frontend/src/visualAssets`.

## Related Tickets
- TCK-20261003-EPIC-VISUAL-ASSET-HARDENING-AND-REHEARSAL (done; PR #309)
- TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION (done; PR #286, #299)
- Children: TCK-20261004-VISUAL-ASSETS-U05-STATUS-DRIFT, TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE, TCK-20261004-VISUAL-ASSETS-M5-GAP-CLOSURE, TCK-20261004-VISUAL-ASSETS-RETENTION-AND-ROLLBACK, TCK-20261004-VISUAL-ASSETS-M5-RERUN-AND-M6-CHARTER

## Related Docs
- docs/assets/budgets.md, docs/assets/surface_rehearsal_result.md, docs/assets/store_contract.md
- docs/plans/visual-asset-management-runtime-integration/README.md, 05_surface_compatibility_rehearsal_plan.md, 06_bounded_activation_pilot_plan.md, 07_incremental_migration_plan.md
- docs/architecture/visual_asset_foundation_adr.md (D2, D8-D10)
- docs/brainstorm/render-and-art/asset_management_and_runtime_integration_proposal.md (gate table, 9.x)

## Related Stored Artifacts
- None (epic).

## Related Code Areas
- visual_assets/, visual_assets/catalog/, tests/visual_assets/, frontend/src/visualAssets/, docs/assets/

## Assumptions / Open Questions
- Planner recommendation for the exact terrain: **Forest** (tile code 6). It is biome flavour and does not decide walkability
  (Wall, Water would). The user may name another terrain before ticket 2 starts.
- Human decisions this batch will need, each asked through a blocking question when reached (not now): adoption of the
  candidate (ticket 2); the supported-client matrix and the crowded-scene review (ticket 3); retention numbers and the
  rollback owner (ticket 4); signing the charter (ticket 5, and outside this batch).

## Implementation Notes
See `SEQUENCE.md`.

## Test Summary
Per child.

## Files Changed
Per child.

## Completion Summary
Open.
