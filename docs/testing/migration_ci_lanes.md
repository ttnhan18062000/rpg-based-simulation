---
status: active
layer: testing
authority: P1
audience: developer
---

# Migration CI Lanes

**Status:** Active  
**Last updated:** 2026-08-19  
**Relates to:** docs/testing/content_migration_test_ownership.md, docs/testing/test_taxonomy.md

This document defines six CI test lanes for targeted execution of content migration tests.
Each lane maps to a set of pytest markers and a Makefile target.

---

## Lane Definitions

| Lane | Makefile target | Marker expression | Speed | Selects |
|---|---|---|---|---|
| Catalog | `make lane-catalog` | `catalog or content_graph` | Fast (<10s) | Schema tests, adapter heuristics, reference graph, active-data-consumer gate |
| World Assembly | `make lane-worldassembly` | `worldassembly and not strict_matrix` | Fast (<30s) | Module normalizers, composition assembly, provenance, archetype preservation |
| Runtime Projection | `make lane-runtime` | `registry_projection or scenario_setup` | Fast (<10s) | Registry bootstrap modes, scenario schema/resolver/modifier |
| Strict Matrix | `make lane-strict-matrix` | `strict_matrix` | Medium (1–3min) | Cumulative world module matrix; end-to-end content builds |
| Legacy Regression | `make lane-legacy-regression` | `legacy_compat` | Slow (5–15min) | Arena simulation runs, certification gates, legacy compat |
| Architecture | `make lane-architecture` | `architecture` | Fast (<5s) | Static guards: import boundaries, hardcoded gameplay ID scan |
| All Fast | `make lane-all-fast` | `(catalog or content_graph or worldassembly or registry_projection or scenario_setup or architecture) and not strict_matrix and not slow` | Fast (<60s) | All fast migration lanes combined |

---

## Lane Isolation Rules

**Fast lanes must not include slow tests:**
- `lane-catalog`, `lane-runtime`, `lane-worldassembly`, `lane-architecture` must stay under 60s total.
- If a new test in these lanes causes slowdown, move it to `lane-strict-matrix` or `lane-legacy-regression`.

**Strict matrix is separate from fast worldassembly:**
- `lane-worldassembly` excludes `strict_matrix` tests — these are medium-speed and run separately.
- This prevents the fast assembly feedback loop from being blocked by slower matrix builds.

**Legacy regression is always isolated:**
- `lane-legacy-regression` always runs separately. Never add unit tests to `legacy_compat`.
- Arena and certification tests must remain marked `slow` to prevent accidental inclusion in fast loops.

---

## Recommended CI Pipeline Order

```
1. lane-catalog        (fast, unblocks catalog-related changes)
2. lane-runtime        (fast, unblocks bootstrap/scenario changes)  
3. lane-architecture   (fast, static guards)
4. lane-worldassembly  (fast, unblocks assembly changes)
5. lane-strict-matrix  (medium, validates full content builds)
6. lane-legacy-regression  (slow, full regression; runs on PR merge or scheduled)
```

---

## Path-Based Skip Condition (CI)

**TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS:** the `migration-lanes` CI job (`.github/workflows/test.yml`)
now carries a job-level `if:` gated on an upstream `changed-files` job's `run_migration_lanes`
output. This applies only to `pull_request` events — on `push` to `main`, the nightly `schedule`,
and `workflow_dispatch`, `migration-lanes` always runs unconditionally, exactly as before.

On a pull request, the `changed-files` gate job computes a three-dot `git diff` (`$BASE...$HEAD`)
between the PR's base and head commits and matches the changed paths against the following
trigger set. If none of the changed paths match, `migration-lanes` reports a skipped (no-op
success) conclusion instead of running `make lane-all-fast` / `make gate-expansion`:

```
tests/architecture/**
tests/integration/content/**
tests/integration/scenarios/**
tests/integration/worldassembly/**
tests/integration/certification/**
tests/integration/runtime/**
tests/unit/certification/**
tests/unit/content/**
tests/unit/runtime/**
tests/unit/scenarios/**
tests/unit/worldassembly/**
tests/conftest.py
src/core/**
src/content/**
src/runtime/**
src/scenarios/**
src/worldassembly/**
src/worldbuilding/**
src/worldmodules/**
src/certification/**
Makefile
requirements.txt
pyproject.toml
uv.lock
.github/workflows/test.yml
```

