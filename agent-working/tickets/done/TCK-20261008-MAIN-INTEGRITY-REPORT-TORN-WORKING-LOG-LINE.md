---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261008-MAIN-INTEGRITY-REPORT-TORN-WORKING-LOG-LINE
phase: done
date: 2026-10-08
tags: [agent-monitoring, data-quality]
---

# TCK-20261008-MAIN-INTEGRITY-REPORT-TORN-WORKING-LOG-LINE

## Title
main_integrity_report reports a torn working_log shard line instead of crashing on it

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
`tools/agent-monitoring/main_integrity_report.py::check_working_log` (line 112) parses each
working_log shard line with a bare `json.loads`. One torn line (a write cut short by a full disk, the
2026-10-08 incident) raises `JSONDecodeError` and the whole report fails. The other readers already
fixed by the disk-incident batch (#437) skip and name the line; this one was left over. Its sibling
`_load_rows` in the same file already wraps the parse, but drops the line silently.

## Scope
- In `check_working_log`, catch `ValueError` around the shard-line parse, skip the line, and add a
  `working_log` finding naming it: `<shard path>:<lineno>: invalid JSON, skipped`. This is an integrity
  report, so it states what it found and does not just print a warning.
- Ignore a parsed value that is not a dict, the way `record_events.py` does.
- Add tests in `tests/tools/test_main_integrity_report.py`: a shard with a torn line between two valid
  rows produces the finding, the report does not raise, and the valid rows still count (a ticket whose
  DONE row sits after the torn line gets no "no DONE row" finding).

## Out of Scope
- `_load_rows`'s silent skip for runs/events shards (they have their own duplicate and seq checks).
  Mention it in the Completion Summary if it looks worth a follow-up; do not change it here.
- Repairing any real torn line on main.
- Gate wiring: the report sits on no gate path and stays report-only.

## Acceptance Criteria
1. A torn working_log shard line produces exactly one `working_log` finding with the shard path and the
   1-based line number, and the report completes.
2. Valid rows before and after the torn line are still read.
3. A shard line that parses to a non-dict is skipped without a crash.
4. The existing tests in `tests/tools/test_main_integrity_report.py` still pass.

## Related Tickets
- TCK-20261008-RECORD-EVENTS-CRASHES-ON-TORN-TOOLS-LINE (the same fix in record_events, #437)
- TCK-20261008-MONITORING-SHARD-TORN-WRITE-ON-DISK-FULL (the writer side, #437)

## Related Docs
- docs/agent-monitoring/ (no behavior doc names this check's parse path; update only if one does)

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- tools/agent-monitoring/main_integrity_report.py (`check_working_log`, `_load_rows`)
- tools/agent-monitoring/record_events.py (the reference pattern, around line 150)
- tests/tools/test_main_integrity_report.py

## Assumptions / Open Questions
- The `search_docs` index is not built and the graphify graph is missing in this worktree, so the
  duplicate scan used the ticket folders and grep: no open ticket covers this.

## Implementation Notes
Hand-orchestrated hotfix. Land it on the agent-working batch branch; it gets no PR of its own (owner
policy 2026-10-08: small logic-only changes wait for a batch).

## Test Summary
`tests/tools/test_main_integrity_report.py`: 11 passed, including the new test (torn line between two valid rows, plus non-dict lines: exactly one finding, rows on both sides still counted).

## Files Changed
- tools/agent-monitoring/main_integrity_report.py
- tests/tools/test_main_integrity_report.py

## Completion Summary
`check_working_log` now skips a torn shard line and reports `<path>:<lineno>: invalid JSON, skipped`; a line that parses to a non-dict is skipped silently. `_load_rows` still drops torn runs/events lines silently (out of scope; a follow-up if wanted). Landed on `agent-working-small-fixes-batch`, no PR of its own.
