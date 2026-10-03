---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261001-INTEGRITY-REPORT-EPIC-TIER-FALSE-POSITIVES
phase: done
date: 2026-10-01
tags: [data-quality]
---

# TCK-20261001-INTEGRITY-REPORT-EPIC-TIER-FALSE-POSITIVES

## Title
Integrity-report working_log probe must not demand a DONE row from epic-tier tickets

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
`main_integrity_report.py::check_working_log` demanded a DONE row from every closed ticket. An
epic-tier ticket closes as EPIC_SCOPED, never DONE, so the probe flagged it. Of 29 epic-tier
findings on origin/main@fe6a2f564, 22 had an EPIC_SCOPED row (false positives) and 7 genuinely
have no row. Draft and verification came from `agent-working-design`
(`.claude/handover/drafts/probe-epic-tier/`).

## Scope
- Epic tier (`## Tier` = epic, read at the ref): any row of any status satisfies the check; zero
  rows reports `<id>: epic has no working-log row (<path>)`.
- Non-epic behaviour and the duplicate-row check are unchanged. One regression test with two controls.

## Out of Scope
- Backfilling the missing row for `TCK-20260924-EPIC-GITHUB-DELIVERY-PROCESS` (a hand-written row;
  reported, left alone). The 7 zero-row epics remain findings; 2 are RPG-side.

## Acceptance Criteria
- EPIC_SCOPED row passes; zero-row epic is reported; non-epic with only an EPIC_SCOPED row is still reported.
- New test fails on the unpatched module.

## Related Tickets
- TCK-20261001-WORKING-LOG-BYTE-DUPLICATE-DEBT

## Related Docs
none

## Related Stored Artifacts
none (hotfix)

## Related Code Areas
- tools/agent-monitoring/main_integrity_report.py
- tests/tools/test_main_integrity_report.py

## Assumptions / Open Questions
- Epic tier is detected by a `## Tier` / `epic` regex on the ticket body at the ref.

## Implementation Notes
Applied design's `probe.patch` verbatim (2 files, +33/-3).

## Test Summary
`tests/tools/test_main_integrity_report.py`: 9 passed. Negative control: the new test fails
(1 failed, 8 passed) against the unpatched module.

## Files Changed
- tools/agent-monitoring/main_integrity_report.py
- tests/tools/test_main_integrity_report.py

## Completion Summary
Probe no longer reports 22 epic false positives (design measured 179 to 157 on the origin/main snapshot).
