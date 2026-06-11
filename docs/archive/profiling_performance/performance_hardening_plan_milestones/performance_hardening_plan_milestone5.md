---
status: archive
authority: P2
audience: historical
layer: performance
original_date: unknown
---

# Milestone 5 — Clean Benchmark Matrix

## Goal

Replace scattered perf tests with a structured matrix.

Current perf tests cover idle, movement, resource, strategic, combat, and mixed scenarios, but profile usage is uneven and often uses local profiles only.  

## Matrix to implement

| Scenario  |            Entity scale | Local profiles    | Concurrent profiles | Metrics                          |
| --------- | ----------------------: | ----------------- | ------------------- | -------------------------------- |
| idle      |     100 / 1,000 / 5,000 | 512MB / 1GB / 2GB | 1GB / 2GB / 4GB     | compute p95, p99, memory         |
| movement  |       100 / 500 / 1,000 | 1GB / 2GB         | 2GB / 4GB           | compute p95, phase costs         |
| resource  |       100 / 500 / 1,000 | 1GB / 2GB         | 2GB / 4GB           | node lookup cost, inventory cost |
| combat    | 10v10 / 50v50 / 100v100 | 2GB               | 2GB / 4GB           | combat phase p95                 |
| strategic |       100 / 500 / 1,000 | 2GB               | 2GB / 4GB           | strategic phase p95              |
| mixed     |       200 / 500 / 1,000 | 1GB / 2GB         | 2GB / 4GB           | total compute p95, memory        |

## Tasks

| Task                                  | Narrow implementation logic                                                          | Files / area             |
| ------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------ |
| M5.1 Normalize perf scenario builders | Scenario builders must have deterministic seed and stable scale parameters.          | `src/perf/scenarios.py`  |
| M5.2 Normalize profile selection      | Explicit profile matrix. No hidden default.                                          | `src/perf/profiles.py`   |
| M5.3 Store per-scenario JSON          | One JSON per scenario/profile combination.                                           | `reports/perf/`          |
| M5.4 Add report aggregator            | Generate summary table by scenario/profile.                                          | `scripts/perf_report.py` |
| M5.5 Separate smoke vs full perf      | Smoke perf runs in CI. Full matrix runs manually/nightly.                            | pytest markers           |
| M5.6 Track phase-level regressions    | Not only total tick time. Track movement/combat/strategic/resource/apply separately. | BenchHarness             |

## Acceptance checklist

```text
[ ] Perf matrix covers local and concurrent profiles.
[ ] Perf matrix covers idle, movement, resource, combat, strategic, and mixed scenarios.
[ ] Every benchmark report includes profile, flags, seed, scale, warmup_ticks, sample_ticks.
[ ] Reports distinguish compute time from wall-clock time.
[ ] Reports include phase-level metrics.
[ ] Smoke perf is small enough for CI.
[ ] Full perf is available as a separate command.
```

## Exit condition

You can answer:

```text
Which profile is safe for which scale?
Which phase is the bottleneck?
Did a change improve real compute cost or just move the cost elsewhere?
```

---
