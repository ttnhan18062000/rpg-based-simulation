---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260523-COGNITION-SCHEMA-RECORDER
artifact_type: test_plan
tags: [cognition, schema, recorder]
---

# test_plan.md - Schema & Recorder Tests

## Unit Tests
- `tests/unit/observability/cognition/test_cognition_artifact_schema.py`:
  - Snapshot serialization tests (validates correct JSON schema fields).
  - Schema constraints (rejects unknown reasons, empty graph counts as valid).
- `tests/unit/observability/cognition/test_cognition_capture_policy.py`:
  - Asserts that OFF mode records nothing.
  - Asserts that LIGHT mode records anomaly triggers.
  - Asserts that DEBUG mode records selected entity project changes.

## Integration Tests
- `tests/integration/observability/test_cognition_snapshot_artifact.py`:
  - Run small mock simulation and verify that snapshots are written to the target run directory under the correct format with zero state hash drift.
