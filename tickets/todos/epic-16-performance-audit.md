# Epic 16: Performance Audit & Optimization

## Summary

Conduct a comprehensive performance audit of both the backend engine and the frontend viewer. Identify bottlenecks, measure baseline metrics, and implement optimizations where needed. Report findings to developer before making changes.

Inspired by: Game development profiling practices, Factorio optimization blog posts, Python performance tuning.

---

## Motivation

- No performance profiling has been done — unknown if bottlenecks exist
- As entity count grows, tick processing time may increase non-linearly
- Frontend polling + canvas rendering may struggle with large maps or many entities
- Event log is unbounded — potential memory leak for long simulations
- Thread pool overhead unknown at scale
- Aligns with project goals — simulation should run smoothly at 50k+ ticks with 50+ entities

---

## Features

### F1: Backend Profiling

- Profile `WorldLoop` tick cycle with `cProfile` or `py-spy`:
  - Per-phase timing: Schedule, Collect, Resolve, Cleanup
  - AI worker evaluation time per entity
  - Spatial hash lookup performance
  - RNG computation overhead
- Benchmark at different scales:
  - 10 entities / 64×64 map (current default)
  - 50 entities / 128×128 map
  - 100 entities / 256×256 map
- Identify: O(n²) hotspots, GIL contention, unnecessary copies

### F2: Memory Profiling

- Measure memory usage over 10k ticks:
  - Entity objects and their growing memory (combat history, etc.)
  - EventLog unbounded growth
  - Snapshot objects (are old snapshots GC'd properly?)
  - Thread-local state
- Identify leaks or unbounded growth

### F3: Frontend Performance

- Measure with Chrome DevTools Performance tab:
  - Canvas render time per frame
  - React re-render frequency and duration
  - Memory usage over time (event accumulation)
  - Network: poll frequency, response sizes
- Test at scale: 100+ entities on canvas, 10k+ events in log

### F4: Optimization Targets (implement after audit)

Potential optimizations (implement only if profiling confirms need):

- **Spatial hash** — verify O(1) lookups, check hash distribution
- **Snapshot creation** — are deep copies necessary everywhere?
- **Event log** — add ring buffer cap (e.g., 10k events max)
- **Frontend event list** — virtualized scrolling for large lists
- **Canvas rendering** — dirty-rect rendering instead of full redraw
- **API response size** — incremental state diffs instead of full state
- **Worker pool** — optimal thread count for entity count

### F5: Performance Dashboard

- Add optional `--profile` flag to CLI/server mode
- Log per-tick timing to a file for analysis
- Add `/api/v1/metrics` endpoint with: avg tick time, entity count, event count, memory usage

---

## Design Principles

- **Measure first, optimize second** — no premature optimization
- All findings documented before any code changes
- Optimizations must not break determinism
- Performance mode in frontend is a separate concern (see epic-14 F9)

---

## Dependencies

- Working simulation at current scale (already exists)
- Python profiling tools (cProfile, tracemalloc — stdlib)
- Chrome DevTools (no code dependency)

---

## Estimated Scope

- Backend: ~3 files new (profiling scripts, metrics endpoint), ~2 modified
- Frontend: ~2 files modified (virtualized lists, render optimization)
- Output: Performance report document with findings and recommendations

---

## Notes

> **Report findings to developer** before implementing any optimizations. This is primarily an audit ticket — implementation follows developer approval.

## Labels

`epic`, `performance`, `audit`, `needs-decision`
