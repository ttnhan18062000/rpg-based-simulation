# Investigation: Combat Movement Observability Stabilization

## Objective
Identify why `ActionSystem` rejections sometimes lacked the "REJECTED: " prefix and verify documentation alignment.

## Findings
- **Prefix Discrepancy**: Legacy string-based rejections in `ActionSystem.apply_action_state_transitions` were manually prefixed. New `ActionReason` objects introduced in Milestone 7 were being serialized via `reason_text` which lacked the logic to prepend the prefix when used as an authoritative rejection.
- **Rollout Tests**: `tests/rollout/test_combat_movement_rollout_boundaries.py` specifically asserts that blocked actions contain "REJECTED: " in their reason strings.
- **Documentation**: Milestone 1-6 docs were updated with implementation details but required a final verification against the specialized services (`LegalityService`, `MovementModel`, etc.) to ensure 100% accuracy.

## Root Cause
The `ActionReason` model was designed for structured observation but didn't have a semantic flag for "this is a rejection" vs "this is an intention".

## Resolution
- Added `is_rejection` boolean to `ActionReason`.
- Updated `ActionReason.reason_text` property to handle conditional prefixing.
- Refactored `ActionSystem` to use the structured model consistently for all legality rejections.
