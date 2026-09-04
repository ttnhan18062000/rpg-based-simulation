---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260904-WORKING-LOG-CSV-PARSER
phase: open
date: 2026-09-04
tags: [ai, data-quality]
---

# TCK-20260904-WORKING-LOG-CSV-PARSER

## Title
Tolerant parser for working_log.csv malformed rows

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
tickets/working_log.csv cannot support automated rework-rate/reopened-ticket signals because grep-level analysis is unreliable — unescaped commas in free-text summary fields corrupt column alignment for a visible subset of rows. The plan is either a proper tolerant CSV parser for existing malformed rows, or migrating to a stricter quoted-field format going forward, with the explicit constraint that parsing repair must never become historical reinterpretation. Investigation confirmed the problem is live and ongoing: 11 currently-live field-count-mismatch rows exist today, dated as recently as 2026-09-03, and this is the third distinct malformed-row class found in this file's history — meaning the manual-append convention itself remains an open corruption source that a parser fix alone won't fully close.

## Scope
- Write a proper parser for tickets/working_log.csv that round-trip parses the full current file (3336+ data rows) without exception, returning exactly one record per physical data row
- Classify every row as clean (field count matches header) or ambiguous/unparseable (mismatch) — never silently drop or merge a row
- Explicitly surface each of the 11 currently-confirmed mismatch rows as flagged/ambiguous, never auto-corrected or reinterpreted into a guessed shape
- Update tools/validate_working_log.py and tools/knowledge_search.py's row-extraction to either adopt the new parser or report the ambiguous-row count as a first-class visible signal, matching tools/ticket_stats_report.py's existing unparseable_rows convention
- Add new tests for tools/validate_working_log.py (no dedicated test file exists today)
- If a stricter future-write schema is adopted (choice deferred to Plan): keep existing pre-cutover rows byte-identical in place with no in-place rewrite of historical rows; any fully normalized query-friendly view must be a separate derived file, not an in-place rewrite

## Out of Scope
- Fixing the 2-3 exact-duplicate-content rows found during investigation (e.g. TCK-20260817-RUNTIMEMODE-BENCH-SCOPING appearing at both lines 1511 and 3104) — flag as discovered-but-out-of-scope, do not silently fix inline
- Changing CLAUDE.md's append-to-bottom convention itself, beyond whatever is needed to close the specific unescaped-comma corruption source going forward
- Any in-place rewrite of historical rows

## Acceptance Criteria
- [ ] Round-trip parse of the full current file (3336+ data rows) succeeds without exception, returns exactly one record per physical data row, every row classified as clean (field count matches header) or ambiguous/unparseable (mismatch) — never silently dropped or merged
- [ ] Each of the 11 currently-confirmed mismatch rows is surfaced as explicitly flagged/ambiguous, not auto-corrected or reinterpreted into a guessed shape
- [ ] tools/validate_working_log.py and tools/knowledge_search.py's row-extraction either adopt the new parser or are updated to report the ambiguous-row count as a first-class visible signal, matching ticket_stats_report.py's existing convention, rather than silently mis-mapping columns via bare DictReader
- [ ] If a stricter future-write schema is adopted, existing pre-cutover rows stay byte-identical in place with no in-place rewrite of historical rows, and any fully normalized view is a separate derived file

## Related Tickets
- TCK-20260705-WORKING-LOG-BACKFILL
- TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP
- TCK-20260819-HOTFIX-WORKING-LOG-LEGACY-SCHEMA-ROWS

## Related Docs
- stored_artifacts/TCK-20260705-WORKING-LOG-BACKFILL/investigation.md

## Related Stored Artifacts
None.

## Related Code Areas
- tickets/working_log.csv
- tools/validate_working_log.py
- tools/knowledge_search.py
- tools/ticket_stats_report.py
- tests/tools/test_ticket_stats_report.py

## Assumptions / Open Questions
- The tolerant-parser-vs-stricter-future-write-format choice is explicitly deferred to the Plan phase; the AC signals differ meaningfully depending on which is picked and Plan must record the decision
- The manual-append convention itself remains an open corruption source unless writes also change, not just parsing — Plan should decide whether this ticket addresses that too or flags it as a further follow-up
- The 2-3 duplicate-content rows found are a related but distinct data-quality defect, to be flagged, not fixed, in this ticket

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
