---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS
phase: done
date: 2026-08-19
tags: [testing]
---

# TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS

## Title
Add path-based skip conditions to CI's most isolated/costly jobs (migration-lanes, perf-cert-arena)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`.github/workflows/test.yml` runs all 11 fast-lane jobs unconditionally on every PR push,
regardless of what files actually changed — confirmed by reading the file directly: no
`paths:`/`paths-ignore:` trigger filter and no per-job `if:` condition based on changed files
exist anywhere except the `slow` job's branch/event-type gate
(`TCK-20260818-STANDARD-SLOW-REGRESSION-OFF-PR-PATH`). User asked whether CI only runs
tests related to a PR's actual change; confirmed it does not.

Blanket path-filtering across all 11 jobs was explicitly considered and rejected as this
ticket's scope: widely-imported modules (`src/core/state.py`, `src/engine/kernel.py`, etc.) can
affect nearly every job's target directory in ways a naive path filter would miss — a
false-negative (a job that should have caught a break, but got skipped) is a worse failure mode
here than the CI-minutes cost, given this project's "test the real thing, no shortcuts" testing
discipline (`CLAUDE.md` Testing Rule). `test-scoper` already performs the real per-ticket
file-to-test-directory scoping locally, before anything reaches CI — CI's per-subsystem job
split exists specifically as the safety net on top of that local scoping, not as a redundant
cost center to optimize away wholesale.

This ticket scopes the idea narrowly instead: only the 2 jobs whose test scope is both
(a) expensive relative to the rest of the suite and (b) cleanly isolated to a specific,
non-widely-imported directory tree, so a path-based skip carries low false-negative risk.

## Scope
- Add a path-based skip condition to the `perf-cert-arena` job (`tests/perf`, `tests/certification`,
  `tests/arena` — all `not slow`-marked): skip when no changed path falls under `tests/perf/`,
  `tests/certification/`, `tests/arena/`, or any `src/` path those suites actually exercise
  (investigation to determine the real dependency set — do not just filter on the 3 test
  directories and ignore what `src/` code they cover).
- Add a path-based skip condition to the `migration-lanes` job (`make lane-all-fast` +
  `make gate-expansion`) — note this job's own test selection is **marker-based**
  (`catalog or content_graph or worldassembly or registry_projection or scenario_setup or
  architecture`), not directory-based, so the investigation must determine a sound path→marker
  mapping (or accept a coarser trigger set) rather than assuming a 1:1 directory match exists.
- Use GitHub Actions' native per-job `if:` condition (mirroring the `slow` job's existing
  pattern) driven by a changed-files check — investigation should confirm whether a
  `paths:`/`paths-ignore:` top-level trigger filter or a `dorny/paths-filter`-style per-job
  action (or an equivalent hand-rolled `git diff` check) is the right mechanism, and document
  the choice.
- The skip condition must be conservative: when in doubt (e.g. the changed-files check itself
  fails, or a change touches something outside the mapped set), the job must still run — never
  fail open to "skip."

## Out of Scope
- Any of the other 9 fast-lane jobs (`unit-core-world`, `unit-gameplay`, `unit-infra`,
  `integration`, `api-tools`, `agent-orchestration`, `simulation-quality`, `arch-docs`,
  `typecheck`) — explicitly rejected for path-filtering per this ticket's own Request Summary;
  their test scopes are too broad/cross-cutting for a safe path-based skip.
- The `slow` job's own trigger gating — already handled by a prior ticket.
- Changing what tests each job runs, or any pytest marker definitions.
- `test-scoper`'s local per-ticket scoping mechanism — already correct, not touched.

## Acceptance Criteria
- [ ] `perf-cert-arena` and `migration-lanes` each skip (report as a no-op success, not a
      failure) when a PR's changed files fall entirely outside their determined dependency set.
      (Mechanism implemented and statically verified; real live-CI skip behavior still requires
      the Manual/CI-Observed Verification steps in `test_plan.md`, not executable from pytest —
      left unchecked pending that observation.)
- [ ] Both jobs still run in full when any file in their dependency set changes, including a
      real end-to-end verification (a PR touching only an unrelated file skips; a PR touching a
      relevant file runs). (Same caveat as above — mechanism + coverage tests pass; live-CI
      confirmation pending.)