`pyproject.toml` and `uv.lock` are on the list because dependencies are declared there (`requirements.txt` is a
generated export of the lock). A side effect: any `pyproject.toml` edit, including tool configuration such as
ruff settings, now also triggers `migration-lanes` and `perf-cert-arena`. That cost was accepted
(`TCK-20261002-UV-REMAINING-CI-JOBS`).

Note: the workflow's regex builds this list as a cross product across
`tests/(integration|unit)/(content|scenarios|worldassembly|certification|runtime)/` — it also
matches `tests/integration/certification/**` and `tests/integration/runtime/**`, even though no
marker-tagged test files currently live in those two combinations (the real dependency set found
during investigation only populated 8 of these 10 slots). This is intentionally over-inclusive,
not a bug: it can only ever bias the job toward running, never toward a false-negative skip, so
it was left as-is rather than narrowed to an exact 1:1 match with today's file layout.

The mechanism fails safe: a non-`pull_request` event, a `git diff` command failure, or the
`changed-files` gate job itself concluding non-`success` all force `migration-lanes` to run
rather than skip. See `tests/static/test_ci_narrow_path_filtered_jobs.py` for the static
verification of this behavior.

`perf-cert-arena` has an analogous, independently-computed skip condition (its own trigger path
set, scoped to `tests/perf/`, `tests/certification/`, `tests/arena/`, and the `src/` dirs those
suites import) — see the `changed-files` job in `.github/workflows/test.yml` for the full detail;
it is CI plumbing shared across both jobs, not migration-lane-specific, so it is not duplicated
here.

**TCK-20260906-CI-FRONTEND-PATH-FILTER:** the `frontend` job (npm install/vitest/build) carries
the same `changed-files`-gated `if:` shape, via its own `run_frontend` output. Its trigger path
set is much simpler than the other two — `frontend/**` plus `.github/workflows/test.yml` — since
`frontend/` is a fully separate TypeScript/npm toolchain with no Python import graph to derive
coverage from (unlike `perf-cert-arena`/`migration-lanes`, whose trigger sets are re-derived live
from what `src/` dirs their tests actually import). Same fail-open guarantees apply.

### Registry re-sync skip (`TCK-20261005-CI-SKIP-HEAVY-JOBS-ON-REGISTRY-ONLY-RESYNC`)

The path-based skips above compare the whole PR with its base, so they cannot tell what the *latest push*
changed. A PR that goes CONFLICTING on `docs/REGISTRY.yaml` alone is fixed by a sync merge from `main` plus a
regenerated REGISTRY, which reran every job although the PR's own code was identical. The `resync-gate` job
(`tools/test_architecture/registry_resync_skip.py`) now answers one question, `pr_content_unchanged`, and
`true` makes the jobs below skip. Owner direction 2026-10-05: "skip if the previous commit passed".

`pr_content_unchanged` is `true` only when ALL hold; anything else, any error or missing data is `false` and
everything runs:

1. The event is `pull_request` / `synchronize` and `github.event.before` exists in the clone (a force-push or
   rebase can drop it).
2. The PR's own patch, ignoring `docs/REGISTRY.yaml`, has the same `git patch-id --stable` before and after
   (diff from `merge-base(base, commit)` to the commit). If `main` changed lines next to the PR's lines the
   context differs and the answer is `false`; that is deliberate.
3. Every `Tests` workflow run on the BEFORE commit has completed and every job in it is `success`, `skipped` or
   `neutral`. A failure, a cancellation (a concurrency-group cancel included), a timeout, a run still in
   progress, no run, or an API error gives `false`. Read through the Actions runs/jobs REST API (`actions: read`),
   not `commits/{sha}/check-runs`, because a check run does not name its workflow. A chain of re-syncs is fine:
   each push compares with its own BEFORE, itself green or validly skipped.

The job summary names the rule that decided and the BEFORE SHA it compared against.

