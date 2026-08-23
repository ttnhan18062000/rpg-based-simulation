---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260823-CI-STEP-SUMMARY-REPORTING
artifact_type: plan
tags: [testing, workflows]
---

# Implementation Plan — TCK-20260823-CI-STEP-SUMMARY-REPORTING

## Summary
Add `--junit-xml=reports/junit/<job-key>.xml` to each of the 9 fast-lane pytest jobs in
`.github/workflows/test.yml`, build a small stdlib-only parser/renderer module
(`tools/ci_junit_summary.py`) that turns a JUnit XML file into a markdown pass/fail/skip/error/
duration table, wire a per-job `if: always()` step that pipes that module's stdout into
`$GITHUB_STEP_SUMMARY`, add a static structural test proving all 9 jobs are wired correctly and
the `slow`/`migration-lanes` jobs stay untouched, and record the new mechanism as a `verified`
entry in `docs/parity_ledger/infrastructure.yaml`. The JUnit path lands under `reports/junit/`
(sibling to the existing `reports/certification/` convention used by the `slow` job's artifact
upload), never under `tests/`, because `tools/gate_checks/ci_workflow_test_coverage.py:91-117`
(`_extract_pytest_paths`) collects any pytest-line token starting with `tests/` as a covered test
directory — a `tests/`-prefixed `--junit-xml` value would silently corrupt that guard without
failing anything visibly. The summary script is designed to never raise and always exit 0, so the
new `if: always()` step can never become a second failure gate on top of the pytest step's own
exit code. This is a re-run of a previously paused pipeline; every factual claim below (line
numbers, current parity-ledger max ID, pytest version, absence of `junit_family`) was independently
re-verified against the live repo files immediately before writing this plan, with no discrepancy
found from the prior paused run.

## Steps

### Step 1 — Add `--junit-xml=` to each of the 9 fast-lane jobs' pytest invocation
**Files:** `.github/workflows/test.yml`

**Change:** For each of the 9 jobs — `unit-core-world` (job header `.github/workflows/test.yml:24`,
body through `:48`), `unit-gameplay` (`:51`–`:75`), `unit-infra` (`:78`–`:106`), `integration`
(`:109`–`:120`), `api-tools` (`:123`–`:139`), `agent-orchestration` (`:146`–`:168`),
`simulation-quality` (`:171`–`:182`), `arch-docs` (`:185`–`:200`), `perf-cert-arena` (`:238`–`:253`)
— append one new flag to the existing multi-line `pytest ...` statement's final line, immediately
after `-m "not slow and not extra_slow" --tb=short -q`: `--junit-xml=reports/junit/<job-key>.xml`,
where `<job-key>` is that job's YAML key (e.g. `unit-core-world`, `perf-cert-arena`) — this
guarantees uniqueness per job (job keys are already distinct, confirmed via
`grep -n "^  [a-z-]*:$" .github/workflows/test.yml`) and keeps the path job-discoverable for the
Step 3 summary step. Do not reorder, retype, or reflow any existing path token or the
`-m`/`--tb`/`-q` flags — only append the new flag as the last token on the statement's last
continuation line.

Facts verified by direct read immediately before writing this plan (not inferred):
- All 9 job header line numbers above confirmed via `grep -n "^  [a-z-]*:$|^jobs:"
  .github/workflows/test.yml` against the live file.
- `requirements.txt:37` reads `pytest==9.0.2` — `--junit-xml` is pytest's own built-in reporter
  flag (bundled with pytest itself, not a plugin), so no new dependency is required.
- `pyproject.toml:52` opens `[tool.pytest.ini_options]`; `grep -n "junit_family" pyproject.toml`
  returns zero hits anywhere in the file — no JUnit-schema override exists, so pytest's default
  `xunit2` writer shape applies unmodified to the new flag's output.

**Do NOT touch:** the `slow` job (`.github/workflows/test.yml:288`–`327`) or `migration-lanes` job
(`:256`–`269`) — deferred, see "Decisions Made by This Plan" below. Do NOT touch `typecheck`
(`:272`–`285`) or `changed-files` (`:207`–`235`) — out of scope, neither has a pytest invocation. Do
NOT touch any existing path token, the `-m` filter string, or the `--tb=short -q` flags in the 9
in-scope jobs.