- [x] No other job's trigger behavior changes. Verified by
      `test_no_other_fast_lane_job_gained_an_if_condition` (none of the 9 out-of-scope jobs
      gained an `if:`) and `test_slow_job_if_condition_is_unchanged` (byte-identical `if:`/`needs:`).
- [x] The skip mechanism fails safe (runs, never silently skips, on any ambiguity/error in the
      changed-files check itself). Verified by `test_gate_job_fails_open_on_non_pull_request_events`,
      `test_gate_job_fails_open_on_diff_command_failure`, and
      `test_gated_jobs_fail_open_on_gate_job_non_success` (gate-job-failure OR-clause +
      `!cancelled()`).

## Related Tickets
- TCK-20260818-STANDARD-SLOW-REGRESSION-OFF-PR-PATH (precedent for gating a job off the default
  per-PR path; same file, same general area)

## Related Docs
- .github/workflows/test.yml (the file being changed)
- Makefile (`lane-all-fast`, `gate-expansion` targets — read-only reference for the
  migration-lanes marker mapping)

## Related Stored Artifacts
None yet.

## Related Code Areas
- .github/workflows/test.yml

## Assumptions / Open Questions
- The exact `src/` dependency set for `perf-cert-arena` and the path→marker mapping for
  `migration-lanes` are not yet determined — this is the core investigation task, not a decision
  to make ahead of time.
- User explicitly chose the narrow scope (this ticket) over a blanket all-11-jobs path-filter,
  given the false-negative risk on widely-imported modules (2026-08-19 decision, recorded here
  for traceability).

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS/plan.md` exactly,
all 5 steps, no deviations:

- **Step 1:** Added an always-on `changed-files` gate job to `.github/workflows/test.yml`,
  inserted immediately before `perf-cert-arena` (no `if:` of its own — must never be
  conditionally skippable). `checkout` uses `fetch-depth: 0`. Declares
  `outputs: run_perf_cert_arena, run_migration_lanes` sourced from a single `id: diff` step
  whose `run:` block, in order: (1) forces both outputs `true` and exits 0 on any non-
  `pull_request` event before any diff is attempted; (2) computes a three-dot diff
  (`git diff --name-only "$BASE...$HEAD"`) guarded with `if ! CHANGED=$(...)`, forcing both
  outputs `true` and exiting 0 on a non-zero exit; (3) on success, matches `$CHANGED` against
  `PERF_RE`/`MIG_RE` (copied verbatim from `investigation.md`) via `grep -qE`, setting each
  output independently.
- **Step 2:** `perf-cert-arena` gained `needs: [changed-files]` and
  `if: ${{ !cancelled() && (needs.changed-files.result != 'success' || needs.changed-files.outputs.run_perf_cert_arena == 'true') }}`.
  `steps:`/`name:`/`runs-on:` untouched.
- **Step 3:** `migration-lanes` gained the equivalent `needs:`/`if:` referencing
  `run_migration_lanes`. `steps:`/`name:`/`runs-on:` untouched; `slow`'s `if:`/`needs:` block
  untouched.
- **Step 4:** Added `tests/static/test_ci_narrow_path_filtered_jobs.py` — 12 test functions
  covering all 11 numbered items in plan.md Step 4 (item 5 splits into 2 test functions, one
  per job). Follows the `yaml.safe_load` fixture pattern from
  `tests/static/test_corpus_diversity_ci_isolation.py`. Tests 8/9
  (`test_perf_cert_arena_path_set_covers_all_actually_imported_src_dirs`,
  `test_migration_lanes_path_set_covers_all_marker_tagged_test_dependencies`) re-derive the real
  `src/` dependency sets at test-run time via a Python regex scan, rather than hardcoding
  investigation.md's lists a second time, so future dependency drift is caught automatically.
- **Step 5:** Added `## Path-Based Skip Condition (CI)` to
  `docs/testing/migration_ci_lanes.md` between `## Recommended CI Pipeline Order` and
  `## Running Locally`; bumped `**Last updated:**` to 2026-08-19.

