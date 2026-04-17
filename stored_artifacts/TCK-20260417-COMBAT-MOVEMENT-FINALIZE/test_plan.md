# Test Plan: Combat Movement Observability

## Unit Tests
- `src/core/models/reason_codes.py`: Verify `ActionReason.reason_text` prepends "REJECTED: " when `is_rejection=True`.

## Integration Tests
- `tests/rollout/test_combat_movement_rollout_boundaries.py`: Ensure legality v2 rejections are correctly caught and formatted for the API.
- `tests/observability/test_combat_movement_observability_contract.py`: Ensure structured reason codes are populated at runtime.

## Documentation Tests
- `tests/docs/test_combat_movement_documentation_integrity.py`: Verify that all milestone rulebooks are present and documented according to the overhaul spec.

## Regression Suite
- Run full suite: `pytest tests/observability/ tests/rollout/ tests/docs/`
