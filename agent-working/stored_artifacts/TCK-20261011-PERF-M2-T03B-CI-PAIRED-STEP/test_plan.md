---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261011-PERF-M2-T03B-CI-PAIRED-STEP
date: 2026-10-12
tags: [performance, benchmarking, testing, regression]
---

# Test plan: TCK-20261011-PERF-M2-T03B-CI-PAIRED-STEP

`tests/static/test_ci_perf_tripwire_step.py` (workflow shape), `tests/unit/perf/test_tripwire.py` (provenance, summary table, `main` exits 0 on a REGRESSION and writes the summary). A real local paired run and the CI runs of this PR show the live behaviour.
