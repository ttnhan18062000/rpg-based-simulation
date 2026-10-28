---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261020-POOLED-OUTCOME-ROWS-DECLARE-SHARE-OR-COUNT
phase: open
date: 2026-10-20
tags: [observability]
---

# TCK-20261020-POOLED-OUTCOME-ROWS-DECLARE-SHARE-OR-COUNT

## Title
Every pooled outcome row declares `aggregate: "share" | "count"`, and share rows must carry numerator and denominator

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
testing-implementer is building TCK-20261020-RPG-GATE-POOLED-SHARE-CHECKED-AGAINST-ITS-COUNT-ROWS: a pooled share's numerator and denominator must name run rows present on every seed, `empty_denominator` must mean Σden == 0, and a defined value must equal Σnum/Σden. It asked how the report can tell a share from another pooled outcome row. Today there are exactly two pooled outcome ids (v1 gate run 39393296888): O1.starvation_share, a share with numerator/denominator, and O2.seeds_with_survivors, a pooled count. The only marker is whether the fields are present. That means a share that drops its fields by mistake would go unchecked, the same kind of blindness as V1/V4. For now testing checks only rows that carry the fields (rpg-planner, 2026-10-20).

## Scope
- In `src/observability/rpg_gate_metrics.py`, every pooled outcome row carries `aggregate: "share"` or `aggregate: "count"`. Share rows must carry numerator and denominator; count rows must not.
- Unit test: every pooled outcome row has `aggregate`, and every share has both fields naming rows in the same document.
- Tell testing-planner and testing-implementer the field name before merge, so the format doc and the report check can make absence a contract_error at the same time.

## Out of Scope
- Any change to values, k or floor.

## Acceptance Criteria
- Every pooled outcome row declares `aggregate`.
- The simulation is unchanged (observer only).
- Testing confirms its check reads the field.

## Related Tickets
- TCK-20261020-RPG-GATE-POOLED-SHARE-CHECKED-AGAINST-ITS-COUNT-ROWS (testing)
- TCK-20261020-RPG-GATE-ROWS-COME-FROM-DECLARED-DOMAINS

## Related Docs
- the rpg gate format doc ("Shares")

## Related Stored Artifacts
- none

## Related Code Areas
- src/observability/rpg_gate_metrics.py

## Assumptions / Open Questions
- The harness hash moves (module source). Fine after v1.

## Implementation Notes
After v1.

## Test Summary

## Files Changed

## Completion Summary
