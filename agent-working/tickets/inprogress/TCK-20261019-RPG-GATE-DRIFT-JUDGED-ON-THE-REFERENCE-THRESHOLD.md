---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-RPG-GATE-DRIFT-JUDGED-ON-THE-REFERENCE-THRESHOLD
phase: inprogress
date: 2026-10-19
tags: [testing, regression, simulation-quality]
---

# TCK-20261019-RPG-GATE-DRIFT-JUDGED-ON-THE-REFERENCE-THRESHOLD

## Title
The rpg gate report judges an outcome row's drift against each reference using the k and floor recorded in that reference, not the candidate run's own.

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
rpg's O2.population floor is relative: `max(3.0, 0.10 * tick-0 population)`. Under the option-2 ruling (TCK-20261019-RPG-GATE-REQUIRED-VALIDITY-PER-LEVEL), rpg's module computes one floor per world from the run set's pooled tick-0 mean.

The designer accepted that on one condition: the floor's base is the **baseline's** pooled tick-0 mean, recorded with the baseline, not recomputed from each candidate. Otherwise a change that moves tick-0 populations (as M2's changed-kind ids did) also moves the threshold it is judged against.

Today `rpg_gate_report._compare` uses `cur_row["floor"]` and `cur_row["k"]`, the candidate's values, while each baseline row already stores its own `k` and `floor` (format doc, "Run outcome rows carry `per_seed`, `mean`, `se` and the row's `k`/`floor`").

**testing-planner ruling, 2026-10-19 (rpg's option (a), applied to every outcome row):**
- The thresholds recorded in a baseline are the thresholds that baseline is judged with.
- A threshold changes only through a re-baseline.
- The module never reads baseline artifacts: rpg's option (b) is refused, because a run's documents must not depend on which baseline happened to be present.

v1 itself is unaffected, because there is no reference. This must land before the first gate run judged against v1.

## Scope
1. **`_compare`:** for each reference (`last` and `milestone-first` separately), judge with the reference row's `k` and `floor`. A reference row with no numeric `floor` (or, for a run row, no numeric `k`) makes that reference `no-data`, reason `contract_error`, detail `reference row has no recorded threshold`. Never fall back to the candidate's values.
2. **Report the move, not an error:** when the candidate's `k`/`floor`/`oracle` differ from the reference row's, the reference result carries `threshold_moved: {k, floor, oracle}` with the candidate's and the reference's values. The markdown shows it on that row. It does not change the state. The within-run-set check (one k/floor/oracle per (world, id, group) across a world's documents) stays a `contract_error`, unchanged.
3. **Candidate (`rpg_gate_candidate.py`):** unchanged. A new baseline records the candidate's own thresholds. Confirm this with a test.
4. **Format doc (`rpg_gate_baseline_format.md`):** add a "Thresholds come from the reference" rule next to the drift rule: a baseline's recorded `k`/`floor` judge it; a relative floor (O2.population) is computed by the module from its own run set and so is fixed once recorded; a moved threshold is reported, not used. Cite this ticket and the designer's condition.
5. **Stub metrics:** if `tests/helpers/rpg_gate_stub_metrics.py` cannot emit a candidate whose floor differs from the baseline's, add a mode (for example `RPG_GATE_STUB_FLOOR_SHIFT`).

## Out of Scope
- rpg's module, and how it computes O2.population's floor.
- Values of any k or floor.
- The re-baseline policy (`baseline_change_policy.md`) beyond citing it.

## Acceptance Criteria
- [ ] AC1: run row: the baseline has floor 3.0, the candidate floor 9.0, and the mean diff is 5.0 with a small se. The result is DRIFT, judged on 3.0, and carries `threshold_moved`. A pooled row behaves the same.
- [ ] AC2: `last` and `milestone-first` with different recorded floors are each judged on their own floor (one case where they disagree on the state).
- [ ] AC3: a reference row with no numeric floor is `no-data`/`contract_error` for that reference only, with no fallback to the candidate's floor.
- [ ] AC4: two documents of one world in the candidate with different floors are still `contract_error` (the regression guard for #663's rule).
- [ ] AC5: the candidate records its own thresholds (unchanged behaviour, now pinned by a test).
- [ ] AC6: the format doc has the rule. rpg-planner confirms on the PR that it meets the designer's condition (comment link).
- [ ] AC7: `tests/simulation_quality/rpg_gate/` and `tests/unit/tools -k rpg_gate` pass.

## Related Tickets
- TCK-20261019-RPG-GATE-REQUIRED-VALIDITY-PER-LEVEL (#663: per-world threshold check; the option-2 floor ruling)
- TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC

## Related Docs
- docs/plans/test_architecture/reference/rpg_gate_baseline_format.md
- docs/plans/test_architecture/reference/baseline_change_policy.md

## Related Stored Artifacts
- agent-working/staging_artifacts/TCK-20261019-RPG-GATE-DRIFT-JUDGED-ON-THE-REFERENCE-THRESHOLD/ (plan, investigation, test_plan)

## Related Code Areas
- tools/test_architecture/rpg_gate_report.py (`_compare`, `_outcome`, markdown rendering)
- tools/test_architecture/rpg_gate_candidate.py (read only, plus a test)
- tests/helpers/rpg_gate_stub_metrics.py
- tests/unit/tools/test_rpg_gate_report.py

## Assumptions / Open Questions
- Every recorded baseline row carries `k`/`floor`; the format doc says it does. If an existing baseline in the repo lacks them, stop and report. Don't backfill.
- Order: after #663 merges, before rpg's first gate run judged against v1. It does not block v1.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
