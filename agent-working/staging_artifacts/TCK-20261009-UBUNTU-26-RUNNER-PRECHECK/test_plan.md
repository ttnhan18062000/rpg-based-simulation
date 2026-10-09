---
status: active
layer: architecture
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261009-UBUNTU-26-RUNNER-PRECHECK
phase: open
date: 2026-10-09
tags: [architecture, delivery]
---

# test_plan — TCK-20261009-UBUNTU-26-RUNNER-PRECHECK

Normal flow: the probe run finishes and every job is read; the doc's table has one row per job.
Edge: path-skipped jobs and advisory jobs (green whatever happens) are read by summary/annotation or marked "not checked".
Failure mode: a red job is classified 26.04 difference vs flake by one re-run; a probe-only artifact (a static test pinning `ubuntu-latest`) is labelled as such.
Regression: `git diff --stat` shows no `src/` or `tests/` path; the doc's frontmatter validates; the doc never says "switches".

## Proof Plan
- level: CI run on the probe branch plus doc validation
- proof kind: real GitHub runs read through `gh api` (jobs, steps, annotations), `tools/validate_frontmatter.py`
- oracle source: main's green run on the same base and the probe run's job records
- expected effect: each probe job result is explained against main's result
- selected commands: `gh run view`/`gh api repos/<r>/actions/runs/<id>/jobs`, `python3 tools/validate_frontmatter.py <doc>`
