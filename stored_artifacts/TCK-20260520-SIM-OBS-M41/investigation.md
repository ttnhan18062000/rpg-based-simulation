# Investigation — Milestone 41

## Existing Infrastructure
- `BenchHarness` in `src/perf/bench_harness.py` provides perf measurement scaffolding
- `V2EntityBuilder` provides entity creation for test scenarios
- `ObservabilityConfig` provides mode switching and deployment profiles
- Stream adapters (`RedisStreamAdapter`, `InProcessEventStreamAdapter`, `NullEventStreamAdapter`) handle graceful degradation
- `LocalWarehouseAdapter` and `NullWarehouseAdapter` provide warehouse fallbacks
- `AlertsManager.get_router()` provides the alert routing singleton

## Key Failure Simulation Strategy
- **Stream outage**: Monkeypatch `RedisStreamAdapter._connect()` to always fail, verify engine continues
- **Warehouse outage**: Monkeypatch `ClickHouseWarehouseAdapter` connection to fail, verify local artifacts remain
- **Worker crash**: Inject exception into `LiveAnomalyWorker._run_loop`, verify engine unaffected and alert generated
- **High event volume**: Saturate the event publisher queue, verify bounded queues hold and critical events preserved
- **Webhook failure**: Already covered by M40 integration tests