**Verify:** `test_all_fastlane_jobs_have_junit_xml_flag`,
`test_junit_xml_path_is_job_local_and_not_under_tests_dir` (both new, Step 4) — plus re-run
`tests/tools/test_ci_workflow_test_coverage.py` (existing) to prove the new flag is not collected
as a bogus covered directory by `_extract_pytest_paths`. Verified directly against that function's
live logic (`tools/gate_checks/ci_workflow_test_coverage.py:91-117`, re-read in full for this plan):
it drops any token starting with `--ignore=` (L108) and otherwise only collects tokens that equal
`tests`/`tests/` or start with `tests/` (L109-114); `--junit-xml=reports/junit/...` matches neither
condition, so it is silently ignored — identical treatment to the pre-existing `-m`, `--tb=short`,
`-q` tokens.

### Step 2 — Build the JUnit → markdown summary module
**Files:** `tools/ci_junit_summary.py` (new), `tests/tools/test_ci_junit_summary.py` (new),
fixture files under `tests/tools/fixtures/ci_junit_summary/` (new: `all_pass.xml`,
`has_failure.xml`, `has_error.xml`, `has_skip.xml`, `empty.xml`, `malformed.xml`; the missing-file
case is exercised via a nonexistent path, not a fixture file)

**Change:** Create `tools/ci_junit_summary.py` as a standalone, directly-invocable script (stdlib
only — `xml.etree.ElementTree`, `argparse`, `sys` — no new `requirements.txt` entry), placed in
`tools/` (not `tools/gate_checks/`) because it needs a CLI entry point, which `tools/gate_checks/`
modules are established to deliberately not have. Verified directly: `tests/tools/
test_ci_workflow_test_coverage.py:421-429` contains `test_module_has_no_argparse_entry_point`,
which asserts `"argparse" not in source` and `"__main__" not in source` against
`tools/gate_checks/ci_workflow_test_coverage.py`'s own source text — this is a live, currently-
passing architecture guard for that package, and a new argparse/`__main__`-bearing module placed
inside `tools/gate_checks/` would either break that guard's intent or require weakening it, both
out of scope. `tools/ci_junit_summary.py` avoids the conflict entirely by living in `tools/`
alongside other standalone scripts.

Module structure:
- `parse_junit_xml(path: Path) -> JUnitSummary` — a small dataclass/namedtuple
  (`total, passed, failed, errors, skipped, duration_seconds, parse_ok`) parsed from the
  `<testsuite>` (or `<testsuites>` wrapping one or more `<testsuite>`) root's `tests`/`failures`/
  `errors`/`skipped`/`time` attributes — pytest's default `xunit2` writer emits these on the
  `<testsuite>` element (confirmed no `junit_family` override in Step 1's findings, so this is the
  unmodified default shape). `passed` is derived as `total - failed - errors - skipped`, never read
  as its own XML attribute (JUnit XML carries no such attribute). Wrapped in try/except:
  `ET.ParseError`, `FileNotFoundError`, `OSError`, and a defensive `KeyError`/`ValueError` around
  attribute access all resolve to a sentinel `JUnitSummary` with all-zero counts and
  `parse_ok=False` — never raise out of this function.
- `render_markdown_table(summary: JUnitSummary, job_name: str) -> str` — pure function, header row
  plus one data row with Passed/Failed/Errors/Skipped/Duration columns; if `parse_ok=False`, renders
  a single-row "no results / parse failed" table instead of omitting output.
- `main(argv) -> int` — argparse with two positional args (`junit_xml_path`, `job_name`); calls
  `parse_junit_xml` then `render_markdown_table`, prints the markdown to stdout, wrapped in a
  top-level `try/except Exception` that on any unexpected error still prints a minimal fallback
  markdown line and returns `0` — never returns non-zero, by design (see Step 3's note on why the
  exit code must stay independent of parse/test outcome).
