# TCK-20260524-LAB-GUARDRAILS

## Title

Token, Time, and Storage Guardrails with E2E System Tests (M104 + M105)

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement Phase 14 guardrails (M104) to prevent agent workflow token exhaustion, oversized sweep execution, and unauthorized raw log access. Then build comprehensive end-to-end integration tests (M105) confirming the full 13-stage human-gated lab pipeline maintains strict pipeline integrity and authorized gating.

## Scope

- Parse workflow-specific context budget limits from frontmatter.
- Enforce `max_evidence_packs`, `max_known_issues`, and `max_previous_runs` bounds inside context pack builder.
- Block raw/heavy log file aggregation by default unless `raw_logs_allowed` is explicitly enabled.
- Check oversized experiments, producing warning or block outcomes based on CI vs local_dev profiles.
- Include run counts, ticks, entities, event volume, artifact size, and retention estimates in readiness report.
- Record all guardrail violations in the central append-only LabAuditTrail.
- Implement comprehensive E2E validation confirming no workflow auto-triggers next workflow, approval gates are respected, and audit trails accurately catalog every state change.
- Gate deep analysis behind `allow_deep_analysis: true` constraint.

## Out of Scope

- Automated scheduling of sweeps beyond the prepared execution phase.

## Acceptance Criteria

- `tests/unit/lab_agent/test_agent_guardrails.py` — 14 unit tests, all passing ✅
- `tests/integration/lab_agent/test_human_gated_agentic_lab_e2e.py` — 5 E2E tests, all passing ✅
- Guardrail violations logged automatically to `LabAuditTrail` ✅
- No sandbox escapes or path traversal opportunities unguarded ✅

## Related Tickets

- None

## Related Docs

- `docs/engine/authoritative_pipeline.md`

## Related Stored Artifacts

- `staging_artifacts/TCK-20260524-LAB-GUARDRAILS/`

## Related Code Areas

- `src/lab/context.py`
- `src/lab/workflows.py`
- `src/lab/audit.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- `UpdateSimulationKnowledgeWorkflow.run()` raises `ValueError` for approval gate rejection (rather than returning a BLOCKED dict). Tests were updated to handle this with try/except.
- Issue index schema from `CompactSimulationDataWorkflow` always includes `tick_range`, `affected_entities` — the investigation workflow was hardened with `.get()` defaults for partial schemas.
- `GenerateSimulationSetupWorkflow` is used in unit tests to produce schema-compliant draft specs, avoiding YAML hand-coding that is fragile against Pydantic validator changes.
- CI profile blocks > 20 runs; local_dev profile warns at > 50 runs. Both produce `guardrail_violation` audit events.

## Test Summary

### Tests Run

- `tests/unit/lab_agent/test_agent_guardrails.py` — 14 tests, 14 passed
- `tests/integration/lab_agent/test_human_gated_agentic_lab_e2e.py` — 5 tests, 5 passed

### Tests Added / Updated

**New**: `tests/unit/lab_agent/test_agent_guardrails.py`
- `TestContextPackLimits` (4 tests) — evidence pack, known_issues, previous_runs, and default limits
- `TestRawLogGuardrail` (4 tests) — raw log exclusion, flag reflection, allowed/blocked states
- `TestDeepAnalysisGate` (2 tests) — deep analysis downgrade + flag-enabled path
- `TestStorageEstimateInReadinessReport` (1 test) — all required estimate keys present
- `TestGuardrailViolationsInAuditLog` (3 tests) — CI block, warning, and audit trail recording

**New**: `tests/integration/lab_agent/test_human_gated_agentic_lab_e2e.py`
- `TestHumanGatedAgenticLabE2E::test_full_e2e_chain` — full 13-stage E2E chain
- `TestNoAutoTrigger::test_generate_does_not_trigger_prepare` — isolation check
- `TestNoAutoTrigger::test_prepare_does_not_execute_simulation` — isolation check
- `TestApprovalGateEnforcement::test_knowledge_update_blocked_without_approved_insights` — approval gate
- `TestApprovalGateEnforcement::test_audit_trail_records_approval_requirement` — audit trail gate

### Known Gaps

- None

## Files Changed

- `src/lab/context.py` — Added `RawLogAccessError`, enforced `raw_logs_allowed` budget flag
- `src/lab/workflows.py` — Integrated `LabAuditTrail`, storage estimates, deep analysis gate, `.get()` hardening on issue schema accesses
- `tests/unit/lab_agent/test_agent_guardrails.py` — New file: 14 M104 unit tests
- `tests/integration/lab_agent/test_human_gated_agentic_lab_e2e.py` — New file: 5 M105 E2E integration tests

## Completion Summary

M104 (Token, Time, and Storage Guardrails) and M105 (Phase 14 E2E Tests) are fully implemented and verified. All 19 new tests pass cleanly. The audit trail correctly records approval events, guardrail violations, and workflow lifecycle events. No workflows auto-trigger the next stage. Simulation execution remains strictly human-gated.
