---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261020-RPG-GATE-POOLED-SHARE-CHECKED-AGAINST-ITS-COUNT-ROWS
phase: done
date: 2026-10-20
tags: [testing, regression, simulation-quality]
---

# TCK-20261020-RPG-GATE-POOLED-SHARE-CHECKED-AGAINST-ITS-COUNT-ROWS

## Title
The rpg gate report checks each pooled share against the numerator and denominator count rows it names. A share marked undefined while its denominator is non-zero, or a defined share that is not Σnum/Σden, is a `contract_error`.

## Status
DONE

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
- [x] AC1: each failure mode in Scope 1 has a test, and a consistent share passes untouched.
- [x] AC2: a report re-run on rpg's v1 documents gives 0 of these contract_errors (quote it).
- [x] AC3: the harness files are unchanged, and CI is green.

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
- Report: `_share_problem(row, seed_docs)` runs for every pooled outcome row before it is judged. A row carrying `numerator`/`denominator` is re-derived from the seed documents with data (rows of the same group, no key): absent row, `empty_denominator` with Σden > 0, defined value != Σnum/Σden (1e-9), or a defined value over Σden = 0 each give a `contract_error` with the ticket's wording.
- Open question answered (rpg-planner, 2026-10-20): pooled non-share rows exist (`O2.seeds_with_survivors`, a pooled count), so field presence is the only marker and absence is NOT an error today. rpg will add `aggregate: "share" | "count"` on every pooled outcome row after v1 and send the field name; the check then makes absence a contract_error. Recorded in the format doc.
- AC2: report re-run (`--no-rerun`) on run 39393296888's documents (3 worlds, 33 documents): 0 contract_errors of any kind; the 6 O1.starvation_share rows (one per world/group) pass the check (no-data only because no baseline exists yet).
- Harness files untouched (empty diff).

## Test Summary
tests/unit/tools -k rpg_gate: 201 passed. 9 new report tests: a consistent share passes, a consistent empty-denominator share stays empty_denominator, absent row (named seeds), row no seed has, undefined with Σden > 0, wrong ratio, within-tolerance pass, defined over zero denominator, a pooled row without the fields is not checked. CI read from the PR.

## Files Changed
- tools/test_architecture/rpg_gate_report.py
- tests/unit/tools/test_rpg_gate_report.py
- docs/plans/test_architecture/reference/rpg_gate_baseline_format.md ("Shares")

## Completion Summary
The report re-derives every pooled share that names its count rows and refuses a share its own rows contradict. Absence of the fields stays unchecked until rpg adds the aggregate marker.
