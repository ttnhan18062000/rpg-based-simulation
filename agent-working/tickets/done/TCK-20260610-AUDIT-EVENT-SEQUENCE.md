---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260610-AUDIT-EVENT-SEQUENCE
phase: done
date: 2026-06-10
tags: [audit, event, sequence]
---

# TCK-20260610-AUDIT-EVENT-SEQUENCE

## Title
Assert minimum ordered audit event sequence in E2E approval test

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
The Phase 40 E2E audit test only checks that some audit events exist and accepts either `workflow_started` or `approval_recorded`. This proves the audit log is non-empty but not that the correct safety sequence happened. The test must assert a minimum ordered sequence of events covering the full generate→register→approve→sync pipeline.

## Scope
- Add audit sequence assertion to `test_human_gated_agentic_lab_e2e.py`
- Required ordered sequence (exact event names may vary; semantics must match):
  1. `workflow_started`: GenerateSimulationSetup
  2. `workflow_completed`: GenerateSimulationSetup
  3. `workflow_started`: PrepareSimulationExecution
  4. `workflow_completed`: PrepareSimulationExecution
  5. `manual_boundary_declared`
  6. `workflow_started`: RegisterSimulationResult
  7. `workflow_completed`: RegisterSimulationResult
  8. `workflow_started`: ProposeSimulationEnhancements
  9. `workflow_completed`: ProposeSimulationEnhancements
  10. `approval_required`
  11. `approval_recorded`
  12. `workflow_started`: UpdateKnowledgeStore
  13. `workflow_completed`: UpdateKnowledgeStore
- Test must fail if approval step is bypassed (approval_required and approval_recorded missing)

## Out of Scope
- Changing the audit trail implementation
- Asserting exact timestamps or payload contents

## Acceptance Criteria
- [x] Audit log records workflow start/completion for all 5 major workflows
- [x] Audit log records manual execution boundary
- [x] Audit log records `approval_required` before `approval_recorded`
- [x] Audit log records knowledge sync result
- [x] Test fails if approval events are absent
- [x] Sequence check tolerates minor ordering gaps (intermediate events) but requires the 13 semantic checkpoints above to appear in order

## Related Tickets
- TCK-20260524-LAB-KNOWLEDGE (prior work — audit trail implemented here)
- TCK-20260610-KNOWLEDGE-APPROVAL-SPLIT (related — tightens approval path tests)

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- `tests/integration/lab_agent/test_human_gated_agentic_lab_e2e.py`
- `src/lab/` — audit trail writer

## Assumptions / Open Questions
- How is the audit log exposed from the workflow result? Check what `e2e_workspace` exposes before writing assertions.
- Do workflow event names follow a stable convention? Verify before hardcoding.

## Implementation Notes
Only `UpdateSimulationKnowledgeWorkflow` emitted `workflow_started`/`workflow_completed` before this ticket. The other four workflows had no lifecycle audit events. Added `trail = LabAuditTrail(...)` + `workflow_started` at the entry point and `workflow_completed` before the success return of each workflow. `manual_boundary_declared` is emitted by `PrepareSimulationExecutionWorkflow` after `workflow_completed` — semantically this is where the agent hands off to the human for manual execution.

The `UpdateSimulationKnowledgeWorkflow` emits `workflow_started` before the approval check (not after), so the 13-checkpoint sequence reflects actual emit order: `workflow_started → approval_required → approval_recorded → workflow_completed`. The test's `UpdateSimulationKnowledge` approved run is now unconditional (not gated on `proposals_list`) to ensure the lifecycle events always appear.

## Test Summary
- `TestHumanGatedAgenticLabE2E::test_full_e2e_chain`: replaces weak 4-assertion audit check with a 13-checkpoint gap-tolerant ordered sequence scan. Gap-tolerant means intermediate events (approval_recorded from GENERATION gate, files_read, etc.) don't break the scan.
- All 43 lab_agent integration tests pass.

## Files Changed
- `src/lab/workflows.py` — added `workflow_started`/`workflow_completed` to GenerateSimulationSetup, PrepareSimulationExecution, RegisterSimulationResult, ProposeSimulationEnhancements; added `manual_boundary_declared` to PrepareSimulationExecution
- `tests/integration/lab_agent/test_human_gated_agentic_lab_e2e.py` — replaced weak audit assertion with 13-checkpoint sequence scan; made approved UpdateSimulationKnowledge run unconditional

## Completion Summary
Added workflow lifecycle audit events to all 5 major workflows and replaced the E2E test's weak "log is non-empty" check with a 13-checkpoint ordered sequence assertion. The test now proves the full generate→prepare→manual-boundary→register→propose→approve→sync pipeline executed in order. 43/43 lab_agent integration tests pass.
