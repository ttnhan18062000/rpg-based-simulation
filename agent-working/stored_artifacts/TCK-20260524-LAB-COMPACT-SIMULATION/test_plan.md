---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260524-LAB-COMPACT-SIMULATION
artifact_type: test_plan
tags: [lab, compact, simulation]
---

# Test Plan - M99 CompactSimulationData Workflow

## 1. Automated Integration Tests

We will implement `tests/integration/lab_agent/test_compact_simulation_data_workflow.py` containing a comprehensive test suite. The suite will initialize active mock sessions, write child run directories with mock `run_report.json` scorecards, and execute both specific and generic workflow requests.

### Test Scenarios

1. **`test_compaction_complete_success`**:
   - Assures that when a complete lab run with multiple child run report folders is compacted, the outputs `compact_summary.json`, `compact_summary.md`, `issue_index.json`, `evidence_pack_index.json`, `metric_digest.json`, `entity_hotspots.json`, and `signal_coverage.json` are successfully generated and correctly structured.
   - Verifies the "Important Data Rule": event streams are not copied, only rollups.

2. **`test_compaction_top_n_respected`**:
   - Assures that when a specific `top_n` limit is provided (e.g. `top_n = 1`), the issue index and entity hotspot indices are capped to exactly `top_n` items.

3. **`test_compaction_focus_domains`**:
   - Assures that domain signal coverage computes `"HIGH_FOCUS"` status correctly when `focus_domains` is specified in specific inputs.

4. **`test_compaction_generic_mode`**:
   - Assures that in generic mode, the workflow resolves the target directory automatically via `registration/actual_lab_run_path.txt` from the active session registry.

5. **`test_compaction_traversal_blocked`**:
   - Proves that trying to compile or traverse outside the workspace root using relative/absolute sandbox breakout parameters (e.g. `../../etc`) is strictly blocked.

---

## 2. Test Execution Command

Run the integration tests:
```bash
pytest tests/integration/lab_agent/test_compact_simulation_data_workflow.py
```
Ensure all tests pass synchronously and reliably.
