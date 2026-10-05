---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-STICKY-ATTACK-TASK-SURVIVES-OUT-OF-RANGE-AFTER-THE-TARGET-MOVES
artifact_type: plan
tags: [engine, combat]
---

# Plan

1. Measure verdicts (`probes/oor_probe.py`, `measure.sh`) and follow the task (`probes/oor_follow.py`). Done: a held
   `ATTACK` task survived about 851 ticks on `frontier_living_world` (see `investigation.md`).
2. Trace why the held task does not re-dispatch once in reach with readiness 100 (unexplained). Needed before choosing
   between "the reset alone fixes it" and "a second defect sits under it".
3. Implement the reset in `src/engine/pipeline_phases/actions.py`: `OUT_OF_RANGE` against a live target that has left
   reach (judged against `legality.py:284`'s multiplied range) clears the payload like `TARGET_INCAPACITATED`;
   `INSUFFICIENT_READINESS` untouched. Correct the `actions.py:221-230` comment.
4. Tests with a disabling control (target leaves reach: task ends; readiness: task survives; dead target: unchanged).
5. Re-measure with `oor_follow.py` on the same world; update `docs/engine/` and the parity ledger.

Awaiting the planner's confirmation of the revised outcome before step 3: its earlier ruling ("close, no change") was based
on the bounded-streak reading, which the task trace contradicts.
