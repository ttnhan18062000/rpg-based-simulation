---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-M1-RECLASSIFY
phase: open
date: 2026-10-04
tags: [architecture, documentation, planning]
---

# TCK-20261004-VISUAL-ASSETS-M1-RECLASSIFY

## Title
Re-derive the `AM-M1` result from the updated register and the `AM-M0` result, align status lines (epic close-out)

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Child 3 (last) of `TCK-20261004-EPIC-VISUAL-ASSET-M1-UNBLOCK`. After the `AM-M0` result (child 1) and the owner
decisions (child 2) land, the register's "Result: `AM-M1` is `BLOCKED`" section is stale. Re-derive it.

## Scope
- `docs/assets/m1_contract_register.md` "Result" section rewritten from the M1 plan's own "Result classification"
  table, against the register as it now stands and the M0 result as recorded. Never reworded to reach a result:
  - If M0 is not `PASS`, M1's `BLOCKED` row still applies on that count; say so.
  - Judge whether the remaining `GAP` rows (expected: `W02.7`, `W06.3`, `W07.4` code follow-ups; `W13.3/4/6` carried
    to `AM-M6`; `W03.1` if child 2 left it `GAP`) keep the "contracts coherent" condition from holding, row by row.
  - Keep the `AM-C01` judgment section; update it only where its inputs changed (the authority map now exists via D13).
  - Rewrite "What would unblock" (or "What remains") to match.
- The register's header line ("the result was added by ...") names this ticket too.
- Dated status update in `docs/plans/visual-asset-management-runtime-integration/README.md` and the status line at the
  top of `01_architecture_decisions_and_contracts_plan.md` (and `00_...` for M0), pointing at the register and the M0
  record.
- `make knowledge-index-update`; `docs/REGISTRY.yaml` regenerated and staged.
- Epic close-out: parent ticket and `SEQUENCE.md` completed, folder moved to `done/` per CLAUDE.md, closure recorded
  with `record_hand_orchestrated_closure.py` for each child (never `--agent <session-name>`).

## Out of Scope
- Any new decision; any change outside `docs/` and `agent-working/`. A `PASS` result authorizes nothing by itself:
  `AM-M2` still needs new authority from the owner.

## Acceptance Criteria
- [ ] The M1 result follows from the register's verdicts, the M0 result and the plan's table (the planner re-derives
  it at review).
- [ ] No doc in the plan package or `docs/assets/` still states the old `BLOCKED` reasons as current
  (`grep -n "BLOCKED\|AM-M0" ` over both folders, output in the ticket).
- [ ] Knowledge index updated; frontmatter valid; `done_checker_static.py` passes for every child.

## Related Tickets
- Parent: TCK-20261004-EPIC-VISUAL-ASSET-M1-UNBLOCK; after M0-RESULT and M1-OWNER-DECISIONS

## Related Docs
- See the parent.

## Related Stored Artifacts
- None.

## Related Code Areas
- None (docs only).

## Assumptions / Open Questions
- The result is not assumed. `PASS` is possible only if M0 passes and every remaining `GAP` is judged not material
  to M1's coherence; otherwise the honest result stands.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
