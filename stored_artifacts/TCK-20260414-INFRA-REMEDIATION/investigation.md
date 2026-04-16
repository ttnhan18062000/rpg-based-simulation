# Investigation: Infrastructure Remediation

## Current Broker Handling
- `src/api/rabbitmq_client.py`: Uses `try-except ImportError` for `pika`. Checks `DISABLE_RABBITMQ` env var.
- `src/api/kafka_client.py`: Likely similar (need to verify).
- **Risk**: Some parts of the engine might not check if the client is `None` before calling methods, although `get_rabbitmq()` returns `None`.

## Stale Assertions
- `src/testing/assertions.py`:
    - `assert_strategic_consistency`: Correctly reads `ticks[-1]["entities"]`.
    - **Issue**: Field names like `project_id` vs `current_project_id` might be inconsistent with the `strategy` block in `ReplayRecorder`. (Replay uses `project_id`, but `ProjectRecord` uses `project_id`).
    - **Missing**: `is_overloaded` and `primary_overload_source` alignment between Replay and Exporter nodes.

## Truth Surfaces
- **Replay**: `src/utils/replay.py` -> `entities_snapshot`.
- **API**: `src/api/schemas.py` -> `StrategicStateSchema`.
- **Graph**: `src/core/logic/cognition_graph_exporter.py` -> `cognition_profile` node data.
- **Contract**: Replay is the *summary*, API is the *live view*, Graph is the *structure*.

## Documentation Integrity
- `test_cognition_integrity.py`: Currently checks `bounded_cognition_ui_contract.md`. Needs to check the newly updated implementation docs.
