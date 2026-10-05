---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-STICKY-ATTACK-TASK-SURVIVES-OUT-OF-RANGE-AFTER-THE-TARGET-MOVES
artifact_type: plan
tags: [engine, combat]
---

# Plan (final)

1. Measure verdicts (`probes/oor_probe.py`, `measure.sh`) and follow the task (`probes/oor_follow.py`). Done: a held `ATTACK` task
   survived about 851 ticks on `frontier_living_world`.
2. Trace why it did not re-dispatch (`probes/posture_check.py`). Done: the action router's combat-posture gate returned a bare no-op
   after the posture flipped to `avoid`; the `OUT_OF_RANGE` at t157 was legitimate.
3. Per the planner: close this ticket as a measured non-defect for its own premise; no `OUT_OF_RANGE` reset; leave the
   `actions.py:221-230` comment alone. The real defect is fixed under
   `TCK-20261005-SILENT-NO-OP-RETURNS-IN-ACTIONROUTER-HOLD-THE-TASK-AND-ANNOTATE-FALSE-SUCCESS`.
