---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT
artifact_type: plan
tags: [testing]
---

# Implementation Plan — TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT

## Summary
Extend `tools/ci_junit_summary.py` with three new, additive layers on top of the existing
aggregate-only parser (`parse_junit_xml`/`JUnitSummary`/`render_markdown_table`, confirmed at
`tools/ci_junit_summary.py:32-116` to never read `<testcase>` children today): (1) per-testcase
status parsing from the head-branch JUnit XML, (2) parsing/normalizing a
`pytest --collect-only -q` text listing from the base branch into a comparable ID set, and (3) a
classifier that splits head-branch test IDs into new-vs-existing buckets with
passed/failed/errors/skipped counts. The renderer and CLI are then extended with optional,
default-`None` parameters so the pre-existing Passed/Failed/Errors/Skipped/Duration table stays
byte-for-byte unchanged when no base data is supplied. Separately, each of the 9 fast-lane jobs in
`.github/workflows/test.yml` gets two new steps — a `git fetch`+`git worktree add` of the PR base
branch and a `cd`-prefixed `pytest --collect-only` pass against it — both gated
`if: github.event_name == 'pull_request'`, plus a third CLI argument added to the existing `Job
summary` step invocation. Non-PR runs never produce the new steps' output file, so the CLI's
existing "missing input renders no breakdown" fallback (built in step 5) is the *entire* fallback
mechanism — no separate non-PR code path is needed. Errors are broken out as their own column in
the new tables (not folded into failed), matching the existing row's shape. `INFRA-379` is updated
in place rather than appended as a new entry, since this is the same mechanism evolving additively.

## Steps

