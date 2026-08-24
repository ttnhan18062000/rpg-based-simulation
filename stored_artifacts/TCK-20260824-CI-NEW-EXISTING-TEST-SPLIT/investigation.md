---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT
artifact_type: investigation
tags: [testing]
---

# Investigation — TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT

## Current Behavior

### `tools/ci_junit_summary.py` — aggregate-only, no per-testcase parsing
Read in full (135 lines). `JUnitSummary` (`tools/ci_junit_summary.py:32-40`) is a frozen dataclass
with only aggregate fields: `total, passed, failed, errors, skipped, duration_seconds, parse_ok`.
`parse_junit_xml` (`:77-98`) parses `<testsuites>`/`<testsuite>` root elements and calls
`_summarize_testsuite_elements` (`:56-74`), which sums only the `tests`/`failures`/`errors`/
`skipped`/`time` **attributes on the `<testsuite>` element itself** — it never calls
`suite.findall("testcase")` or reads any `<testcase>` child. Confirmed against the real fixture
shape (`tests/tools/fixtures/ci_junit_summary/all_pass.xml`): each `<testcase classname="tests.unit.core.test_a" name="test_one" time="0.100" />`
child is present in the fixture but is completely unread by the current module. There is currently
no code path anywhere in the repo that extracts a per-test ID (classname+name) from a JUnit XML
file — this ticket's classification logic must add that capability, not merely reuse existing code.
`render_markdown_table` (`:101-116`) and `main` (`:119-134`) are pure functions of a
`JUnitSummary`/job-name pair and are unaffected by adding new functions alongside them, as long as
the existing exported names/behavior stay unchanged (the AC requires the existing table byte-for-
byte unchanged).

### `.github/workflows/test.yml` — 9 fast-lane jobs, plain shallow checkout
Read the full 363-line file. Each of the 9 fast-lane jobs (`unit-core-world` L24-52,
`unit-gameplay` L55-83, `unit-infra` L86-118, `integration` L121-136, `api-tools` L139-159,
`agent-orchestration` L166-192, `simulation-quality` L195-210, `arch-docs` L213-232,
`perf-cert-arena` L270-289) uses a bare `actions/checkout@v4` with **no `fetch-depth:` override**
(`checkout@v4`'s documented default is `fetch-depth: 1` — a single-commit shallow clone of
whatever ref the trigger event resolves to; for a `pull_request` event that ref is the ephemeral
merge commit `refs/pull/<n>/merge`, not the head branch tip). Each job's `pytest` step is named
`Run` (single `run: |` block, back­slash-continued), ending in
`-m "not slow and not extra_slow" --tb=short -q --junit-xml=reports/junit/<job-key>.xml`
(TCK-20260823 additions). Immediately after, a `Job summary` step (`if: always()`) pipes
`python3 tools/ci_junit_summary.py "reports/junit/<job-key>.xml" "<job-key>" >> "$GITHUB_STEP_SUMMARY"`.
No job currently reads any second ref's tree — a plain depth-1 checkout of the merge commit does
**not** bring the base branch's commit object down at all (shallow clones only fetch the
requested tip's history to the requested depth), so `git checkout <base-sha>` would fail today
with "reference is not a tree" until a base-ref object is fetched.

### `changed-files` job (L239-267) — the existing base/head-ref-detection precedent
This job (added by TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS) is the only place in the workflow
that already resolves a base ref:
- `actions/checkout@v4` with `fetch-depth: 0` (L246-247) — full/unshallowed history.
- `if [ "${{ github.event_name }}" != "pull_request" ]; then ... fail open (both outputs true) ...
  exit 0; fi` (L250-254) — the exact base-ref-availability detection this ticket should reuse.
- `BASE="${{ github.event.pull_request.base.sha }}"` / `HEAD="${{ github.event.pull_request.head.sha }}"`
  (L255-256) — uses the PR event payload's resolved SHAs directly, **not** `github.base_ref` (the
  branch name) and **not** the `GITHUB_BASE_REF` env var.
- `git diff --name-only "$BASE...$HEAD"` wrapped in a `2>&1`/`if !` fail-open pattern that emits a
  `::warning::` annotation and defaults both outputs to `true` on any diff failure (L257-262).

