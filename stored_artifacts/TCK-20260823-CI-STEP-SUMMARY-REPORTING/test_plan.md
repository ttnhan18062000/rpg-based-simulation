---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260823-CI-STEP-SUMMARY-REPORTING
artifact_type: test_plan
tags: [testing, workflows]
---

# Test Plan — TCK-20260823-CI-STEP-SUMMARY-REPORTING

## How this ticket is actually verifiable in this environment
This ticket's changes are (a) YAML edits to `.github/workflows/test.yml`, and (b) a new small
stdlib-only Python parsing/rendering module. There is no `actionlint`/workflow-schema validator
and no `act` binary in this repo or sandbox. The established, already-in-repo pattern for
testing this exact file is `yaml.safe_load()` + dict/text assertions
(`tests/static/test_ci_narrow_path_filtered_jobs.py`,
`tests/static/test_corpus_diversity_ci_isolation.py`) — no live GitHub Actions execution
anywhere in the existing suite. This ticket's new static test file should follow that same
pattern. The parsing/rendering logic itself (pass/fail/skip/error/duration extraction and
markdown rendering) is verified by ordinary unit tests against sample JUnit XML fixtures — this
is the only one of the ticket's AC #4 three alternative verification paths ("real or
`act`-simulated run, or... unit-testing the parser step's logic against a sample JUnit XML
fixture") actually exercisable here, and should be committed to explicitly rather than left as
an ambiguous fallback.

## Regression Surface

Existing tests that must keep passing, byte-for-byte unaffected in outcome, after this
ticket's edits (grouped by domain; all unit/static — this ticket touches no `src/` gameplay
code, so no integration/arena-combat surface applies):

**Unit / static (CI workflow structure):**
- `tests/tools/test_ci_workflow_test_coverage.py` — all tests, especially
  `test_parses_real_workflow_fastlane_job_paths`, `test_parses_real_workflow_slow_job_blanket`,
  `test_ignore_flag_token_is_not_collected_as_a_covered_path`,
  `test_non_pytest_jobs_contribute_no_paths` — these parse the real, live `test.yml` and will
  break if the added `--junit-xml=` flag or new step accidentally mangles an existing `pytest`
  path token, job name, or job structure.
