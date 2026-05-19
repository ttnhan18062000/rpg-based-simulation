# Implementation Plan - Metric Window Recorder

## Approach
1. **Pydantic Model `MetricWindowRecord`**: Define the exact required fields and optional fields representing rolling tick data. Include a standard schema version `observability_metric_v1`.
2. **Accumulator Class `MetricWindowAccumulator`**: Maintain a list/deque of tick snapshots in memory for the duration of the current window.
   - Computes:
     - `avg` for numeric values (`alive_entities`, `gold_total`, `tick_compute_ms`, `worker_utilization`, `queue_utilization`).
     - `max` for memory RSS bytes.
     - `exact p95` for tick compute duration using `numpy` or sorted lists.
     - `sum` for counts (`hard_law_violation_count`, `event_count`, `rejection_count`).
     - `dominant` mode for governor mode (`RuntimeMode.name`).
3. **Recorder Class `MetricWindowRecorder`**: Hooked into `Kernel`, manages `MetricWindowAccumulator` instance, and appends to `metric_windows.jsonl` under the standard run folder using an atomic file writer setup.
4. **Kernel Tick Updates**: Inside `Kernel._phase_observability`, retrieve the current snapshots and call `record_tick`. On simulation shutdown, flush the final partial window cleanly.
