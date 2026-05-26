# Investigation - Codebase Verification for Phases 1 to 8

## Context

We need to match the documentation perfectly to the actual codebase implementation across all 8 phases. Here is our investigation and mapping of the key source files for each phase.

### Phase 1 & 2: Decoupled Semantic Architecture & Baselines
- Core event envelopes defined in `src/observability/events.py`.
- Event extraction delta comparison in `src/observability/event_extractor.py`.
- Bounded thread-safe buffer in `src/observability/event_recorder.py`.
- Prometheus `/metrics` FastAPI mounting in `src/api/server.py`.
- Hard Law checking pipeline integrated into kernel `_phase_observability` loop in `src/observability/hard_law_monitor.py`.

### Phase 3: Single-Run processing
- Run manifestations and contract directory layout handled by `RunArtifactRepository` and `RunManifest` inside `src/observability/reporting/run_repository.py`.
- Metric window accumulation and flush triggers in `src/observability/reporting/metric_recorder.py`.
- Post-run orchestrator `AnalysisPipeline` inside `src/observability/reporting/pipeline.py` (which has since been evolved into the Phase 8 orchestrator in `src/observability/understanding/pipeline.py`).
- Original single-run anomaly rules evaluated post-hoc against stuck, Stall, end-loop, and crowding policies in `src/observability/anomaly/rules.py` and `src/observability/anomaly/post_run_analyzer.py`.
- Health Score and MD dashboard outputs in `src/observability/reporting/run_report.py`.

### Phase 4: Multi-Run baselines
- Config sweeper sequentially running multiple seeds inside `src/observability/sweeper.py`.
- Sweep dataset index (`run_index.jsonl` and `sweep_summary.json`) in `src/observability/reporting/run_set_repository.py`.
- Baseline generator and distribution metrics (p10, p50, p90, stddev, manual exclusion checks, is_weak_baseline flags) in `src/observability/reporting/baseline_generator.py`.
- Baseline comparator and drift triggers in `src/observability/reporting/baseline_comparator.py`.

### Phase 5: Live inspection
- `LiveRunStatus` / `LiveRunSnapshot` and `LiveSnapshotProvider` in `src/observability/live/snapshot_provider.py`.
- Focused `EntityInspector` yielding compact JSON payloads, hp/max_hp, gold/item inventories, quest progress, strategic intents, active anomaly flags, and timeline snippet limits in `src/observability/live/entity_inspector.py`.
- Local pub-sub broker `LiveEventPublisher` applying category/severity subscription filters and bounded backpressure client evictions in `src/observability/live/event_publisher.py`.
- WebSocket mount `GET /api/v1/ws/observe` in `src/api/ws/stream.py`.

### Phase 6: Externalization
- Single-run and sweep pyarrow Parquet formats via `JSONLArtifactExporter` and `ParquetArtifactExporter` in `src/observability/analytics/exporter.py`.
- DuckDB local database mappings and predefined queries (worst-runs, anomaly-summary) in `src/observability/analytics/dataset.py` and `src/observability/analytics/query.py`.
- Bounded client stream adapter boundary defined by `EventStreamAdapter` in `src/observability/stream/base.py`.

### Phase 7: Production platform
- ClickHouse schema management, idempotency checksum skip logic, and pre-built analytical query types (`worst-runs`, `anomaly-summary`, `entity-events`, etc.) in `src/observability/warehouse/clickhouse.py` and `src/observability/warehouse/base.py`.
- Redis Streams non-blocking worker queue publish threads, high-severity evictions, and health check fields in `src/observability/stream/adapters.py`.

### Phase 8: Advanced Post-Run Simulation Understanding
- Base `DomainAnalyzer` class and execution registry mapping finding records in `src/observability/understanding/domain/base.py`.
- Concrete analyzers (`MovementDomainAnalyzer`, `EconomyDomainAnalyzer`, `QuestDomainAnalyzer`, `RuntimeDomainAnalyzer`) in the `domain` subfolder.
- Scenario-aware configuration thresholds and loading rules inside `src/observability/understanding/expectations/`.
- Heuristic inference confidence ranking rules (`StaleResourceTargetSelection`, `MovementBottleneckOrOccupancyCrowding`, `InventoryFullReturnLoopBroken`, `QuestObjectiveImpossible`, `GovernorPressureFromObservabilityOrWorkDebt`, `CombatEngagementCannotResolve`) in `src/observability/understanding/rootcause/`.
- Engine dimensions (`ACTIVITY`, `LIVENESS`, `DOMINANCE`, `RUNTIME_STABILITY`) in `src/observability/understanding/balance/`.
- Emergent narrative pattern matching events in `src/observability/understanding/stories/`.
- Human annotator annotations in `src/observability/understanding/review/`.
- Signal-to-noise quality audits and promotion policies in `src/observability/understanding/quality/`.
- Unified pipeline entry orchestrator `UnderstandingPipeline` in `src/observability/understanding/pipeline.py`.
