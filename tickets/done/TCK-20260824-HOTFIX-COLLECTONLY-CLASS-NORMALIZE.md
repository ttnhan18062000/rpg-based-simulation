---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260824-HOTFIX-COLLECTONLY-CLASS-NORMALIZE
phase: done
date: 2026-08-24
tags: [testing]
---

# TCK-20260824-HOTFIX-COLLECTONLY-CLASS-NORMALIZE

## Title
Fix `_normalize_collect_only_node_id()` to dot-join ALL class segments, not just the file path, so class-based tests classify correctly as new-vs-existing

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`tools/ci_junit_summary.py::_normalize_collect_only_node_id()` (added by
TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT, merged to `main` via PR #65) only normalizes the first
`::`-delimited segment (the file path) of a `pytest --collect-only -q` node ID, leaving any
further `::`-segments (test class names, including nested classes) untouched. JUnit XML's own
`classname` attribute for a class-based test folds the class name INTO the dotted classname
(e.g. `classname="tests.tools.test_x.TestFoo"` `name="test_bar"`, one `::` when joined as
`classname::name`), while today's normalized collect-only node ID keeps the class as a separate
segment (`tests/tools/test_x.py::TestFoo::test_bar` normalizes to
`tests.tools.test_x::TestFoo::test_bar`, two `::`). These two forms never match, so every
class-based test is misclassified as "new" in the new-vs-existing CI job-summary breakdown
regardless of whether it actually changed.

Confirmed via direct local reproduction of PR #68's real `api-tools` CI job (checked out PR #68's
actual head and base refs, ran the exact pytest + collect-only + `ci_junit_summary.py` commands
the CI job runs): a PR that only added 2 brand-new test files reported 933 "new" out of 2659 total
tests — nearly all misclassification from this bug, not genuinely new tests. Root cause verified
with a concrete example:
`tests.tools.test_add_frontmatter_archive.TestInferLayerKeywords::test_combat_keyword` (head
JUnit's actual classname+name form) vs.
`tests.tools.test_add_frontmatter_archive::TestInferLayerKeywords::test_combat_keyword` (current
buggy normalized base form) — never equal.

The original ticket's own test suite (`tests/tools/test_ci_junit_summary.py`) had no fixture
covering a class-based test case at all, and its one normalization test
(`test_id_normalization_reconciles_collect_only_nodeid_with_junit_classname`) actually asserts the
current *buggy* two-segment output as the expected value — which is why this shipped undetected
through that ticket's Test phase and Architecture-Verify.

## Scope
- Fix `_normalize_collect_only_node_id()` in `tools/ci_junit_summary.py` to dot-join ALL
  `::`-segments except the last (the method name) into the classname, matching JUnit's own
  `classname::name` convention — a general algorithm over N segments, not special-cased to
  exactly one class level. E.g. `path/to/file.py::ClassA::ClassB::test_method` (nested classes)
  must normalize to `path.to.file.ClassA.ClassB::test_method` (all middle segments dot-joined,
  one final `::` before the method name), and the existing no-class case
  (`path/to/file.py::test_method` → `path.to.file::test_method`) must remain unchanged.
- Correct the existing wrong assertion in
  `test_id_normalization_reconciles_collect_only_nodeid_with_junit_classname`
  (`tests/tools/test_ci_junit_summary.py`), which currently encodes the buggy two-`::` output as
  the expected value for a one-class case, to assert the correct dot-joined form.
- Add fixture coverage (JUnit XML `classname` + a matching `pytest --collect-only -q`-style
  listing) for at least: one single-level class-based test, and one nested-class test, so both the
  normalization function and `classify_new_vs_existing()`'s end-to-end path exercise a class-based
  test landing in `existing` (not spuriously `new`) when the same test appears in both the head
  JUnit XML and the base collect-only listing.
- Update `INFRA-380` (`docs/parity_ledger/infrastructure.yaml`) — the entry covering
  `classify_new_vs_existing()`/`_normalize_collect_only_node_id()` — to reflect the corrected
  normalization behavior. (Note: the merged ticket's own Implementation Notes claimed it extended
  `INFRA-379` "in place"; the actual appended entry in the file today is `INFRA-380`, not
  `INFRA-379` — confirmed by direct read. Update the entry that actually exists,`INFRA-380`, and do
  not create a stray duplicate under the `INFRA-379` label the notes describe.)
- Re-run the full existing `tests/tools/test_ci_junit_summary.py` and
  `tests/static/test_ci_step_summary_reporting.py` suites to confirm no other assertion depended
  on the buggy two-segment form.

## Out of Scope
- Any change to the base-branch fetch/worktree/collection steps in `.github/workflows/test.yml`
  (the `Fetch base branch for collect-only diff` / `Base branch test collection` steps) — those
  are unaffected by this normalization bug and stay as-is.
- Any change to `classify_new_vs_existing()`'s bucketing logic itself, `parse_testcase_records()`,
  `render_markdown_table()`, or `main()`'s CLI surface — the bug is isolated to
  `_normalize_collect_only_node_id()`; the functions that consume its output are correct given a
  correct input.
- The documented "known limitation" in `INFRA-380` about base-branch collection reusing the head
  job's installed `requirements.txt` (dependency drift causing base-branch collection failures) —
  a separate, already-acknowledged limitation, not this bug.
- Any change to the 9 fast-lane job definitions' pytest path lists, marker filters, or
  `--junit-xml` output convention.
- Re-litigating the stateless-diff-vs-persisted-baseline or per-job-vs-cross-job-aggregate design
  decisions from TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT — those are settled and out of this
  hotfix's scope.

## Acceptance Criteria
- [x] `_normalize_collect_only_node_id("path/to/file.py::TestFoo::test_bar")` returns
  `"path.to.file.TestFoo::test_bar"` (one `::`, matching JUnit's `classname::name` shape).
- [x] `_normalize_collect_only_node_id("path/to/file.py::TestFoo::TestBar::test_baz")` (nested
  class) returns `"path.to.file.TestFoo.TestBar::test_baz"` (all middle segments dot-joined into
  one classname, one final `::`).
- [x] `_normalize_collect_only_node_id("path/to/file.py::test_bar")` (no class, existing case)
  still returns `"path.to.file::test_bar"`, unchanged from current behavior.
- [x] `test_id_normalization_reconciles_collect_only_nodeid_with_junit_classname` in
  `tests/tools/test_ci_junit_summary.py` asserts the corrected dot-joined form, not the old
  buggy two-`::` form.
- [x] A new or extended test demonstrates a class-based test (e.g.
  `classname="tests.tools.test_x.TestFoo"` `name="test_bar"` in the head JUnit XML fixture, with
  a matching `tests/tools/test_x.py::TestFoo::test_bar` line in the base collect-only fixture)
  classifies as `existing`, not `new`, via `classify_new_vs_existing()`.
- [x] A new or extended test covers a nested-class node ID end-to-end through
  `parse_collect_only_ids()` producing the correct dot-joined ID.
- [x] `pytest tests/tools/test_ci_junit_summary.py -v` and
  `pytest tests/static/test_ci_step_summary_reporting.py -v` pass in full after the fix.
- [x] `docs/parity_ledger/infrastructure.yaml`'s `INFRA-380` entry text reflects the corrected
  normalization algorithm.

## Related Tickets
- TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT (done, merged to `main` via PR #65) — introduced the
  buggy `_normalize_collect_only_node_id()` and the under-covered test suite this hotfix corrects.
  Direct parent; this hotfix does not reopen its broader scope (base-ref detection mechanism,
  per-job-only vs. cross-job aggregate, stateless-diff decision), only the normalization bug.
- TCK-20260823-CI-STEP-SUMMARY-REPORTING (done) — grandparent ticket; built the base
  `ci_junit_summary.py` module and `INFRA-379`/`INFRA-380` entries this fix's target function sits
  inside. No scope overlap beyond shared file.

## Related Docs
- No Mechanics Bible chapter or Engine Contract governs CI tooling — same finding as both parent
  tickets; this remains pure process/infra tooling outside `docs/mechanics/` and `docs/engine/`
  scope.
- `docs/testing/test_taxonomy.md` — referenced only for general test-marker conventions; unchanged
  by this fix.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT/investigation.md`,
  `stored_artifacts/TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT/plan.md`,
  `stored_artifacts/TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT/test_plan.md` — prior investigation
  and plan for the module this hotfix corrects; useful context on the collect-only vs. JUnit
  classname reconciliation intent, but did not anticipate the multi-segment class case.

## Related Code Areas
- `tools/ci_junit_summary.py` — `_normalize_collect_only_node_id()` (the buggy function, lines
  ~143-153), `parse_collect_only_ids()` (its caller), `classify_new_vs_existing()` (downstream
  consumer of normalized IDs, unaffected in its own logic but currently receiving mismatched
  input).
- `tests/tools/test_ci_junit_summary.py` — `test_id_normalization_reconciles_collect_only_nodeid_with_junit_classname`
  (currently asserts the buggy output), `test_classify_new_vs_existing_splits_by_base_collect_only_ids`,
  `test_classify_new_vs_existing_all_six_states` (both currently exercise only flat,
  non-class-based fixture data).
- `tests/tools/fixtures/ci_junit_summary/head_with_testcases.xml`,
  `tests/tools/fixtures/ci_junit_summary/base_collect_only.txt` — existing fixtures, all
  file-level `classname` values, no class-based test coverage; need new class-based (and
  nested-class) entries added.
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-380` entry (the actual entry describing
  `classify_new_vs_existing()`/`_normalize_collect_only_node_id()`, despite the merged ticket's
  own Implementation Notes text referring to it as "`INFRA-379`").

## Assumptions / Open Questions
- `layer: testing` chosen to match both parent tickets
  (TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT, TCK-20260823-CI-STEP-SUMMARY-REPORTING), which used
  the same layer for the same file area (`tools/ci_junit_summary.py`, CI test-reporting tooling).
- `tags: [testing]` chosen to match the direct parent ticket's tags exactly; no `bug` tag added
  despite `## Type: bug` — `bug` is registered but its own registry note flags it as overlapping
  the `## Type` body field and not a settled convention, so following the parent ticket's existing
  precedent (tags-by-subsystem, not tags-by-ticket-nature) rather than introducing a new
  convention in a hotfix.
- Confirmed by direct read that the ticket text's assumption about which parity-ledger ID to
  update ("INFRA-380" per the request's own step 5 instruction) is the entry that actually exists
  in `docs/parity_ledger/infrastructure.yaml` today, despite TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT's
  own Implementation Notes claiming (incorrectly) that it extended `INFRA-379` in place. This
  ticket's implementer should treat `INFRA-380` as the correct target and not be misled by that
  prior ticket's self-description.
- Assumes fixing the normalization function alone (without touching
  `classify_new_vs_existing()`, `parse_testcase_records()`, or the workflow YAML) is sufficient to
  resolve the misclassification — consistent with the confirmed root-cause analysis, since
  `classify_new_vs_existing()` only performs set membership on already-normalized IDs and has no
  independent bug of its own.

## Implementation Notes
Rewrote `_normalize_collect_only_node_id()` in `tools/ci_junit_summary.py` to a general
N-segment algorithm: split the node ID on `::`; normalize `segments[0]` (slash-to-dot, strip
trailing `.py`) exactly as before; if there are 2 or fewer segments (no class, or one flat
method), rejoin with `::` unchanged from the old behavior; otherwise (one or more class/nested
class segments present) dot-join the normalized file segment together with every middle
segment (`segments[1:-1]`) into a single classname string and append `::` + the final segment
(the method name). This produces exactly one `::` in the output regardless of class-nesting
depth, matching JUnit XML's own `classname` attribute convention where the class hierarchy is
folded into the dotted classname and only the method name follows `::`.

Fixed the pre-existing wrong assertion in
`test_id_normalization_reconciles_collect_only_nodeid_with_junit_classname`
(`tests/tools/test_ci_junit_summary.py`), which asserted the old buggy two-`::` output
(`"tests.unit.core.test_b::TestFoo::test_bar"`) for a one-class case; it now asserts the
correct one-`::` dot-joined form (`"tests.unit.core.test_b.TestFoo::test_bar"`).

Added test coverage:
- `test_id_normalization_dot_joins_nested_class_segments` — unit test of
  `_normalize_collect_only_node_id()` directly against a 4-segment nested-class node ID.
- `test_parse_collect_only_ids_dot_joins_nested_class_segments` — same nested-class case
  exercised end-to-end through `parse_collect_only_ids()`.
- `test_classify_new_vs_existing_matches_class_based_tests_as_existing` — end-to-end test using
  two new fixtures (`tests/tools/fixtures/ci_junit_summary/head_with_class_testcases.xml`,
  `tests/tools/fixtures/ci_junit_summary/base_collect_only_with_classes.txt`) covering a
  single-level class test and a nested-class test that both appear in both head JUnit XML and
  base collect-only listing (asserted to classify `existing`), plus one genuinely new
  class-based test with no base-branch match (asserted to classify `new`), proving the fix is
  not special-cased to exactly one class level.

Deliberately used new, separate fixture files rather than extending the existing
`head_with_testcases.xml` / `base_collect_only.txt` fixtures, since several existing tests
(`test_parse_testcase_records_extracts_all_states`,
`test_classify_new_vs_existing_all_six_states`,
`test_render_markdown_table_includes_new_existing_breakdown`) assert exact hardcoded counts
against those fixtures; adding entries to them would have required updating every one of those
counts for no benefit, where a small dedicated fixture pair for the class-based case is more
targeted per the "no unnecessary abstractions" / minimal-diff hotfix constraint.

Updated the `INFRA-380` entry in `docs/parity_ledger/infrastructure.yaml` (confirmed as the
actually-present entry, not `INFRA-379`, by direct read before editing) with a new "Fixed by
TCK-20260824-HOTFIX-COLLECTONLY-CLASS-NORMALIZE" paragraph describing the bug and the corrected
algorithm, and updated `v2_evidence` to note the corrected dot-joining behavior of
`_normalize_collect_only_node_id`. `test_path` already covered both relevant test files, so it
was left unchanged. Verified the YAML still parses via `yaml.safe_load` and that
`tests/tools/test_parity_ledger_schema.py` and `tests/tools/test_parity_index_baseline.py` both
still pass (16/16) after the edit.

No changes were needed to `classify_new_vs_existing()`, `parse_testcase_records()`,
`render_markdown_table()`, `main()`, or the workflow YAML — consistent with the ticket's Out of
Scope and the confirmed root-cause analysis that the bug is isolated to
`_normalize_collect_only_node_id()`.

## Test Summary
- `pytest tests/tools/test_ci_junit_summary.py -v` — 26 passed (24 pre-existing + 2 new unit
  tests + 1 new end-to-end fixture test; one pre-existing test's assertion corrected in place,
  not counted as new).
- `pytest tests/static/test_ci_step_summary_reporting.py -v` — 10 passed, unchanged.
- `pytest tests/tools/test_parity_ledger_schema.py tests/tools/test_parity_index_baseline.py -q`
  — 16 passed, confirming the `INFRA-380` YAML edit is schema-valid and did not disturb the
  parity-index baseline.

## Files Changed
- `tools/ci_junit_summary.py` — fixed `_normalize_collect_only_node_id()`.
- `tests/tools/test_ci_junit_summary.py` — corrected the buggy assertion in
  `test_id_normalization_reconciles_collect_only_nodeid_with_junit_classname`; added
  `test_id_normalization_dot_joins_nested_class_segments`,
  `test_parse_collect_only_ids_dot_joins_nested_class_segments`,
  `test_classify_new_vs_existing_matches_class_based_tests_as_existing`.
- `tests/tools/fixtures/ci_junit_summary/head_with_class_testcases.xml` — new fixture.
- `tests/tools/fixtures/ci_junit_summary/base_collect_only_with_classes.txt` — new fixture.
- `docs/parity_ledger/infrastructure.yaml` — updated `INFRA-380` entry `text` and `v2_evidence`.
- `tickets/inprogress/TCK-20260824-HOTFIX-COLLECTONLY-CLASS-NORMALIZE.md` — this file (Status,
  Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary).

## Completion Summary
Fixed `_normalize_collect_only_node_id()` in `tools/ci_junit_summary.py` so it dot-joins ALL
`::`-delimited class segments (including nested classes) into the classname, not just the file
path, matching JUnit XML's own `classname::name` convention. This corrects a real
new-vs-existing misclassification bug where every class-based test was reported as "new"
regardless of whether it actually changed. Corrected the one pre-existing test assertion that
encoded the old buggy two-`::` output as expected, added unit and end-to-end test coverage for
both single-level and nested-class cases (including two new fixture files), and updated the
`INFRA-380` parity ledger entry to document the fix. All targeted test suites pass.