- Module-level `if __name__ == "__main__": sys.exit(main(sys.argv[1:]))`.

Add `tests/tools/test_ci_junit_summary.py` covering: all-passing fixture, has-failure fixture,
has-error fixture, has-skip fixture, empty-testsuite fixture (`tests="0"`), a malformed/truncated
XML fixture, and a missing-file path — each asserting correct counts (or the safe zero-count
fallback) and that `main()` always returns `0` regardless of fixture outcome. Also assert the
rendered table's exact column headers and value formatting for at least one fixture.

**Other writers to these files:** none — `tools/ci_junit_summary.py`, its test file, and its
fixtures are all brand-new paths with no other current writer in the repo (confirmed no pre-existing
file at any of these paths). No ordering/race concern applies to this step.

**Do NOT touch:** anything under `tools/gate_checks/` — this module does not belong there, see
above. Do NOT add `pytest-cov`, `pytest-html`, or any other new dependency to `requirements.txt` —
out of scope per AC #3.

**Verify:** all new tests in `tests/tools/test_ci_junit_summary.py`
(`test_parse_junit_xml_all_passing`, `test_parse_junit_xml_with_failure`,
`test_parse_junit_xml_with_error`, `test_parse_junit_xml_with_skip`,
`test_parse_junit_xml_empty_or_missing_produces_safe_fallback`, `test_markdown_table_output_shape`,
`test_parser_exit_code_independent_of_test_outcome`).

### Step 3 — Wire the per-job `if: always()` summary step
**Files:** `.github/workflows/test.yml`

**Change:** For each of the same 9 jobs, add one new step immediately after the existing `Run`
step (the one modified in Step 1):
```yaml
      - name: Job summary
        if: always()
        run: python3 tools/ci_junit_summary.py "reports/junit/<job-key>.xml" "<job-key>" >> "$GITHUB_STEP_SUMMARY"
```
using each job's own `<job-key>`/path from Step 1.

**Other writers to `$GITHUB_STEP_SUMMARY` in this workflow file:** confirmed via
`grep -rn "GITHUB_STEP_SUMMARY" .github/` returning zero hits before this change — no other step in
`test.yml` (or any other workflow file) currently writes to it, so there is no existing writer to
coordinate ordering or append-collision with. `$GITHUB_STEP_SUMMARY` is a per-job-run, GitHub-
Actions-provided file path; because each of the 9 jobs runs on its own isolated `ubuntu-latest`
runner, there is no cross-job race on it either — it is scoped per job, not shared repo-wide.
Because `main()` (Step 2) always returns 0, this step can never itself flip the job's
Actions-reported conclusion — the pre-existing `pytest` step (Step 1) remains the sole source of
pass/fail for the job, satisfying AC #5.

**Do NOT touch:** the `slow` job's existing `if: always()` `actions/upload-artifact@v4` step
(`.github/workflows/test.yml:320`–`326`) — different job, different mechanism (artifact upload, not
step-summary), out of scope and must stay byte-identical. Do NOT add a `uses:` marketplace Action
anywhere — the new step is a plain `run:` shell invocation of a repo-owned script only.

**Verify:** `test_all_fastlane_jobs_have_always_run_summary_step`,
`test_no_new_requirements_txt_entry_and_no_new_marketplace_action` (both new, Step 4).

### Step 4 — Static structural guard test for the workflow wiring
**Files:** `tests/static/test_ci_step_summary_reporting.py` (new)

