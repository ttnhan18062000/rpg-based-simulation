---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-RETENTION-AND-ROLLBACK
phase: open
date: 2026-10-04
tags: [mcp, testing, architecture]
---

# TCK-20261004-VISUAL-ASSETS-RETENTION-AND-ROLLBACK

## Title
Retention numbers, `gc` with rollback and client roots, and an old-client / new-release rollback drill

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`AM5-W09` and `AM-C09` are `BLOCKED` (no rollback roots, no client roots, retention unset) and `AM-C06` is `BLOCKED`
(no retained previous release, no rollback authority, no old client). The retention row is the last unset U-05 row.
Child 4 of `TCK-20261004-EPIC-VISUAL-ASSET-PILOT-READINESS`.

## Scope
- Retention: measure what exists (store size with the real key and fixtures; growth per adopt/release) and propose
  values for the unset row in `docs/assets/budgets.md` (age-based quarantine and review clean-up), with the same rule
  set (R0-R4). **Ask the user to approve** (blocking question); flip the row to `APPROVED <date>` only after.
- `gc` roots: extend `gc` (dry run first) so the current release candidate, the previous one (rollback root), every
  release a supported client may still hold, in-flight intake/review work and evidence pins are protected. Test with
  M4-style records (the real adoption from ticket 2) that no protected object is removed and an unreferenced one is.
- Rollback under Profile A (D8): rollback is redeploying the previous whole frontend release. Retain a previous release
  fixture (the synthetic release from PR #309) and the new one (with the real key); in the harness, drill: new client +
  old release, old client + new release, release with the key removed (recall). Each must render the role or its
  fallback, never a mixed snapshot.
- Name the rollback/recall owner as a field the user fills (ask, do not assume).

## Out of Scope
- A real deployment or any CI/CD change; the normal Live Map; `src/`.
- Signing (D9 stands).

## Acceptance Criteria
- [ ] Retention row approved by the user, or kept `UNSET` with a new stated reason the user accepted.
- [ ] `gc` tests: each root kind protects its objects (mutant: drop the root kind, test fails); dry run is the default.
- [ ] Rollback drill tests for the three combinations pass in the harness; mutant "accept a mixed snapshot" fails.
- [ ] The rollback/recall owner is recorded as the user's answer, or left explicitly unnamed.
- [ ] `tests/visual_assets/` (scoped, 2 GB cap) and frontend tests pass; boundary/isolation tests green.

## Related Tickets
- TCK-20261003-VISUAL-ASSETS-BUDGETS (done), TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE

## Related Docs
- docs/assets/budgets.md, docs/assets/store_contract.md (gc), docs/assets/surface_rehearsal_result.md (W09, C06, C09)
- docs/architecture/visual_asset_foundation_adr.md (D8, D9)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261003-VISUAL-ASSETS-BUDGETS/

## Related Code Areas
- visual_assets/store/ (gc, release), tests/visual_assets/, frontend/src/visualAssets/

## Assumptions / Open Questions
- "Supported client may still hold" uses the matrix from ticket 3; if ticket 3's matrix is not approved yet, use the
  two releases only and say so.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
