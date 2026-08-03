---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260802-DOC-COVERAGE-CHECK
artifact_type: test_plan
tags: [workflows, documentation]
---

# Test Plan — TCK-20260802-DOC-COVERAGE-CHECK

## Regression Surface

All 65 existing tests in `tests/tools/test_done_checker_static.py` must keep passing, with exactly
two deliberate exceptions: the two `run_static_precheck` aggregate-count assertions
(`test_run_static_precheck_all_pass_eligible`'s `assert len(results) == 6`) must be updated to 7 —
that's the intended behavior change, not a regression.

## New Tests Required

**`check_docs_to_update_coverage` (new test group):**
- `test_docs_coverage_hotfix_is_na` — `tier="hotfix"` → `NA`, regardless of whether
  `investigation.md` exists.
- `test_docs_coverage_missing_investigation_file_fails` — standard tier, no `investigation.md` at
  all → `FAIL`.
- `test_docs_coverage_no_section_heading_passes` — `investigation.md` exists but has no "## Docs
  Requiring Update" heading at all → `PASS` (empty section == no heading, same treatment).
- `test_docs_coverage_explicit_none_passes` — section body is exactly `None.` → `PASS`.
- `test_docs_coverage_unparseable_non_none_section_fails` — section body is non-empty prose that
  isn't the "None." sentinel and contains no valid bullet — `FAIL`, evidence mentions the format
  expectation.
- `test_docs_coverage_all_flagged_paths_touched_passes` — section lists one or more
  backtick-wrapped `docs/` paths; a real git repo fixture (`tmp_path` initialized with `git init` +
  those doc files created and `git status --porcelain` showing them as untracked/modified) confirms
  `PASS`.
- `test_docs_coverage_missing_flagged_path_fails` — section lists a path NOT reflected in
  `git status --porcelain` output → `FAIL`, evidence names the missing path(s).
- `test_docs_coverage_ignores_behavior_changed_entirely` — confirms the function signature/behavior
  never reads or depends on any `behavior_changed`-shaped input — purely a signature/design check
  (the function only takes `ticket_id`/`tier`/`base_dir`).

**`_parse_docs_to_update` (new test group, direct unit tests):**
- `test_parse_docs_extracts_multiple_bullets` — 3 backtick-wrapped bullets with trailing reason text
  → all 3 paths extracted, reason text ignored.
- `test_parse_docs_none_variants` — `""`, `"None"`, `"None."`, `"N/A"`, `"n/a"` (case-insensitive) →
  all return `[]`.
- `test_parse_docs_ignores_non_bullet_prose` — a paragraph of prose mentioning `docs/x.md` without a
  leading `- \`...\`` bullet → returns `[]` (not a false-positive match).

**`_git_touched_paths` (new test group):**
- `test_git_touched_paths_reflects_real_status` — real `tmp_path` git repo, one new untracked file
  → path appears in the returned set.
- `test_git_touched_paths_fails_open_on_non_repo` — `tmp_path` with no `.git` → returns `set()`,
  never raises.

**`run_static_precheck` (updates to existing tests):**
- Update `test_run_static_precheck_all_pass_eligible`'s `assert len(results) == 6` → `== 7`.
- Add `test_run_static_precheck_includes_docs_to_update_coverage_condition` — confirms
  `"docs_to_update_coverage"` appears in the aggregated `condition` names.

**`.claude/workflows/implement-ticket.js` static wiring (new test, mirrors
`test_doc_staleness_gate_wiring.py`'s pattern):**
- `test_verify_prompt_cites_condition_6_alongside_static_conditions` — the "Before checking
  conditions..." line includes `6` in its condition-number list.

## Scoped Pytest Commands

```
pytest tests/tools/test_done_checker_static.py -v
```

(No new dedicated JS-wiring test file needed if the condition-6 citation check is added directly
into `test_done_checker_static.py` or an existing adjacent static-wiring test file — decide at
Implement time based on which existing file already reads `implement-ticket.js`'s Verify block.)

## Anti-Drift Test Guards

- `test_docs_coverage_ignores_behavior_changed_entirely` guards specifically against a future edit
  accidentally re-coupling this check to `behavior_changed` — the whole point of this ticket is that
  it must NOT depend on that self-reported flag, unlike the Implement-phase advisory it complements.
- `test_git_touched_paths_fails_open_on_non_repo` guards against the check ever raising/crashing the
  workflow when git state is unavailable — matches the fail-open convention used everywhere else in
  this file.
- `test_parse_docs_ignores_non_bullet_prose` guards against a false-positive match that would let
  Investigate satisfy the format requirement with loose prose instead of the strict bullet format
  the whole check depends on.