This job's `fetch-depth: 0` is a full unshallow of **all** branches/tags (not scoped to one
branch) — it is the "does the checkout already have enough history to reach an arbitrary base
SHA" answer already validated in this exact repo/workflow, but at the cost of a full-history fetch
run once, in one job. Applying the identical `fetch-depth: 0` treatment to all 9 fast-lane jobs
(rather than a narrower single-branch shallow fetch) would multiply that full-history-fetch cost
by 9 in parallel on every PR run — a materially different cost profile than the single
`changed-files` job pays today, and worth flagging even though this ticket doesn't need to decide
against it (see Risks).

### `tools/gate_checks/ci_workflow_test_coverage.py` — the static guard this ticket's new step(s) must not corrupt
Read `parse_job_pytest_paths` (`:54-73`) and `_extract_pytest_paths` (`:91-117`) in full, and
traced how they interact. `parse_job_pytest_paths` accumulates **every line in a job's YAML body,
across all its steps** (not just the step named `Run`) into `job_bodies[job_name]`, then hands the
whole thing to `_extract_pytest_paths`. That function starts a new "pytest statement" whenever a
**stripped line** equals `"pytest"`, or starts with `"pytest "`, or starts with `"pytest\\"`
(`:97`) — this means **any** second `pytest ...`-prefixed line anywhere in a job's steps (not just
the existing `Run` step) is independently tokenized and its `tests/`-prefixed path tokens are
added to that job's covered-path set (`:108-114`). Concretely: if this ticket's new base-branch
collection step is written as a bare `pytest --collect-only tests/unit/core ... ` line (matching
the head invocation's path list), it will be picked up by this tokenizer as a second statement —
harmless in isolation because it contributes the *same* path tokens already contributed by the
head invocation (set union is a no-op), but only if the two path lists are kept byte-identical. If
the base-branch invocation is instead written with a leading shell prefix that does not start with
literal `"pytest"` — e.g. `cd /tmp/base-checkout && pytest --collect-only ...` — the whole
statement is invisible to `_extract_pytest_paths` (the stripped line starts with `"cd "`, matching
none of the three trigger conditions), which is the safer, dependency-free way to guarantee this
ticket introduces zero risk of ever diverging the tokenizer's covered-path set, rather than relying
on "the two path lists happen to stay identical forever." Recommend the latter form at Plan/Implement
time.

### `docs/testing/test_taxonomy.md` — marker conventions referenced, not modified
Confirms `not slow and not extra_slow` is the standard fast-lane marker filter already used
identically by all 9 jobs' `Run` step; the ticket's own text requires the base-branch
`--collect-only` invocation to reuse this same `-m` filter and the same path list so the two test-ID
sets are comparable — confirmed as the correct approach (a base-branch test ID that only exists
under `slow`/`extra_slow` markers should not spuriously appear as "missing from base," since the
head invocation excludes those markers too).

## Mechanics / Engine Constraints
None. This is CI/process tooling — no `docs/mechanics/` chapter or `docs/engine/` contract governs
GitHub Actions workflow configuration or test-result reporting, consistent with the parent
ticket's identical finding. `search_docs`/`graphify` were confirmed unavailable in this worktree
per the task's own instructions; skipped straight to direct file reads/grep as directed.

## Docs Requiring Update
- `docs/parity_ledger/infrastructure.yaml`: extend `INFRA-379` (or append a new sequential
  `INFRA-380`, re-check current max ID immediately before editing — confirmed `INFRA-379` is the
  current max as of this investigation) documenting the new-vs-existing classification mechanism,
  the base-ref-detection condition, and the non-PR fallback.

## Parity Ledger Overlap
`INFRA-379` (`docs/parity_ledger/infrastructure.yaml:11005-11024`, `status: verified`,
`priority: P2`, `test_path: tests/tools/test_ci_junit_summary.py + tests/static/test_ci_step_summary_reporting.py`)
is the direct parent entry this ticket extends — it describes exactly the `--junit-xml` +
`Job summary` mechanism this ticket builds on top of, and its `text` field would become stale
(silently incomplete, not wrong) if this ticket lands without updating it, since the per-job
summary output shape changes from one table to two. No P0 entries exist in this area — `INFRA-379`
is P2, so there is no inherited passing-test_path obligation beyond what this ticket already plans
(extending the same two test files). Confirmed via `grep -n "^- id: INFRA-" docs/parity_ledger/infrastructure.yaml | tail -5`
that `INFRA-379` remains the current max entry (no other concurrent session has appended past it as
of this investigation) — re-check this again at Implement/Parity time per the append-only-ledger
convention documented in the parent ticket's own plan.md.

## Prior Work
- `stored_artifacts/TCK-20260823-CI-STEP-SUMMARY-REPORTING/investigation.md` and `plan.md` — the
  direct parent artifacts. Established: `tools/` (not `tools/gate_checks/`) as the correct module
  location (that package's own test suite enforces a no-CLI/argparse-entry-point convention this
  new logic must also honor if added to the same module); the `reports/junit/` (not `tests/`-
  prefixed) output-path convention to avoid the `_extract_pytest_paths` tokenizer trap (same trap
  now re-confirmed to also apply to any new `--collect-only` step, see Current Behavior); `main()`-
  always-returns-0 as the load-bearing guarantee that keeps a purely observational step from
  becoming a second failure gate — this ticket's new collection/classification step(s) must honor
  the identical guarantee; and the `yaml.safe_load`-based static-test pattern
  (`tests/static/test_ci_step_summary_reporting.py`) this ticket's new/extended static test should
  continue to follow.
- `tickets/done/TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS.md` and the live `changed-files` job it
  added — the base/head-ref-detection and fail-open pattern this ticket is explicitly directed to
  reuse rather than invent a new mechanism (see Current Behavior above for the exact fields/flow
  read directly from the live job).
- No other `stored_artifacts/` entry mentions per-testcase JUnit parsing, `pytest --collect-only`,
  or a new-vs-existing test split — this ticket is the first to address that gap.

## Risks and Open Questions

### Investigation Question 1 — concrete answer: base-branch test-ID collection mechanism
**Recommendation: do not change the existing 9 jobs' `actions/checkout@v4` step at all.** Keep it
exactly as-is (default shallow, depth 1, head/merge-commit only) — this avoids touching the
Scope-protected head-branch checkout and avoids paying `changed-files`' full-history
(`fetch-depth: 0`, all branches/tags) cost 9x in parallel. Instead, add one new step, after
checkout and after `pip install -r requirements.txt` (dependencies must already be importable for
collection to succeed) and before (or interleaved with, order does not matter relative to) the
existing `Run` step:

```yaml
- name: Fetch base branch for collect-only diff
  if: github.event_name == 'pull_request'
  run: |
    git fetch origin "${{ github.base_ref }}" --depth=1
    git worktree add /tmp/base-checkout FETCH_HEAD
- name: Base branch test collection
  if: github.event_name == 'pull_request'
  run: |
    cd /tmp/base-checkout && pytest <same path list as this job's Run step> \
      -m "not slow and not extra_slow" --collect-only -q > /tmp/base-collect.txt
```

Why this shape, verified directly:
- `git fetch origin "${{ github.base_ref }}" --depth=1` fetches only the **target branch's current
  tip**, shallow (one commit) — cheap, and does not depend on GitHub's optional
  `uploadpack.allowReachableSHA1InWant` arbitrary-SHA-fetch capability (which the alternative,
  fetching `github.event.pull_request.base.sha` directly, would rely on). `github.base_ref` is
  populated with exactly the target branch name whenever `github.event_name == 'pull_request'`
  (see Question 2 below) — same condition already gating the whole step, so no extra availability
  check is needed inside the step itself.
- `git worktree add /tmp/base-checkout FETCH_HEAD` materializes that fetched commit into a second
  working tree outside the current job's `$GITHUB_WORKSPACE`, without disturbing the already-
  checked-out head tree the existing `Run` step depends on — `git worktree` does not require an
  unshallow clone; it works against whatever objects are present, and the just-fetched
  `FETCH_HEAD` object is present after the fetch above.
- Reusing the exact same explicit path list and `-m "not slow and not extra_slow"` filter as the
  job's existing `Run` step (per the ticket's own Related Docs note and the taxonomy consistency
  requirement above) is what keeps the two ID sets comparable — a base-branch test excluded by the
  marker filter must not be misclassified as "doesn't exist in base."
