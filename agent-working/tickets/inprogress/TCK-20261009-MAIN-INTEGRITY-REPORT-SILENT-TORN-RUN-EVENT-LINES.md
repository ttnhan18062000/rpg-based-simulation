---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261009-MAIN-INTEGRITY-REPORT-SILENT-TORN-RUN-EVENT-LINES
phase: open
date: 2026-10-09
tags: [agent-monitoring, data-quality]
---

# TCK-20261009-MAIN-INTEGRITY-REPORT-SILENT-TORN-RUN-EVENT-LINES

## Title
main_integrity_report names the torn runs/events shard lines it skips instead of dropping them silently

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
`tools/agent-monitoring/main_integrity_report.py::_load_rows` reads the runs and events shards for
`check_duplicate_runs` and `check_event_seq`. It catches `ValueError` and passes, so a torn line (a write
cut short by a full disk) disappears without a trace. The report then checks duplicates and seq gaps over
rows that are missing, and nothing says so. Its sibling `check_working_log` now reports such a line as
`<path>:<lineno>: invalid JSON, skipped` (TCK-20261008-MAIN-INTEGRITY-REPORT-TORN-WORKING-LOG-LINE).

This ticket is also the vehicle for TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN: it runs through the
native `implement-ticket.js` at standard tier so that every gate site is reached.

## Scope
- `_load_rows` also returns the torn lines it skipped, as `<path>:<lineno>: invalid JSON, skipped`
  strings. A value that parses to a non-dict is skipped without a finding, matching `check_working_log`.
- `check_duplicate_runs` and `check_event_seq` include those strings in their own findings, so a torn
  runs line appears under the duplicate-runs check and a torn events line under the event-seq check.
  Each torn line is reported once.
- Shards are read in sorted path order (already true in `_load_rows`; keep it).
- Tests in `tests/tools/test_main_integrity_report.py`: a torn runs line and a torn events line are each
  reported once under the right check, valid rows on both sides are still read, and a non-dict line is
  skipped silently.

## Out of Scope
- `check_working_log` (already done by the 2026-10-08 ticket).
- Repairing any real torn line on main, and any gate wiring: the report stays report-only.
- `duplicate_run_record_check` and `event_seq_integrity_check` themselves.

## Acceptance Criteria
1. A torn runs-shard line produces exactly one finding naming its path and 1-based line number under the
   duplicate-runs check, and the report completes.
2. The same holds for a torn events-shard line under the event-seq check.
3. Valid rows around a torn line still reach the duplicate and seq checks.
4. A non-dict line is skipped without a finding or a crash.
5. The existing tests in `tests/tools/test_main_integrity_report.py` still pass.

## Related Tickets
- TCK-20261008-MAIN-INTEGRITY-REPORT-TORN-WORKING-LOG-LINE (the same fix in `check_working_log`)
- TCK-20261008-RECORD-EVENTS-CRASHES-ON-TORN-TOOLS-LINE (#437)
- TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN (this ticket is that run's vehicle)

## Related Docs
- docs/agent-monitoring/ (update only if a doc describes the report's findings)

## Related Stored Artifacts
None yet.

## Related Code Areas
- tools/agent-monitoring/main_integrity_report.py (`_load_rows`, `check_duplicate_runs`, `check_event_seq`)
- tests/tools/test_main_integrity_report.py

## Assumptions / Open Questions
- The `search_docs` index is not built and the graphify graph is missing in this worktree, so the
  duplicate scan used the ticket folders and grep: no open ticket covers this.

## Implementation Notes
Lands on the local batch branch `agent-working-small-fixes-batch` with no PR of its own (owner, 2026-10-08).

## Test Summary
## Files Changed
## Completion Summary
