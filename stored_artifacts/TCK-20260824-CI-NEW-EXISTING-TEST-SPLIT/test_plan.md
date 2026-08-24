---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT
artifact_type: test_plan
tags: [testing]
---

# Test Plan — TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT

## Regression Surface
Existing tests that must keep passing, unchanged in outcome, after this ticket's changes:

**Unit (parser/renderer module):**
- `tests/tools/test_ci_junit_summary.py` — all 10 existing tests
  (`test_parse_junit_xml_all_passing`, `test_parse_junit_xml_with_failure`,
  `test_parse_junit_xml_with_error`, `test_parse_junit_xml_with_skip`,
  `test_parse_junit_xml_empty_testsuite_produces_correct_zero_counts`,
  `test_parse_junit_xml_malformed_produces_safe_fallback`,
  `test_parse_junit_xml_missing_file_produces_safe_fallback`,
  `test_markdown_table_output_shape`, `test_markdown_table_output_shape_for_parse_failure`,
  `test_parser_exit_code_independent_of_test_outcome`) — must all still pass byte-for-byte, since
  the new-vs-existing logic must be additive, not a rewrite of `parse_junit_xml`'s or
  `render_markdown_table`'s existing return contract.

**Integration / architecture guard (workflow wiring):**
- `tests/static/test_ci_step_summary_reporting.py` — all 5 existing tests
  (`test_all_fastlane_jobs_have_junit_xml_flag`,
  `test_junit_xml_path_is_job_local_and_not_under_tests_dir`,
  `test_all_fastlane_jobs_have_always_run_summary_step`,
  `test_no_new_requirements_txt_entry_and_no_new_marketplace_action`,
  `test_slow_and_migration_lanes_jobs_unchanged_by_this_ticket`) — the pre-existing
  Passed/Failed/Errors/Skipped/Duration table wiring and the `slow`/`migration-lanes` deferral must
  stay intact; this ticket is additive to the same jobs.

