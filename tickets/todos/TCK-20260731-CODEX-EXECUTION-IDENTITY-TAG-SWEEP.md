---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260731-CODEX-EXECUTION-IDENTITY-TAG-SWEEP
phase: open
date: 2026-07-31
tags: [ai, workflows, agent-monitoring]
---

# TCK-20260731-CODEX-EXECUTION-IDENTITY-TAG-SWEEP

## Title
Sweep the tag-registry-redesign epic's new `.claude/workflows/implement-ticket.js` surface into CLAUDE-EXECUTION-IDENTITY's provider/execution_id call-site coverage

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
The `tag-registry-redesign` epic (folder `tickets/todos/tag-registry-redesign/`, tickets
`TCK-20260720-TAG-CATEGORY-REGISTRY` through `TCK-20260720-TAG-RELEVANCE-VERIFY`) was scoped and
partially implemented before the provider-agnostic implementation epic
(`TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC`) closed. That epic's closure doc
(`docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_batch_closure_claude.md`,
"Carried-Forward Items" #1) flags that `provider`/`execution_id` fields are schema-supported in
`agent-monitoring/*.jsonl` but not yet populated by any real call site in
`.claude/workflows/implement-ticket.js` — that gap is explicitly deferred to
`TCK-20260730-CLAUDE-EXECUTION-IDENTITY` (currently in `tickets/todos/codex-runtime-activation/`,
not yet implemented).

Two tickets in the tag-registry-redesign batch add new code paths to
`.claude/workflows/implement-ticket.js` in that same region:
- `TCK-20260720-TAG-TOUCHPOINT-CLEANUP` rewrote `classifyChecklistFailure` to shell out to
  `tools/gate_checks/done_checker_static.py::_frontmatter_has_unregistered_tags` (a plain function
  call, not itself a monitoring-jsonl writer).
- `TCK-20260720-TAG-RELEVANCE-VERIFY` (in progress as of this ticket's filing) adds a
  `check_tag_drift` Finalize-phase hook, wired after `writeMonitoring('DONE')`, mirroring
  `check_monitoring_write_recorded`'s existing pattern (including its post-`writeMonitoring`
  `pushEvent` call, which — per that existing pattern — mutates the local `events` array without a
  further disk flush, since `writeMonitoring` has already run).

Neither addition is confirmed to introduce a *new* real `record_events.py`/`record_run.py` disk
write — both currently piggyback on `writeMonitoring`'s existing call sites or exercise an
already-unflushed `pushEvent` pattern. This ticket exists so that fact gets checked, not assumed,
by whichever ticket actually does the `implement-ticket.js` call-site sweep for
`provider`/`execution_id` population, rather than silently missing two call sites added after that
carried-forward item was written.

## Scope
- When `TCK-20260730-CLAUDE-EXECUTION-IDENTITY` (or whatever ticket ends up doing the
  `provider`/`execution_id` call-site sweep of `.claude/workflows/implement-ticket.js`) runs its
  own Investigate phase, it must re-grep the live file at that time (it will, by construction) —
  this ticket's only job is to leave a durable, findable pointer to the two specific
  tag-registry-redesign-era additions above, so that sweep's own investigation.md explicitly
  confirms (not assumes) whether either needs `provider`/`execution_id` treatment.
- No code change is prescribed here. This ticket's Investigate phase (when picked up) should
  re-read the by-then-current state of `classifyChecklistFailure` and `check_tag_drift`'s wiring
  and either (a) confirm CLAUDE-EXECUTION-IDENTITY already covered them, closing this ticket as a
  no-op confirmation, or (b) file the concrete fix if a gap is found.

## Out of Scope
- Implementing `TCK-20260730-CLAUDE-EXECUTION-IDENTITY` itself.
- Any other codex-runtime-activation batch ticket's scope.
- Redesigning `check_tag_drift`/`tag_relevance_flags` to be provider-neutral or to write directly
  into `agent-orchestration/` — the current architecture's own stated direction
  (`agent-orchestration/README.md`) explicitly defers the "contract becomes source of truth"
  flip to unspecified later work; this ticket does not pull that flip forward.

## Acceptance Criteria
- [ ] `TCK-20260730-CLAUDE-EXECUTION-IDENTITY`'s own investigation.md (once that ticket is
      implemented) is confirmed to have swept `classifyChecklistFailure`'s shell-out and
      `check_tag_drift`'s Finalize hook, OR this ticket's own Investigate phase performs that sweep
      directly if CLAUDE-EXECUTION-IDENTITY already closed without covering them.
- [ ] A concrete finding is recorded either way: "no real monitoring-jsonl write introduced by
      either call site, no fix needed" or "gap found, fix filed as \<ticket-id\>" — not left silently
      unresolved.

## Related Tickets
- TCK-20260730-CLAUDE-EXECUTION-IDENTITY
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC
- TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC
- TCK-20260720-TAG-TOUCHPOINT-CLEANUP
- TCK-20260720-TAG-RELEVANCE-VERIFY

## Related Docs
- docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_batch_closure_claude.md
- agent-orchestration/README.md
- docs/ai/monitoring_writer_decision.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/workflows/implement-ticket.js
- tools/gate_checks/done_checker_static.py
- tools/agent-monitoring/record_events.py
- tools/agent-monitoring/record_run.py

## Assumptions / Open Questions
- Assumes `TCK-20260730-CLAUDE-EXECUTION-IDENTITY` will run its own fresh grep of
  `implement-ticket.js` rather than working from a stale file list — if that assumption turns out
  false when that ticket is actually implemented, this ticket becomes the fallback sweep instead.
- Whether `check_tag_drift`'s exact final wiring (still being implemented as of this ticket's
  filing, in `TCK-20260720-TAG-RELEVANCE-VERIFY`) ends up calling `pushEvent` post-`writeMonitoring`
  at all is not yet settled — this ticket's Investigate phase must re-check against whatever
  actually landed, not this description's snapshot.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
