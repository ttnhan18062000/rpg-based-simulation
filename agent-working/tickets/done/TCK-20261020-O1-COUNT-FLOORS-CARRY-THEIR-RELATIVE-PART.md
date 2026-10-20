---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261020-O1-COUNT-FLOORS-CARRY-THEIR-RELATIVE-PART
phase: done
date: 2026-10-20
tags: []
---

# TCK-20261020-O1-COUNT-FLOORS-CARRY-THEIR-RELATIVE-PART

## Title
The O1.starved and O1.at_risk run rows carry floor_rel next to their base floor

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
Designer ruling (a), 2026-10-20: the two O1 count rows are judged as counts with floor max(3, 0.10 x the run set's per-seed mean). The module has no baseline, so it emits the base (`floor` 3.0) and the relative part (`floor_rel` 0.10) on these two rows only; testing's candidate records the computed floor at baseline time and keeps floor_base and floor_rel for audit.

## Scope
- `src/observability/rpg_gate_metrics.py`: `floor_rel: 0.10` on O1.starved and O1.at_risk run rows; the thresholds comment states it.
- A unit test: those two rows carry floor_rel 0.10 and floor 3.0, no other row carries floor_rel.

## Out of Scope
- The candidate's computation of the floor (testing's).

## Acceptance Criteria
- Only the two rows carry `floor_rel`; the final state hash is unchanged (observer code).

## Related Tickets
- TCK-20261020-RPG-GATE-ROWS-COME-FROM-DECLARED-DOMAINS

## Related Docs
- none

## Related Stored Artifacts
- none

## Related Code Areas
- src/observability/rpg_gate_metrics.py

## Assumptions / Open Questions
- The field name `floor_rel` is confirmed with testing in the PR body (their candidate reads it).

## Implementation Notes
Observer code only.

## Test Summary
tests/unit/observability/test_rpg_gate_metrics.py: 31 passed (adds the floor_rel test). mypy gate 0; `import_contracts ci` 17 kept, 0 broken; code-health 0 new. Light checks only (a quiet-host tripwire was running).

## Files Changed
src/observability/rpg_gate_metrics.py, tests/unit/observability/test_rpg_gate_metrics.py

## Completion Summary
Built and closed in the same PR.
