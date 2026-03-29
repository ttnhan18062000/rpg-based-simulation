# Infra 02: Performance Profiling Infrastructure

## Status: DONE (updated with API payload profiler)

## Summary

Automated performance profiling tools covering both **engine tick timing** and **API payload sizes**.

## Deliverables

### Makefile Commands

| Command | Purpose |
|---------|---------|
| `make profile` | Run 500-tick profile, print timing report |
| `make profile-full` | Run 2000-tick profile, save cProfile `.prof` file |
| `make profile-memory` | Run 500-tick profile with tracemalloc memory snapshot |
| `make profile-api` | Measure API payload sizes (map, static, state) |

### Engine Profiling Script

**File:** `scripts/profile_simulation.py`

Features:
- Runs the full engine (EngineManager → WorldLoop) for N ticks
- Measures per-tick timing with `time.perf_counter()`
- Breaks down into 4 phases: Schedule, Collect, Resolve, Cleanup
- Reports: min/max/mean/p50/p95/p99, phase % of total, top 5 slowest ticks
- Optional `--cprofile FILE` to save cProfile output (viewable with `snakeviz` or `pstats`)
- Optional `--memory` flag for tracemalloc top-15 allocations + peak memory
- Configurable: `--ticks`, `--seed`, `--entities`, `--grid`, `--workers`

### API Payload Profiling Script

**File:** `scripts/profile_api_payload.py`

Features:
- Measures JSON payload sizes for all API endpoints: `/map`, `/static`, `/state`
- Compares RLE-compressed vs raw 2D grid sizes
- Breaks down `/state` payload: slim entities, selected entity, terrain_memory, entity_memory
- Shows per-entity average size
- Estimates pre-optimization sizes for comparison
- Reports bandwidth at 80ms poll interval
- Configurable: `--ticks` (run N ticks before measuring), `--seed`

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
# Engine tick profiling
make profile                    # Quick 500-tick report
make profile-full               # 2000 ticks + cProfile dump
make profile-memory             # Memory profiling
python scripts/profile_simulation.py --ticks 1000 --entities 50 --grid 256  # Custom

# API payload profiling
make profile-api                # Measure all endpoint payload sizes
python scripts/profile_api_payload.py --ticks 50   # More ticks = more entity memory accumulated
```

## Related Documents

- `docs/performance-report-epic16.md` — Engine tick optimization report
- `docs/performance-report-api-payload.md` — API payload optimization report
- `tests/test_api_payload.py` — 8 payload size regression tests

## Labels

`infra`, `performance`, `profiling`, `automation`, `api`, `done`
