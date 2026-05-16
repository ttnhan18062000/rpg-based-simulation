# Milestone 9 — CI Performance Regression Guard

## Objective

Prevent future performance regression.

---

## Technical tasks

### 9.1 Add baseline file

```text
reports/perf/baseline.json
```

Contains:

```text
scenario_id
profile
p95_tick_compute_ms
peak_rss_mb
memory_delta_mb
phase_breakdown
```

---

### 9.2 Add regression comparison

Tolerance:

```text
30% initially
15% later
```

Rules:

```text
p95 tick cannot regress > 30%
peak RSS cannot regress > 30%
memory delta cannot regress > 30%
```

---

### 9.3 Add CI job

Do not run on every commit first.

Run:

```text
nightly
manual
release candidate
```

GitLab example:

```yaml
perf_tests:
  stage: test
  rules:
    - if: '$RUN_PERF == "true"'
    - if: '$CI_PIPELINE_SOURCE == "schedule"'
  script:
    - pytest tests/perf -m perf -q
    - python scripts/run_perf_baseline.py
  artifacts:
    paths:
      - reports/perf/
```

---

## Exit criteria

Performance regression becomes visible before release.

---
