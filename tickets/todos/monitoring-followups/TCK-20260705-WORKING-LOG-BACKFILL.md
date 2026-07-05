---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260705-WORKING-LOG-BACKFILL
phase: open
date: 2026-07-05
tags: [agent-monitoring, data-quality]
---

# TCK-20260705-WORKING-LOG-BACKFILL

## Title
Backfill tickets/working_log.csv rows for legitimately-DONE tickets validate.py can now see

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP` fixed `validate.py`'s working-log cross-check to also read the legacy `status` field (not just `final_status`), which correctly surfaced additional tickets that are genuinely `DONE` but have no matching row in `tickets/working_log.csv`. That ticket explicitly deferred the backfill question: "whether to backfill those specific `working_log.csv` rows is a separate, small follow-up decision, not part of fixing the validator itself."

**Count correction**: at the time that ticket shipped, 8-9 such cases were visible. Re-running `python3 tools/agent-monitoring/validate.py` right now (after this session's subsequent tickets landed) shows **62** `TCK-*` tickets currently missing a `working_log.csv` row — the true, current count is materially larger than originally estimated, because more historical/legacy-schema tickets have surfaced as monitoring data accumulated. Use the live re-run's output at implementation time as the authoritative list, not any number cited in a prior ticket.

## Scope
- Re-run `python3 tools/agent-monitoring/validate.py` to get the current, authoritative list of `TCK-*` run_ids missing a `working_log.csv` entry.
- For each one, confirm it is genuinely `DONE` (via `tickets/done/{ticket_id}.md` existing, or an explicit terminal-status field in its `runs.jsonl` record) before adding a row — do not blindly add a row for every warning without individually confirming completion, matching this session's established verification discipline.
- Append one row per confirmed-complete ticket to `tickets/working_log.csv`, following the existing format (`timestamp,ticket_id,title,status,summary,artifacts_path`) — pull `title` from the ticket file's own `## Title` section, `summary` from its `## Completion Summary` if present (or a brief factual summary derived from the ticket if that section is sparse for an older ticket), `artifacts_path` from `stored_artifacts/{ticket_id}/` if it exists, else `none`.
- **Explicitly this is a `working_log.csv` backfill, not a `runs.jsonl`/`events.jsonl` backfill** — the latter remains off-limits per this session's established append-only-log precedent (`runs.jsonl`/`events.jsonl` reflect what was actually written at the time and must never be rewritten). `working_log.csv` is a different artifact — a human-readable ticket ledger meant to have exactly one row per completed ticket — and adding a row for a ticket that is demonstrably, already `DONE` is completing that ledger's own intended invariant, not falsifying history.

## Out of Scope
- Any change to `validate.py` itself — already fixed by the sibling ticket; this ticket only acts on what it now correctly surfaces.
- Any `runs.jsonl`/`events.jsonl` edits — strictly out of bounds, append-only.
- Tickets flagged as missing a `working_log.csv` entry that turn out, on inspection, to NOT actually be complete (should not exist given the schema-gap ticket's fix, but if found, flag and exclude rather than force a row).
- Re-running `make agent-monitoring-retro` to regenerate reports after the backfill — the reports' own DONE/gate-fail counts are computed from `runs.jsonl`, not `working_log.csv`, so this backfill doesn't change any retro numbers; no regeneration needed.

## Acceptance Criteria
- [ ] Every `TCK-*` run_id `validate.py` currently flags as "DONE has no working_log entry" is either given a row in `tickets/working_log.csv`, or explicitly excluded with a documented reason (e.g. ticket file not found, status ambiguous).
- [ ] Re-running `python3 tools/agent-monitoring/validate.py` after the backfill shows zero (or a documented, justified residual) "no working_log entry" warnings.
- [ ] Every added row is individually verified against `tickets/done/` (or an explicit terminal-status field) before being added — no blind bulk-append.
- [ ] `runs.jsonl`/`events.jsonl` show zero diff (`git diff --stat agent-monitoring/runs.jsonl agent-monitoring/events.jsonl` empty) — confirms the append-only invariant was respected.

## Related Tickets
- TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP (fixed the validator that surfaces this gap; explicitly deferred the backfill decision to this ticket)

## Related Docs
- docs/guides/agent_monitoring.md
- tickets/working_log.csv (the artifact being completed)

## Related Stored Artifacts
None yet — staging artifacts to be created under `staging_artifacts/TCK-20260705-WORKING-LOG-BACKFILL/` when implementation begins (standard tier, given the volume — 62 tickets to individually verify — warrants a real investigation/plan pass, not a hotfix-tier shortcut).

## Related Code Areas
- tickets/working_log.csv
- tickets/done/ (read-only — source of truth for verifying each backfilled row)
- agent-monitoring/runs.jsonl (read-only — do not modify)

## Assumptions / Open Questions
- Whether all 62 currently-flagged tickets are genuinely complete, or whether a small number might reveal a real, previously-undetected gap once individually checked, is exactly what this ticket's verification step exists to determine — not assumed here.
- Given the volume (62, not the originally-estimated 8-9), whether this is worth doing as one bulk pass or split into smaller batches is a Plan-phase call.

## Implementation Notes
(not yet implemented — ticket filed for review before proceeding)

## Test Summary
(not yet implemented)

## Files Changed
(not yet implemented)

## Completion Summary
(not yet implemented)
