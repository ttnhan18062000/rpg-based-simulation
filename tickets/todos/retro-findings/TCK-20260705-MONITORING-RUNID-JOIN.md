---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260705-MONITORING-RUNID-JOIN
phase: open
date: 2026-07-05
tags: [agent-monitoring, data-quality, root-cause]
---

# TCK-20260705-MONITORING-RUNID-JOIN

## Title
Investigate and harden against run_id/event join mismatches (crashed runs, zero-event runs)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
The first-ever real `make agent-monitoring-retro`/`validate.py` run (`TCK-20260704-RETRO-LOOP-ENFORCEMENT`'s tooling, exercised for real on 2026-07-05) surfaced 21 "crashed" runs (`start_ts` present, no `end_ts`) and 5 runs with zero matching events. Direct investigation found two distinct, confirmed root-cause patterns behind at least some of these, both a **join failure between `runs.jsonl` and `events.jsonl`**, not necessarily a genuine workflow crash:

1. **Timestamp-generation race.** `run-E43B-1782052024` (in `runs.jsonl`, zero events) vs. `run-E43B-1782052032` (in `events.jsonl`, 7 real Scope/Investigate/Plan/... events) — an 8-second gap between two independently-generated Unix-timestamp-suffixed IDs for what is clearly the same logical run. **Important caveat, confirmed by reading the current code**: `.claude/workflows/implement-ticket.js`'s `tid` (line 109, `const tid = ticketInfo.ticket_id`) and `implement-epic.js`'s `batchRunId` (line 216) are each captured **once** from a stable source and reused consistently for every subsequent write in that same execution — the current workflow scripts, as written, cannot produce this specific race. This mismatch is either (a) debris from an older version of the workflow scripts predating this capture-once pattern, or (b) produced by a direct/manual `record_run.py`/`record_events.py` invocation (e.g. a `manual-hotfix` entry, or an agent generating its own ad hoc run_id) rather than the standard workflow path. Which of these is true is not yet confirmed — that's this ticket's first job.
2. **Ticket-rename mismatch.** `TCK-20260701-HAZARD-NATIVE-IMMUNITY-REDESIGN` (the run record) vs. `TCK-20260701-HAZARD-NATIVE-IMMUNITY` (its events, no `-REDESIGN` suffix). Plausible explanation: two separate execution attempts against the same underlying ticket, where the ticket file/ID was renamed between them — the events from an earlier, incomplete attempt got orphaned under the pre-rename ID while a later run wrote the final run record under the renamed ID. Not yet confirmed against actual ticket/git history.

15 of the 21 "crashed" (no `end_ts`) runs cluster tightly around 2026-06-23 00:00–02:00 (the `E62A`–`E62D`/`E63A`–`E63D` phase batch and their parent `EPIC-*` wrappers) — suggesting a specific historical incident on that date (a session crash, a context-compaction event, or a bug in how that particular epic batch's finalization ran) rather than 15 independent occurrences of the same bug. Worth checking whether those underlying tickets are actually `DONE` in `tickets/done/` (i.e. the real work completed fine and only the monitoring write failed) before assuming anything is actually broken in the simulation/engine work itself.

## Scope
- Confirm, for each of the 21 crashed runs and 5 zero-event runs, whether the underlying ticket/epic actually completed successfully (check `tickets/done/` and `working_log.csv`) — distinguishing "real workflow crash, work never finished" from "work finished fine, only the monitoring write joined incorrectly."
- Confirm whether pattern 1 (timestamp race) is reproducible with the *current* `.claude/workflows/*.js` code, or whether it is exclusively historical/pre-refactor debris and/or a symptom of `manual-hotfix`-style direct script invocations that don't go through the workflow's single-capture `tid` pattern.
- Confirm whether pattern 2 (rename mismatch) is explained by a genuine two-attempt history for that specific ticket (check `tickets/done/TCK-20260701-HAZARD-NATIVE-IMMUNITY-REDESIGN.md` and any git history for a rename).
- Based on findings, add a defensive safeguard appropriate to whatever the confirmed live risk actually is — e.g. `record_run.py`/`record_events.py` warning (not failing — matches this repo's "monitoring write failure must never fail the workflow" hard rule) if a `run_id` passed to one script was never seen by the other within some window, or a stronger convention/lint against direct manual invocation using ad hoc IDs instead of the workflow's stable `tid`.
- Investigate the 2026-06-23 cluster specifically — is there a single, identifiable incident (crash, compaction, bug in a specific commit active that day) that explains 15 of 21 cases at once, rather than treating each as an independent occurrence?

## Out of Scope
- Backfilling or repairing the historical `runs.jsonl`/`events.jsonl` records themselves — append-only log, matching the precedent already established for other agent-monitoring schema drift this session (leave history alone, fix going forward).
- Fixing `validate.py`'s separate schema blind spot around the legacy `status` field (tracked in `TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP`) — related but independent finding from the same retro run.
- Fixing `generate_retro.py`'s misleading empty-summary/epic-DONE-rate metrics (tracked in `TCK-20260705-RETRO-METRIC-ACCURACY`) — a report-generation issue, not a run_id-join issue.

## Acceptance Criteria
- [ ] Each of the 21 crashed runs and 5 zero-event runs is classified: genuine crash (work incomplete) vs. join mismatch (work completed, monitoring write joined incorrectly) vs. legacy-schema debris predating the current write pattern.
- [ ] Root cause of the timestamp-race pattern (E43B example) is confirmed: live risk in current code, manual-invocation artifact, or pre-refactor historical debris only.
- [ ] Root cause of the rename-mismatch pattern (HAZARD-NATIVE-IMMUNITY example) is confirmed against actual ticket/git history.
- [ ] The 2026-06-23 cluster (15 of 21 crashed runs) has an identified common cause, or is confirmed to be 15 independent occurrences with no shared trigger.
- [ ] A safeguard is added matching whatever live risk is actually confirmed — or, if no live risk is found (pure historical debris), the finding is documented in `docs/agent-monitoring/schema.md`'s known-limitations section rather than left as an open, unexplained validator warning.

## Related Tickets
- TCK-20260704-RETRO-LOOP-ENFORCEMENT (shipped the retro skill/hook that surfaced this finding on its first real run)
- TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP (sibling finding from the same investigation — validate.py's own blind spot)
- TCK-20260705-RETRO-METRIC-ACCURACY (sibling finding — misleading retro report metrics)

## Related Docs
- docs/guides/agent_monitoring.md
- docs/agent-monitoring/schema.md
- agent-monitoring/retro/RETRO-ALL.md (this ticket's originating finding, Notes section)
- docs/plans/agent_infrastructure/idea_agent_monitoring_schema_enforcement.md (related schema-drift idea from earlier this session — this ticket's findings are additional evidence for that idea, not a duplicate of it)

## Related Stored Artifacts
None yet.

## Related Code Areas
- tools/agent-monitoring/record_run.py
- tools/agent-monitoring/record_events.py
- tools/agent-monitoring/validate.py
- .claude/workflows/implement-ticket.js (line 109, `tid` capture)
- .claude/workflows/implement-epic.js (line 216, `batchRunId` capture)
- agent-monitoring/runs.jsonl, agent-monitoring/events.jsonl (read-only — data being investigated)

## Assumptions / Open Questions
- Whether any of these 21+5 cases represent a genuinely incomplete, still-broken piece of work (not just a monitoring artifact) — must be checked against `tickets/done/` before assuming this is purely a bookkeeping issue.
- Whether a "manual-hotfix" or similarly direct invocation path (bypassing the workflow JS's single-capture `tid` pattern) is still in active use anywhere in this repo's current tooling — if so, that's the more likely live risk than the workflow scripts themselves.

## Implementation Notes
(not yet implemented — ticket filed for review before proceeding)

## Test Summary
(not yet implemented)

## Files Changed
(not yet implemented)

## Completion Summary
(not yet implemented)
