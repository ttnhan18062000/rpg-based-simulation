# Investigation - TCK-20260529-OBS-PHASE20

## Key Findings

1. **Phase Profiler Location & Structure**:
   - We need to create `src/observability/performance/models.py` and `src/observability/performance/profiler.py`.
   - `PhaseTimingRecord` needs properties: `run_id`, `tick`, `phase_name`, `duration_ns`, `entity_count`, `update_count`, `event_count`, `provider_call_count`, `cache_hit_count`, `cache_miss_count`, `budget_status`, `failed`.
   - `PhaseProfiler` should track phase context, elapsed time using `time.perf_counter_ns()`, and expose `profile_phase(tick, phase_name)` returning a `PhaseProfileScope` context manager.
   - If `ObservabilityConfig.is_runtime_profiling_enabled()` is disabled, `PhaseProfiler` should be completely bypassed or return a no-op scope to minimize performance impact in hot paths.

2. **Metric Window Aggregates Integration**:
   - `MetricWindowRecord` defined in `src/observability/reporting/metric_recorder.py` needs to support the optional new JSON and average fields:
     - `phase_duration_ms_avg_json: Optional[str] = None`
     - `phase_duration_ms_p95_json: Optional[str] = None`
     - `phase_event_count_json: Optional[str] = None`
     - `phase_budget_status_json: Optional[str] = None`
     - `observability_overhead_ms_avg: Optional[float] = 0.0`
     - `event_emission_ms_avg: Optional[float] = 0.0`
     - `event_stream_publish_ms_avg: Optional[float] = 0.0`
     - `behavior_queue_push_ms_avg: Optional[float] = 0.0`
   - We must also ensure these fields default to safe/empty/zero values so that any older metric windows still load correctly without breaking schema validation (using Pydantic `Field(default=...)`).

3. **Observability Overhead Profiling**:
   - We need to define standard counters/accumulators to record durations of:
     - Event extraction (e.g. inside `EventExtractor`)
     - Event recording (e.g. inside `EventRecorder`)
     - Timeline updates
     - Queue push timings
   - These will be averaged and aggregated at the end of each metric window.
