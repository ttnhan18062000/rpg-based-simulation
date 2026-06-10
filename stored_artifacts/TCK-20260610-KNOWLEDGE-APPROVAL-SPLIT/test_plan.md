# Test Plan — TCK-20260610-KNOWLEDGE-APPROVAL-SPLIT

## Tests to run

```
pytest tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py -v
pytest tests/integration/lab_agent/test_human_gated_agentic_lab_e2e.py -v
```

## Acceptance Criteria Checks

| Criterion | Test |
|---|---|
| Unapproved insight cannot sync | `test_knowledge_unapproved_rejected` (existing) |
| Approved empty insight set → NO_INSIGHTS | `test_approved_with_no_insights_returns_no_insights` (new) |
| Approved non-empty insight set → SYNCED | `test_approved_with_insights_not_blocked` (new) + `test_knowledge_update_success` (updated) |
| BLOCKED not accepted on approved+insights path | E2E line 359 asserts SYNCED exactly |
| Audit trail records sync result | both new tests check `knowledge_sync_result` event |
| No `status in (..., "BLOCKED")` on approved path | code review |