**Change:** Following the established `yaml.safe_load` + dict/text-assertion pattern already used
by `tests/static/test_ci_narrow_path_filtered_jobs.py` (confirmed by direct read: that file imports
`yaml` and `re` at L1-4 and defines a `_workflow()` helper at L60 that loads the real
`.github/workflows/test.yml`) — parse `.github/workflows/test.yml` once per test module via
`yaml.safe_load`, then assert, for each of the 9 named fast-lane jobs:
(a) the job's pytest-invoking step's `run:` text contains `--junit-xml=`
(`test_all_fastlane_jobs_have_junit_xml_flag`);
(b) that path value does not start with `tests/` and is unique across all 9 jobs
(`test_junit_xml_path_is_job_local_and_not_under_tests_dir`);
(c) the job has a step *after* the pytest step with `if: always()` whose `run:` text invokes
`tools/ci_junit_summary.py` (`test_all_fastlane_jobs_have_always_run_summary_step`);
(d) `requirements.txt`'s tracked content is unchanged by this ticket (compare against a pre-ticket
snapshot, e.g. `git show HEAD:requirements.txt` from the commit that started this ticket's work)
and no `uses:` value appears anywhere in `test.yml` beyond the pre-existing set
(`actions/checkout@v4`, `actions/setup-python@v5`, `actions/upload-artifact@v4`)
(`test_no_new_requirements_txt_entry_and_no_new_marketplace_action`);
(e) the `slow` job's and `migration-lanes` job's full step lists, `if:`, and `needs:` are
byte-identical to the pre-ticket text captured by this plan's Step 1 reads
(`test_slow_and_migration_lanes_jobs_unchanged_by_this_ticket`).

**Other writers to this file:** none — brand-new path, no other current writer.

**Do NOT touch:** any existing test file. This step only adds a new file.

**Verify:** the file's own new tests (self-verifying), plus a full re-run of the regression surface
from `test_plan.md` (`tests/tools/test_ci_workflow_test_coverage.py`,
`tests/static/test_ci_narrow_path_filtered_jobs.py`,
`tests/static/test_corpus_diversity_ci_isolation.py`,
`tests/static/test_ci_requirements_no_ml_stack.py`) to prove no existing assertion broke.

### Step 5 — Parity ledger entry
**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Append one new entry after the current last entry. Confirmed current max ID via direct
`grep -n "^- id: INFRA-" docs/parity_ledger/infrastructure.yaml | tail -1` re-run immediately before
writing this plan → `INFRA-378` at line 10975 — the new entry is `INFRA-379`.
**Re-run that same grep again immediately before editing at Implement time** (not just trust this
plan's snapshot) — `infrastructure.yaml` is an append-only ledger that other concurrently-running
sessions in this repo's worktree-per-ticket workflow may also be appending to; a stale ID risks
collision with another session's freshly-added entry.

Follow the exact field shape of the `INFRA-227` precedent — confirmed by direct read at
`docs/parity_ledger/infrastructure.yaml:2818`: fields are `id`, `text`, `status`, `priority`,
`legacy_evidence`, `v2_evidence`, `proof_type`, `test_path`, `divergence_note`, `support_boundary`.
New entry: `status: verified`, `priority: P2` (matching INFRA-227's priority for the same class of
CI-observability addition to this same workflow file), `v2_evidence` citing
`.github/workflows/test.yml`'s 9 fast-lane jobs' `--junit-xml`/summary steps plus
`tools/ci_junit_summary.py`, and — unlike INFRA-227 (which has `test_path: null`) — a real,
non-null `test_path: tests/tools/test_ci_junit_summary.py`. This is required, not optional:
confirmed by direct read of `docs/parity_ledger/schema.json:44-54`, whose `allOf` branch for
`status` in `["verified", "divergent"]` sets `"required": ["v2_evidence", "test_path"]` with both
typed `"string"` (not nullable) — a `verified` entry with a null `test_path` fails this schema. This
is the concrete reason Step 2 builds a real, unit-tested module rather than inline-only workflow
shell.

**Other writers to this file:** `infrastructure.yaml` is append-only in current practice — every
other ticket that adds an infrastructure-layer parity entry appends its own new `- id: INFRA-NNN`
block at the end rather than editing an existing block in place (confirmed by the file's structure:
sequential ascending-ID blocks with no cross-references). This step's only interaction risk with
other concurrent writers is an ID collision from stale sequencing, mitigated by the re-check
instruction above, not by any content-level conflict — no existing entry is modified.

**Do NOT touch:** any existing `INFRA-*` entry's `status`, `v2_evidence`, or `test_path` — this is a
pure append. No existing entry describes CI test-result reporting, JUnit XML, or
`$GITHUB_STEP_SUMMARY` (confirmed zero grep hits for `junit|step_summary` in this file prior to this
change).

**Verify:** the parity-ledger schema/structure test(s) under `tests/tools` that validate
`infrastructure.yaml` against `schema.json` (exact file/test name to be confirmed at Implement time
by grepping `tests/tools` for `parity` — `test_plan.md` flags this as illustrative, not a
pre-verified exact path); at minimum, `python3 -c "import yaml; yaml.safe_load(open('docs/
parity_ledger/infrastructure.yaml'))"` must succeed (valid YAML) and the new entry must satisfy
`schema.json`'s `required` fields for `status: verified` as read above.

### Step 6 — Record the slow/migration-lanes deferral decision in the ticket
**Files:** `tickets/inprogress/TCK-20260823-CI-STEP-SUMMARY-REPORTING.md`

**Change:** Fill in `## Implementation Notes` with the deferral decision made explicitly by this
plan (see "Decisions Made by This Plan" below) — do not leave the ticket's Scope-bullet-5 open
question unresolved in the ticket body. This is a ticket-file edit, not a code change; sequence it
after Steps 1-5 land so Implementation Notes can also list the actual files changed.

**Other writers to this file:** none besides this ticket's own workflow phases (Investigate/Test-Plan
already filled their own sections; no other ticket edits this file, since it is this ticket's own
inprogress file).

