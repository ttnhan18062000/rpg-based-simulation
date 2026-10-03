---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260906-CI-FRONTEND-PATH-FILTER
artifact_type: investigation
tags: [testing]
---

# Investigation — TCK-20260906-CI-FRONTEND-PATH-FILTER

## Existing mechanism (`.github/workflows/test.yml`, `TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS`)

A `changed-files` gate job runs unconditionally (no `if:` of its own — a gate job that could
itself be skipped would cascade-skip its downstream jobs via the `needs`-success mechanism). On
`pull_request` events it does a three-dot `git diff --name-only "$BASE...$HEAD"` and sets two
boolean outputs (`run_perf_cert_arena`, `run_migration_lanes`) via hand-rolled regex matches
(`PERF_RE`, `MIG_RE`) against the changed-file list. On any other event type, or if the diff
command itself fails, both outputs are forced `true` (fail-open). `perf-cert-arena` and
`migration-lanes` each carry a job-level `if:` referencing their own output, ORed with
`needs.changed-files.result != 'success'` (so a gate-job failure also fails open) and
`!cancelled()`.

`tests/static/test_ci_narrow_path_filtered_jobs.py` (11 tests) statically guards this shape by
parsing the workflow YAML — no live Actions execution, matching the
`test_corpus_diversity_ci_isolation.py` precedent. Notably, `test_no_other_fast_lane_job_gained_an_if_condition`
hard-codes a 9-job `_OUT_OF_SCOPE_JOBS` list (unit-core-world, unit-gameplay, unit-infra,
integration, api-tools, agent-orchestration, simulation-quality, arch-docs, typecheck) and asserts
none of them gained an `if:`. **`frontend` is not in this list** — confirmed via direct read of
both the test file and the parent ticket's own Out of Scope section (`tickets/done/
TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS.md`), which explicitly enumerates the same 9 jobs and
no others. This is not an oversight in the sense of "should have been included but wasn't caught"
— the parent ticket's own Request Summary describes the job list as "all 11 fast-lane jobs," and
9 (out-of-scope) + 2 (gated) = 11, meaning `frontend` was not counted among the 11 jobs the
scoping decision was made over at all at that time.

## Why `frontend` is safe where the 9 Python jobs were not

The parent ticket's own rejection rationale for the 9 Python jobs: "widely-imported modules
(`src/core/state.py`, `src/engine/kernel.py`, etc.) can affect nearly every job's target directory
in ways a naive path filter would miss — a false-negative... is a worse failure mode here than the
CI-minutes cost." This rationale is about Python's import graph specifically.

`frontend`'s job steps (`.github/workflows/test.yml`): `actions/setup-node@v4` (node-version 20),
`cd frontend && npm ci`, `npx vitest run`, `npm run build`. Confirmed via direct read of
`frontend/package.json`: `"build": "tsc -b && vite build"` — no codegen step, no invocation of any
Python tool, no read of any `src/` file. `npx vitest run` executes only `frontend/src/**/*.test.*`
(TypeScript/React), which import only other `frontend/src/` modules — confirmed no
`from src.` or backend-file read exists anywhere under `frontend/` via
`grep -rn "from src\.\|open(.*\.py" frontend/src/` (no matches). The repo-root `package.json`
(`graphology`/`graphology-layout`/`graphology-layout-forceatlas2`/`sigma`) is a separate,
unrelated dependency set used by `graphify-out/` visualization tooling — confirmed not referenced
by any step in the `frontend` job (no `npm ci`/`npm install` at repo root anywhere in that job).

Conclusion: a Python-only or docs-only change genuinely cannot affect `frontend`'s test/build
outcome — there is no cross-toolchain import graph to create a false-negative, unlike the 9
Python jobs. This makes `frontend` a strictly safer path-filter candidate than the 2 jobs already
gated (`perf-cert-arena`/`migration-lanes`, which are Python jobs subject to the same
same-language import-graph risk the other 9 were rejected for, just narrower/more isolated).

## Trigger path set

`frontend/` (the entire directory — the job's only real dependency) plus
`.github/workflows/test.yml` itself (matching the existing `PERF_RE`/`MIG_RE` convention: editing
the workflow file must always re-run every gated job, since the job's own definition could have
changed). No other repo path affects this job's outcome — confirmed above.

## Decision

Extend the existing `changed-files` gate mechanism with a third output, `run_frontend`, and a
third gated job-level `if:` on `frontend`, mirroring the exact existing pattern byte-for-byte
(fail-open branches, `!cancelled()`, `needs.changed-files.result != 'success'` OR-clause). No new
mechanism invented; no change to the 2 existing gated jobs or the 9 explicitly out-of-scope jobs.
