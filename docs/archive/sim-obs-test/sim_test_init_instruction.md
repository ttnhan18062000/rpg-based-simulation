---
status: archive
authority: P2
audience: historical
layer: testing
original_date: unknown
---

You are an expert simulation-engine architect, observability engineer, and RPG systems designer.

Your task is to review the current RPG simulation project and produce a detailed current-state assessment before we plan the next implementation phase.

Context:

We are building a deterministic RPG-based simulation engine with entities, factions, movement, combat, resource economy, quests, strategic projects, lifecycle, DirtySet optimization, profiling, certification, watchdog, partial event log, centralized Loki logging, and limited Grafana metrics.

We believe unit and integration tests will never cover all emergent cases. We want to design a Simulation Observatory that can run long simulations for hours, observe the world, detect hard law violations, detect strange but not necessarily illegal behavior, summarize balance issues, and help us debug emergent failures.

Important:

Do not propose implementation yet. First, investigate the existing codebase and produce a current-state report.

Review the project for the following areas.

## 1. Existing event and logging mechanisms

- Find all event log, transaction trace, replay trace, audit log, and event interpreter mechanisms.
- Identify what event types are currently emitted or recorded.
- Identify whether events are structured or string-based.
- Identify whether events include tick, entity ID, region ID, system/source, reason, severity, and related entities.
- Identify whether events are deterministic/replay-safe.
- Identify gaps for long-run observability.

## 2. Watchdog and certification mechanisms

- Find current watchdog logic.
- Identify what conditions it detects: tick hang, fast tick, stall, timeout, wipe, semantic drift, etc.
- Identify whether watchdog outputs structured records or only logs.
- Identify how certification results are represented.
- Identify how runtime measurements are sampled.
- Identify gaps for simulation-health monitoring.

## 3. Metrics and runtime telemetry

- Find all runtime status, pressure signals, measurement points, benchmark metrics, profiler metrics, and phase-cost records.
- Identify which metrics are operational/performance metrics versus simulation-semantic metrics.
- Identify whether metrics support rolling windows, p50/p95/p99, trends, and per-scenario aggregation.
- Identify gaps for Grafana dashboards.

## 4. Loki and centralized logging readiness

- Find logging configuration, logger usage, structured logging support, JSON logging support, and log severity usage.
- Identify whether logs are suitable for Loki querying.
- Identify high-cardinality risks such as entity ID, target ID, region ID, quest ID, or tick in labels.
- Recommend what should be Loki labels versus log fields.
- Identify noisy logs or hot-path print statements.

## 5. Grafana metric readiness

- Find existing metric export path if any.
- Identify what metrics are currently available for dashboards.
- Identify missing metrics for world health, movement health, economy health, combat balance, quest progression, strategic progression, anomaly count, long-run stability, and performance trends.
- Recommend dashboard panels, but do not implement them.

## 6. Simulation laws and hard invariants

- Identify existing hard laws in tests, checklists, code comments, and runtime checks.
- Group them by domain: movement, combat, inventory/resource, quest/reward, lifecycle/death, strategic/project, economy/shop, region/faction.
- Identify which hard laws are already enforced at runtime.
- Identify which hard laws are only tested.
- Identify which hard laws are missing runtime monitoring.

## 7. Strange-event and anomaly detection opportunities

Based on current mechanics, identify likely strange events:

- Stuck entities
- Oscillating movement
- Repeated failed action
- Goal churn
- Idle too long
- Quest stalled
- Resource-node crowding
- Economy freeze
- Faction collapse
- Combat never ends
- Reward not delivered
- Entity starves while food exists

For each, suggest:

- Signal source
- Required event fields
- Metric/window needed
- Possible severity
- Likely root causes

## 8. Long-run simulation readiness

- Assess whether the project can run long simulations for 10,000+ ticks or hours.
- Identify current blockers: memory growth, event/log volume, replay storage, cache growth, performance degradation, missing checkpointing, missing report generation.
- Recommend what evidence is required to claim long-run stability.

## 9. Existing tests related to observability

- Find tests for event replay, telemetry, certification, watchdog, profiler, metrics, logs, and deterministic behavior.
- Identify which tests can be reused.
- Identify missing tests needed before implementing Simulation Observatory.

## 10. Recommended architecture direction

Do not write implementation code.

Provide a high-level architecture recommendation for a Simulation Observatory that fits the current project.

The architecture should include:

- `SimulationEvent` model
- `EventBus` or `EventRecorder`
- `MetricsCollector`
- `HardLawMonitor`
- `AnomalyRuleEngine`
- `BalanceAnalyzer`
- `EntityTimelineRecorder`
- `AutoTriageEngine`
- `RunReportGenerator`
- `LokiExporter`
- `GrafanaMetricsExporter`
- `ScenarioSweeper`

For each component, describe:

- Current reusable project pieces
- What is missing
- Integration points
- Risks
- Recommended priority

## 11. Output format

Return the review as a structured report with these sections:

- A. Executive Summary
- B. Current Observability Inventory
- C. Existing Mechanisms We Can Reuse
- D. Major Gaps
- E. Risks and Anti-Patterns
- F. Recommended Simulation Observatory Architecture
- G. Proposed Milestones, high-level only
- H. Tests That Must Be Added Later
- I. Open Questions Before Implementation

Be precise. Cite file paths, class names, function names, and test names wherever possible.

Do not guess. If something is not found, say: “not found in current codebase.”
