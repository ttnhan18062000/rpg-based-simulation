---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260817-HOTFIX-SIMQ-AUDIT-GAPS-ISOLATED-ANCHOR-FALSE-POSITIVE
phase: done
date: 2026-08-17
tags: [testing, bug]
---

# TCK-20260817-HOTFIX-SIMQ-AUDIT-GAPS-ISOLATED-ANCHOR-FALSE-POSITIVE

## Title
Fix `tools/simq_audit_gaps.py` false-flagging anchor keys covered only by standalone isolated
grade-anchor tests

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Part of a large batch of tickets fixing real, pre-existing failures in the 16 test directories
added by commit `29d78798` that were never wired into any CI job. This one:
`tests/unit/tools/test_simq_audit_gaps.py::test_no_false_positive_for_covered_keys` failed because
`find_uncovered_anchor_keys()` flagged `urban_political_selfmodel_probe_seed42_200t` and
`urban_political_selfmodel_execution_probe_seed42_200t` (both added by `29d78798`) as uncovered.

Root cause (confirmed via investigation): `find_uncovered_anchor_keys()`
(`tools/simq_audit_gaps.py`) only considered a `grade_anchors.json` key "covered" if it appeared in
`test_grade_regression.py`'s `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` lists. The two keys above are
genuinely covered, but via two dedicated standalone tests
(`test_urban_political_selfmodel_cognition_isolated_grade_anchor`,
`test_urban_political_selfmodel_execution_isolated_grade_anchor`) that reference the keys as a
literal `run_key = "..."` assignment rather than adding them to either list — a second, legitimate
coverage mechanism the tool's coverage notion never accounted for.

## Scope
- Extend `tools/simq_audit_gaps.py::find_uncovered_anchor_keys()` to also treat anchor keys
  referenced by a standalone isolated test's literal `run_key = "..."` / `guard_run_key = "..."`
  assignment (scanned from `test_grade_regression.py`'s own source) as covered, in addition to
  `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` membership.

## Out of Scope
- Any other ticket in this batch.
- Adding the two keys to `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` directly — they are intentionally
  covered by dedicated isolated tests instead.

## Acceptance Criteria
- [ ] `find_uncovered_anchor_keys()` no longer false-flags keys covered by a standalone isolated
      `run_key`/`guard_run_key` test.
- [ ] All 4 tests in `tests/unit/tools/test_simq_audit_gaps.py` pass.

## Related Tickets
None — standalone, pre-existing, unrelated to recent session work.

## Related Docs
None.

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- `tools/simq_audit_gaps.py`

## Implementation Notes
Added `_ISOLATED_RUN_KEY_PATTERN` (regex matching `run_key = "..."` / `guard_run_key = "..."`) and
`_load_isolated_anchor_keys()`, which scans `test_grade_regression.py`'s own source via
`inspect.getsource()` for these literal assignments. `find_uncovered_anchor_keys()`'s `covered` set
now unions `fast_keys | slow_keys | _load_isolated_anchor_keys()`.

## Test Summary
- `pytest tests/unit/tools/test_simq_audit_gaps.py -q`: 4 passed.

## Files Changed
- `tools/simq_audit_gaps.py` — added isolated-anchor-key detection to `find_uncovered_anchor_keys()`.

## Completion Summary
Fixed a real gap in the audit tool's coverage notion: it only recognized one of two legitimate
coverage mechanisms already in use by `test_grade_regression.py`. The tool now recognizes both,
matching the real, current test suite's actual coverage.
