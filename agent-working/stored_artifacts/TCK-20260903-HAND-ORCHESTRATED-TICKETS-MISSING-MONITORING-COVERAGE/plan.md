---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE
artifact_type: plan
tags: [agent-monitoring, process-improvement]
---

# Plan — TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE

## Decision (see investigation.md for full rationale)

Pursue Scope's **Option 1** only (lightweight standalone recording path for hand-orchestrated
closures). Reject Option 2 (teaching the audit tool an alternate, lower-cost coverage signal) —
it would weaken the audit's real guarantee for no benefit, since Option 1's real path already
exists (`record_run.py`/`record_events.py`) and costs nothing extra to require.

Do **not** add a new blocking/advisory hook or done-checker gate in this ticket — both are
explicitly out of scope per the investigation's two reasons (deliberate `CLAUDE.md` boundary
stating coverage is "guaranteed by workflow — not verified by done-checker"; shared
`.claude/settings.json` hook changes affect every concurrent session immediately, a materially
larger blast radius than this ticket warrants deciding unilaterally). Recorded as a documented
follow-up recommendation instead.

Do **not** backfill the 798 historical missing entries — fabricating records for work that
happened before or without real monitoring instrumentation is forbidden by this project's Durable
State Rule and by the already-established `TCK-20260805-DONE-TICKET-MONITORING-COVERAGE-AUDIT`
precedent.

The 2026-09-03 branch-named isolation-folder question is moot — already resolved by the
already-merged PR #112/#120 unified weekly-shard restructure.

## Implementation steps

1. **New tool**: `tools/agent-monitoring/record_hand_orchestrated_closure.py` — a thin convenience
   wrapper reusing `record_run.py`'s `validate_record`/`compute_duration_s` and
   `record_events.py`'s `validate_record`/`warn_vocabulary_drift`/`compute_tool_stats` directly
   (no reimplementation of validation or duration/cost-proxy logic). Takes `--ticket-id --tier
   --events '[{phase,status,summary},...]'` and auto-fills `run_id`/`execution_id`/`provider`/
   `ticket_id`/`seq`/`agent` — the fields that are identical across every phase of one closure and
   were the real hand-typing burden in this session's own use of the two underlying tools moments
   ago. Writes to the same current-ISO-week shard files the two underlying tools already target.
   **Status: done** (implemented and unit-tested in the Investigate/Implement pass above).

2. **`tests/tools/test_record_hand_orchestrated_closure.py`** — unit tests for `build_records()`
   (pure expansion logic: shared identity fields, sequential seq, agent-override, start/end-ts
   defaulting, and — the real correctness bar — that the expanded output passes both underlying
   tools' own real `validate_record()` unchanged) plus CLI subprocess tests mirroring
   `test_record_run.py`'s isolated-`tmp_path`-cwd pattern. **Status: done.**

3. **`CLAUDE.md`** — add one new bullet under the existing "Always stage `agent-monitoring/`..."
   line in the "After Work" section, stating explicitly that a hand-orchestrated closure (no
   `Workflow` tool call) must record its own run + event coverage via
   `record_hand_orchestrated_closure.py` (or the two underlying tools directly), with the one-line
   recipe, mirroring the Hard Rule's existing requirement for the formal pipeline.

4. **`docs/agent-monitoring/README.md`** — new subsection near the existing "Done-Ticket
   Monitoring Coverage Audit" section documenting the lightweight recording path: why it exists
   (this ticket's own finding — 30 of the audit's `missing` entries are from the last 3 days, not
   historical backlog), the real CLI recipe, and a pointer to `CLAUDE.md`'s requirement.

5. **Ticket closure**: this ticket's own closure will be recorded via the new wrapper — the first
   real dogfooding use, closing the loop (verified as `covered` by a fresh
   `done_ticket_monitoring_coverage.py` run before Finalize completes).

## Explicitly out of scope for this implementation (per investigation.md)
- No new hook in `.claude/settings.json`.
- No change to `tools/gate_checks/done_checker_static.py`'s check set.
- No backfill script or backfilled historical records.
- No change to the `Workflow` tool's own `implement-ticket.js` recording path (already correct).

## Acceptance-criteria map
| AC | Satisfied by |
|---|---|
| A decision is recorded on which fix direction to pursue | investigation.md's Option 1/2 analysis + this plan.md |
| Hand-orchestrated closures have a real, documented, lightweight path | `record_hand_orchestrated_closure.py` (already-working underlying tools, now wrapped + documented) |
| `docs/agent-monitoring/README.md` reflects the new expectation | New subsection (step 4) |
| A decision is recorded on the historical 771/798-ticket gap | investigation.md's explicit no-backfill decision |
