---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS
artifact_type: test_plan
tags: [testing, workflows]
---

# Test Plan — TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS

This ticket changes only `.github/workflows/test.yml` (a GitHub Actions workflow definition) —
there is no Python behavior change and nothing to unit-test in the usual sense. Verification
splits into two tiers: (1) a **static architecture guard**, executable locally via pytest, that
parses the YAML and asserts the new job/step structure is present and well-formed — following
the exact precedent already in this repo (`tests/static/test_corpus_diversity_ci_isolation.py`,
which does the same `yaml.safe_load(...).jobs["slow"]...` pattern for a prior CI-gating change);
and (2) a **real end-to-end CI observation** that cannot run inside pytest at all, which the
orchestrator must execute manually/post-Implement per the ticket's own acceptance criteria.

## Regression Surface

No existing test's *behavior* changes — this ticket adds new jobs/conditions to a workflow file
that today has zero test coverage of its job-trigger structure beyond the two `slow`-job-specific
tests below. "Regression surface" here means: tests that already assert facts about
`.github/workflows/test.yml`'s structure, which must keep passing unmodified (proving this ticket
did not disturb the `slow` job or any of the 9 out-of-scope jobs).

- **Static / architecture** (`tests/static/`):
  - `tests/static/test_corpus_diversity_ci_isolation.py` — asserts `slow` job step ordering and
    `--ignore` flag text. Must keep passing untouched; if this ticket's diff touches the `slow`
    job for any reason (it should not, per the Risks section of investigation.md), re-verify this
    file explicitly.
  - `tests/static/test_ci_requirements_no_ml_stack.py` — asserts `requirements.txt` composition;
    unrelated to this ticket's change but scoped to the same directory, cheap to include.
- **Tools / gate checks** (`tests/tools/`):
  - `tests/tools/test_workflow_meta_conformance.py` — parses `.claude/workflows/*.js` `meta`
    blocks, **not** `.github/workflows/*.yml`; confirmed unrelated by inspecting both the tool
    (`tools/gate_checks/workflow_meta_conformance.py`) and its `DEFAULT_WORKFLOWS_DIR =
    Path(".claude/workflows")` constant — different "workflow" concept entirely (agent pipeline
    phases, not GitHub Actions). Included here only to make explicit that it is *not* regression
    surface for this ticket, since the name overlap invites confusion.
- **Makefile targets** (indirectly, via `migration-lanes`' own steps — not re-run by this ticket's
  tests, but must remain byte-identical): `make lane-all-fast`, `make gate-expansion`. This ticket
  must not change what either target selects/runs — only whether the job invoking them is
  triggered at all.

## New Tests Required

All new tests live in `tests/static/` (matches the existing precedent's location and the
`architecture`-flavored, no-pytest-collection-runtime nature of this check) in a new file, e.g.
`tests/static/test_ci_narrow_path_filtered_jobs.py`.

1. **`test_perf_cert_arena_and_migration_lanes_have_if_conditions`**
   Category: architecture guard.
   Verifies: `yaml.safe_load(test.yml)["jobs"]["perf-cert-arena"]` and `["migration-lanes"]` each
   have a truthy `"if"` key present (proves the skip condition was actually added to both
   in-scope jobs, not silently dropped or added to the wrong job).
   Location: `tests/static/test_ci_narrow_path_filtered_jobs.py`.

2. **`test_no_other_fast_lane_job_gained_an_if_condition`**
   Category: architecture guard (anti-drift).
   Verifies: for every job in the 9 explicitly-out-of-scope list (`unit-core-world`,
   `unit-gameplay`, `unit-infra`, `integration`, `api-tools`, `agent-orchestration`,
   `simulation-quality`, `arch-docs`, `typecheck`), `"if" not in job_dict` — proves the change
   stayed scoped to exactly 2 jobs and did not accidentally spread. This is the single most
   important anti-scope-creep test in this plan.
   Location: same file.

