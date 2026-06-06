# TCK-20260519-SIM-OBS-HARD-LAW

## Title

Implement HardLawMonitor V1 and Observability Configuration (Milestone 3 & 4)

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement HardLawMonitor V1 to perform lightweight, O(1)-efficient, DirtySet-scoped state checks at the end of each authoritative tick, preventing corruption in debug/certification modes while logging/counting in light mode.

## Scope

- Define `ObservabilityMode` Enum (`OFF`, `LIGHT`, `DEBUG`, `CERTIFICATION`, `LONG_RUN`) in `src/observability/config.py`.
- Implement `HardLawMonitor` in `src/observability/hard_law_monitor.py`.
- Define law ID naming scheme, severity levels, and violation result shape.
- Implement DirtySet-scoped entity state checks (HP >= 0, gold >= 0, stamina >= 0, readiness >= 0, position is finite).
- Implement DirtySet-scoped occupancy collision check.
- Hook `HardLawMonitor` into `Kernel` tick finalization (after state advancement, before persistence/replay committed).
- Implement mode-specific failure policies (log only for LIGHT, raise exception for DEBUG, fail scenario for CERTIFICATION).
- Expose Prometheus metrics: `sim_hard_law_violations_total{law_id, severity}` and `sim_hard_law_last_violation_tick`.
- Add comprehensive unit, integration, and performance tests for HardLawMonitor and Kernel integration.

## Out of Scope

- Auto-recovery/self-healing state corrections (Phase 2).
- Non-DirtySet full global scans every tick.

## Acceptance Criteria

- Hard law violations are accurately detected for negative HP, negative gold, negative stamina/readiness, and tile occupancy collisions.
- Valid/clean entities and missing/deleted entities do not cause violations.
- Same violation results in different behaviors by mode (logs in LIGHT, raises in DEBUG, fails scenario in CERTIFICATION).
- Prometheus counter `sim_hard_law_violations_total` and gauge `sim_hard_law_last_violation_tick` are successfully populated and exposed via `/metrics`.
- Performance overhead of the checks is negligible (no full-world scan in every-tick path, TPS benchmark does not regress).
- Unit and integration tests pass perfectly.

## Related Tickets

- TCK-20260519-SIM-OBS-PROM-METRICS
- TCK-20260519-SIM-OBS-BASE-LOKI

## Related Docs

- `obs_sim_phase1.md`
- `docs/observability/hard_law_monitor.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/observability/config.py`
- `src/observability/hard_law_monitor.py`
- `src/engine/kernel.py`
- `src/observability/prometheus_collector.py`
- `src/api/engine_manager.py`
- `src/engine/world_index.py`

## Assumptions / Open Questions

- We assume existing Prometheus /metrics scraping endpoints can easily scrape custom custom collector metrics.

## Implementation Notes

- **O(1) Grid Cache**: Leveraged spatial grids for O(1) occupancy checking.
- **Tile Deduplication**: Optimized double-occupancy checks by skipping tiles already flagged in the reported collisions set, avoiding redundant occupant scans and state lookups.
- **Strict Precedence**: Handled override mode programmatic settings via thread-safe lock precedence resolver in config module.

## Test Summary

- **Unit Tests**: Asserted HP, gold, stamina, readiness, finite positions, dead entity bypass, and double-occupancy in `tests/engine/test_hard_law_monitor.py`.
- **Integration Tests**: Verified Prometheus registry export structure and value updates under simulated violations in `tests/observability/test_metrics_export.py`.
- **Performance Benchmark**: Measured tick execution times under OFF vs LIGHT modes using `BenchHarness` in `tests/perf/test_hard_law_monitor_overhead.py` to verify negligible overhead.

## Files Changed

- `src/observability/config.py` [NEW]
- `src/observability/hard_law_monitor.py` [NEW]
- `src/engine/kernel.py` [MODIFY]
- `src/observability/prometheus_collector.py` [MODIFY]
- `src/api/engine_manager.py` [MODIFY]
- `src/engine/world_index.py` [MODIFY]
- `tests/engine/test_hard_law_monitor.py` [NEW]
- `tests/observability/test_metrics_export.py` [MODIFY]
- `tests/perf/test_hard_law_monitor_overhead.py` [NEW]
- `docs/observability/hard_law_monitor.md` [NEW]
- `docs/engine/kernel.md` [MODIFY]

## Completion Summary

- Implemented and fully verified the HardLawMonitor V1, Observability Configuration, Kernel loop integration, and Prometheus telemetry exporters.
- Created robust test coverage proving high detection correctness, appropriate mode policy behaviors, and negligible performance overhead.
- Cleaned up documentation suite and resolved all structural and semantic requirements in 100% compliance.
