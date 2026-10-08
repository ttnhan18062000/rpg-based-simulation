---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261008-A-HELD-INTERACT-ON-A-DEPLETED-OR-MISSING-NODE-IS-NEVER-RE-DECIDED
artifact_type: plan
tags: [ecology, economy, resource]
---

# Plan

1. `core_actions.py`: add `interact_target_unavailable(state, target_id)` (missing node gives `SOURCE_MISSING`, zero charges gives `SOURCE_DEPLETED`, otherwise none; none with no state or no target). `execute_interact` takes the state and returns only a `NavigationUpdate(failure_reason=...)` when the target is unavailable (no readiness spent), the old update otherwise.
2. `action_router.py`: pass `context` (the sliding state) to `execute_interact`.
3. `pipeline_phases/actions.py`: a per-action table of reasons that end a held task (ATTACK keeps its list; INTERACT gets the two reasons) used by `_is_unrecoverable_action_failure`, one line changed in that function.
4. Tests, a parity entry (TOWN-197), the pinned measurement against PR 1 as the base. No hunger or food logic.
