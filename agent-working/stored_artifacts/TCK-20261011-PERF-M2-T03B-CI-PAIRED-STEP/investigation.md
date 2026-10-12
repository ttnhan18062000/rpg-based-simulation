---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261011-PERF-M2-T03B-CI-PAIRED-STEP
date: 2026-10-12
tags: [performance, benchmarking, testing, regression]
---

# Investigation: TCK-20261011-PERF-M2-T03B-CI-PAIRED-STEP

- `workflow_dispatch` already exists on `test.yml`, so the CI-runner A/A calibration is a manual dispatch step, not a new trigger.
- The first dispatch's calibration went only to the step summary, which the API cannot read; a second step uploads the JSON as an artifact.
- Job p95: 11 successful pull_request runs of `Perf / cert / arena`, 161-262 s.
