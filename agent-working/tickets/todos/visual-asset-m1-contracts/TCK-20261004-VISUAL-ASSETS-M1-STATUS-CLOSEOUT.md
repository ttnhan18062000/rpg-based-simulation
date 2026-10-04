---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-M1-STATUS-CLOSEOUT
phase: open
date: 2026-10-04
tags: [architecture, documentation, planning]
---

# TCK-20261004-VISUAL-ASSETS-M1-STATUS-CLOSEOUT

## Title
Record the `AM-M1` result from the register and bring the plan-package status lines in line with it (epic close-out)

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Child 4 (last) of `TCK-20261004-EPIC-VISUAL-ASSET-M1-CONTRACTS`. The plan package still says `AM1-W01`, `W08` and
others are open although they are decided. Once the register and the two charters exist, write the M1 result and fix
the status text everywhere it is stated.

## Scope
- `AM-M1` result in `docs/assets/m1_contract_register.md` (a "Result" section at the top): `PASS` / `INCONCLUSIVE` /
  `BLOCKED` per the plan's own "Result classification" table, with the reasons and the short list of what would
  close it. Never reworded to pass; `AM-C01` judged on its own clause.
- New dated "Status update" section in `docs/plans/visual-asset-management-runtime-integration/README.md` and a status
  line at the top of `01_architecture_decisions_and_contracts_plan.md`, both pointing at the register.
- `docs/assets/store_contract.md` "Decisions still open" and `docs/plans/visual-asset-foundation/README.md` "open" row
  (`AM1-W01`, `W03`, ...) updated to match the register.
- Added at the ticket-1 review (planner, 2026-10-04), from the register's "Where docs and code disagree" table:
  - `docs/assets/store_contract.md` "Decisions still open" / "Not built" and its budgets line ("the one deliberately
    unset row"): match ADR D8-D10, `budgets.md` and the register.
  - `docs/architecture/visual_asset_foundation_adr.md` Status and Consequences: the store writers are built; `U-02`,
    `AM1-W01` and `AM1-W08` are decided (D8-D10). Status text only; no decision row changes.
  - `docs/assets/pilot_charter_am6.md` **section 2 (agent-filled facts) only**: `pilot/rc-0003`, three slots, the detail
    axis (D11). Sections 3 (human fields) and 5 (signature) are not touched.
  - Remove each fixed line from the register's disagreement table (or mark it "fixed by M1-STATUS-CLOSEOUT").
- `make knowledge-index-update` (worktree: `PYTHON_KNOWLEDGE=/home/vboxuser/Work/rpg-based-simulation/.venv-knowledge/bin/python3`);
  `docs/REGISTRY.yaml` regenerated and staged.
- Epic close-out: parent ticket and `SEQUENCE.md` completed, folder moved to `done/` per CLAUDE.md.

## Out of Scope
- Any new decision; any change outside `docs/` and `agent-working/`.

## Acceptance Criteria
- [ ] The M1 result follows from the register's verdicts and the plan's table (the planner re-derives it at review).
- [ ] No doc in the plan package or `docs/assets/` still calls a `MET` item open or a `GAP` item done
  (`grep -n "AM1-W"` over both folders, output in the ticket).
- [ ] Knowledge index updated; frontmatter valid; done-checker static passes for every child.

## Related Tickets
- Parent: TCK-20261004-EPIC-VISUAL-ASSET-M1-CONTRACTS; after M2-EVIDENCE-CHARTER

## Related Docs
- See the parent.

## Related Stored Artifacts
- None.

## Related Code Areas
- None (docs only).

## Assumptions / Open Questions
- Expected result: `INCONCLUSIVE` (W03/W07/W13 gaps, W06/W11 not owner-approved unless approved at review).

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(open)
