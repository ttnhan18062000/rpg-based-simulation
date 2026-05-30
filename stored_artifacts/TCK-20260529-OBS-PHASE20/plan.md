# Plan - TCK-20260529-OBS-PHASE20

## Goal
Implement Phase 20 (Runtime Performance Profiling Lane) of the Observability & Behavior Profiling roadmap. Track and report phase timing metrics, extend metric windows, and isolate/measure observability overhead separately from the simulation hot path.

## Approach
1. **Define Models**:
   - Define `PhaseTimingRecord` dataclass in `src/observability/performance/models.py`.
2. **Implement Profiler**:
   - Implement `PhaseProfiler` and `PhaseProfileScope` inside `src/observability/performance/profiler.py`.
   - Ensure the profiler yields a context manager, tracks duration in nanoseconds using `time.perf_counter_ns()`, and captures counts of entities, events, updates, cache hits, etc.
   - Guard execution: if `ObservabilityConfig.is_runtime_profiling_enabled()` is False, the profiler should behave as a no-op with near-zero overhead.
3. **Extend Metric Windows**:
   - Locate and examine `MetricWindowRecord` and its serialization/database registry.
   - Extend `MetricWindowRecord` to optionally output averaged JSON metrics and observability overhead averages.
4. **Implement Observability Overhead Tracking**:
   - Measure durations of event extraction, event recording, timeline updates, queueing, and publish times separately and export them.
5. **Implement and Run Tests**:
   - Write unit, integration, and performance budget tests.
   - Run tests to confirm zero regressions.
