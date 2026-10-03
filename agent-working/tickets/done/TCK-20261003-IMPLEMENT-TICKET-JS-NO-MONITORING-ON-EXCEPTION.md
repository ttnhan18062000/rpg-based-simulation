---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261003-IMPLEMENT-TICKET-JS-NO-MONITORING-ON-EXCEPTION
phase: done
date: 2026-10-03
tags: [ai, process-improvement, observability]
---

# TCK-20261003-IMPLEMENT-TICKET-JS-NO-MONITORING-ON-EXCEPTION

## Title
A native `implement-ticket` run that dies on an uncaught exception writes no run or event record, which breaks the rule that every run records both

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary

Project rule (CLAUDE.md, Hard Rules): every `implement-ticket` run, hotfix included, must record a run entry and at least one event
entry; a monitoring *write* failure must never fail the workflow. The second half is implemented (writes are best-effort). The first
half has a gap: on 2026-10-03 the first native run (a throwaway hotfix after #295) died with `ReferenceError: bash is not defined`
at the Scope phase, and the implementer found **no run or event row anywhere** under `agent-working/agent-monitoring/data/2026-W40/`
for it. In `.claude/workflows/implement-ticket.js` (origin/main) `writeMonitoring(...)` is called only on named terminal statuses
(for example `CONFLICTS_DETECTED`, `TESTS_FAILED`, `DOD_BLOCKED`, `FINALIZE_INCOMPLETE` and the final outcome); a scan for `try`/`finally`
found only local parse guards and no top-level handler, so an exception thrown between those points skips every write. Facts
established by the implementer's run and a read of the script; I did not re-run it. A comment in `writeMonitoring` already anticipates a
run that crashed before Scope captured a timestamp, but no code path reaches it on a thrown exception.

The cause of the native run's exception (the runtime has no `bash`, so the remaining `bash()` gate sites at lines 553, 805, 1042, 1360,
1424, 1478, 1569, 1570, 1915 and 1967 will throw) belongs to the native-port epic children and is out of scope here. This ticket
makes **any** such failure leave a record.

## Scope

- On an uncaught exception anywhere in the run, record a run entry and one event whose status names the failure (for example
  `WORKFLOW_ERROR`) with the phase reached and the error message (bounded length), then rethrow so the run still fails visibly.
- The recording must itself be best-effort: if it throws, swallow and rethrow the **original** error, never the recorder's.
- Prefer the smallest structural change: a wrapper around the top-level body, or an equivalent; do not re-indent 1,900 lines if a
  smaller form exists. Preserve the adjacency strings and ordering that `tests/tools/test_current_run_sidecar_orchestrator.py` and the
  other tests pinning this file rely on; run them before and after.
- Tests: a forced-failure test (a stubbed dispatch that throws at a chosen phase) asserting that a run record and an event with the
  error status are written and that the original error propagates; a positive control where the run succeeds and writes the normal record
  once, not twice (the duplicate-run ratchet counts duplicates).

## Out of Scope

- Porting the `bash()` gate sites (native-port epic children `TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT` /
  `NATIVE-PORT-ATTESTED-GATE-SITES`, `NATIVE-PORT-SMALL-TICKET-NATIVE-RUN`).
