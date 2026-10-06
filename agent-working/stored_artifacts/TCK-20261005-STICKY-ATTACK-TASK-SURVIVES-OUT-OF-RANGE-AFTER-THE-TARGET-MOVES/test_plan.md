---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-STICKY-ATTACK-TASK-SURVIVES-OUT-OF-RANGE-AFTER-THE-TARGET-MOVES
artifact_type: test_plan
tags: [engine, combat]
---

# Test plan (final)

No behaviour changed under this ticket, so no new tests and no disabling control. Verification is the measurement:

- `probes/measure.sh`: 4 worlds x 2 runs, 2000 ticks, `audit_mode=True`, budget disabled; matched pairs, so values.
- `probes/oor_follow.py` and `probes/posture_check.py`: task trace and mechanism (samples).
- Positive control: `frontier_living_world` records the `OUT_OF_RANGE` event the probes count.
- `tests/unit/actions/test_action_routing_task_reset.py::test_attack_out_of_range_does_not_reset_task` still pins the unchanged
  `OUT_OF_RANGE` behaviour and passes.
