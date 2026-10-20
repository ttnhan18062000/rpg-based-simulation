---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261020-RPG-GATE-POOLED-SHARE-CHECKED-AGAINST-ITS-COUNT-ROWS
phase: open
date: 2026-10-20
tags: [testing, regression, simulation-quality]
---

# TCK-20261020-RPG-GATE-POOLED-SHARE-CHECKED-AGAINST-ITS-COUNT-ROWS

## Title
The rpg gate report checks each pooled share against the numerator and denominator count rows it names. A share marked undefined while its denominator is non-zero, or a defined share that is not Σnum/Σden, is a `contract_error`.

## Status
OPEN

## Tier
hotfix

## Type
feature

## Priority
P3

## Request Summary
#680 (TCK-20261020-RPG-GATE-RUN-ROW-SET-IS-DECLARED-NOT-OBSERVED) accepts a pooled share row with `value: null, reason: "empty_denominator"` on the module's word. A module bug could then turn a share into quiet no-data.

rpg-planner agreed, 2026-10-20: Lane B adds `numerator:` and `denominator:` (run row ids) to every pooled share row in the combined pre-v1 PR, with a unit test that both name rows in the same document.

**UNBLOCKED 2026-10-20:** #682 is on main, and `rpg_gate_metrics.pool` emits `numerator: "O1.starved"` and `denominator: "O1.at_risk"` on O1.starvation_share. Not a v1 blocker. The report is not in the harness hash.

## Scope
1. Report: for each pooled outcome row that carries `numerator`/`denominator`, find those run rows (same world, group and key) in every seed document.
   - The named row is missing on a seed: `contract_error` "share names <id>, absent from seed(s) [..]".
   - `empty_denominator` while Σden over the seeds > 0: `contract_error` "share marked undefined but its denominator sums to <n>".
   - Defined value ≠ Σnum/Σden (abs tol 1e-9): `contract_error` "share value <v> != Σnum/Σden <w>".
   - A pooled share row without the two fields: decide with rpg whether every share must carry them. If yes, missing fields are a contract_error. Record the answer in the format doc.
2. Format doc: add this to the "Shares" subsection.
3. Do not edit the harness files (the hash).

## Out of Scope
- rpg's module; which rows are shares.

## Acceptance Criteria
- [ ] AC1: each failure mode in Scope 1 has a test, and a consistent share passes untouched.
- [ ] AC2: a report re-run on rpg's v1 documents gives 0 of these contract_errors (quote it).
- [ ] AC3: the harness files are unchanged, and CI is green.

## Related Tickets
- TCK-20261020-RPG-GATE-RUN-ROW-SET-IS-DECLARED-NOT-OBSERVED (#680)
- rpg: TCK-20261020-RPG-GATE-ROWS-COME-FROM-DECLARED-DOMAINS

## Related Docs
- docs/plans/test_architecture/reference/rpg_gate_baseline_format.md ("Shares")

## Related Stored Artifacts
- (none)

## Related Code Areas
- tools/test_architecture/rpg_gate_report.py, tests/unit/tools/test_rpg_gate_report.py

## Assumptions / Open Questions
- The pooled document's shares are computed by rpg's pool() from the same seed documents, so an exact Σ/Σ match is expected. If floats differ by more than the tolerance, ask rpg before widening it.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
