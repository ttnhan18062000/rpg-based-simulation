# Test Plan - Milestone 102 Update Knowledge Base

## Integration Tests
A new suite of integration tests will be implemented in `tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py`.

### Test Cases

1. `test_knowledge_update_success`:
   - Setup session and run directory.
   - Run compaction, investigation, and enhancements.
   - Run knowledge update workflow with approved input markers.
   - Assert all 5 knowledge folders contain correct records.
   - Validate preserved evidence references.

2. `test_knowledge_unapproved_items_rejected`:
   - Run knowledge update with unapproved flag or missing approved markers.
   - Verify that trying to update rules or principles raises a `ValueError`.

3. `test_knowledge_duplicate_insight_rejected`:
   - Run the workflow twice with the same insight ID.
   - Verify that the second execution detects the duplicate and raises a `ValueError` or handles it cleanly as rejected.
