---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS
artifact_type: test_plan
date: 2026-10-19
tags: [testing, workflows, performance]
---

# Test plan — TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS

| AC | proof |
|---|---|
| AC1 | investigation.md, per-job audit |
| AC2 | collect-only counts before/after per job (Integration 1083, Tools f–z 3494, API 2780; visual_assets 1222 + 1329 = 2551) quoted in the ticket; CI Job summary "New vs existing" |
| AC3 | three consecutive green CI runs per job on the PR (re-runs); run ids quoted |
| AC4 | median wall time of the three jobs over those runs vs 8.4 / 6.7 / 6.3 min; target slowest <= 5 min; shortfall reported |
| AC5 | `tests/static/test_ci_xdist_in_critical_path_jobs.py::test_the_job_count_does_not_grow` |
| AC6 | fyi sent to agent-working-planner; reply recorded |
| AC7 | lead-planner-u24 comment link recorded |