- Any change to which statuses count as DONE, to prompts, or to the sidecar logic.
- Running a native `Workflow` end to end (needs the owner's opt-in).

## Acceptance Criteria

1. A thrown exception at a named phase produces exactly one run entry and at least one event entry with an error status and the phase
   reached, then the original exception propagates.
2. A recorder failure does not mask the original exception.
3. A successful run writes the same records as before (no extra row).
4. The tests that pin the file's layout pass; the new tests have a positive control.

## Related Tickets

`TCK-20261003-IMPLEMENT-TICKET-JS-USE-BEFORE-DEFINE` (found the first native run; merged #295), `TCK-20261003-AGENT-WORKING-ROOT-MOVE` (AC 9),
`TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT` (epic), `TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE` (same rule, other path).

## Related Docs
`CLAUDE.md` Hard Rules; `docs/guides/delivery_process.md`.

## Related Stored Artifacts
(None.)

## Related Code Areas
`.claude/workflows/implement-ticket.js` (`writeMonitoring`, the top-level body); `tests/tools/test_current_run_sidecar_orchestrator.py`.

## Assumptions / Open Questions

- Assumed the native runtime's `agent()` still works after an exception so the recorder can dispatch; not verified. If the recorder cannot
  run in the native runtime at all, the test must show that and the ticket records the limit.
- Whether an error event should count toward the run's DONE/FAILED classification in the retro is left to the implementer to match the
  existing status vocabulary.

## Implementation Notes
Verified before editing: `implement-ticket.js` on origin/main had no top-level `try`/`finally` (only local JSON parse guards), and `writeMonitoring` was reached only on named terminal statuses.

The body from `phase('Scope')` to the end now sits inside one `try { ... }` with no re-indentation, opened just after `shOmit` so `sh`, `shOmit`, `legacyBash`, `ticketId` and `tierOverride` stay visible to the recorder. The `catch` calls `recordWorkflowError(err)` and rethrows the original error. The recorder swallows its own failures. `writeMonitoring` sets `workflowMonitoringStarted` first, so an exception inside or after a normal write never writes a second run row. Once `writeMonitoring` exists, `workflowErrorHook` pushes one `failed` event (phase = the last phase an event was pushed for, agent `implement-ticket-orchestrator`, summary `WORKFLOW_ERROR after <phase>: <bounded text>`) and calls `writeMonitoring('WORKFLOW_ERROR')`. Before that (an exception during Scope), a fallback writes a minimal event and run row through `record_events.py` / `record_run.py`, the way `SCOPE_AGENT_FAILED` does.

`WORKFLOW_ERROR` is a new terminal status, so it was added to `agent-working/agent-orchestration/terminal-statuses.yaml` (non-breaking, schema version stays 1) and to the `final_status` table in `docs/agent-monitoring/schema.md`; four count pins moved (16 to 17 statuses, 14 to 15 literal call sites, 13 to 14 distinct literals).

Open question answered: whether the native runtime's `agent()` still works after an exception was NOT verified here. The tests run the script in a node `vm` with stubbed dispatches, not in the native runtime. A native run is not part of this ticket and needs the owner's opt-in.

## Test Summary
New `tests/tools/test_implement_ticket_records_on_exception.py` (5 tests, node `vm` with stubbed `agent()`/`bash()`): an exception after Scope writes exactly one monitoring dispatch carrying `final_status` `WORKFLOW_ERROR` and the rethrown original error; an exception before Scope finishes writes one fallback event and one run row; a throwing recorder does not mask the original error; a normal gate return (`CONFLICTS_DETECTED`) writes one record and no `WORKFLOW_ERROR`; an exception inside the normal monitoring write writes no second run row. The first two fail on the pre-change script. 46 files naming `implement-ticket.js`, `tests/agent_orchestration_claude_adapter`, `tests/docs`, the order test and `test_validate_agent_monitoring.py`: 685 passed, 11 skipped, 2 xfailed. The tests skip when `node` is absent.

## Files Changed
- .claude/workflows/implement-ticket.js (recorder, one `try`/`catch`, flag in `writeMonitoring`, error hook)
- agent-working/agent-orchestration/terminal-statuses.yaml (WORKFLOW_ERROR)
- docs/agent-monitoring/schema.md (WORKFLOW_ERROR row)
- tests/tools/test_implement_ticket_records_on_exception.py (new)
- tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py, test_terminal_status_schema.py, test_generator_containment.py (count pins)

## Completion Summary
An uncaught exception anywhere in `implement-ticket.js` now records one `WORKFLOW_ERROR` event and one run row best-effort, then rethrows the original error; a normal write is never doubled. Not verified: behaviour inside the native `Workflow` runtime (needs the owner's opt-in).