- Running the collect-only invocation as `cd /tmp/base-checkout && pytest ...` (not a bare
  `pytest ...` line) is deliberate: it keeps `tools/gate_checks/ci_workflow_test_coverage.py`'s
  `_extract_pytest_paths` tokenizer from ever tokenizing this second statement at all (see Current
  Behavior above) — a stronger, more future-proof guarantee than relying on the two path lists
  staying byte-identical forever.
- `--collect-only -q` (dropping `--tb=short` and `--junit-xml=`, neither of which apply to a
  collection-only run) prints one test node ID per line in the form
  `path/to/test_file.py::[ClassName::]test_name` — pytest's own short-nodeid format. This is the
  cleanest stdlib-parseable shape (one line per test, no tree indentation to strip, unlike bare
  `--collect-only` without `-q`).

**ID-matching sub-problem (also confirmed, per the ticket's own Assumptions flag).** JUnit XML's
`<testcase classname="..." name="...">` attributes (confirmed against the live fixture,
`tests/tools/fixtures/ci_junit_summary/all_pass.xml:5`, e.g.
`classname="tests.unit.core.test_a" name="test_one"`) use a **dotted module path** for `classname`
(directory separators become `.`, `.py` stripped), with any test-class name appended as a further
dot-joined segment when the test is a method on a class. `pytest --collect-only -q`'s node-ID
format uses `::`-separated segments with the file path kept slash-form and `.py` intact. The
cleanest stdlib-only reconciliation is a single normalization function applied to **both** sides
into one canonical `"dotted.module.path::TestClass::test_name"` (or without the class segment for
plain functions) form: for a JUnit `<testcase>`, the ID is already `f"{classname}::{name}"`
directly, no transform needed; for a collect-only node ID, split on `::`, replace `/` with `.` and
strip the trailing `.py` from the first (file-path) segment only, then rejoin all segments with
`::`. This produces directly comparable strings without needing to touch pytest's internal
nodeid-to-classname logic, and needs no new dependency (pure string manipulation, stdlib
`pathlib`/`str` only).

### Investigation Question 2 — concrete answer: non-PR-run fallback detection
Confirmed directly against GitHub Actions' documented context/env-var population rules and this
repo's own existing `changed-files` job precedent (which already encodes the identical check):

| Trigger this workflow uses | `github.event_name` | `github.base_ref` | `GITHUB_BASE_REF` env var |
|---|---|---|---|
| `pull_request` | `"pull_request"` | target branch name (e.g. `"main"`) | same, non-empty |
| `push` to `main` | `"push"` | `""` (empty — only ever populated for `pull_request`/`pull_request_target` events) | `""` (empty) |
| `schedule` | `"schedule"` | `""` | `""` |
| `workflow_dispatch` | `"workflow_dispatch"` | `""` | `""` |

**The clean, already-precedented detection is `github.event_name == 'pull_request'`** — exactly
the condition the existing `changed-files` job already uses (`.github/workflows/test.yml:250`,
`if [ "${{ github.event_name }}" != "pull_request" ]; then ... exit 0; fi`) and exactly what this
ticket's Scope explicitly directs reusing rather than inventing a new mechanism. Checking
`github.base_ref`/`GITHUB_BASE_REF` for non-emptiness would be logically equivalent (both are
populated if and only if `event_name == 'pull_request'`) but is strictly redundant given
`event_name` is already the simpler, single-field, already-precedented check — no reason to add a
second, weaker-looking check. Recommend gating both new steps (fetch+collect, and any
classification/rendering step) with `if: github.event_name == 'pull_request'` at the YAML step
level (not a shell-level `if` inside the script), so a `push`/`schedule`/`workflow_dispatch` run
skips the new steps entirely — no empty/malformed collect-only output file is ever produced or
read, and the existing `Job summary` step (unconditionally `if: always()`) falls back cleanly to
rendering only the pre-existing single-row table when no new/existing breakdown data exists. This
also means `tools/ci_junit_summary.py`'s renderer needs to accept "no base-collection data" as a
valid, first-class input (not a hard requirement — an absent/empty file) and render only the
existing table, mirroring the defensive `parse_ok=False` pattern already established for a missing
JUnit XML.

### Other risks
- **Collection-time dependency drift between base and head branches is unhandled and untested by
  this ticket's own scope**, and should be explicitly noted rather than silently assumed away: if
  `requirements.txt` differs between base and head (e.g. head just bumped a package the base-branch
  test files import in a way incompatible with head's installed version), the base-branch
  `--collect-only` run — executed with head's already-`pip install`-ed environment, not a fresh
  install from the base branch's own `requirements.txt` — could fail to collect some or all base
  tests. This degrades to "more tests look new than actually are" rather than a hard failure (per
  the required fail-open/defensive design), but is worth flagging as a known edge case in
  Implementation Notes rather than leaving it undiscovered.
- **`git worktree add` from within a shallow-but-single-extra-commit-fetched checkout is untested
  in this exact repo** (no existing job does this) — the `changed-files` job's precedent uses
  `fetch-depth: 0` + `git diff`, not `git worktree`. This ticket's recommended mechanism is a new
  combination (fetch-by-branch-name + worktree), not a byte-for-byte reuse of the existing
  precedent's *commands* — only its *detection condition*. This should be called out plainly during
  Plan/Implement, and the fail-open pattern (a `git fetch`/`git worktree add` failure must not fail
  the job) must be added explicitly, matching the `changed-files` job's own `2>&1`/`if !` guard
  style, since neither `git fetch` nor `git worktree add` currently has any such guard anywhere in
  this repo to copy verbatim.
- **Runtime cost of a second `pip install -r requirements.txt` is avoided** by design (the base
  checkout reuses the head job's already-installed environment rather than re-installing inside
  `/tmp/base-checkout`) — this keeps the added cost to one `git fetch --depth=1` (cheap) and one
  `pytest --collect-only` pass (no test execution) per job, consistent with the ticket's own
  Assumptions section expecting collection to be fast relative to execution.

## Anti-Drift Hazards
- **Do not let the new base-branch collect-only step be tokenized by
  `tools/gate_checks/ci_workflow_test_coverage.py`'s `_extract_pytest_paths`.** Prefix the
  `run:` line with `cd /tmp/base-checkout && pytest ...` (not a bare `pytest ...` line) so the
  stripped-line trigger conditions (`== "pytest"` / `startswith("pytest ")` /
  `startswith("pytest\\")`) never match — see Current Behavior for the exact mechanism. This is a
  stronger guarantee than "keep the two path lists identical," which is also required but is not
  by itself sufficient protection against a future accidental divergence.
- **Do not place the base-branch worktree inside the checked-out repo tree** (e.g.
  `./base-checkout` instead of `/tmp/base-checkout`) — `git worktree add` would create a new
  directory that `git ls-files`/`git status` inside the main checkout could pick up, and a path
  under the repo root beginning with something other than `tests/`/`--ignore=` is otherwise
  harmless to the tokenizer, but keeping it fully outside `$GITHUB_WORKSPACE` (under `/tmp`) avoids
  any possibility of it being swept into an `actions/upload-artifact` step or a later `git`
  operation in the same job.
- **Do not use `fetch-depth: 0` on the existing checkout step** as the mechanism for this ticket —
  tempting because it is the `changed-files` job's literal precedent, but it multiplies a
  full-history fetch cost across 9 parallel jobs instead of the cheaper single-branch shallow fetch
  recommended above; reusing `changed-files`' *detection condition* is required, reusing its exact
  *fetch command* is not.
- **Do not gate the new steps on `github.base_ref` truthiness inside a shell `if` when a YAML-level
  `if: github.event_name == 'pull_request'` says the same thing more simply** and matches the
  existing `changed-files` precedent's own field choice — avoid introducing a second, redundant
  detection mechanism that could drift out of sync with the first if either is edited later without
  the other.
- **Do not let `tools/ci_junit_summary.py`'s existing exported functions/behavior change shape** —
  the AC requires the pre-existing Passed/Failed/Errors/Skipped/Duration table byte-for-byte
  unchanged; new classification logic must be additive (new functions / new optional parameters
  with safe defaults), never a rewrite of `parse_junit_xml`'s existing return contract.
