---
status: active
layer: engine
authority: P3
audience: agent
ticket_id: TCK-20261006-LIVE-TRACKING-TARGET-HELPER-IGNORES-MOVEMENT-MODE
artifact_type: test_plan
tags: [engine, combat]
---

# Test plan

No behavior changes (docs and a new parked ticket only), so no new tests. The existing `resolve_live_tracking_target` tests (`tests/unit/domains/optimization/test_movement_candidate_selector.py`) stay valid because the helper is untouched.

## Proof Plan

- Level: none beyond reading the code; this is a recording ticket.
- Proof kind: documentation, with the facts re-read from `tactical.py`, `positioning.py` and `pipeline_phases/movement.py`.
- Oracle source: the planner's ruling of 2026-10-06 and `docs/engine/kernel.md` (Sticky-Task Law).
- Expected effect: the behavior is documented where a reader of the tactical contract will find it; the latent case has a trigger ticket.
- Selected commands: none.
