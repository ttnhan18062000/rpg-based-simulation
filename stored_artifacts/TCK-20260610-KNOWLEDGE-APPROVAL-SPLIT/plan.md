# Plan — TCK-20260610-KNOWLEDGE-APPROVAL-SPLIT

## Step 1 — Update workflow return code (src/lab/workflows.py)

At the end of UpdateSimulationKnowledgeWorkflow.run():

**Change `workflow_completed` audit event** from hardcoded `"READY"` to computed status.
**Add `knowledge_sync_result` audit event** with synced_insights and synced_patches counts.
**Change final return** from unconditional `"READY"` to:
```python
synced_count = len(stored_insights) + len(stored_patches)
status = "SYNCED" if synced_count > 0 else "NO_INSIGHTS"
```

## Step 2 — Update existing unit test (test_update_simulation_knowledge_workflow.py)

`test_knowledge_update_success`: change `assert res["status"] == "READY"` to `assert res["status"] == "SYNCED"`.

## Step 3 — Add two new tests (test_update_simulation_knowledge_workflow.py)

**`test_approved_with_no_insights_returns_no_insights`**:
- Uses a variant fixture that overwrites `insight_candidates.json` with `[]` after enhancement
- Sends approval credentials
- Asserts `res["status"] == "NO_INSIGHTS"`
- Asserts audit trail has `knowledge_sync_result` event

**`test_approved_with_insights_not_blocked`**:
- Uses existing `mock_workspace_for_knowledge` fixture
- Sends approval credentials
- Asserts `res["status"] == "SYNCED"` (not BLOCKED, not READY, not NO_INSIGHTS)
- Asserts `knowledge_sync_result` event in audit trail with `synced_insights >= 1`

## Step 4 — Tighten E2E assertion (test_human_gated_agentic_lab_e2e.py line 359)

Replace:
```python
assert approved_result["status"] in ("SYNCED", "READY", "NO_INSIGHTS", "BLOCKED")
```
with:
```python
assert approved_result["status"] == "SYNCED", (
    f"Approved non-empty insight set must return SYNCED, got: {approved_result['status']}"
)
```
(The `if proposals_list:` guard on line 349 ensures this branch is only reached when insights exist.)

## Files Changed

- `src/lab/workflows.py`
- `tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py`
- `tests/integration/lab_agent/test_human_gated_agentic_lab_e2e.py`
