---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE
phase: done
date: 2026-09-03
tags: [agent-monitoring, process-improvement]
---

# TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE

## Title
Hand-orchestrated ticket closures never get a run_id in agent-monitoring/runs.jsonl — 771/1773 done tickets already missing coverage

## Status
DONE

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
- [x] A decision is recorded on which fix direction (or combination) to pursue. (Option 1 only —
      see investigation.md/plan.md.)
- [x] Hand-orchestrated ticket closures have a real, documented, lightweight path to monitoring
      coverage — either by writing real entries or by the coverage-audit tool recognizing an alternate
      signal. (Real entries, via new `record_hand_orchestrated_closure.py`.)
- [x] `docs/agent-monitoring/README.md` (or the relevant schema doc) reflects the new expectation.
- [x] A decision is recorded (not necessarily executed) on whether the historical 771-ticket gap gets
      backfilled or explicitly accepted as-is. (Explicitly not backfilled.)

## Related Tickets
None yet — discovered as a byproduct of `TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP`'s closure, not tied
to a prior ticket.

## Related Docs
- `docs/agent-monitoring/README.md`
- `docs/agent-monitoring/schema.md`
- CLAUDE.md's "After Work" checklist and Hard Rules (monitoring requirement)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE/`

## Related Code Areas
- `tools/agent-monitoring/done_ticket_monitoring_coverage.py` (the audit that surfaced this)
- `tools/agent-monitoring/record_run.py` / `record_events.py` (the real writers, reused unchanged)
- `tools/agent-monitoring/record_hand_orchestrated_closure.py` (new — this ticket's deliverable)
- `agent-monitoring/data/<ISO-week>/{runs,events}.jsonl`

## Assumptions / Open Questions
- Whether a lightweight standalone recording helper is worth building (real tooling cost) versus
  teaching the audit tool a second, cheaper coverage signal (lower cost, but weakens the audit's own
  original guarantee that a `run_id` implies a full pipeline run actually happened) — this tradeoff is
  the central decision this ticket needs to make, not pre-resolved here.
- Whether PR #112's weekly-sharding restructure changes the shape of `runs.jsonl`/`events.jsonl` enough
  that this ticket should wait until that lands before scoping further — check PR #112's final state
  before starting investigation.

## Implementation Notes
Re-ran the coverage audit fresh rather than trusting the ticket's own 2-day-old 771/1773 figure:
now 798/1815 missing, 30 of which are dated this month (well after the 2026-06-07 rollout) —
confirmed the gap is a real, ongoing pattern (hand-orchestrated closures never recording, not a
shrinking historical tail as the 2026-08-05 investigation's own verdict concluded at the time).

Discovered the lightweight recording path Scope's Option 1 asks for already exists and already
works — `record_run.py`/`record_events.py`, confirmed by direct use recording this session's own
2 immediately-preceding hotfix closures before this ticket started. The real gap was
discoverability (nothing in `CLAUDE.md` tells a hand-orchestrating session to call them) plus
friction (each closure requires hand-crafting 2 raw JSON payloads with 6+ repeated boilerplate
fields per event). Rejected Option 2 (teaching the audit tool an alternate signal) since it would
weaken the audit's real guarantee for no benefit — Option 1's real path costs nothing extra.

Built `tools/agent-monitoring/record_hand_orchestrated_closure.py` as a thin wrapper: imports and
reuses `record_run.py`'s `validate_record`/`compute_duration_s` and `record_events.py`'s
`validate_record`/`warn_vocabulary_drift`/`compute_tool_stats` directly (zero duplicated
validation/computation logic), auto-filling the shared `run_id`/`execution_id`/`provider`/
`ticket_id`/`seq` fields from a minimal `{phase, status, summary}` event list.

Decided NOT to add a new hook or done-checker gate: `CLAUDE.md`'s Definition of Done already states
coverage is "guaranteed by workflow — not verified by done-checker," a deliberate existing
boundary; and `.claude/settings.json` hook changes affect every concurrent session immediately (3+
other sessions confirmed actively running via `ps aux`/`git worktree list` at implementation time)
— too large a blast radius for a single ticket to decide unilaterally. Recorded as a follow-up
recommendation in `docs/agent-monitoring/README.md` instead of silently dropped.

Decided NOT to backfill the 798 historical missing entries — matches
`TCK-20260805-DONE-TICKET-MONITORING-COVERAGE-AUDIT`'s own established precedent; fabricating
records for real work that happened without real monitoring instrumentation is forbidden by
CLAUDE.md's Durable State Rule.

The 2026-09-03 branch-named isolation-folder question (Scope's third bullet) is moot — already
resolved by the already-merged PR #112/#120 unified weekly-shard restructure.

Dogfooded: this ticket's own closure is recorded through the new wrapper (see Completion Summary),
the first real use beyond its own tests.

## Test Summary
- `pytest tests/tools/test_record_hand_orchestrated_closure.py -v` — 12 passed (pure `build_records()`
  expansion logic: shared identity fields, sequential seq, agent override, start/end-ts defaulting,
  and — the real correctness bar — output passes both underlying tools' own real `validate_record()`
  unchanged; CLI subprocess tests: real write to an isolated `tmp_path` cwd, invalid-tier rejection,
  missing-field rejection with no partial write, empty-events rejection, overridable
  final-status/workflow).
- `pytest tests/tools/test_record_run.py tests/tools/test_record_events.py tests/tools/test_done_ticket_monitoring_coverage.py -v` —
  62 passed (regression check: reusing these 3 modules' functions required zero changes to any of
  them).
- `python3 tools/validate_frontmatter.py docs/agent-monitoring/README.md --content-type doc` — OK.

## Files Changed
- `tools/agent-monitoring/record_hand_orchestrated_closure.py` (new)
- `tests/tools/test_record_hand_orchestrated_closure.py` (new)
- `CLAUDE.md` — new "After Work" bullet requiring hand-orchestrated closures to record their own
  coverage, with the CLI recipe.
- `docs/agent-monitoring/README.md` — corrected the Done-Ticket Monitoring Coverage Audit section's
  "not an ongoing systemic bug" framing with this ticket's live-recurrence finding, and added a new
  "Recording coverage for a hand-orchestrated closure" subsection.

## Completion Summary
Confirmed the coverage gap is real and ongoing (798/1815 missing, 30 from the last ~3 days), not
just a converging historical tail. The lightweight recording path Scope's Option 1 asked for
already existed (`record_run.py`/`record_events.py`) — the real gap was discoverability and
per-call friction, both closed by a new thin wrapper
(`record_hand_orchestrated_closure.py`, reusing both underlying modules' validation/computation
logic unchanged) plus new `CLAUDE.md`/README documentation making the requirement explicit. Option
2 (a weaker audit signal) was rejected in favor of Option 1's real, zero-extra-cost path. No new
gate/hook was added — a deliberate, documented scope boundary (existing done-checker contract,
shared-settings blast radius), not an oversight. The 798 historical entries are explicitly not
backfilled, matching established precedent. Dogfooded: this ticket's own closure was recorded via
the new wrapper and confirmed `covered` by a fresh audit run before Finalize.
