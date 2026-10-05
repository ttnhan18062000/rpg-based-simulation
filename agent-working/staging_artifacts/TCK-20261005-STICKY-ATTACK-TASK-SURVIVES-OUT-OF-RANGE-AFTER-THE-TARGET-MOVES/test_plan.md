---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-STICKY-ATTACK-TASK-SURVIVES-OUT-OF-RANGE-AFTER-THE-TARGET-MOVES
artifact_type: test_plan
tags: [engine, combat]
---

# Test plan

House style: tests with a disabling control (with the new condition disabled, exactly the "task ends when the target leaves
reach" tests fail and every "must not change" test passes).

- Target moves out of reach after an `OUT_OF_RANGE` failure: the task ends and the entity re-decides.
- `INSUFFICIENT_READINESS` at the same range: the task survives, unchanged.
- Target dies: the `TARGET_INCAPACITATED` reset is unchanged.
- Reach is judged against the multiplied range: a weather multiplier that shrinks reach must not leave a sticky task.
- Instrument: `oor_follow.py` reproduces the 851-tick hold before the change (positive control) and shows the task ending after.
- Regression scope: the `actions.py` / tactical / legality test dirs plus the registry and frontmatter tests.
