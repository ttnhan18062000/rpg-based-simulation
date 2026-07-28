---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260728-PHASE0-PREREQ-CONFIRMATION
phase: open
date: 2026-07-28
tags: [observability]
---

# TCK-20260728-PHASE0-PREREQ-CONFIRMATION

## Title
Confirm Phase 0 Prerequisite Is Satisfied for Context-Efficient Retrieval Epic

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Verify that the Phase 0 prerequisite — provider-neutral execution identity, shared monitoring writer, and a stable replay/live boundary — is genuinely in place before any later phase work proceeds. This is a confirmation task only, not new implementation; state plainly whether the prerequisite is satisfied or not.

## Scope
- Verify execution_id/provider/ticket_id model is documented and actually written into tools.jsonl (agent_orchestration_contract.md, post_tool_hook.py)
- Verify writer.py write_line()/write_lines() is the sole append path for post_tool_hook.py, record_run.py, record_events.py
- Verify consent_gate.require_live_consent() and enabled_surface.py correctly restrict the Codex pilot surface
- Run assert_monitoring_writer_landed() directly and the full related test suites to confirm current pass state, enumerating the 5 skipped tests individually
- Produce a written confirmation record stating plainly whether the Phase 0 prerequisite is satisfied

## Out of Scope
- Does NOT fix TCK-20260721-MONITORING-WRITER-UNIFICATION's own frontmatter/body status bug (status:active/phase:open/##Status OPEN contradicting its own Completion Summary and working_log.csv) — that is a known, separately-tracked doc-hygiene issue, handled as its own hotfix outside this ticket
- Does not implement any new monitoring writer, execution-identity, or replay/live boundary behavior — confirmation only
- Does not run a live Codex pilot execution to obtain real end-to-end production evidence beyond structural/test-based verification

## Acceptance Criteria
- [ ] Confirmation record states execution_id/provider/ticket_id model is documented and actually written into tools.jsonl, citing post_tool_hook.py:84-86
- [ ] Confirmation record states writer.py write_line()/write_lines() is verified as the sole append path for post_tool_hook.py, record_run.py, record_events.py
- [ ] Confirmation record states consent_gate.require_live_consent() + enabled_surface.py correctly restrict the pilot, evidenced by assert_monitoring_writer_landed() passing directly and full test suite results (61 passed, 5 skipped) with skip reasons enumerated as consent-gated vs broken
- [ ] Confirmation record explicitly notes zero real live Codex pilot executions have occurred; replay/live boundary is proven structurally/via tests only
- [ ] Confirmation record explicitly flags TCK-20260721-MONITORING-WRITER-UNIFICATION's ticket-file status mismatch as a known, separately-tracked issue not fixed here

## Related Tickets
- TCK-20260721-MONITORING-WRITER-UNIFICATION
- TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC

## Related Docs
- docs/architecture/agent_orchestration_contract.md
- tickets/done/TCK-20260721-MONITORING-WRITER-UNIFICATION.md
- tickets/done/TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/writer.py
- tools/agent-monitoring/post_tool_hook.py
- tools/agent-monitoring/record_run.py
- tools/agent-monitoring/record_events.py
- tools/agent_replay_codex/consent_gate.py
- tools/agent_replay_codex/entry_criterion.py
- tools/agent_replay_codex/provenance_check.py
- tools/agent_codex_pilot_guardrails/enabled_surface.py

## Assumptions / Open Questions
- 5 skipped tests in the full suite run were not individually enumerated to confirm consent-gated vs genuinely broken — needs verification during this ticket's work
- No live Codex pilot has ever run (by design); replay/live boundary is proven structurally/via tests only, not via real end-to-end production execution

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
