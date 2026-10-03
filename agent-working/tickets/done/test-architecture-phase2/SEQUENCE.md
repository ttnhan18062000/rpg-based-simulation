# Implementation Sequence — test-architecture-phase2

`TCK-20261003-EPIC-TEST-SCALE-OUT-SOCIAL` is the epic-tier parent and is not implemented directly. The four
children below keep their own scope and acceptance criteria. Each child's plan goes to
test-architecture-reviewer for review BEFORE implementation, and one PR carries the whole batch.

Binding for every child (plan §9, owner decision 2026-10-03): no social RPG test file is edited, moved,
marked, deleted or strengthened; party*.py, memory.py, perception and dormant paths are excluded; every
figure is re-measured at the then-current `origin/main` with the full SHA; every report states the
RELATIONSHIP-VECTOR staleness line.

## Order

1. `TCK-20261003-SOCIAL-LANE-ROUTING-CASE-AND-SCENARIO-GAP`  (hotfix, plan item 2; the only test-file change in the batch)
2. `TCK-20261003-SOCIAL-TEST-LOCATE-AND-OWNER-ROUTING`  (standard, plan items 1 and 6; no dependency)
3. `TCK-20261003-SOCIAL-ORACLE-MAP-REPORT`  (standard, plan item 3; no dependency)
4. `TCK-20261003-SOCIAL-APPRAISAL-MUTATION-BASELINE`  (standard, plan item 4; the only long run, so last)

Plan item 5 (workflow observation) has no ticket: it is recorded in the batch review.
