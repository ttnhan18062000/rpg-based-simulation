---
name: observability
description: Work in src/observability/ — HardLawMonitor invariant checks, EventRecorder backpressure modes, and debugging a failing observability check. Use when editing anything under src/observability/, investigating a hard-law violation, or debugging missing/dropped events.
source: project
date_added: "2026-08-05"
---

# Observability (This Repo)

`src/observability/` is large (11 subdirectories, 8 top-level modules) and mature (8 real contract
docs under `docs/observability/`, 55+ ticket references) but had zero skill or agent coverage
before this one. This skill is sourced from the real contract docs, not written from scratch —
follow the citations below to the primary source for anything not covered here.

## When to Use

- Editing anything under `src/observability/` (alerts, analytics, anomaly, budget, cognition,
  live, mining, performance, personality, readiness subdirectories; `event_recorder.py`,
  `hard_law_monitor.py`, `queue.py`, `prometheus_collector.py`, etc.)
- Investigating a `HardLawViolationError` or an unexpected hard-law warning log
- Debugging why events seem to be missing, dropped, or sampled
- Working with the Prometheus/Loki export surface

## The 7 Hard Laws (`HardLawMonitor`)

Source: `docs/observability/hard_law_monitor.md` §1. All are `DirtySet`-scoped and O(1) per tick
except the last, which is a one-time full scan:

| Law ID | Scope | Constraint | Severity |
|---|---|---|---|
| `LAW-HP-NONNEGATIVE` | `DirtySet.combat_entities` | HP ≥ 0 (active/alive only) | ERROR |
| `LAW-READINESS-NONNEGATIVE` | `DirtySet.combat_entities` | Readiness ≥ 0 | ERROR |
| `LAW-GOLD-NONNEGATIVE` | `DirtySet.inventory_entities` | Gold ≥ 0 | ERROR |
| `LAW-STAMINA-NONNEGATIVE` | `DirtySet.biological_entities` | Stamina ≥ 0 | ERROR |
| `LAW-POSITION-FINITE` | `DirtySet.movement_entities` | x, y finite (no NaN/Infinity) | ERROR |
| `LAW-OCCUPANCY-COLLISION` | `DirtySet.movement_entities` | ≤1 solid entity per tile | ERROR |
| `LAW-SPAWN-OCCUPANCY` | `Kernel.__init__` (once, pre-tick) | Full spawn-state occupancy scan (entities + buildings + resource nodes) | ERROR |

`LAW-SPAWN-OCCUPANCY` is the one exception to the DirtySet-scoped design: it runs once, before the
first tick, because nothing has "moved" yet for the other six DirtySet-gated laws to catch — it
exists specifically to cover placement collisions `WorldCompiler.compile()` doesn't validate.

## `ObservabilityMode` Policy

Source: `docs/observability/hard_law_monitor.md` §2. Governs what happens when a law is violated:

- **`OFF`** — all health checking bypassed entirely.
- **`LIGHT`** (default) — logs a structured WARNING, increments cumulative violation counts, does
  **not** halt the tick.
- **`DEBUG` / `CERTIFICATION`** — raises `HardLawViolationError` immediately, halts the loop,
  prevents the corrupt state from being persisted or exposed via the API.
- **`LONG_RUN`** — **a real, documented gap**: violations are still persisted to
  `hard_law_violations.jsonl` and routed to `AlertsManager`, but the mode-gating `if`/`elif` chain
  only explicitly handles `LIGHT` (logging) and `DEBUG`/`CERTIFICATION` (fail-fast) — `LONG_RUN`
  falls through both branches silently (neither logged to stdout nor raised). If you're debugging
  "why didn't I see a warning for this violation" under `LONG_RUN` mode, check
  `hard_law_violations.jsonl` and `AlertsManager` directly rather than the log stream — this
  applies identically to all seven laws above.

Integration point: `HardLawMonitor` runs during the Kernel's **Advancement** phase, before state
commit and persistence (`docs/engine/kernel.md`'s "Hard Law Compliance Guard" Law) — it operates on
the tick's own `dirty_set` and the just-refined state, per the same DirtySet mechanism documented
in `docs/core/dirty_state_and_dependency.md` (this skill assumes that context; read it first if
you're not already familiar with the DirtySet optimization layer).

## `EventRecorder` Backpressure (`ObservabilityController`)

Source: `docs/architecture/observability_hot_path_safety_contract.md` §5. Four modes, driven by
queue fill ratio, evaluated on every `record()` call:

| Mode | Fill ratio | Behavior |
|---|---|---|
| `NORMAL` | < 70% | All events recorded as-is |
| `PRESSURE` | 70–90% | INFO/DEBUG sampled 1-in-5; WARNING+ always pass |
| `DEGRADED` | 90–100% | INFO/DEBUG dropped entirely; WARNING+ pass |
| `SURVIVAL` | ≥ 100% | Counter-only — zero IO, no locks, no allocations beyond the counter |

`ObservabilityController.evaluate(queue_fill_ratio)` is a pure function returning the recommended
mode; `observability_status()` exposes `{mode, queue_fill_ratio, events_dropped, survival_counts}`
for debugging. If events seem to be missing under load, check this status first before assuming a
code bug — `PRESSURE`/`DEGRADED` sampling is working as designed.

## Prometheus Metrics

- `sim_hard_law_violations_total{law_id="...", severity="ERROR"}` — cumulative Counter.
- `sim_hard_law_last_violation_tick` — Gauge, `-1` if no violations have occurred yet.

## Debugging a Failing Check — Practical Steps

1. Check `observability_status()` first if events seem to be missing — rule out `PRESSURE`/
   `DEGRADED`/`SURVIVAL` mode sampling before assuming a bug.
2. For a hard-law violation, check the current `ObservabilityMode` first — under `LONG_RUN` you
   won't see it in the log stream (see the gap above); check `hard_law_violations.jsonl` instead.
3. Real test files to read/run first: `tests/engine/test_hard_law_monitor.py` (unit-level law
   checks), `tests/perf/test_hard_law_monitor_overhead.py` (confirms `LIGHT` mode adds no
   measurable tick-compute overhead — useful if you suspect a perf regression from adding a new
   law), `tests/unit/observability/test_event_recorder.py` and
   `tests/unit/observability/test_observability_hardening.py` (`EventRecorder`/backpressure),
   `tests/integration/observability/test_phase28_observability_degradation.py` (mode transitions
   under real load), `tests/architecture/test_phase19_observability_boundaries.py` (hot-path
   isolation rules — see `observability_hot_path_safety_contract.md` §§1-4 for what's forbidden in
   the hot path).

## Out of Scope for This Skill

Development-side work in `src/simulation_quality/` (pillar scoring, `quality_hub.py` internals) is
a related but distinct domain — see the `simq-dev` skill.
