---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260823-CI-STEP-SUMMARY-REPORTING
phase: done
date: 2026-08-23
tags: [testing]
---

# TCK-20260823-CI-STEP-SUMMARY-REPORTING

## Title
Add structured pytest result summaries (pass/fail/skip/error/duration) to $GITHUB_STEP_SUMMARY for all CI pytest jobs

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`.github/workflows/test.yml` currently runs 9 parallel pytest jobs (`unit-core-world`, `unit-gameplay`, `unit-infra`, `integration`, `api-tools`, `agent-orchestration`, `simulation-quality`, `arch-docs`, `perf-cert-arena`) each invoking `pytest ... -m "not slow and not extra_slow" --tb=short -q`, with zero structured output surfaced anywhere — no `$GITHUB_STEP_SUMMARY`, no JUnit XML, no coverage. The only visibility into a run's outcome is raw `-q` log text. This ticket adds a per-job step that appends a markdown summary table (pass/fail/skip/error counts, duration) to `$GITHUB_STEP_SUMMARY` using GitHub's native step-summary mechanism, with no new external dependency and no third-party dashboard service.

## Scope
- Add `--junit-xml=<path>` (pytest's built-in, dependency-free reporter) to each of the 9 fast-lane pytest-invoking jobs' `pytest` command in `.github/workflows/test.yml`: `unit-core-world`, `unit-gameplay`, `unit-infra`, `integration`, `api-tools`, `agent-orchestration`, `simulation-quality`, `arch-docs`, `perf-cert-arena`.
- Add a subsequent per-job step, run with `if: always()` (so it also fires on test failure), that parses that job's JUnit XML and appends a markdown table (pass / fail / skip / error counts, duration) to `$GITHUB_STEP_SUMMARY`.
- The parsing step must use only the Python standard library (e.g. `xml.etree.ElementTree`) or a `pytest`-native mechanism — no new PyPI dependency added to `requirements.txt`, no third-party GitHub Action, no external dashboard/service call.
- The summary step must not alter the job's pass/fail exit code — the existing `pytest` invocation's exit code remains the sole source of job success/failure; the summary step is purely additive/observational.
- Existing test selection (`-m "not slow and not extra_slow"`, the explicit path lists per job) is unchanged.
- Decide and document (in Implementation Notes) whether the same treatment extends to the `slow` job's two pytest-driven steps (`make simq-corpus-diversity-slow-isolated`, the main `pytest tests/ -m "slow or extra_slow" ...` step) and the `migration-lanes` job's `make`-driven steps — these don't share the fast-lane jobs' exact invocation shape and may need their own follow-up scope; if deferred, note it explicitly as an assumption below rather than silently leaving them out.

## Out of Scope
- Cross-run trend tracking (e.g. comparing today's summary against yesterday's).
- Coverage-over-time collection or coverage percentage collection itself (`--cov` / `pytest-cov`) — not part of this change, a separate decision.
- Any third-party dashboard, external test-reporting service, or new GitHub Marketplace Action.
- Changing which tests run, the `-m` marker filters, or any job's pass/fail exit-code semantics.
- The `typecheck` job (mypy, not pytest) and the `changed-files` gate job (no tests) — out of scope, no test results to summarize.
- Retrofitting `--junit-xml` / summary parsing onto the `slow` and `migration-lanes` jobs unless explicitly decided in-scope during implementation (see Scope's last bullet) — if deferred, that deferral itself is the documented outcome, not silent scope-narrowing.

## Acceptance Criteria
- [x] Each of the 9 named fast-lane jobs' `pytest` invocation includes `--junit-xml=<path>` writing to a job-local results file.
- [x] Each of those 9 jobs has a subsequent step with `if: always()` that reads that job's JUnit XML and appends a markdown table with pass/fail/skip/error counts and duration to `$GITHUB_STEP_SUMMARY`.
- [x] The summary-writing step introduces no new entry in `requirements.txt` and no new `uses:` Action beyond what's already in the workflow.
- [x] A run with all tests passing produces a job summary visible on the GitHub Actions run page showing correct counts (verified via a real or `act`-simulated run, or by unit-testing the parser step's logic against a sample JUnit XML fixture).
- [x] A run with at least one failing test still produces a job summary (via `if: always()`) and the job still reports a non-zero exit / failed status — exit-code semantics are unchanged from current behavior.
- [x] Existing `-m "not slow and not extra_slow"` filters and per-job path lists are byte-identical to before, aside from the added `--junit-xml` flag.

## Related Tickets
- TCK-20260627-P2M-CI-ARTIFACTS (done) — added `actions/upload-artifact` for `reports/certification/` in the `slow` job; establishes precedent for CI-artifact-adjacent additions to this same workflow file, but covers artifact upload, not step-summary reporting — no scope overlap.
- TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS (done) — path-filter gating for `perf-cert-arena`/`migration-lanes`; touches the same workflow file, no overlap with reporting.
- TCK-20260817-CI-FAST-LANE-EXTRA-SLOW-FILTER-INCONSISTENCY (done) — fixed marker-filter inconsistency across the same 9-ish fast-lane jobs; same job set, different concern (selection vs. reporting), no overlap.
- TCK-20260818-STANDARD-SLOW-REGRESSION-OFF-PR-PATH (done) — restructured when the `slow` job runs; relevant context for the Scope bullet about whether to extend summary reporting to the `slow` job.

## Related Docs
- `docs/testing/test_taxonomy.md` — test classification rules (marker conventions referenced by the unchanged `-m` filters).
- No Mechanics Bible chapter or Engine Contract governs CI tooling; this is process/infra tooling outside `docs/mechanics/` and `docs/engine/` scope.

## Related Stored Artifacts
- None found covering `$GITHUB_STEP_SUMMARY`, JUnit XML, or CI test-result reporting specifically (searched `stored_artifacts/` for CI/test.yml/reporting investigations).

## Related Code Areas
- `.github/workflows/test.yml` (all 9 fast-lane job blocks: `unit-core-world`, `unit-gameplay`, `unit-infra`, `integration`, `api-tools`, `agent-orchestration`, `simulation-quality`, `arch-docs`, `perf-cert-arena`)
- Possibly a new small helper script under `tools/` (e.g. `tools/ci_junit_summary.py`) if the JUnit→markdown parsing logic is non-trivial enough to warrant its own tested module rather than inline shell/Python in the workflow YAML — left to Investigate/Plan to decide.

## Assumptions / Open Questions
- Assumes `pytest`'s built-in `--junit-xml` flag is available with no extra dependency (it is — bundled with pytest itself, already in `requirements.txt`). If this assumption is wrong the scope would need a different native mechanism.
- Assumes "GitHub's native mechanism" means writing to the `$GITHUB_STEP_SUMMARY` env-var file directly (bash `>>`) or via `actions/github-script`, not a marketplace test-reporter Action — the request explicitly says "no third-party dashboard service," read here as also excluding third-party summary-rendering Actions, to keep the mechanism auditable as plain repo-owned shell/Python. If the requester intended to allow a well-known first-party-adjacent Action (e.g. `dorny/test-reporter`), that would invalidate this scoping and should be raised before implementation.
- Open question, deferred to Implementation Notes per Scope: whether the `slow` job and `migration-lanes` job get the same treatment in this ticket or a follow-up — flagged rather than silently decided, since their invocation shapes differ from the 9 fast-lane jobs.
- `layer: testing` chosen to match the layer already used by the three other recent CI-workflow tickets touching `.github/workflows/test.yml` (TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS, TCK-20260817-CI-FAST-LANE-EXTRA-SLOW-FILTER-INCONSISTENCY, TCK-20260818-STANDARD-SLOW-REGRESSION-OFF-PR-PATH), which is more specific than `misc` and consistent with existing convention for this file.

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260823-CI-STEP-SUMMARY-REPORTING/plan.md` Steps 1-4 and
6 (Step 5, the parity ledger entry, is explicitly deferred to the Parity phase — see that plan
file's "Deviations" section).

- **Step 1 + 3 combined**: for each of the 9 fast-lane jobs (`unit-core-world`, `unit-gameplay`,
  `unit-infra`, `integration`, `api-tools`, `agent-orchestration`, `simulation-quality`,
  `arch-docs`, `perf-cert-arena`), appended `--junit-xml=reports/junit/<job-key>.xml` as the final
  token of the existing `pytest ...` invocation, and added an immediately-following `Job summary`
  step (`if: always()`) that pipes `python3 tools/ci_junit_summary.py "reports/junit/<job-key>.xml"
  "<job-key>"` into `$GITHUB_STEP_SUMMARY`. No existing path token, `-m` filter, or `--tb`/`-q`
  flag was reordered or retyped — only the new flag was appended.
- **Step 2**: built `tools/ci_junit_summary.py` (stdlib-only: `argparse`, `xml.etree.ElementTree`,
  `dataclasses`) with `parse_junit_xml` (defensive against missing file / `ET.ParseError` / OSError,
  returns an all-zero `parse_ok=False` sentinel), `render_markdown_table` (renders a
  Passed/Failed/Errors/Skipped/Duration table, or a "no results" row when `parse_ok=False`), and
  `main()` (always returns 0, even on an unexpected exception, so the new `if: always()` workflow
  step can never flip a job's Actions-reported conclusion). Placed in `tools/`, not
  `tools/gate_checks/`, per the plan's finding that `tools/gate_checks/`'s own test suite enforces
  a no-CLI-entry-point convention this module must violate by design.
- **Step 4**: added `tests/static/test_ci_step_summary_reporting.py` (5 tests) asserting the
  `--junit-xml=` flag is present and job-local/unique per job, every fast-lane job's `Job summary`
  step comes after its pytest step with `if: always()` and pipes into `$GITHUB_STEP_SUMMARY`, no
  banned dependency (`pytest-cov`/`pytest-html`) or marketplace Action
  (`dorny/test-reporter`/`EnricoMi/...`) was introduced, the set of `uses:` values across the whole
  workflow file is unchanged, and the `slow`/`migration-lanes` jobs are byte-identical (verified by
  `yaml.safe_load`-equality against an embedded expected-YAML literal) to their pre-ticket shape.
- **Deferral decision (Scope bullet 5 / Out of Scope bullet 5)**: `slow` and `migration-lanes` are
  NOT given `--junit-xml`/summary treatment in this ticket. `migration-lanes` has no direct
  `pytest` invocation at all (both its steps are `make` targets); `slow` has three differently-
  shaped steps (`make ...`, a bare multi-marker `pytest tests/ -m "slow or extra_slow" ...` line,
  another `make ...`). Neither matches the 9 fast-lane jobs' single-`pytest`-line shape, and
  extending identical treatment to either would require a per-job design decision this ticket's
  Scope did not size. This is recorded as a deliberate deferral to a follow-up ticket, not a
  silent omission — guarded by `test_slow_and_migration_lanes_jobs_unchanged_by_this_ticket`.
- **Deviation**: the parity ledger entry (plan Step 5, `INFRA-379` or current max+1) was not added
  during Implement — this run's dispatch instructions reserved `docs/parity_ledger/` edits for the
  Parity phase. See `staging_artifacts/TCK-20260823-CI-STEP-SUMMARY-REPORTING/plan.md`
  "Deviations" for detail.

## Test Summary
New tests: `tests/tools/test_ci_junit_summary.py` (10 tests: all-pass, failure, error, skip,
empty-testsuite, malformed, missing-file parse outcomes; markdown table shape for both a normal
and a parse-failure result; `main()` always-returns-0 across all fixture outcomes) and
`tests/static/test_ci_step_summary_reporting.py` (5 tests, see Implementation Notes). All 15 new
tests pass. Regression surface re-run and green: `tests/static/test_ci_narrow_path_filtered_jobs.py`,
`tests/static/test_ci_requirements_no_ml_stack.py`, `tests/static/test_corpus_diversity_ci_isolation.py`,
`tests/tools/test_ci_workflow_test_coverage.py` (44 tests, all pass) — confirms the added
`--junit-xml=` flags and new steps did not corrupt any existing path-token parsing or job
structure assertion. Also re-ran the parity-ledger domain (`pytest tests/tools -k "parity"`, 143
passed) since no ledger edit was made in this phase, confirming no unrelated breakage.

## Files Changed
- `.github/workflows/test.yml` — added `--junit-xml=reports/junit/<job-key>.xml` and a `Job
  summary` step to each of the 9 fast-lane jobs; `slow`/`migration-lanes`/`typecheck`/
  `changed-files` untouched.
- `tools/ci_junit_summary.py` (new) — JUnit XML → markdown summary parser/renderer/CLI.
- `tests/tools/test_ci_junit_summary.py` (new)
- `tests/tools/fixtures/ci_junit_summary/all_pass.xml` (new)
- `tests/tools/fixtures/ci_junit_summary/has_failure.xml` (new)
- `tests/tools/fixtures/ci_junit_summary/has_error.xml` (new)
- `tests/tools/fixtures/ci_junit_summary/has_skip.xml` (new)
- `tests/tools/fixtures/ci_junit_summary/empty.xml` (new)
- `tests/tools/fixtures/ci_junit_summary/malformed.xml` (new)
- `tests/static/test_ci_step_summary_reporting.py` (new)
- `staging_artifacts/TCK-20260823-CI-STEP-SUMMARY-REPORTING/investigation.md` (new this run —
  untracked prior to this session)
- `staging_artifacts/TCK-20260823-CI-STEP-SUMMARY-REPORTING/plan.md` (new this run; also had a
  "Deviations" section added during Implement)
- `staging_artifacts/TCK-20260823-CI-STEP-SUMMARY-REPORTING/test_plan.md` (new this run —
  untracked prior to this session)
- `docs/parity_ledger/infrastructure.yaml` — new entry `INFRA-379` (P2, verified), added during
  the Parity phase per the Implementation Notes' documented deferral above.
- `tickets/inprogress/TCK-20260823-CI-STEP-SUMMARY-REPORTING.md` — this file (Status,
  Implementation Notes, Test Summary, Files Changed, Completion Summary, Acceptance Criteria)

## Completion Summary
Added `--junit-xml=` output and a defensive, always-0-exit `Job summary` step (backed by a new
stdlib-only `tools/ci_junit_summary.py` module) to each of the 9 fast-lane pytest jobs in
`.github/workflows/test.yml`, so every fast-lane CI run now surfaces a pass/fail/skip/error/
duration markdown table in `$GITHUB_STEP_SUMMARY` without changing exit-code semantics, adding a
dependency, or adding a marketplace Action. The `slow` and `migration-lanes` jobs are explicitly
deferred (documented above and guarded by a new static test) since their invocation shapes don't
match the 9 fast-lane jobs. A new static structural test file and a new unit test file (15 tests
total) cover the wiring and the parser/renderer logic; the full CI-workflow regression surface
(44 existing tests) stays green. The parity ledger entry is intentionally left to the Parity
phase per this run's own dispatch scope.
