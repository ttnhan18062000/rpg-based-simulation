---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260524-LAB-INVESTIGATION
artifact_type: test_plan
tags: [lab, investigation]
---

# Test Plan - Milestone 100 Investigation Workflow

## Integration Tests
A new suite of integration tests will be implemented in `tests/integration/lab_agent/test_investigate_simulation_result_workflow.py`.

### Test Cases

1. `test_investigation_light_depth`:
   - Setup session and run directory.
   - Run compaction to write base registration artifacts.
   - Run investigation with `analysis_depth="light"`.
   - Assert `investigation_report.json` executive summary and indices are generated.
   - Verify only the top 3 issues are analyzed.

2. `test_investigation_standard_depth`:
   - Setup similar environment with >10 issues.
   - Run investigation with `analysis_depth="standard"`.
   - Assert top 10 issues are examined.
   - Assert missing signals are flagged correctly based on `signal_coverage.json`.

3. `test_investigation_deep_depth`:
   - Run investigation with `analysis_depth="deep"`.
   - Assert that selective child reports are read to fetch specific window ticks.
   - Verify backlog items and next experiment suggestions are successfully populated.

4. `test_investigation_invalid_run_blocked`:
   - Trigger the workflow with an invalid, non-compacted session.
   - Assert workflow enters `BLOCKED` status cleanly.

5. `test_investigation_traversal_blocked`:
   - Attempt a path traversal attack.
   - Assert raising `PermissionError` using sandbox shields.
