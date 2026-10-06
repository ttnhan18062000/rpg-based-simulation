---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-SILENT-NO-OP-RETURNS-IN-ACTIONROUTER-HOLD-THE-TASK-AND-ANNOTATE-FALSE-SUCCESS
artifact_type: plan
tags: [engine, combat, observability]
---

# Plan (planner-ruled direction: typed ReasonCode, reuse the existing clear branch)

1. `src/core/enums.py`: add `ACTION_WITHHELD_BY_POSTURE`, `UNSUPPORTED_ACTION` (`ReasonCode` is not registry-governed or ratcheted).
2. `src/engine/domain/action_router.py`: the posture gate and the fall-through return `NavigationUpdate(failure_reason=...)` with
   `readiness_delta=0.0` (the shape the readiness check and `execute_attack` already use). The gate's policy is not touched.
3. `src/engine/pipeline_phases/actions.py`: widen the existing unrecoverable-clear branch to any action whose reason is in
   `_UNRECOVERABLE_ANY_ACTION_REASONS`; drop a `reason` that sits beside an `outcome` before writing the new annotation.
4. Tests in `tests/unit/actions/test_action_routing_withheld_action.py`, with three disabling controls.
5. `docs/mechanics/02_combat_laws.md`, `docs/engine/kernel.md`, divergence 2.69, parity entry `COMB-330`.
6. Measure exposure before/after (`probes/exposure.sh`) and re-trace the original episode.
Out of scope, held: removing or loosening the posture gate; `scheduler.py`; flee gate; BRACKETING.
