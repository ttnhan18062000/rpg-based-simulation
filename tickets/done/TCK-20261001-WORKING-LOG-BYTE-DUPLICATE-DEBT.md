---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261001-WORKING-LOG-BYTE-DUPLICATE-DEBT
phase: done
date: 2026-10-01
tags: [data-quality]
---

# TCK-20261001-WORKING-LOG-BYTE-DUPLICATE-DEBT

## Title
Remove 56 byte-identical duplicate lines from working_log.csv and tighten the duplicate-pair ratchet 46 to 19

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
`tickets/working_log.csv` carried 27 distinct rows that appear 2-6 times (56 surplus lines). The
duplicate-pair ratchet (`DUPLICATE_PAIR_CEILING`) was pinned at the polluted count (46), so it
could never tighten until the debt was removed. Draft and root-cause analysis came from
`agent-working-design` (`.claude/handover/drafts/working-log-dedupe/`).

Root cause (verified by design, not re-derived here): no live writer defect. The duplicates are
historical: the 2026-09-11 CRLF/LF union-merge cluster (fixed by
`TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION`) plus older `merge=union` identical
appends. None is dated after 2026-09-11T10:27.

## Scope
- `tickets/working_log.csv`: delete the 56 surplus byte-identical lines, keeping the first
  occurrence of each exact line (pure deletion; no csv round-trip).
- `DUPLICATE_PAIR_CEILING` 46 -> 19 and its test pin.

## Out of Scope
- The 152 pre-September "no DONE row" findings and the 9 unexamined September ones.
- Regenerating the gitignored `.json` evidence cited by `TCK-20260907-FILTERED-REPLAY-EVAL-PILOT`.
- The remaining 19 `(ticket_id, title)` pairs (not byte-identical lines; ratchet stays).

## Acceptance Criteria
- `diff` of working_log.csv vs origin/main is 56 deletions, 0 additions.
- Real-corpus duplicate-pair count is 19 and the ceiling pin equals 19.
- Scoped tests pass.

## Related Tickets
- TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION
- TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS

## Related Docs
none

## Related Stored Artifacts
none (hotfix)

## Related Code Areas
- tickets/working_log.csv
- tools/gate_checks/working_log_content_duplicate_check.py
- tests/tools/test_working_log_content_duplicate_check.py

## Assumptions / Open Questions
- Base origin/main fe6a2f564 verified byte-identical for working_log.csv before applying.
- `main_integrity_report.py` reads a snapshot of origin/main, not the working tree, so its
  working_log duplicate-finding drop (26 to 0) can only be observed after merge.

## Implementation Notes
Applied design's `working_log.deduped.csv` verbatim. Docstring line 13 of the check updated to
record the 46 to 19 history.

## Test Summary
`tests/tools/test_working_log_content_duplicate_check.py`, `tests/tools/test_main_integrity_report.py`,
`tests/integrity`: 54 passed, 1 skipped, 1 xfailed, 1 failed.
The failure, `tests/integrity/test_logic_guards.py::test_autonomous_loop_determinism_drift_guard`,
is pre-existing: it fails identically on a clean detached checkout of origin/main fe6a2f564 and
does not read working_log.csv.
CI on the PR then failed `tests/tools`: `test_validate_working_log.py` pins physical line numbers of the real
log (shifted by the dedupe, fixed here) and `monitoring_anomaly_validator` vocabulary_drift counted 12
non-canonical agent literals from this ticket's own closure events (`agent-working-implementer`, corrected to
the tool default `claude`). Full `tests/tools` local run otherwise: 3405 passed.

## Files Changed
- tickets/working_log.csv
- tools/gate_checks/working_log_content_duplicate_check.py
- tests/tools/test_working_log_content_duplicate_check.py
- tests/tools/test_validate_working_log.py (pinned physical line numbers shifted down by the removed lines; the 1658/1666 byte-identical pair is now one row at 1643)

## Completion Summary
Debt removed; the ratchet now pins the true count (19) so any new duplicate pair fails.
