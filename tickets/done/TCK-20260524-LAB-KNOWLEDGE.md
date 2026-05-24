# TCK-20260524-LAB-KNOWLEDGE

## Title

Implement UpdateSimulationKnowledge Workflow (Milestone 102) & Approval Gates/Audit Trail (Milestone 103)

## Status

DONE

## Request Summary

Implement `UpdateSimulationKnowledgeWorkflow` class in `src/lab/workflows.py` to ingest approved insights, patches, and decisions, and securely store them in the global knowledge base folder (`data/lab_knowledge/`) with audit tracking, preventing unapproved rule updates or path breakouts. Additionally, build a human-gated approval gate and an append-only audit trail logger to ensure 100% security, isolation, and transparency.

## Scope

- Create `UpdateSimulationKnowledgeWorkflow` class in `src/lab/workflows.py`
  - Ingest the approved insights and patches.
  - Enforce strict approval validation (require an explicit `approval` flag or marker). If not approved, reject the action.
  - Write outputs to the five structured knowledge directories under `data/lab_knowledge/`:
    1. `data/lab_knowledge/insights/`
    2. `data/lab_knowledge/known_issues/`
    3. `data/lab_knowledge/rules/`
    4. `data/lab_knowledge/principles/`
    5. `data/lab_knowledge/decisions/decision_log.jsonl`
  - Verify that the workflow checks for and blocks duplicate insights using stable semantic identifiers or IDs.
  - Preserve evidence references across insight/known issue records.
- Implement human-gated `LabApprovalGate` and append-only `LabAuditTrail` inside `src/lab/audit.py`.
- Integrate audit logging into `UpdateSimulationKnowledgeWorkflow` for full traceability.
- Apply safe path resolution and sandbox guards to block traversal breakouts.
- Export `UpdateSimulationKnowledgeWorkflow`, `LabApprovalGate`, and `LabAuditTrail` in `src/lab/__init__.py`.
- Write integration tests inside `tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py`.
- Write unit tests for the approval gate and audit trail under `tests/unit/lab_agent/test_approval_gate.py` and `tests/unit/lab_agent/test_audit_trail.py`.

## Out of Scope

- Applying code-level mutations to game engines.

## Acceptance Criteria

- Workflow runs and transitions the stage successfully to `KNOWLEDGE_UPDATE`.
- Approved insights and known issues are serialized correctly to JSON/YAML in the designated global directories.
- Decision log is appended line-by-line in `decision_log.jsonl`.
- Attempts to update rules or principles without approval marker raise a validation error or block.
- Paths are validated with `safe_path_resolution()` to prevent sandbox escapes.
- Human-gated approval gate ensures unapproved specs or items are rejected and audit logs track start/end/completion.

## Related Tickets

- `TCK-20260524-LAB-ENHANCEMENT` (Done)

## Related Docs

- `lab_phase14.md`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260524-LAB-ENHANCEMENT/`

## Related Code Areas

- `src/lab/workflows.py`
- `src/lab/audit.py`
- `src/lab/__init__.py`
- `tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py`
- `tests/unit/lab_agent/test_approval_gate.py`
- `tests/unit/lab_agent/test_audit_trail.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Designed and implemented a robust `LabApprovalGate` class verifying artifact paths cleanly.
- Implemented append-only `LabAuditTrail` writing structured event lines to `audit_log.jsonl`.
- Bound workflows to use `LabAuditTrail` logging on start, file interactions, verification checks, and completion.

## Test Summary

- Added 4 integration tests in `test_update_simulation_knowledge_workflow.py`.
- Added 3 unit tests in `test_approval_gate.py`.
- Added 1 unit test in `test_audit_trail.py`.
- Total 51/51 tests passing.

## Files Changed

- `src/lab/__init__.py`
- `src/lab/workflows.py`
- `src/lab/audit.py`
- `tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py`
- `tests/unit/lab_agent/test_approval_gate.py`
- `tests/unit/lab_agent/test_audit_trail.py`

## Completion Summary

- Milestone 102 & 103 are fully complete and certified with zero structural or security gaps.
