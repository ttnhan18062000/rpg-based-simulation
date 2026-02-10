# Infra 02: Performance Profiling Infrastructure

## Status: DONE

## Summary

Add automated performance profiling tools to measure tick timing, phase breakdown, entity scaling, and memory usage — all runnable via a single `make` command.

## Deliverables

### Makefile Commands

| Command | Purpose |
|---------|---------|
| `make profile` | Run 500-tick profile, print timing report |
| `make profile-full` | Run 2000-tick profile, save cProfile `.prof` file |
| `make profile-memory` | Run 500-tick profile with tracemalloc memory snapshot |

### Profiling Script

**File:** `scripts/profile_simulation.py`

Features:
- Runs the full engine (EngineManager → WorldLoop) for N ticks
- Measures per-tick timing with `time.perf_counter()`
- Breaks down into 4 phases: Schedule, Collect, Resolve, Cleanup
- Reports: min/max/mean/p50/p95/p99, phase % of total, top 5 slowest ticks
- Optional `--cprofile FILE` to save cProfile output (viewable with `snakeviz` or `pstats`)
- Optional `--memory` flag for tracemalloc top-15 allocations + peak memory
- Configurable: `--ticks`, `--seed`, `--entities`, `--grid`, `--workers`

### Per-Tick Phase Timing (in engine)

`WorldLoop._step()` now logs phase timing at DEBUG level:
```
Tick 42: schedule=0.0001s collect=0.0080s resolve=0.0007s cleanup=0.0120s total=0.0208s entities=50 proposals=45 applied=42
```

## Example Output

```
  SIMULATION PERFORMANCE REPORT
  ==============================
  Ticks executed:    500
  Wall clock time:   10.234s
  Throughput:        48.9 ticks/sec
  Avg tick time:     20.47ms

  Phase              Avg (ms)   P95 (ms)    % Total
  Schedule              0.07      0.26       0.4%
  Collect               8.08     11.16      39.0%
  Resolve               0.68      1.33       3.3%
  Cleanup              11.86     19.51      57.3%
```

## How to Run

```bash
make profile                    # Quick 500-tick report
make profile-full               # 2000 ticks + cProfile dump
make profile-memory             # Memory profiling
python scripts/profile_simulation.py --ticks 1000 --entities 50 --grid 256  # Custom
```

## Labels

`infra`, `performance`, `profiling`, `automation`, `done`
