---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261008-A-HELD-INTERACT-ON-A-DEPLETED-OR-MISSING-NODE-IS-NEVER-RE-DECIDED
artifact_type: test_plan
tags: [ecology, economy, resource]
---

# Test plan
New: `tests/unit/actions/test_interact_depleted_node_task_reset.py` (a zero-charge node and a missing node each end the held task with an empty payload and one typed rejection; a node with charges is held as before; a released gatherer is scheduled as the brain on its cadence tick while the held one is the action; the per-action reason table). Existing: `tests/unit/actions/test_action_routing_task_reset.py` (the ATTACK reset), unchanged.

## Proof Plan
- **Level**: unit (the routing phase and the scheduler classification), and a five-seed corpus before and after on three worlds.
- **Proof kind**: regression tests that fail without the fix (3 of 5 checked by reverting the change); before and after measurement reported, not tuned.
- **Oracle source**: the held ATTACK reset precedent (TARGET_INCAPACITATED, OUT_OF_RANGE), parity entry TOWN-197, scheduler.py's is_idle_act rule.
- **Expected effect**: a gatherer on an exhausted or vanished node is released to the brain; alive counts rise or hold and starvation falls or holds; nothing else moves.
- **Selected commands**: `pytest tests/unit/actions`; the scoped run `pytest tests/unit/world tests/unit/resource tests/unit/engine tests/unit/systems tests/unit/core tests/unit/tools tests/unit/strategic tests/unit/actions tests/integration -m "not slow"`; `probes/job3.sh <arm> <rep> <world> <seed>` over the lines of `probes/jobs3.txt`.
