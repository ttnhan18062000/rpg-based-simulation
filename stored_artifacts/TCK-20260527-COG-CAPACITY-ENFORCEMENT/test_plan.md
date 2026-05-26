# Test Plan — Capacity Enforcement

We will verify that cognitive capacity limits are enforced unconditionally, idempotent, and respect prioritization constraints.

## Scenarios to Test

### 1. Standalone Trimming
- Overload an entity with excess leads, concerns, and hypotheses.
- Execute standalone trimming.
- Assert that counts match cognition profile limits exactly.

### 2. Idempotency
- Run trimming on an already trimmed entity.
- Assert that no additional elements are removed.

### 3. Active Project and Priority Preservation
- Ensure the active project (defined by `current_project_id`) is never dropped during project trimming.
- Ensure the highest certainty leads, highest urgency concerns, and highest confidence hypotheses survive the trim.

### 4. Observatory Trace Events
- Verify that a structured `CognitionCapacityTrimmed` log is emitted with before/after counts, entity ID, and dropped IDs.
