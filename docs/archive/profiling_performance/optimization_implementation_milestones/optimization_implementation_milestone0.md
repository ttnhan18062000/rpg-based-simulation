# Milestone 0 — Baseline Performance Measurement

## Objective

Before changing engine behavior, measure current limits.

You need to know:

```text
How many entities can the engine handle now?
Which phase is slow?
How much memory is used?
Does memory grow over time?
Does concurrency help or hurt?
```

## Technical tasks

### 0.1 Add performance profiles

Create:

```text
src/perf/profiles.py
```

Profiles:

```text
PERF_512MB_LOCAL
PERF_1GB_LOCAL
PERF_2GB_LOCAL
PERF_4GB_LOCAL

PERF_512MB_CONC
PERF_1GB_CONC
PERF_2GB_CONC
PERF_4GB_CONC
```

Each profile controls:

```text
max_ram_mb
max_worker_count
max_tick_budget_ms
max_queue_depth
max_replay_buffer_kb
max_observability_budget_percent
```

Recommended starting values:

```text
512 MB, 1 GB, 2 GB, 4 GB
workers: 0 and 4
tick budget: 50 ms
queue depth: 1000
replay buffer: 8 MB
```

---

### 0.2 Add benchmark scenarios

Create:

```text
src/perf/scenarios.py
```

Scenario builders:

```text
build_idle_state(entity_count)
build_movement_state(entity_count)
build_combat_state(team_size)
build_resource_state(entity_count, node_count)
build_strategic_state(entity_count)
build_mixed_state(entity_count)
```

Start with only:

```text
idle
resource-heavy
mixed
```

Then add the rest.

---

### 0.3 Enhance `BenchHarness`

Current `BenchHarness` already measures basic tick performance.

Enhance it to collect:

```text
avg_tick_compute_ms
p50_tick_compute_ms
p95_tick_compute_ms
p99_tick_compute_ms
max_tick_compute_ms
avg_tps
peak_rss_mb
memory_delta_mb
memory_trend_mb_per_tick
phase_breakdown
worker_utilization
queue_utilization
replay_backlog_kb
```

Important:

```text
BenchHarness should only measure.
It should not decide pass/fail.
```

---

### 0.4 Add `tests/perf`

Create:

```text
tests/perf/
  conftest.py
  test_perf_idle.py
  test_perf_resource.py
  test_perf_mixed.py
  test_perf_api_snapshot.py
```

Mark all tests:

```python
@pytest.mark.perf
```

Do not run them with normal unit tests.

Run separately:

```bash
pytest tests/perf -m perf -q
```

---

## Exit criteria

You should have:

```text
reports/perf/latest.json
```

with numbers for:

```text
IDLE_100
IDLE_500
IDLE_1000
IDLE_5000
RESOURCE_1000
MIXED_1000
```

For each profile:

```text
512 MB
1 GB
2 GB
4 GB
```

---
