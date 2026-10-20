---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261020-RPG-GATE-CANDIDATE-RECORDS-A-RELATIVE-FLOOR
phase: open
date: 2026-10-20
tags: [testing, regression, simulation-quality]
---

# TCK-20261020-RPG-GATE-CANDIDATE-RECORDS-A-RELATIVE-FLOOR

## Title
A run outcome row may carry `floor_rel`. The candidate records `floor = max(floor, floor_rel × mean of the run set's per-seed values)`, keeping `floor_base` and `floor_rel`, and the report's threshold-moved check compares base and rel, not the computed floor.

## Status
BLOCKED

## Tier
hotfix

## Type
feature

## Priority
P1

## Request Summary
testing-planner's post-merge review of #682 (2523cd118), 2026-10-20: `rpg_gate_metrics.py` OUTCOME_THRESHOLDS gives O1.starved and O1.at_risk "floor max(3, 0.10 × the v1 pooled per-seed mean): the base 3 is here, the relative part is the report's." Nothing in the report or the candidate applies a relative floor, so v1 would record 3.0.

A seed document cannot carry the relative part, because it needs the other seeds' outcomes. So the candidate fixes it once, from the run set it records, and the baseline keeps it. This keeps the #666 rule: thresholds come from the reference, and the module never reads a baseline.

**BLOCKED** on rpg-designer choosing option (a), asked through rpg-planner on 2026-10-20. If the designer picks (b), recording 3.0 now, close this ticket as not needed and record the ruling.

## Scope
1. **Contract** (format doc, next to "Thresholds come from the reference"): a run outcome row may carry a numeric `floor_rel` (0 < r ≤ 1). The candidate records:
   - `floor = max(floor, floor_rel × mean(per_seed))`,
   - `floor_base` (the document's floor),
   - `floor_rel`.
   A pooled row with `floor_rel` is a contract_error, as is `floor_rel` outside (0, 1].
2. **Candidate:** as above. The within-world check (one k/floor/oracle per (world, id, group)) also covers `floor_rel`.
3. **Report:**
   - Judging uses the reference row's recorded `floor` (unchanged).
   - `threshold_moved` compares `k`, `oracle`, and `floor_base`/`floor_rel` when the reference has them (else `floor`), against the candidate documents' `floor`/`floor_rel`. A relative floor alone must not show as moved.
   - A reference row with `floor_rel` but no numeric `floor` is the existing "no recorded threshold" contract_error.
4. **Baseline lint:** `floor_base` and `floor_rel` are optional and numeric. If `floor_rel` is present, `floor_base` is required and `floor >= floor_base`.
5. Do not edit the harness files (the hash).

## Out of Scope
- rpg's module field (rpg Lane B emits `floor_rel: 0.10` on O1.starved and O1.at_risk).
- Any value of k or floor.

## Acceptance Criteria
- [ ] AC1: candidate: per-seed values [40, 50, 60] with floor 3 and floor_rel 0.10 record floor 5.0, floor_base 3, floor_rel 0.10. [5, 5, 5] records floor 3.0.
- [ ] AC2: report: a candidate whose documents match the reference's floor_base/floor_rel shows no threshold_moved, even though the computed floors differ. A changed floor_rel shows as moved.
- [ ] AC3: the contract_error cases in Scope 1, 2 and 4 are each tested.
- [ ] AC4: the format doc states the rule. rpg-planner confirms on the PR that it meets the designer's ruling (comment link).
- [ ] AC5: the harness files are unchanged. `tests/unit/tools -k rpg_gate` and `tests/simulation_quality/rpg_gate/` pass, and CI is green.

## Related Tickets
- TCK-20261019-RPG-GATE-DRIFT-JUDGED-ON-THE-REFERENCE-THRESHOLD (#666)
- TCK-20261020-RPG-GATE-RUN-ROW-SET-IS-DECLARED-NOT-OBSERVED (#680)
- rpg: TCK-20261020-RPG-GATE-ROWS-COME-FROM-DECLARED-DOMAINS (#682)

## Related Docs
- docs/plans/test_architecture/reference/rpg_gate_baseline_format.md

## Related Stored Artifacts
- (none)

## Related Code Areas
- tools/test_architecture/rpg_gate_candidate.py, rpg_gate_report.py, rpg_gate_baseline.py (lint)
- tests/unit/tools/test_rpg_gate_candidate.py, test_rpg_gate_report.py, test_rpg_gate_baseline.py

## Assumptions / Open Questions
- Order: after #680 merges (same files), before the v1 gate dispatch.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