**Which jobs skip, and why.** A job skips only if its result depends on nothing but the PR content. Which tests
read the *real* `docs/REGISTRY.yaml` was measured, not guessed: a Python audit hook (`sys.addaudithook`,
`open` events, injected into every process and subprocess through `sitecustomize`, tagged with
`PYTEST_CURRENT_TEST`) ran each job's pytest scope on 2026-10-05 at `origin/main` `9bf34765b`, with a positive
control that logged a known read. Result: every real read is in `tests/tools/` or `tests/codebase/` (for example
`test_generate_registry.py::TestRealDocsTree`, `test_premise_staleness_check.py`, `test_post_native_run_check.py`,
`test_registry_query.py`, `test_tools_orphan_check.py`, `test_codebase_health_baseline.py`,
`test_codebase_health_snapshot.py`). `tests/integrity/test_registry_merge_driver.py` and the other test files that
name the file read a temp copy or a fixture (none logged a real read). The audit covers pytest only: the Makefile
targets that `arch-docs` and `code-health` run outside pytest were not audited, which is one more reason those
two jobs keep running.

| Job | Skips | Measured duration (3 PR runs, s) | Reason |
|---|---|---|---|
| Unit · core / world | yes | 134, 113, 130 | no real REGISTRY read |
| Unit · gameplay | yes | 42, 41, 38 | no real read |
| Unit · infra / observability | yes | 201, 163, 163 | no real read (`tests/unit/tools`, `tests/unit/docs` use fixtures) |
| Integration | yes | 408, 419, 349 | no real read |
| API / CLI / engine / logging | yes | 170, 174, 197 | no real read |
| Agent orchestration / codex / replay | yes | 42, 43, 41 | no real read |
| Simulation quality | yes | 36, 39, 47 | no real read |
| Perf / cert / arena, Migration lanes, Scenario lane, Frontend | yes, on top of their own path rule | 113, 123, 28 (Frontend about 2) | no real read |
| Tools · a–e, Tools · f–z | **no** | 195/197/160, 225/258/265 | hold the real readers |
| Architecture / docs / static | **no** | 74, 72, 63 | the cheap docs/registry checks; kept on purpose |
| Type check, Code health (+ SARIF) | **no** | 34, 133, 118 | lint-class; code-health reads the registry |

Skipped runner time is about 1,270 job-seconds (about 21 minutes) per re-sync push; wall time barely moves, since
the jobs ran in parallel and the longest one, Integration, is about 7 minutes. `resync-gate` is its own job, not
a step in `changed-files`, so the heavy jobs do not wait for that gate's full clone; its own duration is
recorded in the live-run evidence in `TCK-20261005-CI-SKIP-HEAVY-JOBS-ON-REGISTRY-ONLY-RESYNC`.

**Accepted risk (owner-accepted 2026-10-05).** On a skipped re-sync the PR's code combined with the new `main`
commits is **not tested before merge**. A clash between them surfaces on the full post-merge run on `main`, which
always runs everything (the event is `push`, not `pull_request`). A skipped job is not a blocking failure either
way: branch protection on `main` is disabled.

---

## Running Locally

```bash
# Fast feedback during development
make lane-catalog
make lane-runtime
make lane-architecture

# Before opening a PR touching world modules
make lane-worldassembly
make lane-strict-matrix

# Full regression (pre-merge)
make lane-legacy-regression

# Everything fast at once
make lane-all-fast
```

---

## Adding a New Lane

1. Add a new pytest marker to `pyproject.toml` (see TCK-20260609-MIGRATION-TEST-MARKERS pattern).
2. Apply the marker to relevant test files.
3. Add a Makefile target with the `lane-` prefix and a `## [speed]` comment.
4. Add the lane to this document.
5. Decide whether it belongs in `lane-all-fast` (must be fast).

---

## Test Count Reference (as of 2026-06-09)

| Lane | Tests selected |
|---|---|
| catalog | 15 |
| worldassembly (excl. strict_matrix) | 52 |
| strict_matrix | 57 |
| runtime | 46 |
| legacy_compat | 40 |
| architecture | 5 |
| all-fast | 118 |
