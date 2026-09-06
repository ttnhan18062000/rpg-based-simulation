---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP
phase: open
date: 2026-09-06
tags: [registry, process-improvement, debugging, data-quality]
---

# TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP

## Title
merge=union .gitattributes protection did not prevent a ~1586-row whole-block duplication in tickets/working_log.csv

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`TCK-20260904-WORKING-LOG-CSV-PARSER`'s investigation discovered (as an out-of-scope side finding, "Finding 2") that `tickets/working_log.csv` physical lines 2-1587 (1586 data rows) are byte-for-byte identical, in the same relative order, to physical lines 1595-3180 — a whole-block duplication, plus a duplicate embedded copy of the header row itself at line 1594. Root-caused with high confidence to commit `5993cac3` (PR #90, "M1 Quick Wins & Housekeeping...", merged 2026-08-31), which shows a pure +1640/-0 insertion for this file. `.gitattributes` already declares `tickets/working_log.csv merge=union` (added by `TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS` on 2026-08-26, five days before this incident, with its own claimed "git-level regression test proving the shipped merge=union .gitattributes behavior actually resolves concurrent-branch appends") — but that protection did not prevent this specific incident. This is a real, confirmed gap in that prior ticket's own verified guarantee, not a hypothetical risk.

Direct production impact already live: `tools/knowledge_search.py::_extract_working_log_rows` indexed the bogus embedded header row (line 1594) as a real corpus document (`id="ticket_id"`) until `TCK-20260904-WORKING-LOG-CSV-PARSER` added a narrow guard against that one specific symptom (not this root cause). A naive "row count per ticket_id > 1 ⇒ reopened ticket" signal would report ~1586 false positives today if built without accounting for this duplication.

## Scope
- Investigate why the existing `merge=union` .gitattributes protection (from `TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS`) did not prevent this specific incident — was it a long-lived branch merged before that protection existed on that branch, a squash-merge losing the attribute's effect, a rebase/fast-forward path that bypasses merge drivers entirely, or something else? Root-cause with real git evidence (`git log`, `git show`, testing the actual merge scenario), not speculation.
- Determine whether the existing `merge=union` regression test (from `TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS`) has a real coverage gap that let this class of incident through, and if so, close it or add a new test that would have caught this specific scenario.
- Decide whether/how to address the already-present ~1586-row duplication in the live file: this ticket's own scope must NOT rewrite any historical row in `tickets/working_log.csv` (same hard constraint as `TCK-20260904-WORKING-LOG-CSV-PARSER`) — investigate whether any safe remediation exists (e.g., a documented, reviewed one-time cleanup commit with full before/after audit trail) or whether the correct answer is "flag only, forever" the same way `TCK-20260904-WORKING-LOG-CSV-PARSER`'s `is_duplicate` mechanism already does.
- Consider whether `tools/knowledge_search.py`'s corpus-indexing should also generically deduplicate exact-content working-log rows (beyond the one narrow embedded-header-row guard already shipped), given ~1586 real duplicate documents are indexed today.

## Out of Scope
- Rebuilding or duplicating anything `TCK-20260904-WORKING-LOG-CSV-PARSER` already shipped (the tolerant parser, `validate_working_log.py`'s adoption of it, the narrow embedded-header-row guard in `knowledge_search.py`) — this ticket is about the git-merge root cause and the still-open ~1586-row duplication, not the field-parsing problem that ticket already solved.
- Any change to `tickets/working_log.csv`'s append-only convention itself beyond what's needed to close this specific merge-mechanics gap.

## Acceptance Criteria
- [ ] Root cause of why `merge=union` did not prevent this specific incident is identified with real git evidence, not speculation
- [ ] The existing merge=union regression test's coverage gap (if any) is identified and closed, or a new test is added that would catch this specific scenario
- [ ] An explicit, evidence-based decision is recorded on whether/how to remediate the already-present ~1586-row duplication (may be "flag only, do not rewrite," but must be an explicit decision, not silence)
- [ ] If `tools/knowledge_search.py`'s corpus indexing is extended to deduplicate exact-content rows, it must not rewrite `tickets/working_log.csv` itself

## Related Tickets
- TCK-20260904-WORKING-LOG-CSV-PARSER
- TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS

## Related Docs
- stored_artifacts/TCK-20260904-WORKING-LOG-CSV-PARSER/investigation.md (Finding 2's full evidence)

## Related Stored Artifacts
None.

## Related Code Areas
- tickets/working_log.csv
- .gitattributes
- tools/knowledge_search.py
- tools/working_log_parser.py

## Assumptions / Open Questions
- Whether this was a squash-merge, a long-lived branch predating the .gitattributes fix, or a rebase/fast-forward bypass is unresolved and must be determined with real evidence during Investigate, not guessed
- Whether any safe remediation of the existing duplication is possible without violating the "never rewrite historical rows" constraint both this and the parser ticket share

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
