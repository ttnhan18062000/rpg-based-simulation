---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-CI-SPLIT-API-TOOLS-JOB
phase: open
date: 2026-10-03
tags: [delivery, testing]
---

# TCK-20261003-CI-SPLIT-API-TOOLS-JOB

## Title
Split the `API / tools / logging` CI job into three parallel jobs

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Owner request 2026-10-02/03: `API / tools / logging` is the longest job on every PR run, so split
it into three jobs, in PR #288 (branch `python-code-craft`). Measured on two successful PR runs of
2026-10-02 (37032971448 and 36997263937): the job took 440 s and 517 s, of which `tests/tools`
took 275 s and 337 s, `tests/api` 71 s and 85 s, `tests/cli` 31 s and 42 s, the other directories
about 25 s together, and checkout, Python setup and install about 35 s. `tests/tools` is 211 flat
test files with no subdirectories, so a split along the current directory lines would leave one
job at about 5 to 6 minutes. The split that helps cuts `tests/tools` in two by filename and puts
the other six directories in a third job. Draft by `codebase-planner`; not investigated by the
create-tickets workflow.

## Scope
- Replace the `api-tools` job in `.github/workflows/test.yml` with three jobs that together run
  exactly the tests it runs today, with the same markers (`-m "not slow and not extra_slow"`):
  - `tools-a-e` ("Tools · a–e"): `pytest tests/tools --ignore-glob='tests/tools/test_[f-z]*.py'`
  - `tools-f-z` ("Tools · f–z"): `pytest tests/tools --ignore-glob='tests/tools/test_[a-e]*.py'`
  - `api-cli-engine` ("API / CLI / engine / logging"): `tests/api`, `tests/cli`, `tests/logging`,
    `tests/engine`, `tests/observability`, `tests/visual_assets`, one step per directory as today
- Keep the literal path `tests/tools` in both tools jobs so
  `tools/gate_checks/ci_workflow_test_coverage.py` still sees the directory as covered. The two
  ignore globs are complementary: a file matched by neither runs in both jobs, and no file can be
  matched by both, so nothing can be skipped
- Each new job keeps the reporting the old job had: per-step `if: always()`, its own JUnit XML,
  the merge step where there is more than one XML, the artifact upload under a job-specific name,
  the base-branch collect-only diff (with the same path list or ignore glob as its Run steps) and
  the Job summary step with the job's own name
- Update what names the old job: the `needs:` list of the `slow` job; the job lists in
  `tests/static/test_ci_narrow_path_filtered_jobs.py` (`_OUT_OF_SCOPE_JOBS`, `_EXPECTED_SLOW_NEEDS`)
  and `tests/static/test_ci_step_summary_reporting.py` (`_FASTLANE_JOBS` and the expected
  `needs` block); the `job_paths["api-tools"]` assertion in
  `tests/tools/test_ci_workflow_test_coverage.py`
- Update live references to the job name in tool docstrings and docs that describe present
  behaviour (`tools/test_architecture/junit_cost_report.py`, `tools/test_architecture/core_rpg_report.py`,
  and any guide found by a search for `api-tools`); leave done tickets, stored artifacts and
  historical parity-ledger evidence text alone
- Record the measured before and after job times in this ticket from a real PR run

## Out of Scope
- Changing which tests run, their markers, or any test's content
- Splitting `Integration` or any other job; adding pytest-xdist or any new dependency
- Moving or renaming files under `tests/tools`
- The install step: these three jobs stay on `pip install -r requirements.txt`;
  `TCK-20261002-UV-REMAINING-CI-JOBS` migrates them with the rest
- Any file under `src/`, `.claude/` or `CLAUDE.md`
- Weakening any assertion in the edited tests: only the job names and lists change

## Acceptance Criteria
- [ ] `.github/workflows/test.yml` has no `api-tools` job and has the three jobs named in Scope; a
      search of the repository for `api-tools` finds only historical text (done tickets, stored
      artifacts, evidence fields) and the JUnit names this ticket deliberately keeps, if any
- [ ] The set of test IDs collected by the three jobs together equals the set the old job
      collected, shown by a `--collect-only` comparison recorded in the ticket: no ID missing; an
      ID collected by both tools jobs is listed and explained
- [ ] A test file under `tests/tools` whose name matches neither glob (for example a name not
      starting with `test_` plus a letter) is shown to run in at least one job
- [ ] `python3 tools/gate_checks/ci_workflow_test_coverage.py` reports no uncovered directory, and
      `pytest tests/static/ tests/tools/test_ci_workflow_test_coverage.py` passes
- [ ] Every edit to an existing test file is listed in the ticket and is limited to job names and
      job lists
- [ ] The `slow` job's `needs:` lists all three new jobs and no longer lists `api-tools`
- [ ] All three jobs are green on a real PR run, each writes a Job summary and uploads its JUnit
      artifact, and the run link and the three job durations are recorded in the ticket
- [ ] `git diff --stat <base>...HEAD` for this ticket's commits lists no path under `src/`,
      `.claude/` and not `CLAUDE.md`

