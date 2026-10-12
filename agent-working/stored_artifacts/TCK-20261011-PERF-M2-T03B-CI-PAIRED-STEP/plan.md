---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261011-PERF-M2-T03B-CI-PAIRED-STEP
date: 2026-10-12
tags: [performance, benchmarking, testing, regression]
---

# Plan: TCK-20261011-PERF-M2-T03B-CI-PAIRED-STEP

- Add to `perf-cert-arena`: `timeout-minutes: 15` (p95 262 s over 11 successful PR runs), a second `actions/checkout` at the PR base SHA under `perf-base/`, the paired step (`tripwire.py run --base perf-base --head . --summary "$GITHUB_STEP_SUMMARY"`), a `perf-tripwire` artifact, and a manual-dispatch calibration step plus artifact.
- `tripwire.py`: `provenance` (both SHAs and the CPU model), `summary_markdown`, `--summary`. `benchmark_record.cpu_model` becomes public (src/perf only).
- Report-only by construction: tripwire exits 0 for any outcome and 1 only when it cannot run; the step has no `continue-on-error`, so only infrastructure failures or the timeout fail the job.
- Shape test `tests/static/test_ci_perf_tripwire_step.py` pins the six conditions.
