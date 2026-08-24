---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT
phase: done
date: 2026-08-24
tags: [testing]
---

# TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT

## Title
Break down each fast-lane CI job's step-summary table into new-vs-existing test counts (with pass/fail/skip splits)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`tools/ci_junit_summary.py` and the 9 fast-lane jobs in `.github/workflows/test.yml`
(`unit-core-world`, `unit-gameplay`, `unit-infra`, `integration`, `api-tools`,
`agent-orchestration`, `simulation-quality`, `arch-docs`, `perf-cert-arena`) currently render one
Passed/Failed/Errors/Skipped/Duration table per job to `$GITHUB_STEP_SUMMARY`
(TCK-20260823-CI-STEP-SUMMARY-REPORTING, merged into this branch/PR #65, not yet on `main`). This
ticket extends that same per-job summary to additionally break the job's tests into "new" vs.
"existing" categories, each showing at minimum a total count and a passed/failed/skipped split.

"New" means a test ID (classname+name) present in the job's JUnit XML on the head/PR branch but
absent from a `pytest --collect-only` listing computed against the PR's base branch, within the
same CI job run — a stateless diff, no persisted baseline file. "Existing" means a test ID present
in both. Both the diff-against-base-branch mechanism (vs. a persisted baseline file) and the
per-job-only scope (vs. a cross-job aggregate) were explicitly decided by the human requester after
being presented alternatives — neither decision is open for re-litigation by this ticket's
implementer. Non-PR-triggered runs (push to `main`, `schedule`, `workflow_dispatch`) have no base
branch to diff against and must fall back gracefully to today's single-row summary, with the
fallback condition and rationale documented.

## Scope
- Extend `tools/ci_junit_summary.py` (or add sibling functions/module within `tools/`) with logic
  that, given (a) the job's head-branch JUnit XML (already produced by the prior ticket) and (b) a
  base-branch `pytest --collect-only` test-ID listing, classifies each head-branch test ID as new
  or existing and computes, per category: total count, passed count, failed count, skipped count
  (errors may be folded into failed or broken out as their own column — implementer's judgment,
  but must stay internally consistent with how the existing all-tests row already shows Errors as
  its own column).
- Determine, within each of the 9 fast-lane jobs' workflow steps, whether a base ref is available
  for the current run (PR event vs. push/schedule/workflow_dispatch) using GitHub Actions job
  context (e.g. `github.event_name`, `github.base_ref`, `github.event.pull_request.base.sha`, or
  the `GITHUB_BASE_REF` env var) — reuse the existing precedent already in this same workflow file:
  the `changed-files` job (`.github/workflows/test.yml`, `github.event_name != 'pull_request'`
  check + `fetch-depth: 0` checkout + `github.event.pull_request.base.sha`/`head.sha` +
  `git diff --name-only "$BASE...$HEAD"` with a documented fail-open pattern, added by
  TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS) rather than inventing a new detection mechanism.
- Wire whatever base-branch collection step(s) are needed (checkout config change, a second
  `pytest --collect-only` invocation per job, etc.) into each of the 9 fast-lane jobs, without
  altering the existing head-branch `pytest ...` invocation's marker filter, path list, or
  `--junit-xml` flag from TCK-20260823-CI-STEP-SUMMARY-REPORTING.
- Extend each of the 9 jobs' existing `Job summary` step (or add an adjacent step) so the rendered
  `$GITHUB_STEP_SUMMARY` output includes the existing Passed/Failed/Errors/Skipped/Duration table
  unchanged, plus the new new-vs-existing breakdown table(s)/rows as additional content.
- On non-PR-triggered runs, skip the new/existing computation entirely and render only today's
  existing single-row summary (current behavior, unchanged) — this is the documented fallback, not
  a broken/empty new-vs-existing table.
- Add or extend stdlib-only unit tests for the new classification/parsing logic (no new
  `requirements.txt` entry), and extend the existing static structural guard test
  (`tests/static/test_ci_step_summary_reporting.py`) to cover the new wiring.
- Update the parity ledger: extend `INFRA-379` (`docs/parity_ledger/infrastructure.yaml`) or add a
  new sequential `INFRA-NNN` entry describing the new-vs-existing mechanism and the non-PR
  fallback.
- Document the base-ref-detection choice and the non-PR fallback behavior in Implementation Notes.

## Out of Scope
- Any cross-job aggregate or overall/repo-wide new-vs-existing summary — explicitly decided
  per-job-only by the human requester; do not add a new job or a combined table across jobs.
- A persisted baseline file (e.g. a committed JSON/YAML of known test IDs) — explicitly decided
  against in favor of a stateless per-run diff against the PR base branch; do not introduce one.
- Any change to the `slow` or `migration-lanes` jobs — these were already deferred out of scope by
  TCK-20260823-CI-STEP-SUMMARY-REPORTING and remain out of scope here; not revisited by this
  ticket.
- Any change to the `typecheck` or `changed-files` jobs — no pytest invocation, nothing to extend.
- Any change to the existing `-m "not slow and not extra_slow"` marker filters, per-job path lists,
  `--junit-xml` output path convention, or pytest exit-code semantics established by
  TCK-20260823-CI-STEP-SUMMARY-REPORTING.
- Removing, reformatting, or altering the existing Passed/Failed/Errors/Skipped/Duration
  table/row — this ticket is strictly additive to it.
- Any new third-party GitHub Action, external dashboard/service, or new `requirements.txt`
  dependency.
- Coverage-percentage collection or cross-run historical trend tracking.
- An alternate diff strategy for non-PR runs (e.g. diffing push-to-main against the previous commit
  on `main`) — the non-PR fallback is simply "skip the breakdown, render the existing single row,"
  not a substitute diff mechanism.

## Acceptance Criteria
- [x] For PR-triggered runs, each of the 9 fast-lane jobs' `$GITHUB_STEP_SUMMARY` output includes,
  in addition to the unchanged existing Passed/Failed/Errors/Skipped/Duration row, a new/existing
  breakdown showing at minimum: New-tests total + passed/failed/skipped counts, and Existing-tests
  total + passed/failed/skipped counts.
- [x] "New" is implemented as: a test ID (classname+name) present in the head-branch JUnit XML but
  absent from a `pytest --collect-only` listing computed against the PR's base branch within the
  same job run, with no baseline file read or written anywhere in the repo.
- [x] "Existing" is implemented as: a test ID present in both the head-branch JUnit XML and the
  base-branch collect-only listing.
- [x] For non-PR-triggered runs (verified for at least `push`/`workflow_dispatch`, and `schedule`
  by code-path inspection since it isn't practical to trigger a real cron run), the job detects the
  absence of a usable base ref and renders only the existing single-row summary — no
  new/existing table is attempted, and no error/broken output results from the missing base ref.
- [x] The breakdown is rendered per-job only: no new CI job is added, and no step anywhere produces
  a cross-job aggregate.
- [x] The pre-existing Passed/Failed/Errors/Skipped/Duration table's format and values are
  byte-for-byte unchanged by this ticket's diff (verified by re-running/extending
  `tests/static/test_ci_step_summary_reporting.py`).
- [x] No new entry in `requirements.txt`; no new `uses:` marketplace Action introduced anywhere in
  `.github/workflows/test.yml`.
- [x] `docs/parity_ledger/infrastructure.yaml` reflects the new mechanism (either `INFRA-379`
  updated or a new sequential `INFRA-NNN` entry appended) with a real `test_path` if `status:
  verified`, per `docs/parity_ledger/schema.json`'s requirement for that status.
- [x] New/extended unit tests cover: a fixture pair (base collect-only ID list + head JUnit XML)
  containing at least one test in each of new-passed, new-failed, new-skipped, existing-passed,
  existing-failed, existing-skipped states; the non-PR fallback code path; and a malformed/missing
  base-listing input resolving to a safe fallback consistent with the existing parser's defensive,
  never-raise design (`tools/ci_junit_summary.py`'s `parse_junit_xml` precedent).

## Related Tickets
- TCK-20260823-CI-STEP-SUMMARY-REPORTING (done, merged into this branch/PR #65, not yet on `main`)
  — the direct parent ticket. Built `tools/ci_junit_summary.py`, the `--junit-xml=` flag and `Job
  summary` step on all 9 fast-lane jobs, and `INFRA-379`. This ticket extends that mechanism
  additively; does not reopen its scope or its `slow`/`migration-lanes` deferral decision.
- TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS (done) — added the `changed-files` job in the same
  workflow file, which already implements the `github.event_name`/PR-base-sha/head-sha detection
  and fail-open diff pattern this ticket should reuse for base-ref detection. Precedent, not
  overlap.
- TCK-20260817-CI-FAST-LANE-EXTRA-SLOW-FILTER-INCONSISTENCY (done) — same 9-job set, marker-filter
  concern only; no scope overlap.
- TCK-20260818-STANDARD-SLOW-REGRESSION-OFF-PR-PATH (done) — restructured when the `slow` job
  runs; relevant only in that it reinforces the `slow` job's deferral, not otherwise overlapping.

## Related Docs
- `docs/testing/test_taxonomy.md` — test classification/marker conventions; unchanged by this
  ticket, referenced only because the base-branch `--collect-only` invocation must use the same
  `-m` filter and path list as the existing head-branch `pytest` invocation to keep the two test-ID
  sets comparable.
- No Mechanics Bible chapter or Engine Contract governs CI tooling — same finding as the parent
  ticket; this remains pure process/infra tooling outside `docs/mechanics/` and `docs/engine/`
  scope.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260823-CI-STEP-SUMMARY-REPORTING/investigation.md`,
  `stored_artifacts/TCK-20260823-CI-STEP-SUMMARY-REPORTING/plan.md`,
  `stored_artifacts/TCK-20260823-CI-STEP-SUMMARY-REPORTING/test_plan.md` — directly relevant prior
  investigation/plan establishing the `tools/` (not `tools/gate_checks/`) module placement,
  `main()`-always-returns-0 defensive design, the `reports/junit/` (not `tests/`-prefixed) output
  path convention (to avoid corrupting `tools/gate_checks/ci_workflow_test_coverage.py`'s
  `_extract_pytest_paths` static guard), and the `INFRA-379` parity-ledger entry shape this ticket
  extends.

## Related Code Areas
- `.github/workflows/test.yml` — the 9 fast-lane job blocks (`unit-core-world`, `unit-gameplay`,
  `unit-infra`, `integration`, `api-tools`, `agent-orchestration`, `simulation-quality`,
  `arch-docs`, `perf-cert-arena`), plus the `changed-files` job as base/head-ref-detection
  precedent (`github.event_name`, `github.event.pull_request.base.sha`/`head.sha`, `fetch-depth: 0`
  checkout, fail-open `git diff` pattern).
- `tools/ci_junit_summary.py` — existing JUnit XML → markdown parser/renderer/CLI to extend with
  new-vs-existing classification.
- `tests/tools/test_ci_junit_summary.py` — existing unit tests to extend.
- `tests/static/test_ci_step_summary_reporting.py` — existing static structural guard test to
  extend for the new wiring.
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-379` entry to update, or a new sequential
  `INFRA-NNN` entry to append (re-check current max ID at Implement time; this is a
  concurrently-appended file per other tickets' documented convention).
- `tools/gate_checks/ci_workflow_test_coverage.py` — read-only reference; its
  `_extract_pytest_paths` tokenizer must not be corrupted by any new path/flag added to the
  base-branch `--collect-only` invocation, same constraint the parent ticket already worked around.

## Assumptions / Open Questions
- Computing base-branch `pytest --collect-only` test IDs within the same job requires the job to
  have access to the base branch's tree. The 9 fast-lane jobs currently use a plain
  `actions/checkout@v4` (shallow, head-commit-only, no `fetch-depth` override). Whether the cleanest
  approach is `fetch-depth: 0` plus `git checkout <base-sha> -- <paths>` in a temp location, a
  second `actions/checkout@v4` step against the base ref into a separate directory, `git worktree
  add`, or another mechanism is left to Investigate/Plan to decide — flagged here because it
  materially affects added step count and per-job runtime across all 9 jobs. The `changed-files`
  job's existing `fetch-depth: 0` + `git diff` pattern is the strongest available precedent and
  should be the starting point, not a novel mechanism.
- "Errors folded into failed or shown separately" is left as an implementer judgment call per the
  request, with the one hard constraint that whichever choice is made must stay internally
  consistent with the existing all-tests row's separate Errors column (i.e. don't silently drop
  error visibility in the new tables if the existing row still shows it).
- Test ID identity is "classname+name," matching JUnit XML's `<testcase classname="..."
  name="...">` attributes. Left to Investigate to confirm the cleanest stdlib-only way to derive a
  comparable ID set from `pytest --collect-only` output (its default text/node-ID output format vs.
  requesting a machine-readable form) that lines up with the JUnit XML's classname+name shape
  without introducing a parsing mismatch.
- Runtime/cost impact of running `pytest --collect-only` a second time (collection-only, no test
  execution) inside each of the 9 jobs is not measured by this ticket; assumed acceptable given
  collection is normally fast relative to execution, but should be sanity-checked during Implement
  if any job's collection step turns out unexpectedly slow.
- `layer: testing` chosen to match the direct parent ticket (TCK-20260823-CI-STEP-SUMMARY-REPORTING)
  and the other CI-workflow tickets already touching `.github/workflows/test.yml` under this same
  layer.
- `tags: [testing]` chosen to match the parent ticket's actual frontmatter tags exactly (its
  staging `plan.md` additionally used a `workflows` tag, but that tag's registry note describes
  Claude Code's own agent-workflow tooling, not GitHub Actions CI workflows — considered a
  potential mismatch and deliberately not carried over here; see `tag_relevance_flags` in the
  scoping output for this same concern raised on the parent ticket's own precedent, not this
  ticket's chosen tags).

## Implementation Notes
Followed `staging_artifacts/TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT/plan.md` step-for-step, no
deviations (see that file's "Deviations" section, added confirming this).

- **`tools/ci_junit_summary.py`**: added `TestCaseRecord` (frozen dataclass, `test_id` +
  `status`) and `parse_testcase_records()` (per-testcase status from `<failure>`/`<error>`/
  `<skipped>` child elements, `test_id = f"{classname}::{name}"`, never raises — same
  try/except-around-`ET.parse` shape as `parse_junit_xml`). Added `parse_collect_only_ids()` +
  `_normalize_collect_only_node_id()` (splits a collect-only node ID on `::`, replaces `/` with
  `.` and strips `.py` from only the first/file-path segment, rejoins — reconciling
  `pytest --collect-only -q`'s slash-form path against JUnit's dotted `classname`). Added
  `NewExistingBreakdown` (frozen dataclass, errors broken out as their own column — `new_errors`/
  `existing_errors` — per plan Decision #1, matching the existing all-tests row's separate Errors
  column rather than folding into failed) and `classify_new_vs_existing()` (`base_ids=None` →
  `None` breakdown, the single signal covering both "non-PR run" and "base-branch fetch/collection
  failed"; `base_ids=set()` → every head record classified `new`, never raises). Extended
  `render_markdown_table(summary, job_name, breakdown=None)` — additive only, verified the 2-arg
  call sites (`test_markdown_table_output_shape`, etc.) produce byte-identical output to before
  this ticket. Extended `main()` with an optional 3rd positional arg
  (`base_collect_only_path`, `nargs="?"`, default `None`) inside the existing top-level
  `try/except Exception`, so `main()` still always returns 0 regardless of a missing/malformed
  base-collect file.
- **`.github/workflows/test.yml`**: for each of the 9 fast-lane jobs, added two new steps between
  the existing `Run` and `Job summary` steps — `Fetch base branch for collect-only diff`
  (`git fetch origin "${{ github.base_ref }}" --depth=1` then `git worktree add
  /tmp/base-checkout FETCH_HEAD`, each guarded by its own `if ! ...; then echo "::warning::...";
  exit 0; fi` so a fetch/worktree failure fails the *step* open, never the job) and `Base branch
  test collection` (`if [ -d /tmp/base-checkout ]; then cd /tmp/base-checkout && pytest <job's
  own path list> -m "not slow and not extra_slow" --collect-only -q > /tmp/base-collect.txt 2>&1
  || true; fi`). Both new steps are gated `if: github.event_name == 'pull_request'`, reusing the
  `changed-files` job's own detection condition verbatim (not its `fetch-depth: 0`/`git diff`
  mechanism — that would multiply a full-history fetch across 9 parallel jobs). Chose
  `continue-on-error` via inline shell guards (`|| true`, `exit 0` inside `if !`) rather than the
  step-level `continue-on-error: true` YAML key, because the shell-level guard lets a
  `::warning::` annotation be emitted with context before failing open, and keeps the fail-open
  behavior visible in the step's own log rather than only in the job UI's step-status icon. The
  `cd /tmp/base-checkout && pytest ...` prefix (never a bare `pytest ...` line) is required so
  `tools/gate_checks/ci_workflow_test_coverage.py::_extract_pytest_paths` never tokenizes the
  base-branch invocation as an independent covered-path contributor — verified structurally by
  the new `test_base_branch_collect_only_step_run_text_not_tokenized_by_pytest_path_guard` test
  and by re-running the full existing `tests/tools/test_ci_workflow_test_coverage.py` suite
  (27/27 passed, no change needed in that file). The existing `Job summary` step's `run:` line
  now unconditionally passes `"/tmp/base-collect.txt"` as a 3rd CLI arg to `ci_junit_summary.py`
  in all 9 jobs — its absence on a non-PR run (or after a fetch/collection failure) is itself the
  fallback: `main()` sees a non-existent path, leaves `base_ids=None`, and
  `classify_new_vs_existing()` returns `None`, so `render_markdown_table()` renders only the
  pre-existing single-row table. No `fetch-depth:` override was added to the existing
  `actions/checkout@v4` steps, and the `slow`/`migration-lanes`/`typecheck`/`changed-files` jobs
  were not touched (confirmed structurally by
  `test_slow_and_migration_lanes_jobs_unchanged_by_this_ticket`, unmodified, still passing).
- **Known limitation (documented, not fixed, per plan Decision #2)**: the base-branch
  `--collect-only` pass reuses the head job's already-`pip install`-ed `requirements.txt`
  environment rather than a fresh base-branch install (avoiding a second install's cost). If
  `requirements.txt` differs meaningfully between base and head, some base-branch tests could fail
  to collect under head's installed versions. This degrades to over-counting tests as "new"
  (fail-open, non-crashing) rather than a hard failure — intentional, out of this ticket's
  measured scope, and recorded here and in the extended `INFRA-379` parity ledger text.
- **Non-PR fallback**: `github.event_name == 'pull_request'` gating (not `github.base_ref`/
  `GITHUB_BASE_REF` truthiness) was chosen as the single detection mechanism, matching the
  `changed-files` job's own precedent field choice, to avoid two redundant checks that could drift
  apart later.
- **Parity ledger**: `INFRA-379` (confirmed still the current max `INFRA-` entry via
  `grep -n "^- id: INFRA-"` re-run immediately before editing) was extended in place — `text`
  now documents the new-vs-existing mechanism, the fetch/worktree/collect-only steps, the PR-only
  gating, and the non-PR/failure fallback; `v2_evidence` lists the new functions/dataclasses.
  `status` stays `verified`, `test_path` unchanged (both cited test files were extended, not
  replaced). No new `INFRA-380` entry was appended, per plan Decision #4.

## Test Summary
Ran (all passing):
- `pytest tests/tools/test_ci_junit_summary.py -v` — 23/23 passed (10 pre-existing + 13 new).
- `pytest tests/static/test_ci_step_summary_reporting.py -v` — 10/10 passed (5 pre-existing,
  unmodified assertions except one added `/tmp/base-collect.txt` check, + 5 new).
- `pytest tests/tools/test_ci_workflow_test_coverage.py -v` — 27/27 passed, no source change in
  that file (confirms the `cd &&`-prefixed base-collection step is invisible to
  `_extract_pytest_paths`).
- `pytest tests/static/test_ci_narrow_path_filtered_jobs.py tests/static/test_corpus_diversity_ci_isolation.py tests/static/test_ci_requirements_no_ml_stack.py -v`
  — 17/17 passed, unaffected by this ticket's edits to the same workflow file.
- `pytest tests/tools -k "parity" -v` — 143/143 passed, confirms the extended `INFRA-379` entry
  keeps `docs/parity_ledger/infrastructure.yaml` schema-valid.
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"` — parses cleanly.
- Manual structural verification script (via `python3 -c`) confirming step ordering (`Run` →
  `Fetch base branch...` → `Base branch test collection` → `Job summary`), `if:` gating, and that
  each job's base-branch path list exactly matches its own `Run` step's path list token-for-token.

## Files Changed
- `tools/ci_junit_summary.py` — added `TestCaseRecord`, `parse_testcase_records`,
  `_normalize_collect_only_node_id`, `parse_collect_only_ids`, `NewExistingBreakdown`,
  `classify_new_vs_existing`; extended `render_markdown_table` and `main()` with optional,
  default-`None` parameters.
- `.github/workflows/test.yml` — added `Fetch base branch for collect-only diff` and `Base branch
  test collection` steps to all 9 fast-lane jobs; extended each job's `Job summary` step with a
  3rd CLI argument.
- `tests/tools/test_ci_junit_summary.py` — added 13 new unit tests covering per-testcase parsing,
  node-ID normalization, classification (all six states + malformed/missing fallback), renderer
  extension, and `main()`'s 3-arg path.
- `tests/tools/fixtures/ci_junit_summary/head_with_testcases.xml` — new fixture, 8 testcases
  spanning new-passed/failed/skipped/error and existing-passed/failed/skipped/passed states.
- `tests/tools/fixtures/ci_junit_summary/base_collect_only.txt` — new fixture, a
  `pytest --collect-only -q`-shaped listing matching 4 of the head fixture's test IDs plus a
  trailing non-node-ID summary line (to exercise the line-filtering behavior).
- `tests/static/test_ci_step_summary_reporting.py` — added 5 new static structural guard tests;
  extended `test_all_fastlane_jobs_have_always_run_summary_step` with a `/tmp/base-collect.txt`
  assertion.
- `docs/parity_ledger/infrastructure.yaml` — extended `INFRA-379` in place (`text`, `v2_evidence`).
- `tickets/inprogress/TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT.md` — this file (Status, Acceptance
  Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary).
- `staging_artifacts/TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT/plan.md` — added "Deviations" section
  (none found).

## Completion Summary
Extended `tools/ci_junit_summary.py` with per-testcase JUnit parsing, base-branch collect-only ID
parsing/normalization, and a new-vs-existing classifier, then wired the classification pipeline
into `main()` behind an optional, default-`None` 3rd CLI argument so the pre-existing
Passed/Failed/Errors/Skipped/Duration table stays byte-for-byte unchanged when no base data is
supplied. Wired two new PR-only-gated steps (base-branch fetch + `git worktree add`, then a
`cd`-prefixed `pytest --collect-only` pass) into all 9 fast-lane jobs in
`.github/workflows/test.yml`, and extended each job's `Job summary` step to pass the resulting
file as the CLI's 3rd argument unconditionally — its absence on non-PR runs is the entire non-PR
fallback mechanism, requiring no separate code path. Added 13 new unit tests and 5 new static
structural guard tests (all passing), extended the parity ledger's `INFRA-379` entry in place, and
verified zero regressions in the full adjacent CI-workflow static-guard test surface plus the
parity-ledger schema test suite.
