# Implementation Plan - M99 CompactSimulationData Workflow

This plan outlines the design and implementation of the `CompactSimulationDataWorkflow` to convert heavy raw simulation logs and scorecards into a highly structured, token-efficient series of compact digests and indexes.

## Proposed Changes

### `src/lab/workflows.py`

Implement the `CompactSimulationDataWorkflow` class:
- **`run(self, session_id: str, request: WorkflowRequest) -> dict[str, Any]`**:
  - Resolves `lab_run_path` safely (using `safe_path_resolution`).
  - Accesses session manifest, sets `current_stage` to `"REGISTRATION"`.
  - Loads manifest and child run summaries (`run_report.json`).
  - Builds the following artifact indexes and reports:
    1. `registration/compact_summary.json`
    2. `registration/compact_summary.md`
    3. `registration/issue_index.json`
    4. `registration/evidence_pack_index.json`
    5. `registration/metric_digest.json`
    6. `registration/entity_hotspots.json`
    7. `registration/signal_coverage.json`
  - Blocks and handles cases where files are missing, corrupted, or have path-traversal escapes.
  - Implements the "Important Data Rule": No raw timeline/event dumps, only aggregates, paths, counts, and top entries.

### `src/lab/__init__.py`

- Export `CompactSimulationDataWorkflow` to make it accessible to tests and other modules.

### `tests/integration/lab_agent/test_compact_simulation_data_workflow.py`

- Implement automated integration tests verifying:
  - Successful compaction and generation of all output files.
  - Correct aggregation of `issue_index`, `entity_hotspots`, and `metric_digest`.
  - Proper enforcement of the `top_n` limit on both issues and hotspots.
  - Exclusion of heavy raw events (`simulation_events.jsonl` not copied).
  - Proper handling of focus domains.
  - Strict path traversal protections.

---

## Verification Plan

### Automated Tests
Run the pytest suite:
```bash
pytest tests/integration/lab_agent/test_compact_simulation_data_workflow.py
```
Verify that all 7 test cases pass successfully.