**Implementation-time finding (not a plan deviation — a test-4 design detail worth recording):**
while re-deriving the `migration-lanes` `src/` dependency set for test 9, a permissive regex
(matching indented/function-local imports, not just column-0 top-of-file imports) initially
over-collected 6 extra `src/` dirs (`config`, `domains`, `engine`, `entities`, `platform`,
`worldgeneration`) that only appear inside `@pytest.mark.slow`-marked test function bodies
(e.g. `tests/unit/worldassembly/test_hero_guild_routing_population_stability.py`,
`tests/unit/worldassembly/test_corpus_diversity.py`). Those functions are excluded from
`lane-all-fast`'s selection (`... and not slow`), so counting their imports would have
overclaimed the required trigger-path coverage. Fixed by matching investigation.md's exact
derivation command (`grep -rhoE "^from src\."` — column-0, `from`-only, no leading whitespace)
in the test's regex, which reproduces the 8-dir set investigation.md originally found. This is
implementation-detail precision, not a deviation from plan.md's spec (plan.md did not specify
the regex's exact anchoring), so no `staging_artifacts/.../plan.md` Deviations note was needed.

## Test Summary
- `pytest tests/static/test_ci_narrow_path_filtered_jobs.py -v --tb=short` — 12/12 passed.
- `pytest tests/static tests/architecture -m "not slow and not extra_slow" --tb=short -q` —
  84/84 passed (includes the new file plus the full existing static/architecture regression
  surface, e.g. `test_corpus_diversity_ci_isolation.py`, `test_ci_requirements_no_ml_stack.py`).
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"` — parses
  cleanly, all 13 jobs present (`changed-files` added; all originals intact).
- Live-CI/end-to-end skip behavior (a PR touching only unrelated files actually skipping;
  `slow`'s `needs` chain never reporting `skipped` for the two gated jobs) is **not**
  pytest-executable, per `test_plan.md`'s Manual/CI-Observed Verification section — remains the
  orchestrator's responsibility post-Implement, flagged here so it is not silently dropped.

## Files Changed
- `staging_artifacts/TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS/investigation.md` — new file,
  written during the Investigate phase: dependency-set derivation for both gated jobs, recommended
  mechanism, docs-to-update determination, and risk/anti-drift analysis.
- `staging_artifacts/TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS/test_plan.md` — new file, written
  during the Investigate phase: regression surface, 9 originally-specified new-test specs, scoped
  pytest commands, and the Manual/CI-Observed Verification section.
- `.github/workflows/test.yml` — added `changed-files` gate job; added `needs:`/`if:` to
  `perf-cert-arena` and `migration-lanes`.
- `tests/static/test_ci_narrow_path_filtered_jobs.py` — new file, 12 static architecture-guard
  tests.
- `docs/testing/migration_ci_lanes.md` — new `## Path-Based Skip Condition (CI)` section; bumped
  `**Last updated:**` header.
- `staging_artifacts/TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS/plan.md` — edited during Review
  (2 substantive fixes: gate-job-failure fail-open OR-clause with `!cancelled()`; three-dot vs
  two-dot diff correctness) plus 2 cosmetic numbering corrections, prior to this Implement pass.
- `tickets/inprogress/TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS.md` — this file (Status,
  Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary).

## Completion Summary
Added a single always-on `changed-files` gate job to `.github/workflows/test.yml` that computes
two path-based boolean outputs via a hand-rolled three-dot `git diff`, and gated
`perf-cert-arena`/`migration-lanes` on those outputs with a fail-open `if:` (covers non-PR
events, diff-command failure, and gate-job non-success). All 5 plan steps implemented with no
deviations; 12 new static tests in `tests/static/test_ci_narrow_path_filtered_jobs.py` pass,
re-deriving both jobs' real `src/` dependency sets live rather than hardcoding them, and the
full existing static/architecture regression surface (84 tests) still passes unmodified.
Documentation updated in `docs/testing/migration_ci_lanes.md`. Remaining work before this ticket
can close is the orchestrator-owned live-CI/Manual Verification step from `test_plan.md` (real
skip/run behavior on an actual PR), which is why the two runtime-behavior Acceptance Criteria
remain unchecked above.
