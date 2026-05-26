# TCK-20260524-LAB-COMPACT-SIMULATION

## Title

Implement CompactSimulationData Workflow (Milestone 99)

## Status

DONE

## Request Summary

Implement the `CompactSimulationDataWorkflow` in `src/lab/workflows.py` to convert large raw simulation run directories into compact summaries and indexes inside the active lab session, preparing data for downstream metamorphic and balance investigations.

## Scope

- Create `CompactSimulationDataWorkflow` class in `src/lab/workflows.py` [x]
  - Load the targeted/latest registered lab run manifest. [x]
  - Parse run summaries, anomalies, metric windows, and event timelines safely. [x]
  - Derive a structured issue index with count-based rollups. [x]
  - Formulate an evidence pack index, rolling metric digest, and hot-spotting entity index. [x]
  - Calculate signal coverage across target gameplay domains. [x]
  - Output registration summaries including `compact_summary.json`, `compact_summary.md`, `issue_index.json`, `evidence_pack_index.json`, `metric_digest.json`, `entity_hotspots.json`, and `signal_coverage.json`. [x]
- Strict Traversal and Escape blocks. [x]
- Enforce the "Important Data Rule": Do not copy full raw event lines, event logs, or metric timelines into summaries. Only include metrics counts, top issues, and short summaries. [x]
- Register `CompactSimulationDataWorkflow` in the package interface. [x]
- Implement integration tests inside `tests/integration/lab_agent/test_compact_simulation_data_workflow.py`. [x]

## Out of Scope

- Implementing the subsequent `InvestigateSimulationResultWorkflow` (M100).
- Building the frontend visual charts for the compact summaries.

## Acceptance Criteria

- Compact summaries and digests are successfully created in `registration/` under the session directory. [x]
- Issue index, evidence pack index, metric digest, entity hotspots, and signal coverage reports are correctly populated. [x]
- Raw events from `simulation_events.jsonl` are NOT copied into summaries (only aggregated count/rollup properties are exported). [x]
- Path traversal escapes are strictly blocked. [x]
- Integration tests cover all required cases (generic/specific mode, top_n limits, formatting). [x]

## Related Tickets

- `TCK-20260524-LAB-RESULT-REGISTRATION` (Done)

## Related Docs

- `lab_phase14.md`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260524-LAB-COMPACT-SIMULATION/`

## Related Code Areas

- `src/lab/workflows.py`
- `src/lab/__init__.py`
- `tests/integration/lab_agent/test_compact_simulation_data_workflow.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Designed and implemented complete class mapping and domain categorizations for gameplay events and rules.
- Integrated fully with LabResultStore and LabSessionStore.
- Added strict path validation and safety boundaries.

## Test Summary

Run:
```bash
pytest tests/integration/lab_agent/test_compact_simulation_data_workflow.py
```
Outcome: 5 passed.

## Files Changed

- `src/lab/workflows.py`
- `src/lab/__init__.py`
- `tests/integration/lab_agent/test_compact_simulation_data_workflow.py`

## Completion Summary

All tasks successfully closed. Compaction outputs are completely structured, premium, and fully covered by dynamic integration tests.
