---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE
phase: open
date: 2026-09-03
tags: [agent-monitoring, process-improvement]
---

# TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE

## Title
Hand-orchestrated ticket closures never get a run_id in agent-monitoring/runs.jsonl — 771/1773 done tickets already missing coverage

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`tools/agent-monitoring/done_ticket_monitoring_coverage.py` (a real, existing audit) confirms **771 of
1773 done tickets (43%) currently have zero matching `run_id` in `agent-monitoring/runs.jsonl`**. Root
cause, confirmed directly: `runs.jsonl`/`events.jsonl` are only ever written by the formal
`implement-ticket.js` Workflow pipeline (per CLAUDE.md's Hard Rule, "Every implement-ticket workflow
run... must record a run entry and at least one event entry"). Any ticket closed by a session
hand-orchestrating the work directly — reading the ticket, editing code, running tests, updating the
parity ledger and working log, moving the file to `tickets/done/` — without invoking the actual
`Workflow` tool, produces zero canonical monitoring records, regardless of how much real, verified work
went into it. This is not rare: it's the pattern this session itself used for several closed tickets in
2026-09-02/03 (e.g. `TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP`), confirmed newly present in the
`missing` list the moment they closed.

Surfaced during 2026-09-03 work: a temporary, user-directed monitoring isolation (writing run/event
entries to a branch-named `agent-monitoring/<branch>/` folder instead of the canonical files, because
another session was mid-restructure on `agent-monitoring/tools.jsonl` via PR #112) made the gap visible
in real time, but the underlying gap predates that isolation entirely and is not caused by it — it is a
structural property of hand-orchestrated ticket work never having had a lightweight recording path of
its own.

## Scope
- Decide the fix direction (see Assumptions/Open Questions — this needs a real decision, not an
  assumed default):
  1. Give hand-orchestrated closures a lightweight, standalone way to record a real run + event entry
     (a small script/helper a session can call directly, without needing the full multi-agent
     `implement-ticket.js` pipeline), and make doing so part of the standard "After Work" checklist in
     the project `CLAUDE.md`.
  2. Teach `done_ticket_monitoring_coverage.py` (and any dashboard/retro tooling built on the same
     assumption) to also recognize an alternate, lower-cost coverage signal for hand-orchestrated work
     (e.g. a `working_log.csv` row plus a specific marker), rather than requiring the full
     `implement-ticket.js`-shaped run record.
  3. Some combination of both.
- Whatever direction is chosen, backfill or explicitly accept the existing 771-ticket gap (a mass
  backfill is likely not worth it for historical tickets — decide and record the call rather than
  leaving it implicit).
- If a branch-named isolation folder pattern (like the one used 2026-09-03) recurs in the future, decide
  whether it should be a first-class supported mode (with its own reconciliation step back into the
  canonical files) rather than an ad hoc one-off.

## Out of Scope
- The specific PR #112 monitoring-restructuring work itself (weekly sharding) — separate, already
  in-flight effort with its own tickets.
- Fixing the 771 already-missing historical entries individually — a bulk-backfill decision (if any) is
  in scope, per-ticket investigation is not.
- Any change to when/how the full `implement-ticket.js` Workflow pipeline itself records monitoring data
  — that path already works correctly; this ticket is only about the hand-orchestrated gap.

## Acceptance Criteria
- [ ] A decision is recorded on which fix direction (or combination) to pursue.
- [ ] Hand-orchestrated ticket closures have a real, documented, lightweight path to monitoring
      coverage — either by writing real entries or by the coverage-audit tool recognizing an alternate
      signal.
- [ ] `docs/agent-monitoring/README.md` (or the relevant schema doc) reflects the new expectation.
- [ ] A decision is recorded (not necessarily executed) on whether the historical 771-ticket gap gets
      backfilled or explicitly accepted as-is.

## Related Tickets
None yet — discovered as a byproduct of `TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP`'s closure, not tied
to a prior ticket.

## Related Docs
- `docs/agent-monitoring/README.md`
- `docs/agent-monitoring/schema.md`
- CLAUDE.md's "After Work" checklist and Hard Rules (monitoring requirement)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/agent-monitoring/done_ticket_monitoring_coverage.py` (the audit that surfaced this)
- `tools/agent-monitoring/record_events.py` (the real writer, currently only called by the Workflow
  pipeline)
- `agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`

## Assumptions / Open Questions
- Whether a lightweight standalone recording helper is worth building (real tooling cost) versus
  teaching the audit tool a second, cheaper coverage signal (lower cost, but weakens the audit's own
  original guarantee that a `run_id` implies a full pipeline run actually happened) — this tradeoff is
  the central decision this ticket needs to make, not pre-resolved here.
- Whether PR #112's weekly-sharding restructure changes the shape of `runs.jsonl`/`events.jsonl` enough
  that this ticket should wait until that lands before scoping further — check PR #112's final state
  before starting investigation.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
