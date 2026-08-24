---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260823-CI-STEP-SUMMARY-REPORTING
artifact_type: investigation
tags: [testing, workflows]
---

# Investigation — TCK-20260823-CI-STEP-SUMMARY-REPORTING

## Current Behavior

### `.github/workflows/test.yml` — the 9 in-scope fast-lane jobs
Read the full 327-line file directly. Each of the 9 named jobs —
`unit-core-world` (L24-48), `unit-gameplay` (L51-75), `unit-infra` (L78-106),
`integration` (L109-120), `api-tools` (L123-139), `agent-orchestration` (L146-168),
`simulation-quality` (L171-182), `arch-docs` (L185-200), `perf-cert-arena` (L238-253) —
shares an identical step shape: `actions/checkout@v4` → `actions/setup-python@v5` →
`pip install -r requirements.txt` → one step named `Run` whose `run: |` block is a single
`pytest <explicit path list> -m "not slow and not extra_slow" --tb=short -q` invocation
(multi-line via trailing `\` continuation). There is exactly one `pytest` invocation per job,
always the last step. Nothing in the file writes to `$GITHUB_STEP_SUMMARY` today (confirmed —
zero matches for `GITHUB_STEP_SUMMARY` anywhere under `.github/`), no `--junit-xml` or other
report flag is present, and no coverage flag (`--cov`) appears on any of these 9 invocations.
`-q` suppresses per-test names, so the only visibility into a run's outcome is the final
pass/fail/error summary line in the raw `-q` log — not surfaced anywhere structured.

### `slow` job (L288-327) and `migration-lanes` job (L256-269) — both out of scope
`slow` has three pytest/make-driven steps of three different shapes: `make
simq-corpus-diversity-slow-isolated`, a bare multi-line `pytest tests/ -m "slow or
extra_slow" --resource-budget large --tb=short -q --ignore=tests/unit/worldassembly/test_corpus_diversity.py`
step, and `make lane-legacy-regression`, plus an existing `if: always()`
`actions/upload-artifact@v4` step (L320-326) uploading `reports/certification/` with 30-day
retention. `migration-lanes` runs two `make`-driven steps only (`make lane-all-fast`, `make
gate-expansion`, L266-269) — no direct `pytest ...` line is visible in the workflow text at
all; any test results are nested inside those Makefile targets. Neither job matches the 9
fast-lane jobs' single-`pytest`-line shape, and the ticket's own Scope (bullet 5) / Out of
Scope (bullet 5) already flag this as requiring an explicit, documented decision rather than a
silent default.

### No prior JUnit XML / step-summary / coverage mechanism exists anywhere in the repo
Grepped `.github/`, `Makefile`, `tools/`, `pyproject.toml` for `junit`, `GITHUB_STEP_SUMMARY`,
`GITHUB_OUTPUT` — zero hits for the first two outside this ticket's own staging artifacts;
`GITHUB_OUTPUT` is used only by the pre-existing `changed-files` job's path-filter output
variables (L219-235), an unrelated mechanism. `requirements.txt:37` pins `pytest==9.0.2`;
`--junit-xml` is pytest's own built-in flag (bundled with pytest itself, not a plugin), so no
new dependency is required — confirms the ticket's stated assumption. `pyproject.toml`'s
`[tool.pytest.ini_options]` block (L52-88, read in full) sets `pythonpath`, `norecursedirs`,
and the project's custom marker registry (`slow`, `extra_slow`, `architecture`, etc.) but has
no `junit_family` or other JUnit-related key — pytest's default `xunit2` JUnit schema applies
unmodified if `--junit-xml` is added.

### The static guard this ticket must stay compatible with: `tools/gate_checks/ci_workflow_test_coverage.py`
Read the full 305-line module directly and confirmed the exact tokenization behavior of
`_extract_pytest_paths()` (L91-117) myself, first-hand:
- It scans a job's body line-by-line. A statement starts when a stripped line equals
  `"pytest"`, or starts with `"pytest "`, or starts with `"pytest\\"`.
- Once started, it accumulates words across `\`-continued lines (stripping the trailing `\`)
  until a line that does not end in `\`.
- It then drops every token that starts with `--ignore=` (L108).
- For every remaining token (after stripping surrounding quotes), it adds the token to the
  covered-paths set **only if** the token is exactly `"tests"` or `"tests/"`, or the token
  **starts with** `"tests/"` (L109-114, `elif token.startswith("tests/")`).
- Any token that doesn't match those conditions (e.g. `-m`, `"not slow and not extra_slow"`,
  `--tb=short`, `-q`) is silently dropped — not collected, not flagged, no error.

Consequence verified directly against this exact logic: appending
`--junit-xml=reports/junit/<job>.xml` to a job's `pytest` statement is safe — the token starts
with `--junit-xml=`, not `tests/`, so it is simply ignored by the tokenizer, identical
treatment to the pre-existing `-m`/`--tb`/`-q` tokens. The one concrete way to break this
guard would be choosing a JUnit output path that itself starts with `tests/` (e.g.
`tests/junit-results.xml`) — that token would be silently added to `fastlane_paths` as a bogus
"covered directory," which could mask a real orphaned-test-directory regression without ever
failing anything today. `--ignore=` tokens are also explicitly excluded from collection
(L108), confirming that mechanism is unrelated to this ticket's new flag either way.

`check_ci_workflow_test_coverage()` (the aggregator, L228-304) walks every real `test_*.py`-
containing directory (via `git ls-files`) and requires each to be covered by a fast-lane job's
path set, individually file-listed, or fully `slow`/`extra_slow`-marked. Adding a new
`--junit-xml=` flag and a new summary step do not touch any existing path token, so this
aggregator's PASS/FAIL results for existing directories are unaffected by this ticket as
scoped — confirmed by re-reading `tests/tools/test_ci_workflow_test_coverage.py` (the module's
own test suite), whose assertions (`test_parses_real_workflow_fastlane_job_paths`,
`test_ignore_flag_token_is_not_collected_as_a_covered_path`,
`test_non_pytest_jobs_contribute_no_paths`) exercise exactly the tokenizer behavior described
above against the real, live `test.yml` file.

### Existing structural-test precedent for this workflow file
`tests/static/test_ci_narrow_path_filtered_jobs.py` and
`tests/static/test_corpus_diversity_ci_isolation.py` both `yaml.safe_load()` the real
`.github/workflows/test.yml` and assert on the parsed `jobs[...]` dict — `if:` conditions,
`needs:` lists, and specific `run:` step text substrings. No `act`, no live GitHub Actions
execution anywhere in the existing suite. This is the established, in-repo pattern this
ticket's own new static test file should extend, and matches AC #4's third verification path
("unit-testing the parser step's logic against a sample JUnit XML fixture") as the only path
actually exercisable in this sandbox — there is no `act` binary available and no live-runner
mechanism in this environment.

## Mechanics / Engine Constraints
None. This is CI/process tooling — no `docs/mechanics/` chapter and no `docs/engine/` contract
governs GitHub Actions workflow configuration or test-result reporting. `search_docs` (MCP)
returned `{"error": "index not found"}` in this worktree; the documented fallback
(`python3 tools/knowledge_search.py query ...`) failed on a `sentence-transformers`
offline-model-download error (expected — no network access, matches this project's known
environment gaps); `graphify query` failed with `graph file not found` in this worktree
checkout (no `graphify-out/graph.json` here). Per the task's fallback instructions, read the
main checkout's `graphify-out/GRAPH_REPORT.md` instead and grepped it for
`ci_workflow|test\.yml|junit|step_summary|gate_checks`, which surfaced exactly the
`check_ci_workflow_test_coverage()` / `_extract_pytest_paths()` community — the same module
read directly above — and no mechanics/engine-layer nodes. This is consistent with the
ticket's own "Related Docs" conclusion.

## Docs Requiring Update
- `docs/parity_ledger/infrastructure.yaml`: add a new `INFRA-379` entry (current max is
  `INFRA-378`, confirmed via `grep -oE "id: INFRA-[0-9]+" docs/parity_ledger/infrastructure.yaml
  | sort -t- -k2 -n | tail -1` — re-check immediately before editing, since this is an
  append-only ledger other concurrent sessions may also be appending to) documenting the new
  `--junit-xml` + `$GITHUB_STEP_SUMMARY` reporting mechanism on the 9 fast-lane jobs. Follow the
  `INFRA-227` precedent (`docs/parity_ledger/infrastructure.yaml:2818-2827`, `status: verified`,
  `priority: P2`, for the structurally similar `actions/upload-artifact` addition from
  `TCK-20260627-P2M-CI-ARTIFACTS`) — but unlike `INFRA-227` (which has `test_path: null`), this
  entry needs a real, non-null `test_path`: `docs/parity_ledger/schema.json` requires both
  `v2_evidence` and `test_path` as non-null strings whenever `status` is `verified` (confirmed
  by reading `schema.json` L47-54, `"required": ["v2_evidence", "test_path"]` under the
  `verified`/`divergent` branch) — this is itself a concrete reason the JUnit-parsing logic
  needs a real, unit-tested module rather than inline-only workflow shell.

## Parity Ledger Overlap
No existing entry in `docs/parity_ledger/infrastructure.yaml` covers CI test-result reporting,
JUnit XML, or `$GITHUB_STEP_SUMMARY` (grepped the file for `junit|step_summary|reporting|
ci_workflow` — the only reporting-adjacent hits are unrelated: content-adapter-heuristic
reporting tests, `src/observability/reporting/*` module citations, and `INFRA-227`'s CI
artifact-upload entry). `INFRA-227` (`status: verified`, `priority: P2`, `test_path: null`) is
the nearest sibling — same subsystem (CI-observability additions to this same workflow file),
different mechanism (artifact upload vs. step-summary reporting), no direct overlap. No P0
entries exist in this scope, so there is no inherited passing-test_path obligation on an
existing entry — this ticket creates a brand-new entry rather than updating one.

## Prior Work
- `tickets/done/TCK-20260627-P2M-CI-ARTIFACTS.md` (hotfix tier, no staging artifacts) —
  established the precedent for an additive, `if: always()`, non-blocking CI-observability step
  on this exact workflow file; produced `INFRA-227`. Directly informs this ticket's parity-ledger
  entry shape and the "additive, never fails the job" design constraint.
- `stored_artifacts/TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS/` — most recent standard-tier
  ticket to touch `test.yml`; its investigation/test_plan confirm the `yaml.safe_load`-based
  structural testing pattern, and its own `tests/static/test_ci_narrow_path_filtered_jobs.py` is
  the closest existing template for a new static test file covering this ticket's wiring.
- `TCK-20260817-CI-FAST-LANE-EXTRA-SLOW-FILTER-INCONSISTENCY` (done) — touched the same 9-job
  set for marker-filter consistency, not reporting; confirms the 9-job enumeration is current
  and stable.
- `stored_artifacts/TCK-20260818-STANDARD-SLOW-REGRESSION-OFF-PR-PATH/` — restructured the
  `slow` job's trigger conditions; relevant background for the deferral decision on `slow`/
  `migration-lanes`, does not itself touch reporting.
- `TCK-20260819-HOTFIX-CI-TEST-DIR-COVERAGE-CHECK` — built
  `tools/gate_checks/ci_workflow_test_coverage.py`, the static parser this ticket's
  `--junit-xml` addition must remain compatible with (see Current Behavior above). No dedicated
  `stored_artifacts/` folder found for it; its `tools/`/`tests/` output was read directly and in
  full instead.
- No `stored_artifacts/` entry anywhere mentions `$GITHUB_STEP_SUMMARY`, JUnit XML, or CI
  test-result reporting specifically — this ticket is the first to address that gap, consistent
  with the ticket's own "Related Stored Artifacts" section.
- A `staging_artifacts/TCK-20260823-CI-STEP-SUMMARY-REPORTING/plan.md` already exists in this
  worktree from a prior, paused pipeline run (this ticket is a resume). Its Steps 1-6, Decisions,
  Scope Guards, and Anti-Drift Notes are consistent with every fact independently re-verified in
  this investigation (the tokenizer behavior, the `reports/junit/` path choice, the schema's
  `test_path` requirement, the `slow`/`migration-lanes` deferral, and the current `INFRA-378`
  max ID) — no discrepancy found between this fresh pass and that plan's factual claims.

## Risks and Open Questions
- **`slow`/`migration-lanes` deferral is a real open decision, not blocking implementation of
  this ticket's core scope.** `migration-lanes` has no visible `pytest` line at all (results
  nested inside `make lane-all-fast` / `make gate-expansion`), so the same `--junit-xml`-based
  mechanism can't be applied without first modifying those Makefile targets — a materially
  larger, differently-shaped change. `slow`'s three steps are three different shapes
  (`make ...`, a bare `pytest tests/ ...` line, another `make ...`), none matching the 9
  fast-lane jobs' single-line shape either. Recommend deferring both to a follow-up ticket and
  recording that explicitly in `## Implementation Notes` (ticket body) rather than silently
  omitting them — the ticket's own Scope/Out of Scope bullets already require this to be a
  stated decision.
- **Report-path collision risk with `ci_workflow_test_coverage.py`'s tokenizer** (see Current
  Behavior) — the implementer must pick a `--junit-xml=` path that does not start with
  `tests/`. `reports/junit/<job-key>.xml` (mirroring the existing `reports/certification/`
  convention from the `slow` job's artifact-upload step) is the safe, precedented choice.
  Nothing currently asserts the *value* is not `tests/`-prefixed, so this ticket's new test
  suite must add that assertion explicitly rather than relying on convention.
- **The new summary step must never become a second failure gate.** Since it must run under
  `if: always()` (so it also fires on a failing job), the parsing/rendering logic must be
  defensive against a missing/malformed/truncated XML file (e.g. the job crashed before pytest
  finished writing output) and must never itself exit non-zero — otherwise a purely
  observational feature would silently start flipping job conclusions, violating the ticket's
  explicit "exit-code semantics are unchanged" requirement (AC #5, Scope bullet 4).
- **No `act` or live-runner verification is available in this sandbox.** AC #4 offers three
  alternative verification paths; only the third ("unit-testing the parser step's logic against
  a sample JUnit XML fixture") is actually exercisable here. This should be committed to
  explicitly at Plan/Implement time rather than left as an ambiguous "or a real run" fallback
  nobody will execute.
- **Whether "GitHub's native mechanism" excludes even first-party-adjacent marketplace
  Actions** (e.g. `dorny/test-reporter`) is flagged by the ticket's own Assumptions section as
  something that would invalidate scope if the requester actually intended to allow one — this
  investigation does not re-decide it; AC #3 and Scope bullet 3 already read as unambiguous
  ("no new `uses:` Action beyond what's already in the workflow"), so it is not treated as a
  blocking open question, only reported here per the ticket's own flag.

## Anti-Drift Hazards
- **Do not touch the `-m "not slow and not extra_slow"` filter or any job's explicit path
  list** while adding `--junit-xml=` — `tests/tools/test_ci_workflow_test_coverage.py`'s
  `test_parses_real_workflow_fastlane_job_paths` and sibling tests assert exact path-token
  membership per job; reordering or retyping any existing token (not just appending the new
  flag) breaks that regression surface, and the AC itself requires byte-identical text aside
  from the added flag.
- **Do not let the new `if: always()` summary step change a job's overall conclusion.** A
  GitHub Actions `run:` step fails its job by default on non-zero exit. The summary-writing
  script must be defensive (missing file, malformed XML, zero collected tests) and always
  return 0 — swallowing that correctly is the entire difference between "purely
  additive/observational" (required) and "a second, redundant, forbidden failure gate."
- **Do not introduce a `uses:` marketplace Action** (`dorny/test-reporter`,
  `EnricoMi/publish-unit-test-result-action`, etc.) even though several exist for exactly this
  use case — AC #3 and Scope bullet 3 are explicit that only plain shell/Python writing to
  `$GITHUB_STEP_SUMMARY` is in scope.
- **Do not place the JUnit XML output path under `tests/`** — the single most concrete,
  easy-to-get-wrong implementation trap in this ticket (see Risks above); would silently
  corrupt `ci_workflow_test_coverage.py`'s directory-coverage guard without failing anything
  visibly today.
- **Do not place a new CLI-invocable parsing module inside `tools/gate_checks/`.** That
  package's own test suite enforces a no-CLI/argparse-entry-point convention (its modules are
  pure functions consumed by `done-checker`, never directly executed as a script) — a new
  module that must be `python3`-invocable from a workflow `run:` line belongs in `tools/`
  itself, alongside other standalone scripts, not in `tools/gate_checks/`.
- **Do not touch `slow` or `migration-lanes`** unless the deferral decision above is explicitly
  overturned and documented — any "just add it here too since it's adjacent" edit to either job
  would be undocumented scope creep beyond what this ticket's Scope sized.
- **Do not add `--cov`/`pytest-cov`** or any coverage-percentage collection while touching these
  same `pytest` invocations — explicitly Out of Scope, easy to conflate with "structured test
  reporting" since both are commonly bundled together in other projects.
