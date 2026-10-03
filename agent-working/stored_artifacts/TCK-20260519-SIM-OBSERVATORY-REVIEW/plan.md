---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260519-SIM-OBSERVATORY-REVIEW
artifact_type: plan
tags: [sim, observatory, review]
---

# Simulation Observatory Review Plan (Phases 1-3)

## Objective
Investigate the existing RPG simulation engine codebase and produce a comprehensive current-state assessment report (`observability_assessment_report.md`), a second-pass clarification report (`observability_clarification_report_v2.md`), and a final feasibility and milestone roadmap report (`observability_feasibility_and_milestones_v3.md`) structured exactly as specified in `sim_test_init_instruction_3.md`.

## Phase 1 Steps (Completed)
1. Investigated existing event and logging mechanisms (`src/logging/`, `src/replay/`, `src/engine/`).
2. Investigated watchdog and certification mechanisms (`src/certification/`, `src/engine/watchdog/`).
3. Investigated metrics and runtime telemetry (`src/perf/`, `src/engine/kernel.py`).
4. Checked Loki and Grafana readiness (Loki configs, Prometheus/Grafana configs in root, structured loggers).
5. Reviewed simulation laws and hard invariants across combat, movement, economy, social, strategy.
6. Analyzed strange events and anomaly detection opportunities.
7. Assessed long-run simulation readiness (memory, log volume, tick limits).
8. Inventoried existing tests related to observability (`tests/certification/`, `tests/perf/`, `tests/engine/`).
9. Synthesized into recommended architecture direction for Simulation Observatory.
10. Formatted and output final report (`observability_assessment_report.md`).

## Phase 2 Steps (Completed)
11. Deep-dive into Loki label safety: inspect `promtail-config.yml`, `JsonFormatter`, and determine safe stream labels vs JSON fields.
12. Inspect Prometheus and Grafana metric mapping: examine `docker-compose.yml`, `prometheus.yml`, `simulation.json`, FastAPI backend, and worker daemons to list all PromQL metrics and map them to existing runtime classes.
13. Complete inventory of existing event and trace mechanisms: search for `TraceEvent`, `transaction_trace`, `intent_results`, `latest_result`, `audit`, etc.
14. Analyze architectural trade-offs between `TraceEvent` and new `SimulationEvent`.
15. Formulate domain event volume policies across 11 key domains (movement, combat, harvesting, economy, quests, etc.).
16. Inventory hard laws across all domains, evaluating enforcement locations, test coverage, and DirtySet monitoring suitability.
17. Define `HardLawMonitor` V1 scope.
18. Evaluate Anomaly Engine architectural options (in-process vs out-of-process vs post-run).
19. Propose Entity Timeline retention model.
20. Conduct gap analysis for semantic metrics against `WorldMetrics` and `PressureSignals`.
21. Assess balance profile readiness (scenario expectations, YAML configs).
22. Assess production watchdog readiness in worker daemons vs certification harnesses.
23. Format and output second-pass clarification report exactly matching Sections A through N.

## Phase 3 Steps (Active)
24. Verify 8 referenced active V2 paths against codebase: check `src/engine/concurrency.py`, `src/workers/daemon.py`, `src/systems/world_systems/calamity.py`, `src/systems/world_systems/governance.py`, `src/services/inventory_service.py`, `src/engine/governor.py`, `src_legacy/workers/ai_worker_daemon.py`, `src_legacy/utils/watchdog.py`. Construct validation table.
25. Classify Prometheus metrics into P0 (first export), P1 (minor collector logic), P2 (optional domains), and Not Ready. Construct metrics readiness table.
26. Refine HardLawMonitor V1 laws into DirtySet-scoped (per-tick), Periodic full scan, and Certification/post-run groups. Detail domain, data, cost, cadence, and failure behavior across light/debug/certification/long_run modes.
27. Classify concrete event types into V1 emission scopes (always emit, anomaly-only, metrics-only, later) to prevent event storming. Construct event classification table.
28. Design TraceEvent vs SimulationEvent migration plan ensuring zero replay disruption, specifying emission boundaries and verification tests.
29. Compare staged anomaly architecture (V1 post-run chunk analyzer -> V2 in-process counters -> V3 out-of-process Redis/Kafka daemon). Detail value, risk, complexity, dependencies, and gating requirements.
30. Refine Entity Timeline retention model: compare per-entity ring buffer, global event ring buffer, flagged-entity timeline, and chunk reconstruction. Detail memory cost, debug value, complexity, and recommend V1 model.
31. Propose a specific, practical 6-milestone implementation roadmap with clear goals, included/excluded components, acceptance criteria, and main risks.
32. Format and output final report `observability_feasibility_and_milestones_v3.md`.
