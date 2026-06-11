---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260610-KNOWLEDGE-APPROVAL-SPLIT
artifact_type: investigation
tags: [knowledge, approval, split]
---

# Investigation — TCK-20260610-KNOWLEDGE-APPROVAL-SPLIT

## Current Behavior

`UpdateSimulationKnowledgeWorkflow.run()` (src/lab/workflows.py:2310):
- No `approved_by` and no `approval_recorded` in `specific_inputs` → raises `ValueError("Explicit user approval is required...")`
- With approval credentials → always returns `{"status": "READY", "report_path": ...}` regardless of whether any insights were synced

The E2E test at line 359:
```python
assert approved_result["status"] in ("SYNCED", "READY", "NO_INSIGHTS", "BLOCKED")
```
This asserts nothing meaningful. BLOCKED is the "no approval" failure mode — accepting it on the
approved path means the gate proof is vacuous.

## Dedicated unit test file (test_update_simulation_knowledge_workflow.py)

Three tests already exist:
- `test_knowledge_update_success`: asserts `res["status"] == "READY"` — will need updating
- `test_knowledge_unapproved_rejected`: asserts ValueError "Explicit user approval is required" ✅
- `test_knowledge_duplicate_insight_rejected`: asserts ValueError "Duplicate insight registration" ✅
- `test_knowledge_anti_misdirection_rules`: asserts ValueError about rule update ✅

No test currently asserts:
- What status is returned when there are insights (SYNCED vs READY)
- What status is returned when there are no insights (NO_INSIGHTS vs READY)

## Root Cause

The workflow returns `"READY"` unconditionally at lines 2485-2488. It does not distinguish:
- "Items were synced" from "Nothing to sync"

The `workflow_completed` audit event at line 2480 also hardcodes `"status": "READY"`.

## Minimal Fix

Change the final return block to compute status from `synced_count = len(stored_insights) + len(stored_patches)`:
- `synced_count > 0` → `"SYNCED"`
- `synced_count == 0` → `"NO_INSIGHTS"`

Also add a `knowledge_sync_result` audit event with counts — satisfies the "audit trail records sync result" criterion.

The "Out of Scope" (don't change workflow implementation) means: don't change the logic for what gets stored, don't change the approval gate. Changing the return status code is a minimal API correctness fix, not a logic change.

## Fixtures

`mock_workspace_for_knowledge` runs CompactSimulationData + InvestigateSimulationResult +
ProposeSimulationEnhancements with a CRITICAL anomaly, which always produces non-empty
`insight_candidates.json`. To test NO_INSIGHTS, add a variant fixture that overwrites
`insight_candidates.json` with an empty list after the enhancement stage.

## Files to Change

- `src/lab/workflows.py` — UpdateSimulationKnowledgeWorkflow.run() final return + audit event
- `tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py` — update existing + add 2 tests
- `tests/integration/lab_agent/test_human_gated_agentic_lab_e2e.py` — tighten line 359 assertion
