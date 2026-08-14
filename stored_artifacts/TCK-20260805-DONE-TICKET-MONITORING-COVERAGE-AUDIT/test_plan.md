---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260805-DONE-TICKET-MONITORING-COVERAGE-AUDIT
artifact_type: test_plan
tags: [skills, agent-monitoring]
---

# Test Plan — TCK-20260805-DONE-TICKET-MONITORING-COVERAGE-AUDIT

## Normal Flow
- Real corpus run: `TCK-20260802-CODEX-POSTTOOL-HOOK-COMMAND` appears in `missing`; a handful of
  this session's own real, recently-recorded tickets (e.g. `TCK-20260805-COMBAT-SKILL`) appear in
  `covered`, not `missing` — the exact regression this ticket's own stale-index bug produced.

## Edge Cases
- Legacy tickets with no frontmatter or no `ticket_id` field fall back to filename stem, never
  silently dropped from the audit.
- `SEQUENCE.md`/`README.md` index files under `tickets/done/` are excluded, not misparsed as
  tickets.

## Failure Modes
- The stale-SQLite-index bug this ticket's own Investigate phase found must never silently
  regress — a dedicated source-guard test asserts `_load_runs_and_events` is never imported.

## Regression-Prone Paths
- Zero-mutation test against real `tickets/done/`/`agent-monitoring/` (this is a read-only tool).
- CLI JSON-shape test against the real corpus.
