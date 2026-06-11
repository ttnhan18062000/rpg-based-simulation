---
status: archive
authority: P2
audience: historical
layer: performance
original_date: unknown
---

# Milestone 10 — Tune Final Profiles

## Objective

After optimization, define production-ready profiles.

---

## Final profile examples

### Small profile

```text
RAM: 1 GB
Workers: 2
Target: up to 500 entities
Tick budget: 50 ms
```

### Normal profile

```text
RAM: 2 GB
Workers: 4
Target: 1000-2000 entities
Tick budget: 50 ms
```

### Large profile

```text
RAM: 4 GB
Workers: 4-8
Target: 5000+ entities with LOD
Tick budget: 50 ms
```

### Certification profile

```text
RAM: 4 GB
Workers: fixed
Replay: enabled
Observability: enabled
Tick budget: stricter
```

---

# Recommended execution order

Do not do all milestones at once.

Recommended order:

```text
Milestone 0: Baseline measurement
Milestone 1: Profile selection
Milestone 2: Cadence scheduling
Milestone 3: Dirty tracking
Milestone 4: Spatial indexing
Milestone 5: API/replay snapshot optimization
Milestone 6: Worker batching
Milestone 7: LOD
Milestone 8: ApplyPath optimization
Milestone 9: CI regression guard
Milestone 10: Final profile tuning
```

---

# First 3 implementation tasks to start now

## Task 1

Add:

```text
src/perf/profiles.py
src/perf/scenarios.py
```

With only:

```text
idle scenario
resource scenario
512MB / 1GB / 2GB / 4GB profiles
```

---

## Task 2

Enhance:

```text
src/perf/bench_harness.py
```

To output:

```text
p95
p99
max
RSS
memory delta
phase breakdown
```

---

## Task 3

Add:

```text
tests/perf/test_perf_idle.py
tests/perf/test_perf_api_snapshot.py
scripts/run_perf_baseline.py
```

Then run:

```bash
pytest tests/perf -m perf -q
python scripts/run_perf_baseline.py
```

After that, inspect `reports/perf/latest.json`.

That report decides whether you should optimize:

```text
strategic cadence
dirty tracking
spatial indexing
API snapshot
worker batching
ApplyPath
```

not guess.