## Related Tickets
- TCK-20261002-UV-FIRST-CI-JOB
- TCK-20261002-UV-REMAINING-CI-JOBS
- TCK-20260925-CI-API-TOOLS-LOGGING-PER-DIRECTORY-STEPS
- TCK-20260916-CI-PER-DIRECTORY-STEPS-FOR-BLOCKED-LOGS
- TCK-20260817-CI-COVERAGE-GAP-16-ORPHANED-TEST-DIRS

## Related Docs
- docs/guides/delivery_process.md
- docs/plans/codebase_health/python_code_craft_roadmap.md

## Related Stored Artifacts
- staging_artifacts/TCK-20261003-CI-SPLIT-API-TOOLS-JOB/plan.md
- staging_artifacts/TCK-20261003-CI-SPLIT-API-TOOLS-JOB/investigation.md
- staging_artifacts/TCK-20261003-CI-SPLIT-API-TOOLS-JOB/test_plan.md

## Related Code Areas
- .github/workflows/test.yml
- tools/gate_checks/ci_workflow_test_coverage.py
- tools/ci_junit_merge.py
- tools/ci_junit_summary.py
- tests/static/test_ci_narrow_path_filtered_jobs.py
- tests/static/test_ci_step_summary_reporting.py
- tests/tools/test_ci_workflow_test_coverage.py
- tools/test_architecture/junit_cost_report.py
- tools/test_architecture/core_rpg_report.py

## Assumptions / Open Questions
- Owner decision 2026-10-03 ("yes, do it in this PR"), given to the `codebase-planner` session after
  it was told that the tests pinning CI belong to the testing domain and need an owner decision:
  the split is done on `python-code-craft` in PR #288, including the edits to those tests
- Not an epic child: `TCK-20261002-PYTHON-CODE-CRAFT-EPIC` keeps its seven children. This ticket
  shares the branch and PR only. It lands before `TCK-20261002-UV-REMAINING-CI-JOBS`, which then
  migrates three jobs where it would have migrated one
- Split point from the JUnit timings of run 37032971448 (`tests/tools` total 268 s of test time):
  files `test_a*` to `test_e*` 125 s, `test_f*` to `test_z*` 143 s. Largest files:
  `test_entity_lifecycle_score` 57 s, `test_generate_retro` 33 s. The split will drift as files
  are added; rebalancing is a one-line glob change
- Expected result: the three jobs at about 2.5 to 3 minutes each. The longest job on a PR run then
  becomes `Integration` (315 s and 428 s in the two measured runs), so the wall-clock gain is from
  about 7.3 to 8.6 minutes down to about 5 to 7 minutes
- To verify, not assumed: `ci_workflow_test_coverage.py::_extract_pytest_paths` strips words that
  start with `--ignore=`; a `--ignore-glob=tests/tools/...` word does not start with that prefix,
  so confirm the parser does not collect it as a path. If it does, extend the parser's strip rule
  and add a test for it, and say so here
- Each job repeats about 35 s of checkout, setup and install, so total runner time rises by about
  70 s per run; the repository is public, so this has no cost
- The repository has no branch protection, so no required-check name depends on the old job name
- The quoting of the glob inside the workflow YAML and the shell must keep the brackets literal
  until pytest sees them; check the step's log line on the first run
- Layer `testing` and tags `delivery`, `testing` follow the sibling `TCK-20261002-UV-FIRST-CI-JOB`

## Implementation Notes
**State: implemented and verified locally; open until a real PR run supplies the green result and the three job durations.** Not pushed yet.

Owner decision 2026-10-03 ("yes, do it in this PR"), relayed by `codebase-planner`, covers the workflow change and the job-name edits in the tests that pin CI.