### Step 1 — Add per-testcase status parsing
**Files:** `tools/ci_junit_summary.py`
**Change:** Add a new frozen dataclass `TestCaseRecord(test_id: str, status: str)` (status one of
`"passed"`/`"failed"`/`"error"`/`"skipped"`) and a new function
`parse_testcase_records(path: Path) -> list[TestCaseRecord]`. Confirmed by reading the live
fixtures directly (`tests/tools/fixtures/ci_junit_summary/has_failure.xml:6-8`,
`has_error.xml:5-7`, `has_skip.xml:5-7`, `all_pass.xml:5-9`) that pytest's JUnit writer encodes
per-testcase outcome as a **child element** of `<testcase>`: a `<failure>` child means `failed`, an
`<error>` child means `error`, a `<skipped>` child means `skipped`, and no such child means
`passed`. `test_id` is `f"{classname}::{name}"` directly from the `<testcase classname=... name=...
>` attributes (confirmed shape at `all_pass.xml:5`, e.g.
`classname="tests.unit.core.test_a" name="test_one"` — this is already the JUnit-side canonical ID,
no transform needed, per investigation.md's ID-matching sub-problem finding). Reuse the same
try/except-around-`ET.parse` structure as `parse_junit_xml` (`tools/ci_junit_summary.py:81-84`) so
a missing/malformed file returns `[]` rather than raising — this function must be at least as
defensive as the existing parser since it will be called from the same `if: always()` CI step.
**Do NOT touch:** `JUnitSummary`, `_summarize_testsuite_elements`, or `parse_junit_xml`'s existing
return contract — this is a new, separate function reading the same file, not a modification of
the aggregate path.
**Verify:** New fixtures `tests/tools/fixtures/ci_junit_summary/head_with_testcases.xml` (built for
this step, containing at least one passed/failed/error/skipped testcase) plus a new unit test
asserting `parse_testcase_records` returns the correct `(test_id, status)` pairs for each state.

### Step 2 — Add base-collect-only ID parsing and node-ID normalization
**Files:** `tools/ci_junit_summary.py`
**Change:** Add `parse_collect_only_ids(text: str) -> set[str]` and a private helper
`_normalize_collect_only_node_id(node_id: str) -> str`. `pytest --collect-only -q` prints one node
ID per line in the form `path/to/test_file.py::[TestClass::]test_name` (slash-form path, `.py`
intact) — per investigation.md's confirmed reconciliation, the normalizer splits on `::`, replaces
`/` with `.` and strips the trailing `.py` from the first (file-path) segment only, then rejoins
all segments with `::`, producing the same canonical form as Step 1's `classname::name` IDs.
`parse_collect_only_ids` must skip blank lines and any non-node-ID line pytest's `-q` collection
output can include (e.g. a trailing `N tests collected in Ys` summary line) — filter to lines
containing `::`; anything else is silently dropped, never raised. Empty or garbage input (no `::`
on any line) must resolve to an empty set, not an exception — this is the base for Step 3's
malformed-input fallback.
**Do NOT touch:** Any existing function signature in the module.
**Verify:** New unit test `test_id_normalization_reconciles_collect_only_nodeid_with_junit_classname`
(test_plan.md #6) asserting both the plain-function and class-method node-ID shapes normalize to
match `head_with_testcases.xml`'s actual `classname`/`name` values from Step 1.

### Step 3 — Add the new-vs-existing classifier
**Files:** `tools/ci_junit_summary.py`
**Change:** Add a frozen dataclass `NewExistingBreakdown` with fields `new_total, new_passed,
new_failed, new_errors, new_skipped, existing_total, existing_passed, existing_failed,
existing_errors, existing_skipped` (errors broken out as their own column, not folded into failed —
see Decisions Made by This Plan #1) and a function
`classify_new_vs_existing(head_records: list[TestCaseRecord], base_ids: set[str] | None) ->
NewExistingBreakdown | None`. If `base_ids is None`, return `None` immediately (this is the
single signal the renderer in Step 4 uses to omit the breakdown entirely — it is also what a
missing/unreadable base-collect file resolves to, once Step 5 wires file-reading around this
function, so this one `None` path covers both the non-PR fallback and any fetch/collection
failure). If `base_ids` is an empty set (e.g. from Step 2's malformed-input fallback), classify
every head record as `new` (nothing was found in the base) rather than raising — this keeps the
function total and matches the "malformed/missing base listing resolves to a safe fallback"
requirement without inventing a second sentinel value. For each `head_records` entry, `new` iff
`test_id not in base_ids`, `existing` iff `test_id in base_ids`; within each bucket, increment the
passed/failed/errors/skipped counter matching `status`.
**Do NOT touch:** `JUnitSummary`'s existing fields (no `errors`-folding change to the pre-existing
aggregate row's shape).
**Verify:** New unit tests `test_classify_new_vs_existing_splits_by_base_collect_only_ids` and
`test_classify_new_vs_existing_all_six_states` (test_plan.md #1, #2) using a fixture pair
(`base_collect_only.txt` + `head_with_testcases.xml`, both new fixtures under
`tests/tools/fixtures/ci_junit_summary/`) containing at least one test in each of new-passed,
new-failed, new-skipped, existing-passed, existing-failed, existing-skipped states; and
`test_classify_malformed_or_missing_base_listing_resolves_to_safe_fallback` (test_plan.md #3) for
`base_ids=None` and `base_ids=set()`.

### Step 4 — Extend the renderer, additive and default-safe
**Files:** `tools/ci_junit_summary.py`
**Change:** Change `render_markdown_table`'s signature to
`render_markdown_table(summary: JUnitSummary, job_name: str, breakdown: NewExistingBreakdown | None
= None) -> str`. When `breakdown is None`, the function body is untouched — must produce the exact
same string as today (confirmed against `tools/ci_junit_summary.py:101-116`, the existing
`header + ...` return value). When `breakdown is not None`, append a second markdown table after
the existing one with columns `New total | New passed | New failed | New errors | New skipped` and
a third with `Existing total | Existing passed | Existing failed | Existing errors | Existing
skipped` (two tables, or one combined table with a leading New/Existing label column — implementer
may pick either shape as long as both category totals and their passed/failed/errors/skipped
splits are present, per the AC's "at minimum" wording). This is the only writer of
`render_markdown_table`'s return value into the workflow's step output — no other code path renders
this table, so no ordering/collision concern applies here (contrast with Step 6/7 below, where the
*workflow* has other writers to the shared step-summary stream).
**Do NOT touch:** The existing table's header text, column order, or number formatting
(`f"{summary.duration_seconds:.2f}"` etc.) — any of these being touched would fail
`test_markdown_table_output_shape` (`tests/tools/test_ci_junit_summary.py:94-99`), which calls
`render_markdown_table(summary, "unit-core-world")` with only two positional args and must keep
passing unmodified.
**Verify:** `test_markdown_table_output_shape` and `test_markdown_table_output_shape_for_parse_failure`
(existing, must still pass unmodified — proves the 2-arg call site is untouched); new
`test_render_markdown_table_includes_new_existing_breakdown` and
`test_render_markdown_table_omits_breakdown_when_no_base_data` (test_plan.md #4, #5).

### Step 5 — Wire the classification pipeline into `main()`
**Files:** `tools/ci_junit_summary.py`
**Change:** Add a third, optional positional CLI argument to `main()`'s `argparse.ArgumentParser`
(`tools/ci_junit_summary.py:121-124`): `base_collect_only_path` with `nargs="?", default=None`.
Inside `main()`, after computing `summary` (unchanged line at `:126`), also call
`parse_testcase_records(Path(args.junit_xml_path))` (Step 1) to get head records; if
`args.base_collect_only_path` is given and the file exists and is non-empty, read it and call
`parse_collect_only_ids` (Step 2) to get `base_ids`, else leave `base_ids = None`. Call
`classify_new_vs_existing(head_records, base_ids)` (Step 3) to get `breakdown`, then call
`render_markdown_table(summary, args.job_name, breakdown)` (Step 4). The whole new block must stay
inside the existing `try/except Exception` in `main()` (`:120,128-129`) so any unexpected failure
in the new code path still falls through to the existing "Failed to render job summary" fallback
string and `return 0` — this is the same `main()`-always-returns-0 guarantee the module's docstring
(`tools/ci_junit_summary.py:6-9`) already documents as load-bearing for the `if: always()` step; the
new code must not weaken it.
**Do NOT touch:** The two existing required positional args' names/order (`junit_xml_path`,
`job_name`) — the existing `main([str(...), "unit-core-world"])` 2-arg call sites in
`test_parser_exit_code_independent_of_test_outcome` (`tests/tools/test_ci_junit_summary.py:109-114`)
must keep working unmodified since the new arg is optional.
**Verify:** `test_parser_exit_code_independent_of_test_outcome` (existing, must still pass with only
2 args); new test exercising `main()` with a 3rd arg pointing at a fixture `base_collect_only.txt`
file, asserting exit code is still 0 and the breakdown appears in stdout.

### Step 6 — Wire base-branch fetch + collect-only steps into the 9 fast-lane jobs
**Files:** `.github/workflows/test.yml`
**Change:** For each of the 9 fast-lane jobs (`unit-core-world` L24-52, `unit-gameplay` L55-83,
`unit-infra` L86-118, `integration` L121-136, `api-tools` L139-159, `agent-orchestration` L166-192,
`simulation-quality` L195-210, `arch-docs` L213-232, `perf-cert-arena` L270-289 — line numbers as
read directly from the live file this session), insert two new steps after the existing `Run` step
and before the existing `Job summary` step:
```yaml
- name: Fetch base branch for collect-only diff
  if: github.event_name == 'pull_request'
  run: |
    if ! git fetch origin "${{ github.base_ref }}" --depth=1 2>&1; then
      echo "::warning::base-branch fetch failed — new/existing breakdown will be skipped"
      exit 0
    fi
    if ! git worktree add /tmp/base-checkout FETCH_HEAD 2>&1; then
      echo "::warning::base-branch worktree add failed — new/existing breakdown will be skipped"
      exit 0
    fi
- name: Base branch test collection
  if: github.event_name == 'pull_request'
  run: |
    if [ -d /tmp/base-checkout ]; then
      cd /tmp/base-checkout && pytest <same path list as this job's Run step> \
        -m "not slow and not extra_slow" --collect-only -q > /tmp/base-collect.txt 2>&1 || true
    fi
```
using each job's own existing path list (e.g. `tests/unit/core tests/unit/kernel ...` for
`unit-core-world`, read verbatim from that job's `Run` step at L34-47) so the two ID sets stay
comparable per the taxonomy-consistency requirement in investigation.md. The worktree is placed
under `/tmp` (outside `$GITHUB_WORKSPACE`), and the `cd /tmp/base-checkout &&` prefix is deliberate
and non-negotiable: it keeps the whole `pytest --collect-only ...` line invisible to
`tools/gate_checks/ci_workflow_test_coverage.py::_extract_pytest_paths`
(`tools/gate_checks/ci_workflow_test_coverage.py:91-117`), which starts a new pytest-statement scan
on any stripped line that equals `"pytest"` or starts with `"pytest "`/`"pytest\\"` (`:97`) — a bare
`pytest --collect-only ...` line would be independently tokenized into that job's covered-path set
(`parse_job_pytest_paths`, `:54-73`, which walks every line under a job's YAML body across all its
steps, not just `Run`). Both new steps are gated `if: github.event_name == 'pull_request'` at the
YAML step level, matching the investigation's confirmed table (`github.base_ref` is non-empty iff
`github.event_name == 'pull_request'`) and the existing `changed-files` job's own detection
condition (`.github/workflows/test.yml:250`, `if [ "${{ github.event_name }}" != "pull_request" ];
... exit 0; fi`) — reusing that job's *detection condition*, not its *fetch mechanism*
(`changed-files` uses `fetch-depth: 0` + `git diff`; this is a new fetch-by-branch-name +
`git worktree add` combination, called out explicitly in investigation.md as untested-in-this-repo
and requiring its own fail-open guard, added above via the `if ! ... ; then ... exit 0; fi` pattern
matching `changed-files`' own `2>&1`/warning-then-continue style at L257-262).
**Shared-resource / other-writers note:** `.github/workflows/test.yml` is edited by many tickets
over time; the other writers whose work this step must not disturb, all confirmed by direct read of
the current file: `changed-files` (L239-267, TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS — read-only
precedent here, not touched), `perf-cert-arena`'s `needs`/`if` gating (L270-289,
TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS), `slow` (L323-362) and `migration-lanes` (L292-306,
both out of scope per the ticket and guarded by `test_slow_and_migration_lanes_jobs_unchanged_by_this_ticket`,
`tests/static/test_ci_step_summary_reporting.py:196-208`), and `typecheck` (L308-321, no pytest
invocation, untouched). None of these share a step list with the 9 fast-lane jobs this step edits,
so there is no ordering/race concern between this step's edits and any of them — the only actual
collision risk is the static tokenizer above, addressed by the `cd &&` prefix.
**Do NOT touch:** The existing `Run` step's `run:` text (marker filter, path list, `--junit-xml=`
flag) in any of the 9 jobs, the existing `actions/checkout@v4` step (no `fetch-depth:` override
added there), and the `slow`/`migration-lanes`/`typecheck`/`changed-files` job blocks.
**Verify:** New static tests `test_all_fastlane_jobs_have_base_branch_collect_only_step` and
`test_base_branch_collect_only_step_run_text_not_tokenized_by_pytest_path_guard` (test_plan.md #7,
#8) in `tests/static/test_ci_step_summary_reporting.py`; existing `tests/tools/test_ci_workflow_test_coverage.py`
suite re-run to confirm `_extract_pytest_paths` output is unaffected (regression, no source change
in that file).

### Step 7 — Extend each job's `Job summary` step to pass the base-collect-only path
**Files:** `.github/workflows/test.yml`
**Change:** In each of the 9 jobs' existing `Job summary` step (`if: always()`, confirmed present
in all 9 at the line ranges cited in Step 6), extend the `run:` line from
`python3 tools/ci_junit_summary.py "reports/junit/<job-key>.xml" "<job-key>" >> "$GITHUB_STEP_SUMMARY"`
to also pass `"/tmp/base-collect.txt"` as a third argument:
`python3 tools/ci_junit_summary.py "reports/junit/<job-key>.xml" "<job-key>" "/tmp/base-collect.txt" >> "$GITHUB_STEP_SUMMARY"`.
This invocation stays unconditional (`if: always()` unchanged) — on a non-PR run, Step 6's steps
never ran, `/tmp/base-collect.txt` never exists, and Step 5's `main()` treats a missing path as
`base_ids = None`, which Step 3's classifier turns into `breakdown = None`, which Step 4's renderer
treats as "omit the breakdown, render only the existing table" — this is the entire non-PR fallback
mechanism; no separate `if:` branch or duplicate summary step is needed for the fallback case.
**Shared-resource / other-writers note:** The `Job summary` step's `run:` line is read by two other
things that must keep working: `tests/static/test_ci_step_summary_reporting.py`'s
`test_all_fastlane_jobs_have_always_run_summary_step` (`:146-163`), which asserts
`"tools/ci_junit_summary.py" in run_text` and `"$GITHUB_STEP_SUMMARY" in run_text` (both still true
after this change — the test doesn't assert argument count) and `if: always()` (unchanged); and
`docs/parity_ledger/infrastructure.yaml`'s `INFRA-379` entry text (Step 9 below), which currently
describes the pre-extension invocation and must be updated in the same session so it doesn't go
stale.
**Do NOT touch:** The `if: always()` condition, the `>> "$GITHUB_STEP_SUMMARY"` redirect, or the
first two arguments' values/order.
**Verify:** Extend `test_all_fastlane_jobs_have_always_run_summary_step`
(`tests/static/test_ci_step_summary_reporting.py:146-163`) with an added assertion that
`"/tmp/base-collect.txt" in run_text` for each of the 9 jobs; existing assertions in that same test
must still pass unmodified.

### Step 8 — Add remaining structural guard tests
**Files:** `tests/static/test_ci_step_summary_reporting.py`
**Change:** Add `test_new_steps_gated_on_pull_request_event_only`,
`test_no_cross_job_aggregate_step_or_job_added`, and extend
`test_no_new_requirements_txt_entry_and_no_new_marketplace_action` (or add a sibling test) per
test_plan.md #9, #10, #11. `test_no_cross_job_aggregate_step_or_job_added` asserts
`set(_jobs().keys())` is exactly the pre-existing job-name set (the 9 fast-lane jobs plus
`changed-files`, `perf-cert-arena`, `migration-lanes`, `typecheck`, `slow` — confirmed as the
complete current set by reading the full workflow file this session) with zero additions, directly
guarding the "no cross-job aggregate" Out-of-Scope bullet structurally.
`test_no_new_requirements_txt_entry_and_no_new_marketplace_action`'s existing `_PRE_EXISTING_USES`
set (`tests/static/test_ci_step_summary_reporting.py:33-37`) does not need to change — Step 6/7 add
no `uses:` line, only `run:` blocks, so the existing assertion already covers this ticket's changes
without modification; confirm this by re-running it, not by editing `_PRE_EXISTING_USES`.
**Do NOT touch:** `_FASTLANE_JOBS`, `_EXPECTED_MIGRATION_LANES_YAML`, `_EXPECTED_SLOW_YAML` module
constants (`tests/static/test_ci_step_summary_reporting.py:21-31,42-92`).
**Verify:** The new tests themselves, run alongside the full existing file
(`pytest tests/static/test_ci_step_summary_reporting.py -v`).

### Step 9 — Update the parity ledger and ticket documentation
**Files:** `docs/parity_ledger/infrastructure.yaml`, `tickets/inprogress/TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT.md`
**Change:** Update `INFRA-379` (`docs/parity_ledger/infrastructure.yaml:11005-11024`, confirmed the
current max `INFRA-` ID by `grep -n "^- id: INFRA-" docs/parity_ledger/infrastructure.yaml | tail -5`
this session, showing `INFRA-379` as the last entry with no concurrent append past it) in place —
extend its `text` field to also describe the new-vs-existing breakdown mechanism, the
`git fetch`+`git worktree add`+`cd &&`-prefixed `pytest --collect-only` base-branch collection, the
`if: github.event_name == 'pull_request'` gating, and the non-PR fallback (missing base-collect
file → no breakdown rendered) — and extend `v2_evidence` to also list the new functions in
`tools/ci_junit_summary.py`. `status` stays `verified`; `test_path` stays
`tests/tools/test_ci_junit_summary.py + tests/static/test_ci_step_summary_reporting.py` (both
already extended by Steps 1-5 and 6-8 respectively, so no new test file needs to be listed). At
Implement time, re-run the `grep` above immediately before editing, per the append-only-ledger
convention documented in the parent ticket's own plan.md and re-affirmed in investigation.md's
Parity Ledger Overlap section — if another concurrent session has appended past `INFRA-379` by
then, this is still the entry to update in place (see Decisions Made by This Plan #4), just
re-verify `INFRA-379` is still the correct, un-superseded ID for this feature before editing. Also
fill the ticket's own `## Implementation Notes` section documenting the
`github.event_name == 'pull_request'` base-ref-detection choice and the non-PR fallback behavior,
per the ticket's own Scope bullet requiring this.
**Do NOT touch:** Any other `INFRA-` entry, or append a new `INFRA-380` entry (see Decisions Made by
This Plan #4).
**Verify:** `pytest tests/tools -k "parity" -v` (schema validity); manual read confirming the
updated `text`/`v2_evidence` fields describe the shipped mechanism accurately.

## Scope Guards
- Do not add a cross-job or repo-wide aggregate new-vs-existing summary, and do not add a new CI
  job — guarded structurally by Step 8's `test_no_cross_job_aggregate_step_or_job_added`.
- Do not introduce a persisted baseline file (committed JSON/YAML of known test IDs) — the base-ID
  set is always recomputed per-run from `pytest --collect-only` against the fetched base branch,
  never read from or written to a repo-tracked file.
- Do not touch the `slow` or `migration-lanes` job blocks — guarded by the existing
  `test_slow_and_migration_lanes_jobs_unchanged_by_this_ticket` test, which must keep passing
  unmodified.
- Do not touch the `typecheck` or `changed-files` jobs.
- Do not alter the existing `-m "not slow and not extra_slow"` marker filter, any job's existing
  pytest path list, the `--junit-xml=` output path convention, or pytest exit-code semantics on the
  existing `Run` step in any of the 9 jobs.
- Do not remove, reformat, or change the values of the existing
  Passed/Failed/Errors/Skipped/Duration table/row — Step 4 is strictly additive to it, verified by
  the existing `test_markdown_table_output_shape` test continuing to pass with its original 2-arg
  call site unmodified.
- Do not add a `fetch-depth: 0` override to the existing 9 jobs' `actions/checkout@v4` steps — the
  base-branch tree is obtained via the new `git fetch --depth=1` + `git worktree add` steps instead
  (see investigation.md's rejection of the `changed-files`-style full-history fetch for cost
  reasons).
- Do not add any new `requirements.txt` entry or any new `uses:` marketplace Action — the entire
  mechanism is stdlib Python plus plain `git`/`pytest` shell invocations.
- Do not append a new `INFRA-380` parity ledger entry — update `INFRA-379` in place (Decisions Made
  by This Plan #4).

## Dependency Map
- Steps 1, 2 are independent of each other (different parsing concerns) and can be implemented in
  either order.
- Step 3 depends on Steps 1 and 2 (consumes `TestCaseRecord` and the base ID set).
- Step 4 depends on Step 3 (consumes `NewExistingBreakdown`).
- Step 5 depends on Steps 1-4 (wires all of them into `main()`).
- Step 6 is independent of Steps 1-5 (pure workflow YAML change) but must land before Step 7, since
  Step 7's added CLI argument only has meaning once Step 6's collection step can produce
  `/tmp/base-collect.txt`.
- Step 7 depends on Step 6 (references the file Step 6 produces) and on Step 5 (the CLI must accept
  the third argument before the workflow passes it).
- Step 8 depends on Step 6 and Step 7 (asserts their shape).
- Step 9 depends on Steps 1-8 being complete (documents the finished mechanism); can be drafted
  early but should be finalized last so the parity ledger text matches what actually shipped.

## Acceptance Criteria Map
| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Each of the 9 jobs' step summary includes the new/existing breakdown (New/Existing total + passed/failed/skipped) for PR runs | Steps 1-7 | `test_render_markdown_table_includes_new_existing_breakdown`, `test_all_fastlane_jobs_have_base_branch_collect_only_step` |
| "New" = present in head JUnit XML, absent from base collect-only listing, no baseline file | Steps 1, 2, 3 | `test_classify_new_vs_existing_splits_by_base_collect_only_ids` |
| "Existing" = present in both | Step 3 | `test_classify_new_vs_existing_splits_by_base_collect_only_ids`, `test_classify_new_vs_existing_all_six_states` |
| Non-PR runs render only the existing single-row summary, no error/broken output | Steps 5, 6, 7 | `test_render_markdown_table_omits_breakdown_when_no_base_data`, `test_new_steps_gated_on_pull_request_event_only` |
| Per-job only, no cross-job aggregate | Step 6 (no new job added), Step 8 | `test_no_cross_job_aggregate_step_or_job_added` |
| Existing Passed/Failed/Errors/Skipped/Duration table byte-for-byte unchanged | Step 4 | `test_markdown_table_output_shape` (existing, unmodified), `test_slow_and_migration_lanes_jobs_unchanged_by_this_ticket` |
| No new `requirements.txt` entry, no new marketplace Action | Steps 6, 7 (shell/git/stdlib only) | `test_no_new_requirements_txt_entry_and_no_new_marketplace_action` |
| Parity ledger reflects the new mechanism with a real `test_path` | Step 9 | `pytest tests/tools -k "parity"` |
| New/extended unit tests cover all six states, non-PR fallback, malformed/missing base listing | Steps 1-5 | `test_classify_new_vs_existing_all_six_states`, `test_classify_malformed_or_missing_base_listing_resolves_to_safe_fallback` |

## Decisions Made by This Plan
1. **Errors are broken out as their own column** in the new/existing breakdown tables (`new_errors`,
   `existing_errors`), not folded into failed. The ticket's AC text lists "passed/failed/skipped" as
   the minimum required columns, but its Assumptions section requires whichever choice is made to
   "stay internally consistent with the existing all-tests row's separate Errors column" and not
   "silently drop error visibility." Breaking errors out separately is a strict superset of the AC's
   minimum and avoids any error-visibility loss, so it is the safer default and is adopted directly
   rather than left open.
2. **Dependency drift between base and head branches is a documented, accepted known limitation, not
   a defect to fix.** The base-branch `--collect-only` pass reuses the head job's already-installed
   `requirements.txt` environment rather than a fresh base-branch install (per investigation.md's
   explicit design choice to avoid a second `pip install` cost). If this causes some base-branch
   tests to fail to collect, the classifier degrades to over-counting tests as "new" rather than
   failing — this is the intended fail-open behavior, not a bug. Documented in Step 9's
   Implementation Notes update; no code change addresses it, since the ticket's own Scope
   explicitly leaves this unmeasured and only asks it be sanity-checked, not fixed.
3. **`git fetch`/`git worktree add` failures fail open by returning early (`exit 0`) from the
   collection step**, leaving `/tmp/base-collect.txt` absent — this reuses the exact same
   "missing file → no breakdown" code path Step 5 already builds for the non-PR case, rather than
   inventing a second fallback mechanism. One fallback path serves both "no base ref available" and
   "base ref available but fetch/collection failed," which is simpler and reduces the number of
   distinct states the renderer needs to handle correctly.
4. **`INFRA-379` is updated in place; no new `INFRA-380` entry is appended.** This ticket is the
   same CI-job-summary mechanism evolving additively (a new breakdown on top of the same
   `--junit-xml`/`Job summary` step pairing), not a new, independently-identifiable capability — the
   parent ticket's own `INFRA-379` entry already describes the exact step/module pairing this ticket
   extends. Appending a new entry would fragment one mechanism's parity record across two IDs for no
   traceability benefit. Re-verify `INFRA-379` is still the current max entry immediately before
   editing at Implement time (see Step 9), since the ledger is append-only and shared across
   concurrent sessions.

## Anti-Drift Notes
- The single most concrete implementation trap (per investigation.md) is a bare
  `pytest --collect-only ...` line anywhere in a fast-lane job's steps being independently
  tokenized by `tools/gate_checks/ci_workflow_test_coverage.py::_extract_pytest_paths`
  (`:91-117`, triggers on any stripped line equal to `"pytest"` or starting with `"pytest "`/
  `"pytest\\"`). Step 6's `run:` text must always begin with `cd /tmp/base-checkout &&`, never a
  bare `pytest` line — this is the direct guard, not just "keep the two path lists identical,"
  which is also required but is not by itself sufficient.
- The base-branch worktree must live under `/tmp`, never under `$GITHUB_WORKSPACE` — a path inside
  the checked-out repo tree risks being picked up by `git status`/`git ls-files` in the same job or
  swept into a later `git`/upload-artifact operation.
- `main()`'s "always returns 0, never raises" guarantee (`tools/ci_junit_summary.py:6-9`,
  `:119-130`) must be preserved end-to-end through Step 5's new wiring — the new classification
  block must sit inside the existing top-level `try/except Exception`, not add a second unguarded
  code path.
- The existing 2-arg call sites (`render_markdown_table(summary, job_name)` and
  `main([xml_path, job_name])`) must keep working unmodified after Steps 4 and 5 — both new
  parameters must be optional with safe (`None`) defaults, never required.
- Do not attempt to fix the dependency-drift edge case (Decision #2) — it is out of this ticket's
  measured scope; only document it.

## Deviations
None. All 9 steps were implemented exactly as specified: `TestCaseRecord`/`parse_testcase_records`
(Step 1), `parse_collect_only_ids`/`_normalize_collect_only_node_id` (Step 2),
`NewExistingBreakdown`/`classify_new_vs_existing` with errors broken out as their own column
(Step 3, per Decision #1), the additive `render_markdown_table` extension verified byte-identical
for the 2-arg call sites (Step 4), the optional 3rd `main()` CLI arg inside the existing
try/except (Step 5), the two new PR-gated steps in all 9 fast-lane jobs using the
`cd /tmp/base-checkout && pytest ...` prefix and per-job path lists (Step 6), the unconditional
3rd argument on each `Job summary` step (Step 7), the new static structural guard tests (Step 8),
and `INFRA-379` updated in place with no new `INFRA-380` entry (Step 9, re-confirmed as the
current max entry immediately before editing). The only implementer judgment calls exercised were
ones the plan explicitly left open: the fail-open mechanism used shell-level `if !`/`exit 0`/
`|| true` guards rather than step-level `continue-on-error: true` (both were plan-compatible; the
shell-level form preserves a `::warning::` annotation with context), and the breakdown is rendered
as a single combined New/Existing table rather than two separate tables (plan Step 4 explicitly
allowed either shape).