3. **`test_slow_job_if_condition_is_unchanged`**
   Category: architecture guard (anti-drift / regression).
   Verifies: `jobs["slow"]["if"]` string is byte-identical to the pre-ticket value
   (`"github.ref == 'refs/heads/main' || github.event_name == 'schedule' || github.event_name ==
   'workflow_dispatch'"`) and `jobs["slow"]["needs"]` still lists exactly the same 10 job names in
   the same order. Directly encodes the Out-of-Scope boundary ("the `slow` job's own trigger
   gating — already handled by a prior ticket, not touched") as an executable assertion, and
   guards against the skip-propagation risk documented in investigation.md by proving the
   `slow`-job workaround (scoping the new skip logic to `pull_request` events only) was actually
   used instead of an edit to this line.
   Location: same file.

4. **`test_changed_files_gate_job_has_no_if_condition`**
   Category: architecture guard.
   Verifies: whatever upstream job computes the changed-files outputs (name TBD at Implement —
   test should locate it by checking which job `perf-cert-arena`/`migration-lanes` list in
   `needs:`, not by a hardcoded job-name string) has **no** `"if"` key of its own. Directly
   encodes the "must always run, never itself skippable" constraint from investigation.md's
   Anti-Drift Hazards — a gate job with its own `if:` would cascade-skip both target jobs
   unconditionally, defeating the fail-safe-to-run requirement.
   Location: same file.

5. **`test_perf_cert_arena_if_references_changed_files_gate_output`** /
   **`test_migration_lanes_if_references_changed_files_gate_output`**
   Category: architecture guard.
   Verifies: each job's `"if"` string contains `needs.` and references an `.outputs.` key
   distinct per job (proves the two jobs are gated independently, not by a single shared boolean
   that would make them always skip/run together — investigation.md's dependency-set analysis
   showed they are NOT identical, e.g. `perf-cert-arena` needs `src/api/` but not `src/content/`,
   while `migration-lanes` is the reverse).
   Location: same file.

6. **`test_gate_job_fails_open_on_non_pull_request_events`**
   Category: architecture guard (semantic, string-based).
   Verifies: the gate job's `run:` step text contains an explicit branch/check for
   `github.event_name != 'pull_request'` (or equivalent) that sets both run-outputs to `true`
   before any `git diff` is attempted — encodes safeguard #1 from investigation.md's Fail-Safe
   section as a literal text assertion (this repo's established pattern per
   `test_corpus_diversity_ci_isolation.py`, which also asserts on `run:` text content rather than
   executing it).
   Location: same file.

7. **`test_gate_job_fails_open_on_diff_command_failure`**
   Category: architecture guard (semantic, string-based).
   Verifies: the `run:` step text contains a failure-handling branch for the `git diff` command
   itself (e.g. an `if ! CHANGED=$(git diff ...)` guard or equivalent `||` fallback) that also
   sets both outputs to `true` on that path — encodes safeguard #2 from investigation.md. This is
   the test most directly protecting the ticket's hardest acceptance criterion ("fails safe...
   never silently skip on any ambiguity/error").
   Location: same file.

8. **`test_perf_cert_arena_path_set_covers_all_actually_imported_src_dirs`**
   Category: architecture guard (anti-drift, computed against real imports — not just YAML
   text).
   Verifies: re-derives the real `src/` top-level dependency set for `tests/perf/`,
   `tests/certification/`, `tests/arena/` at test-run time (same grep-equivalent logic used during
   this investigation: scan for `^from src\.` / `^import src\.` in those three directories,
   reduce to top-level dir names) and asserts every one of them appears as a path pattern
   substring somewhere in the `perf-cert-arena` job's (or its gate's) `if:`/pattern text. This is
   the test proposed in investigation.md's Anti-Drift Hazards to catch future dependency drift —
   it will fail the day a new test file under those 3 directories imports a `src/` dir not yet in
   the trigger set, forcing a conscious update rather than a silent false-negative skip.
   Location: same file (or a dedicated `test_ci_path_filter_dependency_drift.py` if the planner
   prefers separating "structure" tests from "computed dependency" tests — either is acceptable).

9. **`test_migration_lanes_path_set_covers_all_marker_tagged_test_dependencies`**
   Category: architecture guard (anti-drift, computed against real imports).
   Verifies: same technique as #8, but re-derives the marker-tagged test file set (files carrying
   `catalog`/`content_graph`/`worldassembly`/`registry_projection`/`scenario_setup`/`architecture`
   markers) and their `src/` imports at test-run time, asserting coverage against the
   `migration-lanes` trigger path set. Also asserts `tests/integration/content/
   test_expansion_gate.py`'s own 3 imports (`src.content.reference_graph`,
   `src.content.repository`, `src.worldmodules.repository`) are covered, since `gate-expansion` is
   part of the same job.
   Location: same file.

