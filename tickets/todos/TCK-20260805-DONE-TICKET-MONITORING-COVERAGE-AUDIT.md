---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260805-DONE-TICKET-MONITORING-COVERAGE-AUDIT
phase: open
date: 2026-08-05
tags: [skills, agent-monitoring]
---

# TCK-20260805-DONE-TICKET-MONITORING-COVERAGE-AUDIT

## Title
Audit whether other tickets/done/ tickets are missing agent-monitoring run/event records like TCK-20260802-CODEX-PILOT-ENTRYPOINT and TCK-20260802-CODEX-POSTTOOL-HOOK-COMMAND

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Follow-up from `TCK-20260805-CODEX-EVENT-TRACE-GAP-INVESTIGATION`. That ticket confirmed
`TCK-20260802-CODEX-PILOT-ENTRYPOINT` and `TCK-20260802-CODEX-POSTTOOL-HOOK-COMMAND` are both
`DONE` in `tickets/done/` with real Completion Summaries, yet have **zero** `agent-monitoring/runs.jsonl`
records — not incomplete records, no records at all. The only local session transcript that
substantially references either ticket
(`~/.claude/projects/-home-u24desktop-Working-rpg-based-simulation/c531094f-78db-4cfa-9fcc-37dcb069456e.jsonl`)
shows this was a *later* closure-verification/audit pass (found a `NEEDS_CHANGES` closure_review
verdict for one of them), not the original implementation session — that original session could
not be located, so whether it itself skipped the monitoring-write step, or whether these two
tickets were finalized through some other path entirely, remains unresolved. This is a real,
apparent violation of CLAUDE.md's own Hard Rule: "Every implement-ticket workflow run (including
hotfix) must record a run entry and at least one event entry to `agent-monitoring/`." Whether this
is a one-off (these 2 tickets only) or a broader gap is the open question this ticket resolves.

## Scope
- Write a read-only audit script (or reuse/extend an existing `tools/agent-monitoring/*.py` tool)
  that, for every ticket file under `tickets/done/` (recursive, including subfolders), checks
  whether at least one `runs.jsonl` record exists with a matching `run_id`/`ticket_id`.
- Report the full list of `DONE` tickets with zero matching run records (if any beyond the 2
  already known).
- If the list is exactly these 2 known tickets: report that finding, close as "isolated, not
  systemic" — no further fix needed beyond documenting it.
- If more tickets are found missing records: escalate scope — this ticket's own Plan phase decides
  whether a backfill mechanism or a going-forward gate (e.g. a Finalize-time check preventing a
  ticket from reaching `tickets/done/` without at least one prior monitoring write this session)
  is warranted.

## Out of Scope
- Retroactively fabricating monitoring records for tickets found missing them — a backfilled
  record would misrepresent real historical data; if backfill is ever warranted, it must be
  explicitly marked as reconstructed/best-effort, not presented as an original real-time record.
- Diagnosing the root cause for any newly-found missing ticket beyond the 2 already investigated —
  scope creep; file further follow-ups if warranted.

## Acceptance Criteria
- [ ] Audit script/tool built, run against the real `tickets/done/` corpus.
- [ ] Full list of tickets (if any, beyond the 2 already known) missing `runs.jsonl` coverage
      reported.
- [ ] Explicit isolated-vs-systemic verdict recorded with reasoning.

## Related Tickets
- TCK-20260805-CODEX-EVENT-TRACE-GAP-INVESTIGATION (the investigation that found this gap)
- TCK-20260802-CODEX-PILOT-ENTRYPOINT, TCK-20260802-CODEX-POSTTOOL-HOOK-COMMAND (the 2 known-affected tickets)
- TCK-20260805-SECURITY-GATE-FIRING-MONITOR (a related but narrower checker — only covers
  `security`-tagged tickets' `Security-Review` coverage specifically, not general run-record
  existence for all `DONE` tickets)

## Related Docs
None new yet — this ticket's own Investigate phase decides if `docs/agent-monitoring/README.md`
needs a new section, mirroring the pattern of `SECURITY-GATE-FIRING-MONITOR` and
`SKILL-USAGE-METRIC`.

## Related Stored Artifacts
None yet (standard tier, will be created).

## Related Code Areas
- `tools/agent-monitoring/` (likely new script, following the established house pattern)
- `agent-monitoring/runs.jsonl` (read-only data source)
- `tickets/done/` (read-only data source)

## Assumptions / Open Questions
Whether this is isolated to the 2 known tickets or reflects a broader gap is the central open
question — resolved by this ticket's own audit, not assumed.

## Implementation Notes
(filled during Implement)

## Test Summary
(filled during Test)

## Files Changed
(filled during Implement)

## Completion Summary
(filled during Finalize)
