---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261019-CI-RUNTIME-EPIC
phase: open
date: 2026-10-19
tags: [testing, workflows, performance]
---

# Investigation: CI runtime baseline (7 days to 2026-10-19)

Measured by testing-planner on 2026-10-19, after the user asked whether the effective CI runtime is large.

## Method
- **Runs:** `gh api --paginate 'repos/{owner}/{repo}/actions/runs?per_page=100&created=>=2026-10-12&status=completed'` returned 706 runs across all workflows. Dependabot update runs were pooled as one group.
- **Jobs:** `gh api --paginate 'repos/{owner}/{repo}/actions/runs/<id>/jobs?per_page=100&filter=latest'` returned 6,063 jobs.
  - Runner time per job = `completed_at - started_at`. Jobs with no timestamps (skipped) count 0.
  - Runner-minutes per run = the sum over its jobs. Wall time per run = `updated_at - run_started_at`.
- **Queue:** `started_at - created_at` per job, over 1,038 non-skipped jobs in the Tests runs created on or after 2026-10-16.
- **Steps:** step durations from one successful main push (run 39189031425), split into setup (set up job, checkout, setup-uv, uv sync, post steps) and work.
- **Trend:** median wall time of successful `pull_request` runs of test.yml per ISO week, for W36-W43.
- The runner image was `ubuntu-latest` before the Ubuntu 26 rollout (which starts 2026-10-19). Child 2 re-takes its baseline after the shift.

## Results
| Workflow | Runs | Runner-min (7 days) | Median wall/run | Median runner-min/run | p90 runner-min/run |
|---|---|---|---|---|---|
| Tests (test.yml) | 264 | 11,323 | 9.5 | 43.9 | 55.3 |
| Slow regression | 26 | 1,998 | 111.3 | 110.7 | 120.2 |
| publish-images | 99 | 244 | 1.7 | 2.4 | 3.1 |
| Dependabot updates | 27 | 93 | 2.8 | 2.7 | 8.1 |
| PR body lint | 241 | 21 | 0.1 | 0.1 | 0.1 |
| Slow regression watchdog | 37 | 6 | 0.2 | 0.1 | 0.2 |
| iac | 3 | 5 | 0.5 | 1.5 | 1.6 |
| RPG gate report | 9 | 3 | 0.5 | 0.3 | 0.4 |
| **Total** | 706 | **13,692 (228 h)** | | | |

Tests jobs, ranked by total time:

| Job | Runs | Median min | p90 min | Total min |
|---|---|---|---|---|
| Integration | 245 | 8.4 | 9.5 | 1,932 |
| Tools · f–z | 260 | 6.7 | 7.2 | 1,637 |
| API / CLI / engine / logging | 246 | 6.3 | 7.4 | 1,491 |
| Unit · infra / observability | 246 | 3.9 | 4.3 | 906 |
| Tools · a–e | 260 | 3.5 | 3.7 | 850 |
| Unit · core / world | 246 | 3.3 | 3.6 | 768 |
| SimQ grade-anchor drift (informational) | 78 | 10.3 | 11.4 | 714 |
| Perf / cert / arena | 135 | 4.2 | 4.5 | 516 |
| Architecture / docs / static | 260 | 1.5 | 1.6 | 374 |
| Migration lanes | 139 | 2.2 | 2.5 | 291 |
| Code health | 260 | 0.8 | 2.2 | 289 |
| Unit · gameplay | 245 | 1.1 | 1.3 | 264 |
| Changed files gate | 260 | 0.5 | 1.9 | 213 |
| Code health SARIF | 182 | 0.8 | 2.1 | 198 |
| Simulation quality | 245 | 0.7 | 0.8 | 176 |
| Scenario lane | 67 | 2.9 | 3.0 | 169 |
| Agent orchestration | 246 | 0.7 | 0.8 | 169 |
| Type check | 260 | 0.6 | 0.7 | 150 |
| Frontend | 110 | 0.8 | 0.9 | 82 |
| Registry re-sync gate | 260 | 0.3 | 0.3 | 70 |
| Backend image build | 122 | 0.5 | 0.6 | 62 |

Tests runner-hours by event and outcome:

| Event | Success | Failure | Cancelled |
|---|---|---|---|
| pull_request | 86.6 | 28.2 | 6.1 |
| push (all to main) | 39.9 | 12.7 | 5.4 |
| schedule | 4.7 | 0.9 | 0.8 |
| workflow_dispatch | 2.0 | 1.2 | — |

- 70 pushes to main used about 58 h, 31% of Tests.
- Cancelled runs used about 12 h.

**Queue:** median 2 s, p90 13 s, max 129 s. **Setup:** about 11% of job time (checkout 3.1 min, setup-uv 1.4 min, uv sync 0.2 min across all jobs of one run).

**Trend** (median wall, successful PR runs):

| Week | W36 | W37 | W38 | W39 | W40 | W41 | W42 |
|---|---|---|---|---|---|---|---|
| Median wall (min) | 8.0 | 6.3 | 7.0 | 7.5 | 7.1 | 7.8 | 9.2 |

**Context:** the repo is public, so standard runners cost nothing. The free plan allows 20 concurrent jobs, and Tests starts 21. No job uses pytest-xdist.

## Conclusions
- The cost is the PR feedback wait, which is growing, not money or queueing. The critical path is Integration, Tools f–z and API (child 1).
- Growth went unseen (child 2).
- Main pushes spend about 31% of Tests time. Most of it is the post-merge safety net and stays; the informational drift job is the trim candidate (child 3).
