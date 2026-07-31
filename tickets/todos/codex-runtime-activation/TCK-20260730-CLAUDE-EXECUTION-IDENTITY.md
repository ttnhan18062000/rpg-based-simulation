---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260730-CLAUDE-EXECUTION-IDENTITY
phase: open
date: 2026-07-30
tags: [ai, workflows, agent-monitoring, observability, testing]
---

# TCK-20260730-CLAUDE-EXECUTION-IDENTITY

## Title
Activate additive execution identity for new Claude workflow records

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Make the active Claude `implement-ticket` workflow supply coherent provider, execution, ticket, and run identity on new monitoring records before any real concurrent-provider protection is relied on. The shared schema and writer already support these fields, but the real workflow only writes `run_id`, sequence, phase, and agent today. This must preserve legacy data and all current workflow/sidecar behavior.

## Scope
- Update `.claude/workflows/implement-ticket.js` so one immutable execution identity is generated only after a real ticket ID is known, then reused for that one Claude execution.
- Use `provider="claude"` as the canonical new-write token. Treat the older illustrative `claude-code` vocabulary in `docs/ai/monitoring_writer_decision.md` as reader-compatible legacy/documentation vocabulary, never as an alternative newly emitted token.
- Thread `provider`, `execution_id`, and `ticket_id` through subsequent `.claude/current_run` writes and through the new event/run records emitted by `writeMonitoring()`.
- Keep an initial new-ticket Scope call and scope-failure path identity-less until a ticket ID exists; do not synthesize malformed identifiers.
- Preserve `run_id`, sequence-offset/resume behavior, phase/agent sidecar coverage, untracked monitoring-write behavior, and fail-open monitoring semantics.
- Add controlled validation evidence with a pre/post monitoring prefix or manifest comparison; new records may append, but no pre-existing line may change.

## Out of Scope
- Any Codex runtime, hook registration, or Codex monitoring writer.
- A solution for shared-sidecar concurrency across unrelated workflows.
- Historical JSONL backfill, migration, or rewriting.
- Changing dashboard field semantics beyond the established additive reader behavior.

## Acceptance Criteria
- [ ] A controlled Claude `implement-ticket` execution appends coherent `provider`, `execution_id`, `ticket_id`, and `run_id` values to relevant new tools, events, and run records.
- [ ] Every record from one execution uses the same non-empty execution ID; a subsequent execution receives a different ID.
- [ ] New workflow writes use exactly `provider="claude"`; tests define the intended treatment of legacy `claude-code` input without allowing it as a new-write alternative.
- [ ] The no-ticket Scope and scope-failure paths remain identity-less rather than emitting an invalid ticket/execution identity.
- [ ] Existing sidecar adjacency, pause/resume sequence, tool-count attribution, reader/dashboard legacy normalization, and non-blocking writer behavior remain covered and green.
- [ ] Baseline verification proves all pre-existing monitoring JSONL lines/bytes remain unchanged.

## Related Tickets
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC (parent)
- TCK-20260721-MONITORING-WRITER-UNIFICATION (DONE; additive writer/schema)
- TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS (DONE; real-data coverage gap identified)
- TCK-20260731-CODEX-EXECUTION-IDENTITY-TAG-SWEEP (OPEN; filed after the tag-registry-redesign
  batch landed two new `.claude/workflows/implement-ticket.js` code paths in this ticket's own
  target region — `classifyChecklistFailure`'s shell-out to `done_checker_static.py` and a new
  `check_tag_drift` Finalize-phase hook, both added after this ticket was already filed. Investigate
  here must confirm whether either is a real `record_events.py`/`record_run.py` disk-write call
  site needing `provider`/`execution_id` population, or a no-op — see that ticket for the specific
  file:line pointers as of 2026-07-31.)

## Related Docs
- docs/plans/archive/agent_infrastructure/current_codex_runtime_status_and_activation_plan.md
- docs/ai/monitoring_writer_decision.md
- agent-orchestration/monitoring-schema.yaml
- agent-orchestration/intentional-divergences.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- .claude/workflows/implement-ticket.js
- tools/agent-monitoring/post_tool_hook.py
- tools/agent-monitoring/record_events.py
- tools/agent-monitoring/record_run.py
- tests/tools/test_current_run_sidecar_orchestrator.py
- tests/tools/test_post_tool_hook.py
- tests/tools/test_record_events.py
- tests/tools/test_record_run.py
- tests/tools/test_agent_ops_dashboard_ingest.py

## Assumptions / Open Questions
- The controlled validation run is a Claude workflow run and adds only new append-only records.
- The provider-token documentation may need a narrow compatibility clarification rather than a broad schema migration.

## Implementation Notes
(pending — Investigate phase)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
