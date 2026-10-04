---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-U05-STATUS-DRIFT
phase: open
date: 2026-10-04
tags: [documentation, mcp]
---

# TCK-20261004-VISUAL-ASSETS-U05-STATUS-DRIFT

## Title
Docs still say the U-05 budget numbers await owner approval; they were approved on 2026-10-04

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Every row of `docs/assets/budgets.md` is `APPROVED 2026-10-04` (blocking question on PR #309), but three docs written
before the approval still say `PROPOSED` / "awaiting owner approval". Child 1 of
`TCK-20261004-EPIC-VISUAL-ASSET-PILOT-READINESS`.

## Scope
Update the stale sentences, nothing else:
- `docs/plans/visual-asset-management-runtime-integration/README.md`, "Status update 2026-10-03 (hardening and isolated rehearsal)":
  "budgets are measured and `PROPOSED` (... awaiting owner approval)". Add the approval as a dated note; do not rewrite the dated paragraph's history.
- `docs/assets/store_contract.md` (around line 175): "numeric budgets (`U-05`: proposed, awaiting owner approval, ...)".
- `docs/plans/aseprite-mcp-pixel-art/README.md` lines 20 and 34: `U-05` listed as still open / "every row `PROPOSED`".
Each now says: approved 2026-10-04, see `docs/assets/budgets.md`; retention is the one deliberately unset row (ticket 4 of this batch).
Grep `docs/` and `visual_assets/` once more for `awaiting owner approval` and `PROPOSED` tied to U-05 and fix any other hit.

## Out of Scope
- Any number in `budgets.md` or in code; the retention row (ticket 4).

## Acceptance Criteria
- [ ] No doc outside `budgets.md`'s own history sentence says the U-05 numbers are proposed or awaiting approval.
- [ ] `tests/visual_assets/test_budgets_parity.py` still passes.
- [ ] `make knowledge-index-update` run (docs changed).

## Related Tickets
- TCK-20261003-VISUAL-ASSETS-BUDGETS (done)

## Related Docs
- docs/assets/budgets.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261003-VISUAL-ASSETS-BUDGETS/

## Related Code Areas
- None (docs only).

## Assumptions / Open Questions
- None.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
