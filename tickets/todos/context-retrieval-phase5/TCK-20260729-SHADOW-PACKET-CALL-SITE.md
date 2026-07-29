---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260729-SHADOW-PACKET-CALL-SITE
phase: open
date: 2026-07-29
tags: [workflows, agent-monitoring, observability]
---

# TCK-20260729-SHADOW-PACKET-CALL-SITE

## Title
Add advisory shadow context-packet call site to implement-ticket.js Investigate phase

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Insert a shadow-packet-build call site into implement-ticket.js's Investigate phase, built via tools/context_packet_assembler.py, that stays strictly advisory (never blocks, never changes gate outcomes, never read by the agent doing that phase's work) and is trivially disable-able. Record the resulting shadow-packet request/outcome through tools/retrieval_events.py's existing emit_retrieval_event() schema/writer path, extending it additively only if a genuinely new field turns out to be necessary — and per this ticket's own resolution, reusing the real ticket's TCK-... run_id as the real-vs-synthetic provenance signal instead of adding a new field.

## Scope
- Add one orchestrator-side bash() call inside implement-ticket.js's Investigate phase (only) that invokes tools/context_packet_assembler.py's assemble_context_packet() via wrap_context_packet_assembly(), mirroring the existing orchestrator-only pattern used by tagCheckOutput/archCheckOutput/docStalenessOutput
- Wrap the invocation with a coreutils `timeout <N>s` around the python3 call — the only fail-open primitive available since no existing timeout primitive exists elsewhere in .claude/workflows/*.js
- Gate the call behind a new `SHADOW_CONTEXT_PACKET_ENABLED` env var, off by default (opt-in), adapting consent_gate.py's env-var pattern into the orchestrator's bash()-based idiom
- Pass the real ticket's TCK-... run_id into wrap_context_packet_assembly() so the emitted retrieval event is attributable to the real workflow run
- Leave wrap_context_packet_assembly()'s hardcoded phase="Retrieval" field unmodified — treated as a deliberate, distinct observation-category label, not a duplicate of implement-ticket.js's own phase names
- Use a minimal smoke-test candidate set (derived from the ticket's own title/summary, or empty) as input to assemble_context_packet() — no real retrieval pipeline wired in
- Verify no new field is required in RETRIEVAL_EVENT_FIELDS; the real run_id alone distinguishes a real workflow-triggered shadow event from Phase 4's synthetic RETRIEVAL-EVENT-<slug> standalone invocations
- Ship the required docs/ path update in the same diff so implement-ticket.js's doc-staleness gate does not hard-block the behavior-changing .claude/workflows/*.js diff

## Out of Scope
- No promotion to default/mandatory workflow behavior — toggle stays opt-in, off by default
- No packet content surfaced to any agent's real prompt/context (that is Phase 6)
- No execution_id/provider fields added to the retrieval event schema
- No live Codex pilot
- No real-candidate wiring via tools/hybrid_retrieval.py — deferred to a follow-up ticket once call-site/disable-toggle/fail-open mechanics are proven safe in production
- No call site added to any phase other than Investigate (not Plan, not any other phase)
- No modification of wrap_context_packet_assembly()'s phase="Retrieval" field or its function signature
- No new shadow_mode (or equivalent) field added to RETRIEVAL_EVENT_FIELDS

## Acceptance Criteria
- [ ] implement-ticket.js's Investigate phase contains an orchestrator-side bash() call invoking assemble_context_packet() via wrap_context_packet_assembly(), matching the tagCheckOutput/archCheckOutput/docStalenessOutput orchestrator-only pattern
- [ ] The invocation is wrapped in `timeout <N>s python3 ...` so a hang or crash cannot delay or block the Investigate phase
- [ ] Forcing the packet-build call to fail or time out does not change the Investigate phase's pushEvent status or the workflow's overall return value (covered by a test that simulates failure)
- [ ] The call site is skipped entirely unless SHADOW_CONTEXT_PACKET_ENABLED=1 is set — verified by a test run with the var unset producing zero shadow-packet events
- [ ] No packet variable or its contents are interpolated into any agent()-prompt template — verified by grep showing zero occurrences inside any agent()-prompt backtick literal
- [ ] The call passes the real ticket's TCK-... run_id into wrap_context_packet_assembly(); wrap_context_packet_assembly()'s phase="Retrieval" field is left unchanged
- [ ] The candidate list passed to assemble_context_packet() is a minimal smoke-test set (ticket title/summary derived, or empty) — no hybrid_retrieval.py call present in the diff
- [ ] No field is added to RETRIEVAL_EVENT_FIELDS; test_retrieval_event_parity_check.py passes unmodified
- [ ] A docs/ path is included in files_changed so the doc-staleness gate does not block the diff

## Related Tickets
None.

## Related Docs
- docs/engine/contracts/context_packet_contract.md
- docs/ai/default_packet_scenarios_decision.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/workflows/implement-ticket.js
- tools/context_packet_assembler.py
- tools/retrieval_events.py
- tools/agent_replay_codex/consent_gate.py
- tools/agent-monitoring/record_events.py
- tools/agent-monitoring/writer.py
- tools/agent-monitoring/vocabulary.py
- tests/tools/test_retrieval_events.py
- tests/tools/test_retrieval_event_parity_check.py
- tests/tools/test_retrieval_event_wrapper_single_source.py

## Assumptions / Open Questions
- Exact timeout duration N (seconds) for the coreutils timeout wrapper is an implementation-time decision, left to the Plan phase, since no existing precedent value exists in this repo
- The specific docs/ file to update to satisfy the doc-staleness gate is a Plan-phase decision (e.g. docs/ai/default_packet_scenarios_decision.md or a new short note under docs/engine/contracts/) — must ship in the same diff

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
