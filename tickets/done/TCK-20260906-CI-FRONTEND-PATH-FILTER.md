---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260906-CI-FRONTEND-PATH-FILTER
phase: done
date: 2026-09-06
tags: [testing]
---

# TCK-20260906-CI-FRONTEND-PATH-FILTER

## Title
Extend the existing changed-files path-filter gate to skip the Frontend CI job on backend/docs-only PRs

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS` added a `changed-files` path-filter gate job to
`.github/workflows/test.yml`, conditionally skipping `perf-cert-arena` and `migration-lanes` on
PRs that don't touch their dependency sets. It explicitly and deliberately rejected extending this
to the other 9 Python fast-lane jobs (`unit-core-world`, `unit-gameplay`, `unit-infra`,
`integration`, `api-tools`, `agent-orchestration`, `simulation-quality`, `arch-docs`, `typecheck`)
— those have too broad/cross-cutting an import surface (widely-imported modules like
`src/core/state.py` could affect nearly every job) for a safe path-based skip.

That ticket's own Out of Scope list of 9 jobs never mentions the `Frontend` job (`cd frontend &&
npm ci && npx vitest run && npm run build`) — it was simply never considered, not deliberately
excluded. Unlike the 9 Python jobs, `Frontend` is a genuinely safe candidate: it is a fully
separate toolchain (TypeScript/npm, no Python import graph), so the "widely-imported module"
false-negative risk that ruled out the other 9 jobs does not apply. Confirmed via direct
inspection: `frontend/package.json`'s `build` script is `tsc -b && vite build` with no codegen
step reading any Python/`src/` source; the repo-root `package.json` (graphology/sigma, used by
`graphify-out/` visualization tooling) is unrelated and not a dependency of the Frontend job.
Currently a pure-backend or pure-docs PR still pays the full npm-install + vitest + tsc/vite-build
cost (~30-60s per recent CI runs) for no reason.

## Scope
- Extend the `changed-files` gate job's `run:` step (`.github/workflows/test.yml`) with a new
  output, `run_frontend`, using a new regex trigger-path set (e.g. `FRONTEND_RE`) covering
  `frontend/` and `.github/workflows/test.yml` (the workflow file itself, matching the existing
  `PERF_RE`/`MIG_RE` convention of including it so editing the workflow always re-runs every
  gated job).
- Add `needs: [changed-files]` and a job-level `if:` condition to the `frontend` job, mirroring
  the exact existing `perf-cert-arena`/`migration-lanes` pattern: fail-open on non-`pull_request`
  events, on a failed/errored gate job (`needs.changed-files.result != 'success'`), and on a
  failed `git diff` inside the gate job itself.
- Extend `tests/static/test_ci_narrow_path_filtered_jobs.py`'s static guards to cover `frontend`
  alongside the 2 existing gated jobs, without weakening any existing assertion (in particular,
  `test_no_other_fast_lane_job_gained_an_if_condition`'s 9-job out-of-scope list must stay
  unchanged — `frontend` was never in it, so no change needed there, but the new fail-open/gate
  tests need a `frontend` case).
- Update `docs/testing/migration_ci_lanes.md`'s "Path-Based Skip Condition (CI)" section to
  document the third gated job.

## Out of Scope
- Any of the 9 jobs `TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS` already explicitly rejected for
  path-filtering — that decision stands, not being revisited here.
- Changing what tests the `frontend` job itself runs, or its own `vitest`/`tsc`/`vite` config.
- The `slow`/`simq-grade-drift` jobs' own separate branch/event-type gating (unrelated mechanism,
  already handled by prior tickets).

## Acceptance Criteria
- `frontend` skips (reports as a no-op success, not a failure) when a PR's changed files fall
  entirely outside `frontend/` and the workflow file itself.
- `frontend` still runs in full when any file under `frontend/` or `.github/workflows/test.yml`
  changes, including a real end-to-end verification (a PR touching only an unrelated file skips;
  a PR touching a `frontend/` file runs) — mirroring the same Manual/CI-Observed Verification
  caveat the precedent ticket's own ACs carried (static verification from pytest, live-CI
  confirmation via this ticket's own PR).
- No other job's trigger behavior changes — verified by re-running
  `test_no_other_fast_lane_job_gained_an_if_condition`/`test_slow_job_if_condition_is_unchanged`
  unmodified and confirming they still pass.
- The skip mechanism fails safe (runs, never silently skips) on any ambiguity/error in the
  changed-files check itself, matching the existing fail-open tests' pattern for the new job.

## Related Tickets
- TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS (parent precedent — the gate mechanism this ticket
  extends, not re-litigates)

## Related Docs
- .github/workflows/test.yml
- docs/testing/migration_ci_lanes.md
- tests/static/test_ci_narrow_path_filtered_jobs.py

## Related Stored Artifacts
- stored_artifacts/TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS/ (precedent, read-only reference)

## Related Code Areas
- .github/workflows/test.yml
- tests/static/test_ci_narrow_path_filtered_jobs.py
- docs/testing/migration_ci_lanes.md

## Assumptions / Open Questions
- Whether `frontend/` alone is a sufficiently complete trigger set, or whether some root-level
  config (e.g. a future shared lint config) could also affect the Frontend job without living
  under `frontend/` — not currently the case (confirmed: no such file exists today), flagged for
  whoever next adds one to also update `FRONTEND_RE`.

## Implementation Notes
Extended the existing `changed-files` gate job (`TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS`) with
a third output, `run_frontend`, and a `FRONTEND_RE='^(frontend/|\.github/workflows/test\.yml$)'`
trigger set — mirroring the existing `PERF_RE`/`MIG_RE` fail-open shape byte-for-byte (both
branches force `run_frontend=true` alongside the 2 existing outputs). Added `needs:
[changed-files]` and the standard `if: ${{ !cancelled() && (needs.changed-files.result !=
'success' || needs.changed-files.outputs.run_frontend == 'true') }}` to the `frontend` job.
Confirmed via direct inspection (`frontend/package.json`'s `build` script, a grep for
`from src.`/Python-file reads under `frontend/src/`) that this job has zero cross-toolchain
dependency risk — unlike the 9 Python jobs the parent ticket explicitly rejected for
path-filtering, there is no shared import graph that could cause a false-negative skip.
Extended `tests/static/test_ci_narrow_path_filtered_jobs.py`'s 11 existing static guards to also
cover `frontend` (tests 1, 5c new, 6, 7, 10) plus one new test (12) asserting `FRONTEND_RE`
covers both `frontend/` and the workflow file — no live-import derivation needed (unlike tests
8/9's Python-import re-derivation) since `frontend/`'s dependency set is definitionally itself.
Updated `docs/testing/migration_ci_lanes.md`'s "Path-Based Skip Condition (CI)" section with a
new bullet. `_OUT_OF_SCOPE_JOBS` (the 9 Python jobs) and the `perf-cert-arena`/`migration-lanes`
mechanisms were left completely untouched.

## Test Summary
`pytest tests/static/test_ci_narrow_path_filtered_jobs.py -v` → 14 passed (11 existing + 3 new).
`pytest tests/architecture tests/docs tests/integrity tests/static tests/refactor -m "not slow
and not extra_slow" -q` (the exact `arch-docs` CI command) → 221 passed, 2 skipped, 1 deselected,
2 xfailed (pre-existing). `python3 -c "import yaml; yaml.safe_load(...)"` parses
`.github/workflows/test.yml` cleanly. `git diff --stat -- .github/workflows/test.yml` confirms a
clean, additive-only 12-insertion/1-deletion diff. Live-CI verification: this PR itself touches
`.github/workflows/test.yml`, so the `frontend` job must run in full on its own CI run (positive
trigger observation); a real "skip" observation on an unrelated-file-only PR is left as a
follow-up (matching the parent ticket's own precedent).

## Files Changed
- `.github/workflows/test.yml` — new `run_frontend` gate output/regex; `frontend` job gains
  `needs`/`if`.
- `tests/static/test_ci_narrow_path_filtered_jobs.py` — extended tests 1/5c(new)/6/7/10, added
  test 12.
- `docs/testing/migration_ci_lanes.md` — new bullet documenting the third gated job.
- `staging_artifacts/TCK-20260906-CI-FRONTEND-PATH-FILTER/{investigation,plan,test_plan}.md`
  (new).

## Completion Summary
Extended `TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS`'s changed-files path-filter gate mechanism
to a third job, `frontend`, which that prior ticket's own scoping decision never considered (its
Out of Scope list enumerates exactly 9 Python jobs plus the 2 it gated — 11 total — and
`frontend` wasn't among them). Confirmed `frontend` is a strictly safer path-filter candidate
than even the 2 already-gated jobs: it's a fully separate TypeScript/npm toolchain with zero
Python import-graph overlap, so none of the false-negative risk that ruled out the other 9 jobs
applies. Implementation mirrors the existing mechanism's exact shape (fail-open on non-PR
events, diff failures, and gate-job non-success) with zero changes to the 2 existing gated jobs
or the 9 out-of-scope jobs. All acceptance criteria met via static verification; live-CI skip
confirmation on an unrelated-file-only PR remains a follow-up observation, consistent with the
parent ticket's own precedent.
