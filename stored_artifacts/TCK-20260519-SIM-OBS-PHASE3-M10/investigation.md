# Investigation - Metric Window Recorder

## Sources of Metric Snapshots
1. **WorldMetrics**: Extracted by `MetricsService.extract_metrics(state)`. It holds `tick`, `total_entities`, `alive_entities`, `total_gold`, `rejection_counts`, and `quest_status_counts`.
2. **PressureSignals**: Extracted per tick inside `Kernel` and recorded on `self._status`. It holds `tick_compute_ms`, `worker_utilization`, `queue_utilization`, `memory_estimate_mb`, `phase_costs_ms`, etc.
3. **Events and Violations**: During `_phase_observability`, we have access to `generated_events` list and `current_violations` list, which are perfect sources to aggregate counts without scanning the global state space.
4. **Dominant Governor Mode**: Tracked in `self._status.current_mode` (type `RuntimeMode`). We can track the frequency of each mode and find the dominant one at the end of the window.