## Scoped Pytest Commands

```bash
# New tests for this ticket (once written):
pytest tests/static/test_ci_narrow_path_filtered_jobs.py -v --tb=short

# Full static/architecture regression surface (includes the new file + existing precedents):
pytest tests/static tests/architecture -m "not slow and not extra_slow" --tb=short -q

# Confirm the arch-docs CI job's own scope (which already runs tests/static) is unaffected:
pytest tests/architecture tests/docs tests/integrity tests/static tests/refactor \
       -m "not slow and not extra_slow" --tb=short -q
```
Never `pytest tests/` — scoped to the `tests/static`/`tests/architecture` domain per Testing
Rule, matching the `arch-docs` CI job's own existing scope (this ticket's tests belong in the job
that would have caught a `.github/workflows/test.yml` regression before this ticket, i.e.
`arch-docs`, which is itself one of the always-run 9-out-of-scope jobs — appropriately, since the
verification tests *for* the path-filter feature must never themselves be path-filtered out).

## Anti-Drift Test Guards

- Test #2 (`test_no_other_fast_lane_job_gained_an_if_condition`) is the primary scope-creep guard
  — it fails loudly if a future edit (by this ticket's own implementation or a later one)
  accidentally adds gating to any of the 9 explicitly out-of-scope jobs.
- Test #3 (`test_slow_job_if_condition_is_unchanged`) is the primary silent-regression guard for
  the cross-job interaction identified in investigation.md — without it, a future edit could
  "fix" a perceived bug by tightening `slow`'s `needs`/`if:` and nobody would notice it now
  requires the gated jobs to explicitly succeed (breaking fail-safe-to-run for the `slow` safety
  net) until a real nightly/post-merge run silently stopped executing.
- Tests #8 and #9 are the only guards in this plan that verify *coverage correctness* rather than
  *structural presence* — they are what prevents the path filter from becoming a slow-accreting
  false-negative source as the codebase grows new test files with new imports.
- No test in this plan can verify that the mechanism actually causes GitHub Actions to skip or
  run a job — that is inherently a live-CI behavior, not something `yaml.safe_load` + string
  assertions can prove. That gap is covered by the manual/CI-observed step below, not silently
  left unverified.

## Manual / CI-Observed Verification (cannot run inside pytest — orchestrator to execute post-Implement)

Per the ticket's own Acceptance Criteria ("including a real end-to-end verification"), this step
is explicitly flagged as **not executable by the investigator or by pytest** and must be run for
real by whoever executes Implement/Verify:

1. Push a trivial commit to a scratch branch that touches only a file outside both trigger path
   sets (e.g. a comment-only change in `docs/guidelines/` or a file under `tests/unit/systems/`).
   Open/update a PR against `main`. Confirm via `gh run view <run-id>` or `gh api
   repos/:owner/:repo/actions/runs/<run-id>/jobs` that `perf-cert-arena` and `migration-lanes`
   report conclusion `skipped` (not `failure`, not silently absent from the job list).
2. On the same branch, push a second commit touching a real dependency path for each job in turn
   (e.g. a no-op whitespace change in `src/core/state.py` for both; then separately a change under
   `tests/perf/` only, and a change under `tests/unit/worldassembly/` only, to confirm each job's
   filter is independently correct and not accidentally OR'd together). Confirm both jobs report
   `success`/`failure` as normal (i.e. they actually ran) in each case.
3. Confirm a push directly to `main` (or the nightly `schedule` trigger, or a manual
   `workflow_dispatch`) still runs both jobs unconditionally regardless of changed paths — this is
   the concrete verification of the "resolved risk" in investigation.md (no `slow`-job
   skip-propagation). If a real `main` push isn't practical to test standalone, `workflow_dispatch`
   is an acceptable substitute since the recommended mechanism treats all three non-`pull_request`
   events identically.
4. Confirm the `slow` job, on whichever of the above runs makes its own `if:` true, still shows
   `perf-cert-arena` and `migration-lanes` as `success`/`failure` (never `skipped`) in its `needs`
   chain, and that `slow` itself actually executes (not silently skipped due to
   needs-success propagation).

This step is explicitly the orchestrator's responsibility, not this investigation's — flagged
here so it is not silently dropped between Plan and Verify.