- `.github/workflows/test.yml`: `api-tools` is replaced by `tools-a-e` ("Tools · a–e"), `tools-f-z` ("Tools · f–z") and `api-cli-engine` ("API / CLI / engine / logging"). Each tools job runs `pytest tests/tools` with the other half's `--ignore-glob='tests/tools/test_[f-z]*.py'` or `...[a-e]...` (the `=` form, so the coverage parser never reads the glob as a path), one `Run: tests/tools (a–e|f–z)` step, its own JUnit file, upload, base-branch collection carrying the same glob, and a Job summary under its own name. `api-cli-engine` keeps the per-directory `if: always()` steps for `tests/api`, `cli`, `logging`, `engine`, `observability`, `visual_assets`, the JUnit merge to `reports/junit/api-cli-engine.xml`, upload, the base-branch collection with the `mkdir -p` for `visual_assets`, and the summary. The `slow` job's `needs:` lists the three new jobs in place of `api-tools`. Install steps stay `pip install -r requirements.txt`; `TCK-20261002-UV-REMAINING-CI-JOBS` migrates these three later.
- **Parser check (first listed check):** `_extract_pytest_paths` does not collect a `--ignore-glob=tests/tools/...` word, because it starts with `--`; both tools jobs parse as exactly `{tests/tools}`. No parser change was needed; the synthetic and real cases are pinned in the new test file.
- **Equivalence (measured on the real tree):** the old job's seven paths collect 4,040 test IDs (4,069 minus 29 deselected); `tools-a-e` 1,469, `tools-f-z` 2,110 (28 deselected), `api-cli-engine` 461 (1 deselected); the sum is 4,040, the union equals the old set (0 missing, 0 extra), and no ID is collected by more than one job, so there is no ID to explain.
- A file matching neither glob runs in both tools jobs: shown on a scratch directory with `test_9digits.py` and `test_Upper.py` (in the new test file). Every file in `tests/tools` today starts `test_` plus a lowercase letter.
- **Existing test files edited (names and lists only, no assertion weakened):** `tests/static/test_ci_narrow_path_filtered_jobs.py` (`_OUT_OF_SCOPE_JOBS` and `_EXPECTED_SLOW_NEEDS`: `api-tools` replaced by the three job names); `tests/static/test_ci_step_summary_reporting.py` (`_FASTLANE_JOBS` and the `needs` block of `_EXPECTED_SLOW_YAML`: same replacement); `tests/tools/test_ci_workflow_test_coverage.py` (the one assertion on `job_paths["api-tools"]` now asserts `tests/tools` for both `tools-a-e` and `tools-f-z`). No other existing test was touched; `tests/tools/test_parity_index.py` has a comment mentioning the old job that was left alone.
- **Bug found in planner review and fixed (same branch, before any push):** the five continuation lines of `api-cli-engine`'s "Merge JUnit XML" step ended in two backslashes instead of one (an escaping slip in how I generated the YAML), which inside a `run: |` block is an escaped backslash plus a real newline, so the next line would run as its own command and the step, and the job, would fail with every test passing. Nothing pinned it. Fixed; two tests added (no workflow line ends in two backslashes; the merge arguments equal the written XML paths) and a third checks the detector itself. Proved both ways by executing the real step script under `bash -e` against six JUnit files: the old form exits 1, the fixed form exits 0 and merges all 6 testcases; and the detector flags exactly lines 476 to 480 of `ac512a84`'s workflow and nothing in the fixed one. Also ran the two tools jobs' real `Run` scripts through bash in collect-only mode to confirm the glob quoting reaches pytest intact: `tools-f-z` 2,110 and `tools-a-e` 1,485. The 16 over the earlier 1,469 are the new test file itself, which starts `test_c` and so lands in the a to e half; the equivalence figures above were measured before that file existed. The duplicate comment block on `tools-f-z` is replaced by a pointer to the one on `tools-a-e`.
- Updated live references: `tools/test_architecture/junit_cost_report.py` and `core_rpg_report.py` docstrings (the report text keeps the literal `api-tools` as "the former `api-tools` job", because `tests/unit/tools/test_core_rpg_report.py` asserts it), two lines in `docs/plans/test_architecture/roadmap.md`, and the lane table in `docs/plans/test_architecture/reference/current_test_system_overview.md`. Left alone as historical: done tickets, stored artifacts, parity-ledger evidence text, `docs/plans/archive/`, `audit_phase0_5.md` and the decision record `visual_asset_foundation_adr.md` D7.
- Not an epic child: `TCK-20261002-PYTHON-CODE-CRAFT-EPIC` keeps its seven.
- Still to record after a real run: the run link, the three job durations, and the before figures (440 s and 517 s from runs 37032971448 and 36997263937).

## Test Summary
- `pytest tests/tools/test_ci_split_tools_jobs.py` (new, 16 tests): old job gone, three jobs present, `slow.needs`, each tools job's ignore glob in both its `Run` and base-collection steps, complementary letter ranges over the real `tests/tools` file names, the per-directory steps and JUnit merge of `api-cli-engine`, reporting steps in each new job, pip install kept, parser reads `{tests/tools}` for both tools jobs and ignores the glob word (real and synthetic), a file matching neither glob runs in both, no workflow line ends in a doubled backslash, and the merge step's argument list equals the six XML files the `Run` steps write (parsed with `shlex` after joining continuations).
- `pytest tests/static tests/tools/test_ci_workflow_test_coverage.py tests/tools/test_dashboard_makefile_targets.py tests/unit/tools/test_core_rpg_report.py tests/docs tests/tools/test_tools_orphan_check.py`: 217 passed, 2 skipped, 1 xfailed.
- `python3 tools/gate_checks/ci_workflow_test_coverage.py`: exit 0.
- No `src/`, `.claude/` or `CLAUDE.md` path in the diff.
- Real PR run: not yet.

## Files Changed
- .github/workflows/test.yml
- tests/static/test_ci_narrow_path_filtered_jobs.py, tests/static/test_ci_step_summary_reporting.py, tests/tools/test_ci_workflow_test_coverage.py (names and lists only)
- tests/tools/test_ci_split_tools_jobs.py (new)
- tools/test_architecture/junit_cost_report.py, tools/test_architecture/core_rpg_report.py (docstrings and report limit text)
- docs/plans/test_architecture/roadmap.md, docs/plans/test_architecture/reference/current_test_system_overview.md
- staging_artifacts/TCK-20261003-CI-SPLIT-API-TOOLS-JOB/

## Completion Summary
Not complete: waiting for a real PR run to record the green result and the job durations.
