---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality, process-improvement]
---

# TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC

## Title
Agent-monitoring records implausible data that no mechanism flags — eight anomaly classes found in one sweep, none of which register as a failure anywhere

## Status
EPIC_SCOPED

## Tier
epic

## Type
repair

## Priority
P1

## Request Summary
A deep two-week review (`agent-monitoring/retro/RETRO-LAST14D.md`, 2026-09-15) ran a structural
anomaly sweep over the full corpus — 1,609 runs / 10,594 events / 225,500 tool rows — looking for
records that are *strange* rather than *failed*. Eight distinct classes turned up. **None of them
appears as a failure in any existing report, gate, or validator.** Every one reads as green.

This is the same shape as the thirteen dead mechanisms catalogued across the 2026-09-11→15 batch
(`docs/plans/agent_infrastructure/reachability_verification_findings.md`), but located in the
monitoring corpus itself: the system is good at recording failures and blind to implausibility.
`make agent-monitoring-validate` checks that records are *present* (DONE has a working_log row, a
run has at least one event); nothing checks that a present record is *coherent*.

**Why this matters concretely:** the review's own headline figure — 249 runs in the window — is
inflated by an unknown share of the 60 duplicate run records found below. A retro cannot report
throughput it cannot trust, and every spend table is computed on ~76% of real tool volume.

### Findings deliberately NOT ticketed — checked and found healthy

Recorded so no child ticket re-investigates them:

- **232 DONE runs containing a `failed` event → 223 are healthy retries.** The failed phase later
  succeeded or had a Recheck. That is the gate loop working as designed. Only 9 never show a later
  success, all June–August, and they are folded into the integrity-backlog child.
- **345 runs with 5+ events sharing one timestamp → not a defect.** Initially suspected as
  hand-orchestration bulk writes; the agent mix in those runs is the full subagent roster
  (`ticket-scoper`, `done-checker`, `implementer`, …), identical to normal runs. It is the
  orchestrator flushing a batch. The *consequence* — per-phase timing is meaningless for those runs
  — is real and belongs to the seq-integrity child, but the bulk write itself is not a bug.
- **82 of 142 duplicate `run_id`s are legitimate re-runs** with distinct `execution_id`/`start_ts`.
- Clean: no out-of-bounds timestamps, no runs with a duration but zero events, no per-run tool
  volume outliers above 10x median.

## Scope
Track the eight child tickets below. Each is independently investigable and independently
landable; none blocks another. This epic itself performs no implementation.

The capstone child (`MONITORING-ANOMALY-VALIDATOR`) should be scoped **last**, after the others
report, so its checks are written against confirmed causes rather than against this epic's
hypotheses.

## Out of Scope
- Re-litigating the healthy findings listed above.
- The `Perf / cert / arena` redness on `main` — different subsystem, separately tracked.
- Any change to `tickets/working_log.csv` history itself; the ratchets
  (`TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS` items 1 and 6) deliberately freeze the
  historical baseline.

## Acceptance Criteria
- [ ] Each child ticket reaches a recorded disposition — fixed, or explicitly accepted with a
      reason. "Accepted" is a legitimate outcome; silently dropping one is not.
- [ ] The duplicate-run-record count is resolved well enough that a retro's run count can be
      trusted, or the retro states its own uncertainty.
- [ ] Whatever is learned is written back into `RETRO-LAST14D.md`'s notes or a successor report,
      not left in ticket bodies.

## Related Tickets
Children, in suggested order (see `SEQUENCE.md`):

1. `TCK-20260915-DUPLICATE-RUN-RECORDS`
2. `TCK-20260915-SIDECAR-ATTRIBUTION-GAP`
3. `TCK-20260915-TOOL-CALL-COUNT-MISMATCH`
4. `TCK-20260915-EVENT-SEQ-INTEGRITY`
5. `TCK-20260915-EVENT-SUMMARY-TRUNCATION`
6. `TCK-20260915-RETRO-INDEX-REPORTS-ZERO`
7. `TCK-20260915-MONITORING-INTEGRITY-BACKLOG`
8. `TCK-20260915-MONITORING-ANOMALY-VALIDATOR`
9. `TCK-20260915-RETRO-CLI-OVERWRITES-HAND-AUTHORED-NOTES` — added 2026-09-15, not from the
   original sweep: found by the implementer when regenerating a report to verify ticket 1's fix
   destroyed 177 lines of hand-authored analysis. Same "two correct instructions combine into a
   defect" shape as `TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE`.

Related prior work:
- `TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS` (done) — the six-defect bundle this extends
- `TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE` (done)
- `TCK-20260911-COST-PROXY-EPIC-TICKETS-RUN-CONFIRMATION` (blocked by design)

## Related Docs
- `agent-monitoring/retro/RETRO-LAST14D.md` — the review that produced every number here
- `docs/plans/agent_infrastructure/reachability_verification_findings.md` — the pattern this extends
- `docs/agent-monitoring/schema.md`

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `tools/agent-monitoring/` — `generate_retro.py`, `validate.py`, `record_run.py`,
  `record_events.py`, `vocabulary.py`, `build_index.py`
- `agent-monitoring/data/` — the sharded corpus
- `.claude/current_run` — the shared sidecar behind two of the children

## Assumptions / Open Questions
- Every number in this epic and its children was derived directly from the JSONL shards, not from
  `monitoring.db` (last built 2026-09-13 and documented as going stale) and not from an agent
  report. They are reproducible; re-derive before relying on any of them, since the corpus grows.
- Whether the duplicate run records are a write-path bug or an artifact of re-running a workflow
  with the same `run_id` is **unknown** — that is the first child's actual question.

## Implementation Notes
Scoped by `agent-working-design`; implementation belongs to `agent-working-implementer`.

## Test Summary
_Epic — no direct implementation._

## Files Changed
_Epic — no direct implementation._

## Completion Summary
_Open._
