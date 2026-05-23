# Test Plan & Coverage Matrix for Cognition Graph Observability

## Test Suites

We execute and verify the following test suites:

### 1. Artifact Schema & Snapshot Tests
- File: `tests/unit/observability/cognition/test_cognition_artifact_schema.py`
  - Valid snapshot serialization.
  - Required fields.
  - Unknown reason rejection.
  - Graph hash validation.
  - Large metadata safety rejection.
- File: `tests/integration/observability/test_cognition_snapshot_artifact.py`
  - Recorder creates snapshot files on anomalies.
  - State change capturing in debug mode.
  - State hash determinism.
  - Kernel post-commit integration.

### 2. Capture Policy Throttling
- File: `tests/unit/observability/cognition/test_cognition_capture_policy.py`
  - `OFF` mode records nothing.
  - `LIGHT` mode only records on anomalies.
  - `DEBUG` mode captures all reasons.
  - State changes detection.

### 3. Diff Building & Event Mapping
- File: `tests/unit/observability/cognition/test_cognition_graph_diff_builder.py`
  - Empty diff for identical graphs.
  - Blocker addition/removal detection.
  - Project/objective/metadata status shifts.
  - Deterministic key ordering and non-mutating behavior.
- File: `tests/unit/observability/cognition/test_cognition_event_mapper.py`
  - Strategic events mapping (project/objective changed).
  - Blocker events.
  - Detour loops detection.

### 4. Feature Extraction & Pattern Mining
- File: `tests/unit/observability/cognition/test_cognition_feature_extractor.py`
  - Safe handling of missing/empty logs.
  - Metric aggregation timelines.
- File: `tests/unit/observability/cognition/test_cognition_pattern_miner.py`
  - Project churn, detour loop, and stale blocker detection.
- File: `tests/integration/observability/test_cognition_pattern_mining_flow.py`
  - Full end-to-end extraction and mining run.

### 5. API & CLI Security
- File: `tests/api/test_cognition_history_api.py`
  - Paginated snapshot retrieval.
  - Security validation against path traversal.
  - Graceful missing run error handling.
- File: `tests/cli/test_cognition_cli.py`
  - CLI subcommand parameter checks and alphanumeric validation.
