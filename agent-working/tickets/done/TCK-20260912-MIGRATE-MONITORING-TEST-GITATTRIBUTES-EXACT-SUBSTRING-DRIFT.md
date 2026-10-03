---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260912-MIGRATE-MONITORING-TEST-GITATTRIBUTES-EXACT-SUBSTRING-DRIFT
phase: done
date: 2026-09-12
tags: [data-quality, process-improvement]
---

# TCK-20260912-MIGRATE-MONITORING-TEST-GITATTRIBUTES-EXACT-SUBSTRING-DRIFT

## Title
`test_migrate_monitoring_data.py`'s gitattributes guard broke on TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION's `text eol=lf` reordering

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
CI (PR #167, "API / tools / logging" job) failed:
`tests/tools/test_migrate_monitoring_data.py::test_gitattributes_no_longer_references_any_of_the_3_retired_paths`
asserts the exact substring `"agent-monitoring/data/*/*.jsonl merge=union" in content`. TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION
added `text eol=lf` ahead of `merge=union` on that `.gitattributes` line, so the literal substring
no longer appears verbatim, breaking this pre-existing assertion. This is a real regression caused
by that ticket's own (correct, already-reviewed) attribute reordering, not caught by that ticket's
own narrower Test-phase scope (`tests/integrity/ tests/tools/test_record_hand_orchestrated_closure.py`)
since this file lives outside both paths. It is the exact same class of break already found and
fixed twice within that ticket (Deviation 3, in `tests/integrity/test_merge_union_gitattributes.py`)
— a third pre-existing sanity assertion of the identical shape, missed because it lives in a
different test file entirely.

## Scope
Update the one broken assertion in `test_gitattributes_no_longer_references_any_of_the_3_retired_paths`
to check membership via the shared `_merge_union_glob_patterns()` parser (imported from
`tests/integrity/test_no_duplicate_content_blocks.py`, same as the two prior fixes) instead of an
exact substring, so it stays correct regardless of future attribute-token ordering. No other
change to this file or to `.gitattributes` itself.

## Out of Scope
- Any other test file — this is the only remaining CI failure on PR #167.
- Re-litigating the `text eol=lf` reordering itself (already reviewed and approved).

## Acceptance Criteria
- `test_gitattributes_no_longer_references_any_of_the_3_retired_paths` passes against the real
  current `.gitattributes`.
- The scoped CI job's full local reproduction (`pytest tests/api tests/cli tests/tools
  tests/logging tests/engine tests/observability -m "not slow and not extra_slow"`) passes clean.

## Related Tickets
TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION (root cause of the drift)

## Related Docs
None.

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
tests/tools/test_migrate_monitoring_data.py

## Assumptions / Open Questions
None.

## Implementation Notes
Changed the one broken assertion from an exact-substring check to a shared-parser membership
check, importing `_merge_union_glob_patterns()` from `tests/integrity/test_no_duplicate_content_blocks.py`
(same helper already reused by the two other fixed test files in this exact same lineage). The
three `not in content` assertions above it were left untouched — they check absence of retired
paths, unaffected by the token-ordering change.

## Test Summary
```
pytest tests/tools/test_migrate_monitoring_data.py -q
pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability -m "not slow and not extra_slow" --tb=short -q
```

## Files Changed
- `tests/tools/test_migrate_monitoring_data.py` -- one assertion fixed to use the shared parser

## Completion Summary
Fixed a real CI regression on PR #167 (TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION's
branch): a third pre-existing test asserting the exact `.gitattributes` substring
`"agent-monitoring/data/*/*.jsonl merge=union"`, broken by that ticket's `text eol=lf` reordering,
same class of break already fixed twice in that ticket's own Deviation 3. Updated it to check via
the shared `_merge_union_glob_patterns()` parser instead. No other content, behavior, or file
changed.
