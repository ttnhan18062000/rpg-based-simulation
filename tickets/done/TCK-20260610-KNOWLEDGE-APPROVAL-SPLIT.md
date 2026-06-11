---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260610-KNOWLEDGE-APPROVAL-SPLIT
phase: done
date: 2026-06-10
tags: [knowledge, approval, split]
---

# TCK-20260610-KNOWLEDGE-APPROVAL-SPLIT

## Title
Split permissive knowledge-update approval assertion into three explicit status-path tests

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
In `test_human_gated_agentic_lab_e2e.py` (line 359), the approved knowledge update path asserts:
`assert approved_result["status"] in ("SYNCED", "READY", "NO_INSIGHTS", "BLOCKED")`.
This means an approved update can return BLOCKED and the test still passes — the approval gate proof is not meaningful. The test must be split into three explicit cases so each terminal status is verified precisely.

## Scope
- Split the single approved-path assertion into three dedicated test cases (or parametrized cases):
  1. No approval → must be BLOCKED (or ValueError mentioning "approval")
  2. Approval present but no approved insights → must be NO_INSIGHTS
  3. Approval present with approved insights → must be SYNCED exactly (not BLOCKED, not READY)
- Remove the permissive 4-status union assertion from the success path
- Audit trail must record approval check and sync result in each case

## Out of Scope
- Changing the workflow implementation itself
- Changing the unapproved path (line 341 already asserts BLOCKED/NO_INSIGHTS/SKIPPED correctly)

## Acceptance Criteria
- [x] Unapproved insight cannot sync (existing test — verify still passes)
- [x] Approved empty insight set returns NO_INSIGHTS exactly
- [x] Approved non-empty insight set returns SYNCED exactly
- [x] BLOCKED is not accepted as a success result in the approved+insights path
- [x] Audit trail entries recorded for approval check and sync result in each case
- [x] No test uses `status in ("SYNCED", ..., "BLOCKED")` for a success assertion

## Related Tickets
- TCK-20260524-LAB-KNOWLEDGE (prior work — implemented the workflow)

## Related Docs
- `docs/guidelines/design_patterns.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260610-KNOWLEDGE-APPROVAL-SPLIT/`

## Related Code Areas
- `tests/integration/lab_agent/test_human_gated_agentic_lab_e2e.py`
- `tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py`
- `src/lab/workflows.py` — UpdateSimulationKnowledgeWorkflow

## Assumptions / Open Questions
- Workflow previously returned "READY" unconditionally — a minimal API fix was needed: return "SYNCED" when items stored, "NO_INSIGHTS" when nothing to sync. Logic unchanged.
- Proposed patches directory also needed clearing in the empty-insights fixture (not just insight_candidates.json).

## Implementation Notes
- `UpdateSimulationKnowledgeWorkflow.run()`: Changed return from `{"status": "READY"}` to `{"status": "SYNCED" | "NO_INSIGHTS", "synced_count": N}`. Added `knowledge_sync_result` audit event with insight/patch counts. Updated `workflow_completed` event to use computed status.
- `test_update_simulation_knowledge_workflow.py`: Updated `test_knowledge_update_success` to assert `SYNCED`. Added `mock_workspace_empty_insights` fixture (clears both `insight_candidates.json` and `proposed_patches/`). Added `test_approved_with_no_insights_returns_no_insights` and `test_approved_with_insights_not_blocked`.
- `test_human_gated_agentic_lab_e2e.py` line 359: Replaced 4-status union with exact `== "SYNCED"` assertion.

## Test Summary
`pytest tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py tests/integration/lab_agent/test_human_gated_agentic_lab_e2e.py -v`
11/11 passed.

## Files Changed
- `src/lab/workflows.py`
- `tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py`
- `tests/integration/lab_agent/test_human_gated_agentic_lab_e2e.py`

## Completion Summary
Approval gate proof is now meaningful. SYNCED/NO_INSIGHTS distinguish successful sync from empty-insights runs. BLOCKED is no longer accepted as a success result. Audit trail records `knowledge_sync_result` event with counts in every approved run.