- `tests/static/test_ci_narrow_path_filtered_jobs.py` — all tests, especially any asserting the
  `slow`/`perf-cert-arena`/`migration-lanes` jobs' `if:`/`needs:` shape stays byte-identical
  (this ticket does not touch those jobs' triggering logic).
- `tests/static/test_corpus_diversity_ci_isolation.py` — both tests; unaffected in scope
  (touches only the `slow` job) but parses the same file and must keep passing.
- `tests/static/test_ci_requirements_no_ml_stack.py` — unaffected in scope, included as
  regression surface since it also asserts against workflow/requirements structure in the same
  area.

**No integration/arena-combat tests are in this ticket's regression surface** — pure
CI-tooling/process work, zero gameplay/engine/combat `src/` changes.

## New Tests Required

Per acceptance criteria:

1. **`test_all_fastlane_jobs_have_junit_xml_flag`**
   Category: unit / architecture guard (static YAML structure).
   Verifies: each of the 9 named fast-lane jobs' `pytest`-invoking step's `run:` text contains
   a `--junit-xml=` token (AC #1).
   Location: `tests/static/test_ci_step_summary_reporting.py` (new file, following
   `tests/static/test_ci_narrow_path_filtered_jobs.py`'s `yaml.safe_load` pattern).

2. **`test_junit_xml_path_is_job_local_and_not_under_tests_dir`**
   Category: unit / architecture guard.
   Verifies: the `--junit-xml=<path>` value for each of the 9 jobs does not start with
   `tests/` (the `ci_workflow_test_coverage.py::_extract_pytest_paths` tokenizer-collision
   trap identified in investigation.md — verified first-hand against the real function's
   logic) and is unique per job path (no two jobs writing the same file, even though each
   runs on its own isolated runner and there is no real cross-job race).
   Location: `tests/static/test_ci_step_summary_reporting.py`.

3. **`test_all_fastlane_jobs_have_always_run_summary_step`**
   Category: unit / architecture guard.
   Verifies: each of the 9 jobs has a step *after* its `pytest` step with `if: always()` whose
   `run:` text invokes the new summary-writing logic (AC #2).
   Location: `tests/static/test_ci_step_summary_reporting.py`.

4. **`test_no_new_requirements_txt_entry_and_no_new_marketplace_action`**
   Category: unit / architecture guard.
   Verifies: `requirements.txt` is unchanged by this ticket (no new package line), and no new
   `uses:` value appears anywhere in `test.yml` beyond the pre-existing set
   (`actions/checkout@v4`, `actions/setup-python@v5`, `actions/upload-artifact@v4`) (AC #3,
   Scope bullet 3).
   Location: `tests/static/test_ci_step_summary_reporting.py`.

5. **`test_slow_and_migration_lanes_jobs_unchanged_by_this_ticket`**
   Category: architecture guard / anti-drift.
   Verifies: the `slow` job's and `migration-lanes` job's full step lists, `if:`, and `needs:`
   are byte-identical to their pre-ticket text — no `--junit-xml`/summary step leaked into
   either job, confirming the deferral decision (investigation.md Risks) was actually honored.
   Location: `tests/static/test_ci_step_summary_reporting.py`.

6. **`test_parse_junit_xml_all_passing`, `test_parse_junit_xml_with_failure`,
   `test_parse_junit_xml_with_error`, `test_parse_junit_xml_with_skip`,
   `test_parse_junit_xml_empty_or_missing_produces_safe_fallback`**
   Category: unit.
   Verifies: the new parser correctly extracts pass/fail/skip/error counts and duration from
   one sample JUnit XML fixture per outcome shape, and that a missing, malformed/truncated, or
   empty (`tests="0"`) XML input degrades to a safe zero-count fallback rather than raising.
   This is the concrete evidence for AC #4's "unit-testing the parser step's logic against a
   sample JUnit XML fixture" path, and is also the `test_path` this ticket's new parity-ledger
   entry (`docs/parity_ledger/infrastructure.yaml`) must cite, since `docs/parity_ledger/
   schema.json` requires a non-null `test_path` whenever `status: verified`.
   Location: `tests/tools/test_ci_junit_summary.py` (new; mirrors a new `tools/ci_junit_summary.py`
   — final module name confirmed at Implement time), with fixture XML files under
   `tests/tools/fixtures/ci_junit_summary/`.

7. **`test_markdown_table_output_shape`**
   Category: unit.
   Verifies: the rendered markdown table contains a header row plus
   Passed/Failed/Errors/Skipped/Duration columns with correct values for a given parsed
   result — proves the "correct counts... visible" half of AC #4 independent of the XML
   parsing step itself.
   Location: `tests/tools/test_ci_junit_summary.py`.

8. **`test_parser_exit_code_independent_of_test_outcome`**
   Category: unit.
   Verifies: the summary script's entry point always completes and returns 0 regardless of
   whether the parsed JUnit XML shows failures, errors, or is missing/malformed — directly
   proving the "purely additive/observational, never a second failure gate" requirement (Scope
   bullet 4, AC #5) and closing the exact risk flagged in investigation.md about an `if:
   always()` step accidentally flipping a job's conclusion.
   Location: `tests/tools/test_ci_junit_summary.py`.

## Scoped Pytest Commands

Regression + new tests, scoped to the affected CI-tooling domain (never `pytest tests/`):

```
pytest tests/static/test_ci_narrow_path_filtered_jobs.py \
       tests/static/test_ci_requirements_no_ml_stack.py \
       tests/static/test_corpus_diversity_ci_isolation.py \
       tests/static/test_ci_step_summary_reporting.py \
       tests/tools/test_ci_workflow_test_coverage.py \
       tests/tools/test_ci_junit_summary.py \
       -m "not slow and not extra_slow" --tb=short -q
```

(`tests/tools/test_ci_junit_summary.py` is the projected new-module test file name — if the
implementer names the module differently, adjust the scoped command to match.)

Since this ticket's Docs Requiring Update touches `docs/parity_ledger/infrastructure.yaml`,
also run the existing parity-ledger schema/structure tests as part of verification (no new
test needed for this part — exact file path TBD at Implement time, this command is
illustrative of the domain, not a pre-verified exact path):

```
pytest tests/tools -k "parity" -m "not slow and not extra_slow" --tb=short -q
```

## Anti-Drift Test Guards

- `test_junit_xml_path_is_job_local_and_not_under_tests_dir` (New Test #2) directly guards
  against the single most concrete implementation trap in this ticket: a `--junit-xml=` path
  starting with `tests/` would silently corrupt `ci_workflow_test_coverage.py`'s
  directory-coverage tokenizer (verified first-hand at
  `tools/gate_checks/ci_workflow_test_coverage.py:91-117`) without failing anything visibly
  today.
- Re-running `tests/tools/test_ci_workflow_test_coverage.py`'s existing assertions after the
  edit (Regression Surface, above) is itself an anti-drift guard: those tests parse the real,
  live `test.yml`, so any accidental corruption of an existing path token by this ticket's edit
  fails immediately, not just the new tests.
- `test_slow_and_migration_lanes_jobs_unchanged_by_this_ticket` (New Test #5), together with the
  existing `tests/static/test_ci_narrow_path_filtered_jobs.py` assertions on those same two
  jobs, catches any "just add it here too since it's adjacent" scope creep into the two jobs
  this ticket explicitly defers.
- `test_parser_exit_code_independent_of_test_outcome` (New Test #8) guards against the most
  behaviorally dangerous regression this ticket could introduce: a summary step that starts
  failing jobs on its own, turning a purely additive/observational feature into a second,
  undocumented failure gate — exactly what Scope bullet 4 and AC #5 forbid.
- `test_no_new_requirements_txt_entry_and_no_new_marketplace_action` (New Test #4) guards the
  "no new dependency / no third-party Action" constraint (AC #3, Scope bullet 3) with an
  automated check rather than relying on manual diff review at PR time.
- `test_all_fastlane_jobs_have_junit_xml_flag` and `test_all_fastlane_jobs_have_always_run_summary_step`
  (New Tests #1, #3) together prevent silent partial rollout — e.g. wiring 8 of the 9 named jobs
  and missing one, which would otherwise only surface as a quiet gap in Actions run summaries
  with no automated signal.
