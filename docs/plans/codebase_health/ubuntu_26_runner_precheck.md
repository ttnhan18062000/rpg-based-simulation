---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-09
tags: [architecture, delivery]
---

# Ubuntu 26.04 runner pre-check for `test.yml`

Ticket `TCK-20261009-UBUNTU-26-RUNNER-PRECHECK`. `ubuntu-latest` begins migrating to Ubuntu 26.04 on 2026-10-19 and
rolls out over 2026-10-19 to 2026-11-19 (actions/runner-images issue 14748; main's own annotations say "will migrate
to Ubuntu 26 beginning October 19, 2026"). All 26 `runs-on` entries in `.github/workflows/` are `ubuntu-latest`
(`test.yml` 21, `slow-regression.yml` 2, `deploy-docs.yml`, `pr-body-lint.yml`, `slow-regression-watchdog.yml` 1 each).
Before this, only `Code health` and `Type check` had run on `ubuntu-26.04` (PR #331, both passed; see
`python_code_craft_gates_soak_review.md`).

## Recommendation

**No pin.** Every job of `test.yml` that ran on `ubuntu-26.04` ended as it does on main, except one static test that
fails only because the probe edited the line it pins (a probe artifact, below). Let `ubuntu-latest` migrate. Re-check
main's first `test.yml` runs after 2026-10-19 (and again while the rollout runs to 2026-11-19, since the label may
resolve to either image in between).

If a job fails after the rollout, pin only that job to `ubuntu-24.04` with a comment naming the ticket and a dated exit.
No pin is added in this batch and none is named here, because no job needs one.

## Method

- Probe: throwaway draft PR #477 (never merged), branch `ci-runner-26-probe` at `a5ce529e7`, based on `0c3a5654b`. It
  changes only the 21 `runs-on: ubuntu-latest` lines of `test.yml` to `ubuntu-26.04`. The runner image in the logs is
  `ubuntu-26.04`, version 20260901.588, image release `ubuntu26/20260927.149`.
- Baseline: main's `test.yml` run on the same sha, which was all green. The probe run: https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/37959405085 .
  Baseline run: https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/37955084870 (image `ubuntu-24.04`, version 20261002.596).
- Every job's conclusion, every step's conclusion (so a `continue-on-error` step that failed under a green job would
  show), the annotations of both runs, and durations were read through the Actions API.

## Per-job table

| Job | main on 24.04 | probe on 26.04 | Cause of any difference |
|---|---|---|---|
| Changed files (path-filter gate) | success | success | none |
| Registry re-sync gate | success | success | none |
| Code health | success | success | none |
| Type check | success | success | none |
| Code health SARIF (advisory) | skipped | success | not a 26.04 difference: the job is `pull_request`-only and main's run is a push. Every step that ran succeeded and only the "paths unavailable" report step was skipped (the SARIF step and the upload step both ran), so it is read as passed, not as an unread green |
| Architecture / docs / static | success | **failure** | probe artifact, see below; the run was 1 failed, 321 passed, 3 skipped, 1 deselected, 2 xfailed |
| Tools · a–e | success | success | none |
| Tools · f–z | success | success | none |
| Unit · core / world | success | success | none |
| Unit · gameplay | success | success | none |
| Unit · infra / observability | success | success | none |
| API / CLI / engine / logging | success | success | none |
| Agent orchestration / codex / replay | success | success | none |
| Simulation quality | success | success | none |
| Integration | success | success | none (slower, see Timing) |
| Perf / cert / arena | success | success | none |
| Migration lanes | success | success | none |
| Frontend | success | success | none (Node 20 deprecation warnings appear on both runs) |
| Backend image build | success | success | none; `docker build --check` reported "Check complete, no warnings found" |
| SimQ grade-anchor drift (informational) | success | skipped | not checked on 26.04: the job runs only on a push to main, and the probe is a pull request. Its 24.04 result was not repeated on 26.04 |
| Scenario lane | skipped | skipped | not checked, same on both: its `if` needs `run_scenario_lane` true and `run_perf_cert_arena` not true, and `Perf / cert / arena` ran on the probe (so `run_perf_cert_arena` was true: the PR changes `test.yml`), which suppresses the lane |

The path-gated jobs (`Perf / cert / arena`, `Migration lanes`, `Frontend`, `Backend image build`) all ran on the probe
because the PR changes `test.yml`, which every gate matches; none was skipped. `SimQ grade-anchor drift` and
`Scenario lane` are the two jobs this probe did not exercise on 26.04.

### The one failure: a probe artifact

`tests/static/test_ci_step_summary_reporting.py::test_slow_and_migration_lanes_jobs_unchanged_by_this_ticket` compares
the `migration-lanes` job to an expected dict that contains `runs-on: ubuntu-latest`; the assertion diff shows exactly
`ubuntu-26.04` against `ubuntu-latest`. It is not a 26.04 behavior. It disappears when the label is `ubuntu-latest`
(main), and the job's other 321 tests passed. After the rollout `runs-on` stays `ubuntu-latest`, so this test is
unaffected by the migration; it would matter only if a job were pinned to `ubuntu-24.04` (the pin would need this
expected dict updated, a testing-owned file under decision 8.11).

## Other differences

- **Annotations.** The 19 "ubuntu-latest label will migrate to Ubuntu 26" notices on main are the only annotation main
  has beyond the shared Node.js 20 deprecation warnings (`setup-node@v4`, `upload-artifact@v4`, same on both runs). The probe has
  no migration notices (it already uses the new label), plus 9 warnings from `setup-uv`: "Failed to save: Unable to
  reserve cache with key setup-uv-2-x86_64-unknown-linux-gnu-ubuntu-26.04-3.13-…, another job may be creating this
  cache". The cache key contains the OS version, so the first run on 26.04 has no cache and many jobs try to save the
  same key at once; no job failed on it. Expect the same on the first runs after the rollout; it is a cold-cache
  effect, read from the key, not from a measured cause.
- **Timing (one sample per job, not a cause).** Most jobs are within a few seconds to tens of seconds of main's run.
  `Integration` took 540 s against 363 s on main; one re-run of that job gave 534 s, so it repeats on 26.04. Main's own
  recent runs for that job span 349 to 521 s (five runs, 24.04), so the probe is above that range by a small margin.
  `Backend image build` took 47 s against 24 to 32 s on main. I did not decompose either; no pass/fail consequence.
  If `Integration` approaches a timeout after the rollout, look at it then.

## Not probed

- `slow-regression.yml`: can be dispatched (`workflow_dispatch`), but it is a roughly two-runner-hour job with
  `issues: write`, so dispatching it from a throwaway branch has side effects. Not dispatched.
- `slow-regression-watchdog.yml`: its dispatch runs `gh workflow run slow-regression.yml --ref main`, which starts the
  slow regression on main. Not dispatched.
- `deploy-docs.yml`: Pages is not enabled and it deploys; never dispatched, as specified.
- `pr-body-lint.yml`: a `pull_request` workflow that still runs on `ubuntu-latest` (the probe did not change it); it
  passed on the probe PR, which says nothing about 26.04.

These four hold 5 of the 26 `ubuntu-latest` entries. They are plain steps (`gh`, `actions/checkout`, shell), but that
is a reading of the files, not a measurement; they are checked by their first scheduled runs after 2026-10-19.

## Follow-ups (not done here)

- After 2026-10-19: read main's first `test.yml` runs, `slow-regression` and the watchdog, and note the image each
  reports.
- The probe PR #477 is closed; its branch is kept until the owner says to delete it.