**Adjacent CI-workflow static guards (same file, different tickets' regression surface):**
- `tests/tools/test_ci_workflow_test_coverage.py` — proves the new base-branch collect-only step
  does not get miscollected as a bogus covered-path contributor by `_extract_pytest_paths` (see
  investigation.md's Anti-Drift Hazards on the `cd /tmp/base-checkout && pytest ...` prefix choice).
- `tests/static/test_ci_narrow_path_filtered_jobs.py` — `changed-files`/`perf-cert-arena`/
  `migration-lanes` `if:`/`needs:` wiring must stay unaffected.
- `tests/static/test_corpus_diversity_ci_isolation.py`, `tests/static/test_ci_requirements_no_ml_stack.py`
  — unrelated workflow-file assertions that must not regress from this ticket's edits to the same
  file.
- Parity-ledger domain: `pytest tests/tools -k "parity"` — confirms the `INFRA-379` extension (or
  new `INFRA-380`) keeps `docs/parity_ledger/infrastructure.yaml` schema-valid.

## New Tests Required

Per acceptance criteria:

1. **Test name:** `test_classify_new_vs_existing_splits_by_base_collect_only_ids`
   **Category:** unit
   **Verifies:** given a fixture pair (base collect-only text listing + head JUnit XML with
   per-testcase entries), a test ID present in the head XML but absent from the base listing is
   classified `new`; a test ID present in both is classified `existing`. Covers the AC's exact
   "New"/"Existing" definitions.
   **Location:** `tests/tools/test_ci_junit_summary.py` (extended) or a new sibling test module if
   the classification logic is split into its own function group.

2. **Test name:** `test_classify_new_vs_existing_all_six_states`
   **Category:** unit
   **Verifies:** a single fixture pair containing at least one test in each of the six required
   states — new-passed, new-failed, new-skipped, existing-passed, existing-failed, existing-skipped
   — and that the classifier's totals/pass/fail/skip counts are correct per category (AC's explicit
   fixture requirement). Errors folded into failed or shown separately per whichever
   implementer-judgment choice is made — this test must assert whichever shape is actually chosen,
   and must assert the choice is internally consistent with the existing all-tests row's separate
   Errors column (i.e., the implementer's judgment call is itself testable).
   **Location:** `tests/tools/test_ci_junit_summary.py` (extended), new fixtures under
   `tests/tools/fixtures/ci_junit_summary/` (e.g. `base_collect_only.txt`,
   `head_with_testcases.xml`).

3. **Test name:** `test_classify_malformed_or_missing_base_listing_resolves_to_safe_fallback`
   **Category:** unit
   **Verifies:** a malformed or missing base-listing input (empty file, garbage text, nonexistent
   path) never raises and resolves to a defined, safe fallback — consistent with
   `parse_junit_xml`'s existing `parse_ok=False`-sentinel, never-raise design. Directly required by
   the AC's last bullet.
   **Location:** `tests/tools/test_ci_junit_summary.py` (extended).

4. **Test name:** `test_render_markdown_table_includes_new_existing_breakdown`
   **Category:** unit
   **Verifies:** the extended renderer emits the pre-existing Passed/Failed/Errors/Skipped/Duration
   table unchanged, plus additional new/existing breakdown row(s)/table(s) when classification data
   is supplied, and the exact pre-existing table text is unaffected byte-for-byte when compared
   against `test_markdown_table_output_shape`'s expected string.
   **Location:** `tests/tools/test_ci_junit_summary.py` (extended).

5. **Test name:** `test_render_markdown_table_omits_breakdown_when_no_base_data`
   **Category:** unit
   **Verifies:** when no base-collection data is supplied (the non-PR fallback path — `None` or an
   empty/absent input, not a malformed one), only the existing single-row table renders — no
   broken/empty new/existing table is emitted. Directly required by AC's non-PR fallback bullet.
   **Location:** `tests/tools/test_ci_junit_summary.py` (extended).

6. **Test name:** `test_id_normalization_reconciles_collect_only_nodeid_with_junit_classname`
   **Category:** unit
   **Verifies:** the normalization function that turns a `pytest --collect-only -q` node ID
   (`path/to/test_file.py::TestClass::test_name` or `path/to/test_file.py::test_name`) into the
   same canonical form as a JUnit `<testcase classname="..." name="...">` pair, for both the
   plain-function and class-method shapes, matches the fixture XML's actual `classname`/`name`
   attribute values (dotted-path reconciliation described in investigation.md).
   **Location:** `tests/tools/test_ci_junit_summary.py` (extended).

7. **Test name:** `test_all_fastlane_jobs_have_base_branch_collect_only_step`
   **Category:** architecture guard (static)
   **Verifies:** each of the 9 fast-lane jobs has a new step (after the existing `Run`/pytest step)
   that fetches the base branch and runs `pytest --collect-only` scoped to the same path list as
   the job's own `Run` step, gated by `if: github.event_name == 'pull_request'`.
   **Location:** `tests/static/test_ci_step_summary_reporting.py` (extended) — follows the existing
   `_jobs()`/`yaml.safe_load` pattern already used by the file's five existing tests.

8. **Test name:** `test_base_branch_collect_only_step_run_text_not_tokenized_by_pytest_path_guard`
   **Category:** architecture guard (static)
   **Verifies:** the new collect-only step's `run:` text is prefixed with a non-`pytest`-leading
   shell construct (e.g. `cd /tmp/base-checkout &&`) so
   `tools/gate_checks/ci_workflow_test_coverage.py::_extract_pytest_paths` never tokenizes it as an
   independent pytest statement — directly guards the anti-drift hazard identified in
   investigation.md. Complements test 7 by asserting the *shape*, not just the *presence*, of the
   new step.
   **Location:** `tests/static/test_ci_step_summary_reporting.py` (extended).

9. **Test name:** `test_new_steps_gated_on_pull_request_event_only`
   **Category:** architecture guard (static)
   **Verifies:** every newly added step (base fetch, base collect-only, and any extended
   classification/render step distinct from the existing always-on `Job summary` step) carries
   `if: github.event_name == 'pull_request'` — proves the non-PR fallback is structurally wired,
   not just logically possible. Directly required by the AC's "no error/broken output on missing
   base ref" bullet.
   **Location:** `tests/static/test_ci_step_summary_reporting.py` (extended).

10. **Test name:** `test_no_cross_job_aggregate_step_or_job_added`
    **Category:** architecture guard (static)
    **Verifies:** the full job-name set in `.github/workflows/test.yml` is exactly the pre-existing
    set plus zero new jobs (no new aggregate/summary job appended) — guards the "per-job only, no
    cross-job aggregate" Out of Scope bullet structurally, not just by omission.
    **Location:** `tests/static/test_ci_step_summary_reporting.py` (extended).

11. **Test name:** `test_no_new_requirements_txt_entry_for_new_existing_split` (or extend existing
    `test_no_new_requirements_txt_entry_and_no_new_marketplace_action`)
    **Category:** architecture guard (static)
    **Verifies:** the base-branch collection mechanism (git fetch + git worktree, pure shell/git,
    stdlib-only Python for classification) introduces no new `requirements.txt` entry and no new
    `uses:` marketplace Action — extends the existing test's coverage to this ticket's new steps
    specifically, since the existing test only scanned the pre-ticket `uses:` set.
    **Location:** `tests/static/test_ci_step_summary_reporting.py` (extend the existing test, or add
    a new one if the existing one's scope is kept narrow to the parent ticket).

## Scoped Pytest Commands
```
pytest tests/tools/test_ci_junit_summary.py tests/tools/test_ci_workflow_test_coverage.py -v
pytest tests/static/test_ci_step_summary_reporting.py tests/static/test_ci_narrow_path_filtered_jobs.py tests/static/test_corpus_diversity_ci_isolation.py tests/static/test_ci_requirements_no_ml_stack.py -v
pytest tests/tools -k "parity" -v
```
Never `pytest tests/` — scoped to the CI-tooling/static-guard domain under modification, per
project testing rules.

## Anti-Drift Test Guards
- `test_base_branch_collect_only_step_run_text_not_tokenized_by_pytest_path_guard` (new, #8 above)
  is the direct regression guard for the single most concrete implementation trap identified in
  investigation.md: a bare `pytest --collect-only ...` line (no non-pytest shell prefix) anywhere
  in a fast-lane job's steps would be independently tokenized by
  `tools/gate_checks/ci_workflow_test_coverage.py::_extract_pytest_paths`, silently adding to (or,
  if the path list ever diverges from the head invocation's, corrupting) that job's covered-path
  set.
- `test_slow_and_migration_lanes_jobs_unchanged_by_this_ticket` (existing, parent ticket) must
  still pass unmodified — this ticket must not touch either job, matching this ticket's own Out of
  Scope bullet 3.
- `test_no_cross_job_aggregate_step_or_job_added` (new, #10 above) guards the explicit human
  decision (documented in the ticket's Request Summary) that the new/existing breakdown stays
  per-job only — the single most likely scope-creep vector for this ticket given how natural a
  "roll it all up" follow-on would be.
- `test_new_steps_gated_on_pull_request_event_only` (new, #9 above) guards against the new steps
  silently running (and failing open in a way that produces garbage output, or hard-failing) on
  `push`/`schedule`/`workflow_dispatch` runs — the exact failure mode the ticket's AC explicitly
  calls out as unacceptable ("no error/broken output results from the missing base ref").
- Full existing `tests/tools/test_ci_junit_summary.py` + `tests/static/test_ci_step_summary_reporting.py`
  regression pass (all pre-existing test names, unmodified assertions) is itself the guard against
  this ticket silently altering the pre-existing Passed/Failed/Errors/Skipped/Duration table's
  format or values, per the AC's explicit "byte-for-byte unchanged" requirement.
