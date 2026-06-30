---
title: Observability — Getting Started Guide
layer: observability
authority: P1
audience: developer
tags: [observability, events, traces, prometheus, hard-law, eventbus]
---

# Observability — Getting Started Guide

How to emit, read, and act on observability signals from a simulation run.
Contracts: [`docs/observability/decision_trace_contract.md`](../observability/decision_trace_contract.md),
[`docs/observability/hard_law_monitor.md`](../observability/hard_law_monitor.md),
[`docs/observability/prometheus_metrics.md`](../observability/prometheus_metrics.md).

---

## What the observability stack does

Every meaningful simulation event (combat, quests, cognition decisions, economic transactions,
faction changes) is converted to a `SimulationEvent` and published on a shared queue by the
`EventRecorder`. Subscribers — including the SimQ scoring hub, the replay system, and
persistence writers — drain that queue asynchronously.

Key source files:

| File | Role |
|---|---|
| `src/observability/event_recorder.py` | Writes `SimulationEvent` objects to the shared queue; controls backpressure |
| `src/observability/events.py` | `SimulationEvent` and `ObservabilityEventEnvelope` dataclasses, `EventCategory` type |
| `src/observability/event_extractor.py` | Reads state diffs per tick, produces `SimulationEvent` objects; read-only observer |
| `src/observability/queue.py` | Global observability queue, `QueueDrainWorker` |
| `src/observability/hard_law_monitor.py` | Listens for `InvariantViolation` events; raises hard stops |
| `src/observability/trace.py` | Decision trace capture and replay |
| `src/observability/watchdog.py` | Run-level watchdog (stall detection, heartbeat) |
| `src/observability/prometheus_collector.py` | Prometheus metric collectors |

---

## EventRecorder backpressure

`EventRecorder` adapts to queue pressure automatically — no manual configuration needed.

| Mode | Queue fill | Behaviour |
|---|---|---|
| `NORMAL` | < 70% | All events recorded |
| `PRESSURE` | 70–90% | INFO/DEBUG sampled 1-in-5; WARNING+ always recorded |
| `DEGRADED` | 90–100% | INFO/DEBUG dropped; WARNING+ recorded |
| `SURVIVAL` | ≥ 100% | Counter-only — no queue push, no I/O |

Mode transitions are logged at INFO level. Check current pressure at runtime:

```bash
python3 -m src diagnostics resources
# JSON output for scripting
python3 -m src diagnostics resources --format json
```

Exit 0 = OK/WARN. Exit 1 = DEGRADED (CI gate).

If a run regularly hits PRESSURE or DEGRADED, reduce entity count (`--entities`) or increase
worker threads (`--workers`). See the hot-path safety contract:
[`docs/architecture/observability_hot_path_safety_contract.md`](../architecture/observability_hot_path_safety_contract.md).

---

## Reading the event log

After a run, the raw event log is at `data/runs/<run_id>/simulation_events.jsonl`. Each line
is a JSON-serialized `SimulationEvent`.

Key fields:

```json
{
  "event_id": "evt_abc123",
  "event_type": "combat_kill",
  "category": "combat",
  "tick": 47,
  "entity_id": "hero_7",
  "region_id": "region_east",
  "payload": { "target_id": "monster_3", "damage": 42 }
}
```

`event_type` values are internal engine names (e.g. `combat_kill`, `quest_event`). The SimQ
module translates them to contract vocabulary — see
[`docs/guides/simulation_quality.md`](simulation_quality.md) §Event translation.

Query the log via the warehouse:

```bash
python3 -m src warehouse ingest-run <run_id>
python3 -m src warehouse query entity-events --entity-id 12 --limit 50
```

---

## Decision traces

Decision traces record what an entity *considered* and *decided* on each tick — the full
cognition graph traversal, not just the outcome.

```bash
# Capture traces during a run
python3 -m src cli --ticks 200 --seed 42 --replay

# Inspect a specific entity's trace
python3 -m src cognition snapshot --entity-id 12 --run-id <run_id>

# Find repeated patterns across entities
python3 -m src cognition patterns --run-id <run_id>
```

Trace data lands in `data/runs/<run_id>/cognition_snapshots.jsonl`. The trace contract:
[`docs/observability/decision_trace_contract.md`](../observability/decision_trace_contract.md).

---

## Hard-law monitor

The hard-law monitor (`src/observability/hard_law_monitor.py`) listens for `InvariantViolation`
events emitted by the engine when a simulation law is broken. It is always active.

Violations are written to `data/runs/<run_id>/hard_law_violations.jsonl`:

```json
{
  "tick": 94,
  "law_id": "CONSERVATION-001",
  "description": "Gold created without a source transaction",
  "entity_id": "town_1",
  "severity": "HARD"
}
```

A `HARD` violation stops the run immediately. A `SOFT` violation is logged and continues.

To check violations after a run:

```bash
cat data/runs/<run_id>/hard_law_violations.jsonl
```

Laws and their IDs are documented in [`docs/mechanics/03_economic_laws.md`](../mechanics/03_economic_laws.md)
(conservation) and [`docs/mechanics/02_combat_laws.md`](../mechanics/02_combat_laws.md) (combat).

---

## Prometheus metrics

When the FastAPI server is running, Prometheus metrics are scraped from `/metrics`.
Key metrics and their meaning are documented in
[`docs/observability/prometheus_metrics.md`](../observability/prometheus_metrics.md).

Performance baselines for CI gates are in `docs/observability/baselines/`. To compare a run
against a baseline:

```bash
python3 -m src compare-sweep <sweep_id> --baseline docs/observability/baselines/latest.json
```

---

## Adding a new event type

1. Add the `event_type` string and optional `category` to `src/observability/events.py`
   (`EventCategory` Literal, if a new category is needed).
2. Emit the event in `src/observability/event_extractor.py` from the appropriate per-tick
   loop (entity loop, faction loop, world-events loop). `EventExtractor` is read-only —
   it observes state diffs, never mutates.
3. If the new event should be scored by SimQ, add a translation entry in
   `src/simulation_quality/quality_hub.py` and a scorer handler. See
   [`docs/guides/simulation_quality.md`](simulation_quality.md) §Adding a new scoring rule.
4. Add tests in `tests/unit/observability/` — at minimum: event emitted on the correct
   condition, event not emitted when condition is absent (anti-drift guard).

**Architecture boundary:** `src/observability/` must never import from `src/engine/`,
`src/domains/`, or `src/systems/`. All observations flow through state diffs passed into
`EventExtractor`, not through direct coupling to engine internals.

---

## Further reading

- [`docs/observability/how_to_run_simulation.md`](../observability/how_to_run_simulation.md) — full CLI reference for running and sweeping
- [`docs/architecture/observability_behavior_profiling_boundary.md`](../architecture/observability_behavior_profiling_boundary.md) — boundary contract
- [`docs/guides/simulation_quality.md`](simulation_quality.md) — using observability events for quality scoring
- [`docs/guides/testing.md`](testing.md) — observability test coverage requirements
