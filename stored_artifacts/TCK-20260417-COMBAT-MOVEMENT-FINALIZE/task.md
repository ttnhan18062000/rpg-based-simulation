---
content_type: doc
status: historical
layer: engine
authority: P2
audience: agent
tags: [combat, movement, finalize]
---

- [x] ActionSystem Stabilization
    - [x] Add `is_rejection` field to `ActionReason` in `src/core/models/reason_codes.py`
    - [x] Update `ActionReason.reason_text` to handle "REJECTED: " prefix
    - [x] Update `ActionSystem.apply_action_state_transitions` to use `ActionReason` consistently
- [x] Documentation Polish
    - [x] Audit Milestone 1-6 implementation comments
    - [x] Polish `combat_movement_overhaul_spec.md`
- [x] Final Verification
    - [x] Run test suite: `pytest tests/observability/ tests/rollout/ tests/docs/`