**Do NOT touch:** `## Acceptance Criteria` or `## Scope`/`## Out of Scope` — those are fixed by the
ticket as scoped; Implementation Notes documents the decision within that existing scope, it does
not renegotiate scope.

**Verify:** no automated test; verified by human/done-checker review that Implementation Notes is
non-empty and states the deferral rationale (Definition-of-Done's "no important decision is
undocumented" clause, not a pytest-verifiable AC).

## Decisions Made by This Plan

1. **`slow` and `migration-lanes` jobs are deferred to a future ticket, not included here.**
   Rationale: `migration-lanes` (`.github/workflows/test.yml:256`–`269`) has no direct `pytest`
   invocation at all — both its steps (`make lane-all-fast`, `make gate-expansion`) run pytest
   nested inside `Makefile` targets (confirmed by direct read: the job's only two `run:` lines are
   bare `make` invocations), so adding `--junit-xml` there would first require modifying those
   `Makefile` targets to accept and pass through a JUnit-XML flag — a materially larger and
   differently-shaped change than appending one flag to an existing top-level `pytest` line. The
   `slow` job (`.github/workflows/test.yml:288`–`327`) has three pytest/make-driven steps of three
   different shapes (`make simq-corpus-diversity-slow-isolated`; a bare `pytest tests/ -m "slow or
   extra_slow" ...` step; `make lane-legacy-regression`), none matching the 9 fast-lane jobs'
   single-`pytest`-line shape either — extending identical treatment to it would require a
   per-step design decision this ticket's Scope did not size. Both jobs are explicitly named in the
   ticket's own Scope bullet 5 / Out of Scope bullet 5 as requiring an explicit, documented decision
   rather than a silent default — this is that decision, made now rather than left open, per the
   ticket's own stated fallback ("if deferred, note it explicitly... rather than silently leaving
   them out").
2. **The summary-writing step is defensive by construction inside the script, not via a
   workflow-level escape hatch.** `tools/ci_junit_summary.py`'s `main()` (Step 2) never returns
   non-zero and never lets an exception propagate — on missing file, malformed XML, or zero
   collected tests, it prints a best-effort fallback markdown row and returns `0`. This is done
   inside the script itself (not via `continue-on-error: true` on the workflow step) so the
   guarantee remains independently unit-testable
   (`test_parser_exit_code_independent_of_test_outcome`), leaving GitHub's own
   `$GITHUB_STEP_SUMMARY` redirection mechanism (outside the script's control) as the only
   remaining failure mode — an existing GitHub Actions primitive this ticket does not change.

## Scope Guards
- Do not modify the `-m "not slow and not extra_slow"` marker filter or any existing path token in
  any of the 9 fast-lane jobs, beyond appending the single new `--junit-xml=` flag (Step 1).
- Do not modify the `slow` job or `migration-lanes` job in any way (see Decision 1 above) — guarded
  by `test_slow_and_migration_lanes_jobs_unchanged_by_this_ticket` (Step 4) and the existing
  `tests/static/test_ci_narrow_path_filtered_jobs.py` assertions on those jobs' `if:`/`needs:`.
- Do not modify `typecheck` or `changed-files` — no pytest invocation, explicitly out of scope.
- Do not add any new entry to `requirements.txt` — `--junit-xml` is pytest's existing built-in flag,
  no new package needed.
- Do not add a `uses:` marketplace Action (e.g. `dorny/test-reporter`,
  `EnricoMi/publish-unit-test-result-action`) anywhere in `test.yml`.
- Do not place `tools/ci_junit_summary.py` under `tools/gate_checks/` — that package's own test
  suite (`tests/tools/test_ci_workflow_test_coverage.py::test_module_has_no_argparse_entry_point`)
  enforces a no-CLI-entry-point convention this module must not follow.
- Do not place the JUnit XML output path under `tests/` — would silently corrupt
  `tools/gate_checks/ci_workflow_test_coverage.py`'s `_extract_pytest_paths` static guard.
- Do not add `--cov`/`pytest-cov` or any coverage-percentage collection — out of scope per the
  ticket's Out of Scope section.
- Do not implement cross-run trend tracking or any external dashboard/service call.
- Do not edit any existing `INFRA-*` entry in `docs/parity_ledger/infrastructure.yaml` — append
  only.

## Dependency Map
- Step 1 (add `--junit-xml` flags) has no dependency on other steps; can start immediately.
- Step 2 (build parser module + its own unit tests) has no dependency on Step 1 — it operates on
  standalone XML fixture files, not on the real workflow file — and can be built in parallel with
  Step 1.
- Step 3 (wire the summary step into `test.yml`) depends on both Step 1 (needs the `--junit-xml`
  path convention already established, to reference the same `reports/junit/<job-key>.xml` path)
  and Step 2 (the step's `run:` line invokes `tools/ci_junit_summary.py`, which must exist).
- Step 4 (static structural guard test) depends on Steps 1 and 3 being complete — it asserts on the
  final `test.yml` text.
- Step 5 (parity ledger entry) depends on Steps 1-4 being complete — its `v2_evidence`/`test_path`
  cite the finished workflow steps and the finished test file.
- Step 6 (ticket Implementation Notes) depends on Steps 1-5 — documents what was actually built and
  the deferral decision, sequenced last.

## Acceptance Criteria Map
| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Each of the 9 fast-lane jobs' pytest invocation includes `--junit-xml=<path>` | Step 1 | `test_all_fastlane_jobs_have_junit_xml_flag` |
| Each of those 9 jobs has a subsequent `if: always()` step that reads the JUnit XML and appends a markdown table to `$GITHUB_STEP_SUMMARY` | Steps 2, 3 | `test_all_fastlane_jobs_have_always_run_summary_step`; `tests/tools/test_ci_junit_summary.py` (parser + renderer tests) |
| No new `requirements.txt` entry, no new `uses:` Action | Steps 1-3 (by construction: stdlib-only script, plain `run:` step) | `test_no_new_requirements_txt_entry_and_no_new_marketplace_action` |
| A passing run produces a job summary with correct counts (verified via unit-testing the parser against a sample JUnit XML fixture, per test_plan.md's committed verification path) | Step 2 | `test_parse_junit_xml_all_passing`, `test_markdown_table_output_shape` |
| A failing run still produces a job summary (`if: always()`) and the job still reports failed status — exit-code semantics unchanged | Steps 2, 3 | `test_parse_junit_xml_with_failure`, `test_parse_junit_xml_with_error`, `test_parser_exit_code_independent_of_test_outcome` |
| Existing `-m` filters and path lists byte-identical aside from the added flag | Step 1 (additive-only edit) | `tests/tools/test_ci_workflow_test_coverage.py` (regression), `test_junit_xml_path_is_job_local_and_not_under_tests_dir` |

## Anti-Drift Notes
- The single most concrete implementation trap in this ticket: a `--junit-xml=` path starting with
  `tests/` would silently corrupt `tools/gate_checks/ci_workflow_test_coverage.py`'s
  `_extract_pytest_paths` tokenizer (`tools/gate_checks/ci_workflow_test_coverage.py:108-114`),
  which treats any token starting with `tests/` as a covered test directory. Step 1 uses
  `reports/junit/<job-key>.xml` specifically to avoid this; Step 4's
  `test_junit_xml_path_is_job_local_and_not_under_tests_dir` closes the gap with an explicit
  assertion rather than relying on convention alone.
- The new summary step must never become a second failure gate. `main()` in
  `tools/ci_junit_summary.py` (Step 2) must return 0 unconditionally — verified directly by
  `test_parser_exit_code_independent_of_test_outcome`, and structurally by the fact that the
  workflow step itself (Step 3) has no `continue-on-error:` — the guarantee lives in the script, not
  a workflow-level escape hatch, so it is enforceable by a plain unit test.
- `tools/ci_junit_summary.py` belongs in `tools/`, not `tools/gate_checks/` — the latter package's
  own test suite (`tests/tools/test_ci_workflow_test_coverage.py::test_module_has_no_argparse_entry_point`,
  confirmed at L426-429) enforces a no-CLI convention this new module must violate by design (it
  needs to be `python3`-invocable from a workflow `run:` line).
- `slow` and `migration-lanes` are deliberately out of this ticket (Decision 1 above) — any
  temptation to "just also add it to `slow` since it's right there" must be resisted; that job's
  three differently-shaped steps were not sized by this ticket's Scope.
- Do not introduce a third-party `uses:` Action even though several exist for this exact use case
  (`dorny/test-reporter`, `EnricoMi/publish-unit-test-result-action`) — AC #3 and Scope are explicit
  that only plain shell/Python writing to `$GITHUB_STEP_SUMMARY` is acceptable.
- Before editing `docs/parity_ledger/infrastructure.yaml` at Implement time, re-run
  `grep -n "^- id: INFRA-" docs/parity_ledger/infrastructure.yaml | tail -1` fresh — do not trust
  `INFRA-378` as fixed; another concurrent worktree session may have appended a newer entry since
  this plan was written.

## Deviations

- **Step 5 (parity ledger entry) was NOT performed during Implement.** The implementer's own
  dispatch instructions for this run explicitly said "Do NOT touch
  `docs/parity_ledger/infrastructure.yaml` — that is the Parity phase's job, not Implement's,"
  which supersedes this plan's Step 5 sequencing (this plan had sequenced the ledger entry inside
  Implement, before Step 6). No code or behavior is affected by this — the `INFRA-379` entry (or
  whatever ID is current at that point) is deferred to the pipeline's dedicated Parity phase,
  which owns `docs/parity_ledger/` updates. All of Steps 1-4 and Step 6 were completed as planned.
- **Step 2's test-name grouping was split for clarity, coverage unchanged.** The plan's summary
  line names one combined test,
  `test_parse_junit_xml_empty_or_missing_produces_safe_fallback`, covering the empty-testsuite,
  malformed, and missing-file cases together. The implementation splits this into three separate
  tests — `test_parse_junit_xml_empty_testsuite_produces_correct_zero_counts` (asserts a
  genuinely empty `tests="0"` suite parses successfully with `parse_ok=True` and all-zero counts,
  since it is valid XML, not a parse failure), `test_parse_junit_xml_malformed_produces_safe_fallback`,
  and `test_parse_junit_xml_missing_file_produces_safe_fallback` (both asserting the
  `parse_ok=False` sentinel) — plus one bonus test,
  `test_markdown_table_output_shape_for_parse_failure`, not named in the plan. All fixture files
  and outcome shapes named in the plan (`all_pass.xml`, `has_failure.xml`, `has_error.xml`,
  `has_skip.xml`, `empty.xml`, `malformed.xml`, missing-file) are present and covered; this is a
  test-granularity choice, not a scope change.
