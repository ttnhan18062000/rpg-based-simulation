# Test Plan - Milestone 101 Enhancement Proposals

## Integration Tests
A new suite of integration tests will be implemented in `tests/integration/lab_agent/test_propose_simulation_enhancements_workflow.py`.

### Test Cases

1. `test_enhancement_proposals_success`:
   - Setup session and run directory.
   - Run compaction and investigation.
   - Run enhancements workflow with standard allowed types.
   - Assert all 5 output files and directories exist.
   - Validate that proposed patches contain evidence references.

2. `test_enhancement_proposals_forbidden_rejected`:
   - Run with `forbidden_change_types=["EngineCode"]` or similar.
   - Verify that trying to propose an engine change triggers a clear `ValueError`.

3. `test_enhancement_proposals_no_direct_mutation`:
   - Assert that no files outside the active session directory (such as active gameplay YAML specs under `data/scenarios/` or `src/`) are mutated.

4. `test_enhancement_proposals_unsupported_operation_rejected`:
   - Attempt to configure a patch with an unsupported operation (e.g. `delete`).
   - Verify validation fails and raises `ValueError`.

5. `test_enhancement_proposals_evidence_free_critical_rejected`:
   - Attempt to configure a patch for a critical rule change with empty `evidence` references.
   - Verify validation fails and raises `ValueError`.
