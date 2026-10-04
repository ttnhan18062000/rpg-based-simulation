---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-M5-RERUN-AND-M6-CHARTER
phase: open
date: 2026-10-04
tags: [planning, live-map, documentation]
---

# TCK-20261004-VISUAL-ASSETS-M5-RERUN-AND-M6-CHARTER

## Title
Rerun and re-record `AM-M5` for the terrain role, draft the `AM6-W01` pilot charter, and date the M6/M7 plan status

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`AM-M6` starts only after M5 `PASS` and a signed charter plus a new authorization. Child 5 (close-out) of
`TCK-20261004-EPIC-VISUAL-ASSET-PILOT-READINESS`.

## Scope
- Rerun every M5 check (tests, local capture per approved client, gc dry run, rollback drill) on one commit and rewrite
  `docs/assets/surface_rehearsal_result.md` as a new dated result (keep the 2026-10-03 result as history): each `AM5-W*`
  and `AM-C05`/`C06`/`C07`/`C09` gets `PASS`/`FAIL`/`BLOCKED`/`INCONCLUSIVE` with evidence. Never a pass by default; a gap
  that remains stays named.
- Draft `docs/assets/pilot_charter_am6.md` (`AM6-W01`): role and key, release and manifest hashes, clients (from ticket
  3), environment, exposure, duration, owners (activation, rollback, recall), predeclared stop thresholds, forbidden
  scope, and the `AM6-W02`..`W09` evidence list. Every field that needs a human is marked `TO BE SIGNED BY OWNER`;
  the agent fills only facts. Status `DRAFT — not an authorization`.
- Dated status notes (2026-10-xx) in `06_bounded_activation_pilot_plan.md` (prerequisites met / not met, charter draft
  link) and `07_incremental_migration_plan.md` (still dormant: needs M6 `PASS` and a disposition), and in the package `README.md`.
- Epic close-out.

## Out of Scope
- Signing the charter, authorizing or executing `AM-M6`, any deployment, any `AM-M7` planning beyond the dated note.

## Acceptance Criteria
- [ ] New M5 result record with a classification and evidence per deliverable and gate, on a named commit.
- [ ] Charter draft exists, marked `DRAFT`, with every human field marked and no field invented.
- [ ] M6, M7 and README status notes dated and consistent with the result record.
- [ ] `make knowledge-index-update` run.

## Related Tickets
- All children of TCK-20261004-EPIC-VISUAL-ASSET-PILOT-READINESS

## Related Docs
- docs/assets/surface_rehearsal_result.md
- docs/plans/visual-asset-management-runtime-integration/05_surface_compatibility_rehearsal_plan.md, 06_bounded_activation_pilot_plan.md, 07_incremental_migration_plan.md, README.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261003-VISUAL-ASSETS-SURFACE-REHEARSAL/

## Related Code Areas
- None new; reruns frontend/src/visualAssets/ and visual_assets/ checks.

## Assumptions / Open Questions
- If M5 is still not `PASS`, the charter draft is still written, with the blocking gates listed at its top.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
