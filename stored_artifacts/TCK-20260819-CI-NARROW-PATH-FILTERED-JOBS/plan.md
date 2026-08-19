---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS
artifact_type: plan
tags: [testing, workflows]
---

# Implementation Plan — TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS

## Summary
Add a single always-on upstream `changed-files` gate job to `.github/workflows/test.yml` that
computes two boolean outputs (`run_perf_cert_arena`, `run_migration_lanes`) via a hand-rolled
`git diff --name-only` check, scoped to `github.event_name == 'pull_request'` only (all other
event types unconditionally output `true`). `perf-cert-arena` and `migration-lanes` each gain
`needs: [changed-files]` plus an `if:` referencing their own output. This mirrors the `slow`
job's existing per-job `if:` precedent (`.github/workflows/test.yml:255`) without touching that
job at all, because scoping the new logic to `pull_request` events means `perf-cert-arena`/
`migration-lanes` can never report `skipped` on the event types where `slow`'s own `if:` can be
true — sidestepping the needs-success skip-propagation risk investigation.md identified. Two
path sets (14 `src/` dirs for `perf-cert-arena`, 8 `src/` dirs + `tests/conftest.py` for
`migration-lanes`) are copied verbatim from investigation.md's "Recommended trigger path set"
sections into the `run:` block's regexes. A new single test file,
`tests/static/test_ci_narrow_path_filtered_jobs.py`, adds all 9 tests from test_plan.md as
static YAML/text assertions (no live-CI execution possible from pytest — that gap is covered by
test_plan.md's Manual/CI-Observed Verification section, which is the orchestrator's
responsibility post-Implement, not part of this plan's steps). `docs/testing/migration_ci_lanes.md`
gets a new section documenting the skip condition and its header bump.

## Judgment Call: Single Test File (Not Split)
test_plan.md treats splitting tests #8/#9 (the coverage-correctness tests) into a separate
`test_ci_path_filter_dependency_drift.py` as optional. This plan keeps all 9 tests in one file,
`tests/static/test_ci_narrow_path_filtered_jobs.py`. Reasoning: the repo's direct precedent,
`tests/static/test_corpus_diversity_ci_isolation.py`, is itself a single file mixing structural
presence assertions and content assertions for one CI-gating change — there is no existing
precedent in this repo for splitting "structure" tests from "computed dependency" tests into
separate files for a single feature. All 9 tests share one fixture (loading and parsing
`.github/workflows/test.yml`), splitting would duplicate that fixture or require an import
between the two files for no isolation benefit, since both files would need to run together for
this ticket's regression surface anyway (`pytest tests/static/test_ci_narrow_path_filtered_jobs.py -v --tb=short`
per test_plan.md's Scoped Pytest Commands section already assumes one file).

## Steps

### Step 1 — Add the always-on `changed-files` gate job
**Files:** `.github/workflows/test.yml`
**Change:** Insert a new job named `changed-files` immediately before the `perf-cert-arena` job
(currently at `.github/workflows/test.yml:200-214`, comment header `# ── Perf / certification /
arena`). The new job has **no `if:` of its own** (must always run — investigation.md's
Anti-Drift Hazards: "Do not let the `changed-files` gate job itself become conditionally
skippable"). Its `checkout` step must use `fetch-depth: 0` (default depth-1, per
`actions/checkout@v4`'s documented default, will not have `github.event.pull_request.base.sha`
reachable — investigation.md's Recommended Mechanism section). It declares two `outputs`
(`run_perf_cert_arena`, `run_migration_lanes`) sourced from a single `id: diff` step whose `run:`
block implements, in order:
1. Non-`pull_request` event check first: `if [ "${{ github.event_name }}" != "pull_request" ];
   then` set both outputs to `true` via `>> "$GITHUB_OUTPUT"` and `exit 0` before any `git diff`
   is attempted (safeguard #1, investigation.md Fail-Safe-to-Run Verification).
2. For `pull_request` events, first compute the merge-base and diff using **three-dot** semantics
   (`git diff --name-only "$BASE...$HEAD"`, or an explicit `git merge-base "$BASE" "$HEAD"`
   followed by a two-dot diff against that merge-base commit) rather than a plain two-dot
   `git diff "$BASE" "$HEAD"` — a two-dot diff against `base.sha` (which is the base branch's
   *current* tip, not the PR's actual branch point) would also pick up files changed on `main`
   after the PR branched but never touched by the PR itself, on any PR that sits open while `main`
   advances. This does not create an unsafe false-negative (it only ever biases toward running
   more, not skipping), but it defeats the ticket's own cost-reduction purpose on long-lived PRs if
   left as a plain two-dot diff — fix it in this same edit. Wrap the diff itself:
   `CHANGED=$(git diff --name-only "$BASE...$HEAD" 2>&1)`, guarded with `if ! CHANGED=$(...)` so a
   non-zero exit (distinct from a successful empty-diff) is caught — on failure, both outputs
   forced `true` and the step exits 0 without failing the job (safeguard #2).
3. On successful diff, match `$CHANGED` against two regexes with `grep -qE` and set each output
   `true`/`false` independently:
   ```
   PERF_RE='^(tests/(perf|certification|arena)/|src/(ai|api|certification|cognition|config|core|domains|engine|observability|perf|platform|replay|world|worldbuilding)/|Makefile$|requirements\.txt$|\.github/workflows/test\.yml$)'
   MIG_RE='^(tests/architecture/|tests/(integration|unit)/(content|scenarios|worldassembly|certification|runtime)/|tests/conftest\.py$|src/(core|content|runtime|scenarios|worldassembly|worldbuilding|worldmodules|certification)/|Makefile$|requirements\.txt$|\.github/workflows/test\.yml$)'
   ```
4. **Gate-job-failure fail-open (safeguard #4, required — closes a gap flagged at Review):** the
   two safeguards above only cover branches the script itself reaches and exits 0 from. They do
   **not** cover the `changed-files` job concluding non-`success` for a reason outside those
   branches — e.g. the `actions/checkout@v4` (`fetch-depth: 0`) step itself failing (network flake,
   unreachable history) or a runner-level failure. Because `perf-cert-arena`/`migration-lanes` each
   carry `needs: [changed-files]` with a plain-boolean `if:` (no status-check function), GitHub
   Actions implicitly ANDs that `if:` with `success()` on every job in `needs:` (the same mechanism
   investigation.md documents for the pre-existing `slow` job) — so a `changed-files` job that fails
   outright would make both gated jobs report `skipped`, which is exactly the outcome Acceptance
   Criteria #4 prohibits ("fails safe... never silently skips, on any ambiguity/error in the
   changed-files check itself" — a checkout failure is squarely "an ambiguity/error in the
   changed-files check itself"). Fix: give `perf-cert-arena`'s and `migration-lanes`' `if:`
   conditions an explicit OR-clause for a non-`success` gate-job conclusion, so the downstream job
   still runs even if the gate job itself failed:
   ```
   if: ${{ !cancelled() && (needs.changed-files.result != 'success' || needs.changed-files.outputs.run_perf_cert_arena == 'true') }}
   ```
   (and the `migration-lanes` equivalent, substituting `run_migration_lanes`). `!cancelled()` is
   required alongside the custom boolean because any `if:` expression that references a
   status-check function at all (here, implicitly needed since we're now overriding the default
   `success()`-AND behavior) must explicitly restate what to do on `cancelled`/`failure` upstream
   states; without it, a workflow-level cancellation would still evaluate the custom boolean instead
   of correctly short-circuiting. This condition reads: run this job unless the workflow was
   cancelled, and (the gate job didn't cleanly succeed OR this job's own path actually matched) —
   i.e. any ambiguity in the gate job's own execution forces a run, exactly matching AC #4.

   These path sets are copied verbatim from investigation.md's "Recommended trigger path set for
   `perf-cert-arena`" (14 `src/` dirs: `ai api certification cognition config core domains engine
   observability perf platform replay world worldbuilding`, plus `tests/perf/`,
   `tests/certification/`, `tests/arena/`, `Makefile`, `requirements.txt`,
   `.github/workflows/test.yml`) and "Recommended trigger path set for `migration-lanes`" (8
   `src/` dirs: `core content runtime scenarios worldassembly worldbuilding worldmodules
   certification`, plus `tests/architecture/`, `tests/integration/{content,scenarios,worldassembly}/`,
   `tests/unit/{certification,content,runtime,scenarios,worldassembly}/`, `tests/conftest.py`,
   `Makefile`, `requirements.txt`, `.github/workflows/test.yml`). Do not re-derive or narrow
   these sets — they were computed from a live `grep -rhoE "^from src\." tests/perf
   tests/certification tests/arena` and an equivalent scan of the 28 marker-tagged
   `migration-lanes` test files, cited in investigation.md lines 141-254.

**Other writers to `.github/workflows/test.yml` (shared resource):** This file currently defines
11 fast-lane jobs (`unit-core-world` through `typecheck`, lines 20-244) plus `slow` (lines
246-286) — all authored by prior tickets, most recently `slow`'s `if:`/`needs:` block by
TCK-20260818-STANDARD-SLOW-REGRESSION-OFF-PR-PATH. No other ticket is concurrently editing this
file in this session. This step's insertion point (immediately before line 200) does not
renumber or touch any line in jobs 1-9 (lines 20-198) or the `slow` job (lines 246-286) — it only
shifts line numbers for `perf-cert-arena`/`migration-lanes` downward, which Steps 2 and 3 account
for. No other workflow file (`.github/workflows/*.yml`) references `changed-files` by name today
(confirmed by investigation.md's grep of all `uses:`/job-reference lines), so there is no
cross-workflow collision risk from the new job name.
**Do NOT touch:** any of the 9 out-of-scope jobs (lines 20-198), the `typecheck` job (lines
231-244), or the `slow` job's `if:`/`needs:` block (lines 255-266) — see Scope Guards.
**Verify:** `tests/static/test_ci_narrow_path_filtered_jobs.py::test_changed_files_gate_job_has_no_if_condition`,
`::test_gate_job_fails_open_on_non_pull_request_events`, `::test_gate_job_fails_open_on_diff_command_failure`,
`::test_gate_job_diff_uses_three_dot_range`
(all added in Step 4 — no standalone test exists until then; see Dependency Map).

### Step 2 — Gate `perf-cert-arena` on the new output
**Files:** `.github/workflows/test.yml`
**Change:** On the `perf-cert-arena` job (originally lines 201-214, shifted down by Step 1's
insertion), add `needs: [changed-files]` and
`if: ${{ !cancelled() && (needs.changed-files.result != 'success' || needs.changed-files.outputs.run_perf_cert_arena == 'true') }}`
immediately under the job's `name:`/`runs-on:` keys — the `needs.changed-files.result != 'success'`
OR-clause is required (see Step 1 safeguard #4) so this job still runs if the gate job itself failed,
not just when it succeeded and reported `run_perf_cert_arena == 'false'`. Do not otherwise modify this
job's `steps:` block (checkout, setup-python, pip install, pytest invocation at lines 205-214
must remain byte-identical — this ticket changes only whether the job runs, never what it runs
once running, per the ticket's Scope).
**Other writers to `.github/workflows/test.yml`:** same file as Step 1; `perf-cert-arena` is not
referenced by `needs:` in any job except `slow` (line 265, unchanged by this plan — see Scope
Guards). No concurrent editor.
**Do NOT touch:** the job's `steps:` list, `name:`, or `runs-on:` values; the `slow` job's
`needs:` entry for `perf-cert-arena` (line 265) — it must keep listing `perf-cert-arena` exactly
as today, unmodified.
**Verify:** `tests/static/test_ci_narrow_path_filtered_jobs.py::test_perf_cert_arena_and_migration_lanes_have_if_conditions`,
`::test_perf_cert_arena_if_references_changed_files_gate_output`,
`::test_perf_cert_arena_path_set_covers_all_actually_imported_src_dirs`,
`::test_gated_jobs_fail_open_on_gate_job_non_success` (added in Step 4).

### Step 3 — Gate `migration-lanes` on the new output
**Files:** `.github/workflows/test.yml`
**Change:** On the `migration-lanes` job (originally lines 217-228, shifted down by Step 1's
insertion), add `needs: [changed-files]` and
`if: ${{ !cancelled() && (needs.changed-files.result != 'success' || needs.changed-files.outputs.run_migration_lanes == 'true') }}`
immediately under the job's `name:`/`runs-on:` keys — same gate-job-failure OR-clause as Step 2
(see Step 1 safeguard #4). Both existing `run:` steps (`make lane-all-fast`, `make gate-expansion`
at lines 225-228) stay in the same single job — investigation.md's Anti-Drift Hazards explicitly
warns against splitting them into two jobs with independent filters, since they share the same
broad dependency set and this ticket's scope is "exactly 2 jobs," not 3.
**Other writers to `.github/workflows/test.yml`:** same file as Steps 1-2. `migration-lanes` is
referenced by `needs:` only in `slow` (line 266, unchanged — see Scope Guards). No concurrent
editor. Also note: this step does not touch `Makefile:210-214` (`lane-all-fast`,
`gate-expansion` target bodies) — those targets are read-only reference for this ticket per the
ticket's own Related Docs section; only whether the job invoking them runs is in scope.
**Do NOT touch:** the job's `steps:` list, `name:`, or `runs-on:` values; `Makefile` target
bodies; the `slow` job's `needs:` entry for `migration-lanes` (line 266).
**Verify:** `tests/static/test_ci_narrow_path_filtered_jobs.py::test_perf_cert_arena_and_migration_lanes_have_if_conditions`,
`::test_migration_lanes_if_references_changed_files_gate_output`,
`::test_migration_lanes_path_set_covers_all_marker_tagged_test_dependencies`,
`::test_gated_jobs_fail_open_on_gate_job_non_success` (added in Step 4).

### Step 4 — Add the new static test file (all 11 tests)
**Files:** `tests/static/test_ci_narrow_path_filtered_jobs.py` (new file)
**Change:** Following the exact precedent of `tests/static/test_corpus_diversity_ci_isolation.py`
(a `yaml.safe_load(".github/workflows/test.yml")["jobs"][...]` pattern, cited in
investigation.md's Prior Work section), add all 9 tests specified in test_plan.md's "New Tests
Required" section plus 2 additional tests added at Review to close gaps found in the plan gate
(safeguard #4 for gate-job-failure fail-open, and the two-dot/three-dot diff correctness gap):
1. `test_perf_cert_arena_and_migration_lanes_have_if_conditions` — both jobs have a truthy `"if"` key.
2. `test_no_other_fast_lane_job_gained_an_if_condition` — for each of the 9 out-of-scope job
   names (`unit-core-world`, `unit-gameplay`, `unit-infra`, `integration`, `api-tools`,
   `agent-orchestration`, `simulation-quality`, `arch-docs`, `typecheck`), assert `"if" not in
   job_dict`. Primary anti-scope-creep guard.
3. `test_slow_job_if_condition_is_unchanged` — `jobs["slow"]["if"]` string byte-identical to
   `"github.ref == 'refs/heads/main' || github.event_name == 'schedule' || github.event_name ==
   'workflow_dispatch'"` (verified against `.github/workflows/test.yml:255` read during this
   plan) and `jobs["slow"]["needs"]` still lists the same 10 job names in the same order
   (`unit-core-world, unit-gameplay, unit-infra, integration, api-tools, agent-orchestration,
   simulation-quality, arch-docs, perf-cert-arena, migration-lanes` — verified against
   `.github/workflows/test.yml:256-266`).
4. `test_changed_files_gate_job_has_no_if_condition` — locate the gate job dynamically via
   `perf-cert-arena`'s `needs:` list (not a hardcoded job-name string, per test_plan.md), assert
   it has no `"if"` key.
5. `test_perf_cert_arena_if_references_changed_files_gate_output` /
   `test_migration_lanes_if_references_changed_files_gate_output` — each job's `"if"` string
   contains `needs.` and an `.outputs.` key distinct per job.
6. `test_gate_job_fails_open_on_non_pull_request_events` — gate job's `run:` text contains an
   explicit `github.event_name != 'pull_request'` (or equivalent) branch that sets both outputs
   `true` before any `git diff` call.
7. `test_gate_job_fails_open_on_diff_command_failure` — gate job's `run:` text contains a
   failure-handling branch for the `git diff` command (`if ! CHANGED=$(git diff ...)` or
   equivalent) that also sets both outputs `true`.
8. `test_perf_cert_arena_path_set_covers_all_actually_imported_src_dirs` — re-derive, at
   test-run time, the real `src/` top-level dirs imported by `tests/perf/`, `tests/certification/`,
   `tests/arena/` (same technique as investigation.md's grep) and assert each appears as a
   substring in the gate job's `if:`/pattern text.
9. `test_migration_lanes_path_set_covers_all_marker_tagged_test_dependencies` — re-derive, at
   test-run time, the marker-tagged (`catalog`/`content_graph`/`worldassembly`/
   `registry_projection`/`scenario_setup`/`architecture`) test files' `src/` imports plus
   `tests/integration/content/test_expansion_gate.py`'s 3 imports
   (`src.content.reference_graph`, `src.content.repository`, `src.worldmodules.repository`) and
   assert coverage against the `migration-lanes` trigger path set.
10. `test_gated_jobs_fail_open_on_gate_job_non_success` (added at Review to close a gap flagged
    against AC #4) — for both `perf-cert-arena` and `migration-lanes`, assert their `"if"` string
    contains `needs.changed-files.result != 'success'` (or equivalent non-`success`-forces-run
    logic) ORed with the output check, and contains `!cancelled()` — proves a gate-job failure
    (not just a clean `run_X == 'false'` result) still allows the downstream job to run, per Step 1
    safeguard #4.
11. `test_gate_job_diff_uses_three_dot_range` (added at Review to close the two-dot/three-dot gap)
    — gate job's `run:` text uses `git diff --name-only "$BASE...$HEAD"` (three-dot) or an explicit
    `git merge-base` call, not a plain two-dot `git diff "$BASE" "$HEAD"` — proves the diff reflects
    only the PR's actual changes, not accumulated drift from `main` on long-lived PRs.
**Other writers to this test file:** none — new file, no concurrent editor.
**Do NOT touch:** `tests/static/test_corpus_diversity_ci_isolation.py` or
`tests/static/test_ci_requirements_no_ml_stack.py` — both must keep passing unmodified (test
plan's Regression Surface section); read them for the YAML-parsing pattern only, do not edit
them.
**Verify:** `pytest tests/static/test_ci_narrow_path_filtered_jobs.py -v --tb=short` (all 11
tests pass); `pytest tests/static tests/architecture -m "not slow and not extra_slow" --tb=short -q`
(full regression surface, confirms `test_corpus_diversity_ci_isolation.py` and
`test_ci_requirements_no_ml_stack.py` still pass unmodified).

### Step 5 — Update `docs/testing/migration_ci_lanes.md`
**Files:** `docs/testing/migration_ci_lanes.md`
**Change:** Insert a new section, `## Path-Based Skip Condition (CI)`, between the existing
`## Recommended CI Pipeline Order` section (ends at line 60, verified by direct read) and `##
Running Locally` (starts at line 62). Document: (a) that `migration-lanes` now carries a
job-level `if:` gated on the `changed-files` job's `run_migration_lanes` output, scoped to
`pull_request` events only; (b) the full trigger path set for `migration-lanes` copied from
investigation.md's "Recommended trigger path set for `migration-lanes`" section (same list as
Step 1's `MIG_RE`); (c) a one-line cross-reference noting `perf-cert-arena` has an analogous
independent skip condition (full detail for that job is CI plumbing, not migration-lane-specific,
so it does not need full duplication in this migration-lanes-scoped doc — a pointer to
`.github/workflows/test.yml`'s `changed-files` job is sufficient). Also bump the header
`**Last updated:** 2026-06-09` (line 10, verified by direct read) to `**Last updated:**
2026-08-19`.
**Other writers to this doc:** none identified — `docs/audits/D18_ci_release_pipeline.md` lines
169/187 reference `migration-lanes` only as historical resolved notes (investigation.md's Docs
Requiring Update section) and do not need updating; no other doc references the job's trigger
conditions.
**Do NOT touch:** `## Lane Definitions`, `## Lane Isolation Rules`, `## Running Locally`, `##
Adding a New Lane`, or `## Test Count Reference` sections — none describe trigger conditions and
are out of scope for this edit.
**Verify:** No automated test asserts doc prose content (confirmed no such test exists in
test_plan.md); verify manually that the new section renders correctly and the header bump is
present. This step is a documentation-completeness requirement under CLAUDE.md's Authoritative
Mechanics Rule / Docs Requiring Update, not an acceptance-criteria item on its own.

## Scope Guards
- Do not add an `if:` condition to any of the 9 out-of-scope jobs: `unit-core-world`,
  `unit-gameplay`, `unit-infra`, `integration`, `api-tools`, `agent-orchestration`,
  `simulation-quality`, `arch-docs`, `typecheck`.
- Do not modify the `slow` job's `if:` (line 255) or `needs:` (lines 256-266) in any way — the
  event-scoping design in Step 1 is specifically chosen so this is never necessary. If any future
  finding suggests the `slow` job needs to change, that is a separate ticket, not this one.
- Do not modify pytest marker definitions, `Makefile` target bodies (`lane-all-fast`,
  `gate-expansion`), or `test-scoper`'s local scoping mechanism.
- Do not extract the diff/regex logic into a `tools/` script — keep it inline in the `run:` block
  per repo precedent (`test_corpus_diversity_ci_isolation.py` asserts on `run:` text directly).
- Do not split `gate-expansion` and `lane-all-fast` into separate jobs.
- Do not widen the trigger path sets beyond what investigation.md derived, and do not narrow them
  either — copy verbatim.
- Do not touch `docs/audits/D18_ci_release_pipeline.md` (historical notes only, confirmed
  unrelated to trigger conditions).
- No `docs/parity_ledger/` entry is needed or should be added — confirmed in investigation.md
  (pure CI plumbing, no simulation-mechanic parity implication).

## Dependency Map
- Step 1 (gate job) must land before Step 2 and Step 3 — both reference
  `needs.changed-files.outputs.*`, which does not exist until the gate job is defined.
- Step 2 and Step 3 are independent of each other (different jobs, different output keys) and
  can be done in either order once Step 1 is complete.
- Step 4 (test file) depends on Steps 1-3 being complete — its assertions read the final
  `.github/workflows/test.yml` structure (job names, `if:` text, `needs:` values). Writing Step 4
  before Steps 1-3 land would produce a test file asserting against a workflow file that doesn't
  yet have the structure to test.
- Step 5 (doc update) is independent of Step 4 and can be done any time after Step 1 (needs the
  final path sets, which are fixed at Step 1 and not expected to change in Steps 2-3).

## Acceptance Criteria Map
| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `perf-cert-arena` and `migration-lanes` each skip (no-op success, not failure) when changed files fall entirely outside their dependency set | Steps 1, 2, 3 | `test_perf_cert_arena_and_migration_lanes_have_if_conditions`, `test_perf_cert_arena_if_references_changed_files_gate_output`, `test_migration_lanes_if_references_changed_files_gate_output`; real skip behavior confirmed only by test_plan.md's Manual/CI-Observed Verification step 1 (not pytest-executable) |
| Both jobs still run in full when a relevant file changes, including real end-to-end verification | Steps 1, 2, 3 | `test_perf_cert_arena_path_set_covers_all_actually_imported_src_dirs`, `test_migration_lanes_path_set_covers_all_marker_tagged_test_dependencies`; real run behavior confirmed only by test_plan.md's Manual/CI-Observed Verification step 2 |
| No other job's trigger behavior changes | Steps 1, 2, 3 (Scope Guards) | `test_no_other_fast_lane_job_gained_an_if_condition`, `test_slow_job_if_condition_is_unchanged` |
| Skip mechanism fails safe (runs, never silently skips) on any ambiguity/error in the changed-files check itself | Steps 1, 2, 3 (safeguard #4 OR-clause) | `test_changed_files_gate_job_has_no_if_condition`, `test_gate_job_fails_open_on_non_pull_request_events`, `test_gate_job_fails_open_on_diff_command_failure`, `test_gated_jobs_fail_open_on_gate_job_non_success`, `test_gate_job_diff_uses_three_dot_range`; real fail-safe behavior confirmed only by test_plan.md's Manual/CI-Observed Verification steps 3 and 4 |

## Unresolved Questions
None. The one open judgment call flagged by investigation.md (single test file vs. split) is
resolved above under "Judgment Call: Single Test File (Not Split)." All other mechanism
decisions were made in investigation.md with cited evidence and are followed as-is by this plan.

## Anti-Drift Notes
- The `changed-files` job must never gain an `if:` of its own (Step 1) — this is the single
  highest-consequence mistake possible in this plan, since it would cascade-skip both gated jobs
  unconditionally via the same `needs`-success mechanism this ticket exists to avoid.
- The event-type check (`github.event_name != 'pull_request'`) must run and `exit 0` **before**
  any `git diff` invocation — do not reorder so the diff runs first and the event check is used
  only to interpret its result; on a `push`/`schedule`/`workflow_dispatch` event,
  `github.event.pull_request.base.sha` does not exist at all, so any `git diff` attempt using it
  would fail regardless of the failure-handling branch's presence.
- `github.event.pull_request.head.sha` (not `github.sha`) is the correct head reference for
  `pull_request` events — `github.sha` resolves to the synthetic merge commit under
  `pull_request`, which investigation.md flags as a small but real precision difference.
- The trigger path sets are a known future drift risk (investigation.md's Anti-Drift Hazards): if
  a later PR adds a new test file under `tests/perf/`, `tests/certification/`, `tests/arena/`, or
  the `migration-lanes` marker-tagged directories that imports a `src/` top-level dir not already
  in `PERF_RE`/`MIG_RE`, the path filter becomes a silent false negative until Step 4's tests #8/#9
  catch it on the next test run — those two tests are the only safety net for this, keep them
  passing and do not weaken their assertions to "structural presence only."
- `fetch-depth: 0` on the gate job's checkout is required, not optional — a depth-1 clone will
  make `github.event.pull_request.base.sha` unreachable and cause every PR's diff to fail (which
  the fail-safe branch would mask as "both jobs run," silently defeating the entire feature's
  purpose while still passing all fail-safe tests, since forced-true-on-failure is
  indistinguishable from forced-true-on-genuine-no-match at the test level).
- **(Added at Review)** The gated jobs' `if:` conditions must include the
  `needs.changed-files.result != 'success'` OR-clause (safeguard #4) — without it, a
  `changed-files` job failure (e.g. the checkout step itself failing) would make both gated jobs
  report `skipped` via GitHub Actions' implicit `success()`-AND-on-`needs` semantics, which is
  exactly the "ambiguity/error in the changed-files check itself" that Acceptance Criteria #4
  prohibits from resolving to a skip. This is distinct from, and in addition to, the two
  script-internal safeguards (non-PR event, diff command failure) — those only cover cases where
  the script itself reaches an `exit 0`; this covers the job failing before or outside that script
  entirely.
- **(Added at Review)** The diff must use three-dot range semantics (`git diff --name-only
  "$BASE...$HEAD"`) or an explicit `git merge-base` step, not a plain two-dot `git diff "$BASE"
  "$HEAD"` — a two-dot diff against `base.sha` (the base branch's current tip, not the PR's actual
  branch point) would include files changed on `main` after the PR branched but never touched by
  the PR, causing progressively noisier false-positive "run" decisions (never unsafe, but
  defeats the ticket's cost-reduction purpose) the longer a PR stays open while `main` advances.
