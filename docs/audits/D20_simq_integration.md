---
status: active
layer: observability
authority: P1
audience: developer
tags: [audit, simulation-quality, simq, integration, observability, event-bus]
---

# D20 — Simulation Quality Module Integration

## Dimension Profile

| Axis | Value |
|---|---|
| **Group** | A — Simulation Quality |
| **State** | `done` |
| **Impact** | 4 / 5 |
| **Interest** | 5 / 5 |
| **Priority** | 9 |
| **Method** | run-sim + code-read |
| **Audit date** | 2026-06-30 |

**What this dimension answers:** Is the SimQ module actually receiving events and scoring
live simulation runs — or is it built but disconnected? This audit exercises the full path
from kernel tick → observability queue → SimQ hub → pillar scores, using the in-process feed
mode across two deterministic seeds.

**Related dimensions:**
| Dimension | Relationship |
|---|---|
| D03 (Behavioral Emergence) | Prior run observations that SimQ is now meant to quantify |
| D06 (Long-Run Health) | SimQ should replace manual metric-window inspection for health monitoring |
| D04 (Balance & Tuning) | Calibration of SimQ thresholds is a prerequisite for D04 tuning |

---

## Run Configuration

| Field | Value |
|---|---|
| World | `sandbox_world` (worldtemplate.v1, 23 entities) |
| Ticks | 200 |
| Seeds | 42, 137 |
| Feed mode | `InProcessQualityFeed` (in-process queue drain) |
| Scorers active | All 10 pillar scorers (COGNITION, AGENCY, COMBAT, FACTION, ECONOMY, PROGRESSION, SOCIAL, INFORMATION, WORLD, NARRATIVE) |
| Config profile | `default` |
| Run date | 2026-06-30 |

---

## Observed Results

Both seeds completed 200 ticks without error. Final state hashes were stable and
deterministic. The simulation engine ran correctly.

| Metric | Seed 42 | Seed 137 |
|---|---|---|
| Outcome | SUCCESS | SUCCESS |
| Elapsed | 11.02s | 10.86s |
| Entity count | 23 | 23 |
| Final state hash | `9b42f891…` | `69572fb8…` |
| Hard law violations | 0 | 0 |
| Feed dropped events | 0 | 0 |
| **SimQ tick count** | **0** | **0** |
| **Total events scored** | **0** | **0** |

### Pillar scores — Seed 42

| Pillar | Raw score | Normalized | Grade | Event count |
|---|---|---|---|---|
| COGNITION | 0.0 | 0.0 | C | 0 |
| AGENCY | 0.0 | 0.0 | C | 0 |
| COMBAT | 0.0 | 0.0 | C | 0 |
| FACTION | 0.0 | 0.0 | C | 0 |
| ECONOMY | 0.0 | 0.0 | C | 0 |
| PROGRESSION | 0.0 | 0.0 | C | 0 |
| SOCIAL | 0.0 | 0.0 | C | 0 |
| INFORMATION | 0.0 | 0.0 | C | 0 |
| WORLD | 0.0 | 0.0 | C | 0 |
| NARRATIVE | 0.0 | 0.0 | C | 0 |

Results for seed 137 were identical. All grades C (normalized score = 0.0) — not from
degenerate behavior, but from zero events reaching the hub.

---

## Root Cause: Integration Bridge Not Connected

The SimQ module infrastructure is fully built and tested in isolation. The failure is
a wiring gap in the event delivery path.

### How the path is designed to work

```
Kernel.tick_once()
  → EventExtractor.extract()         # read-only state diff observer
  → EventRecorder.record(events)     # pushes ObservabilityEventEnvelope to global queue
  → BoundedObservabilityQueue        # module-level singleton
  → QueueDrainWorker._run()          # background thread, pops envelopes
      → if quality_fn: quality_fn(envelope)   # calls hub.on_envelope()
  → QualityHub.on_envelope()         # routes to pillar scorers
```

`QueueDrainWorker` already has a `quality_fn: Optional[Callable]` slot (
`src/observability/queue.py:97`) intended for exactly this purpose. When set, the worker
calls it for every envelope it drains.

### What actually happens today

The kernel creates `EventRecorder` which creates its own `QueueDrainWorker` — but passes
**no** `quality_fn`. The hub is never registered as a callback.

`InProcessQualityFeed` (used by this audit) creates a **second** `QueueDrainWorker` on
the same queue. Both workers race to drain the same items. Because the EventRecorder's
worker is started first as part of kernel init, it consumes events before the feed's
worker can reach them. `hub.on_envelope()` is never called. `tick_count` stays 0.

Additionally, `set_quality_hub()` in `src/api/dependencies.py` is defined but never
called from the server startup (`server.py` lifespan) or the CLI (`cli/entry.py`). There
is no execution path where the hub is registered with the server-side dependency injector.

### Three independent gaps

| Gap | Location | Description |
|---|---|---|
| G1 | `src/engine/kernel.py` | EventRecorder's QueueDrainWorker created without `quality_fn` |
| G2 | `src/api/server.py` | `set_quality_hub()` never called in server lifespan |
| G3 | `src/simulation_quality/feed.py` | `InProcessQualityFeed` creates competing consumer instead of using existing slot |

---

## Recommended Fix

**Minimal wiring (G1 only — addresses in-process and CLI paths):**

In `Kernel.__init__`, after constructing the hub and feed, pass
`quality_fn=hub.on_envelope` to the `EventRecorder`'s `QueueDrainWorker`. This avoids
the competing-consumer issue entirely and uses the already-designed callback slot.

```python
# Kernel.__init__ (pseudocode — exact lines TBD at implementation time)
from src.simulation_quality.feed import build_feed_from_env
from src.simulation_quality.quality_hub import QualityHub

feed = build_feed_from_env()
if feed is not None:
    hub = QualityHub(scorers, weights, persistence, run_id=self._run_id)
    self._event_recorder = EventRecorder(
        ...,
        quality_fn=hub.on_envelope,   # thread-safe; QueueDrainWorker already handles this
    )
    self._quality_hub = hub
```

**Server wiring (G2):**

Call `set_quality_hub(hub)` in the `lifespan` function of `server.py` after the manager
starts, so REST endpoints return live data. The shutdown handler already reads
`get_quality_hub()` for the final report write — it just needs the hub set on startup.

**Remove competing consumer (G3):**

`InProcessQualityFeed` should be deprecated or changed to a thin wrapper that injects
`quality_fn` into an existing `QueueDrainWorker` rather than creating its own. The broker
mode path (`BrokerQualityFeed`) is unaffected as it uses a separate Redis stream.

---

## What SimQ Would Show Once Wired

Based on D06 observations (quest_event, combat_damage, entity lifecycle events flowing
across 200-tick runs), a wired 200-tick run on sandbox_world would surface:

- **COMBAT**: positive signal from `combat_active` and `combat_resolved` events — expected B or A
- **AGENCY**: positive from `action_executed` and project completions — expected A
- **ECONOMY**: likely B/C — sandbox_world has minimal trade and zero gold flow in D06
- **FACTION**: likely C/D — no faction diplomacy observed in sandbox_world
- **COGNITION/SOCIAL/NARRATIVE**: insufficient events in 200 ticks for sandbox_world to leave the zero-score zone without time-gate negatives activating

Calibration with a richer world composition over 500–1000 ticks is required to establish
meaningful grade baselines. Threshold calibration (`tools/calibrate_simq.py`) is unblocked
once G1 is fixed.

---

## Module Health (Independent of Integration Gap)

The SimQ module itself is well-built:

| Component | Status |
|---|---|
| 10 pillar scorers | Implemented, unit-tested |
| QualityHub | Implemented with thread-safe accumulators |
| PillarAccumulator | Sliding window, loop detection, worst-event tracking |
| QualityPersistence | Write-through to `data/runs/` |
| REST API (5 endpoints) | Implemented; returns `{"enabled": false}` when disabled |
| Event translation layer | `_TRANSLATE_SIMPLE` + `_TRANSLATE_CONDITIONAL` in quality_hub.py |
| EventExtractor emissions | Social, faction, narrative events added (TCK-20260629-SIMQ-EMIT-*) |
| Parity ledger | SIMQ-CALIBRATED-001 marked `verified` |

The module passes its tests and the API routes respond correctly. Only the kernel→hub
event bridge is missing.

---

## Findings Summary

| # | Finding | Severity |
|---|---|---|
| F1 | `QueueDrainWorker.quality_fn` slot exists but is never populated at kernel init | High |
| F2 | `set_quality_hub()` is never called; REST quality endpoints always return hub=None path | High |
| F3 | `InProcessQualityFeed` creates a competing consumer that races against EventRecorder | Medium |
| F4 | Zero events scored across both 200-tick seeds — SimQ produces no actionable signal | High |
| F5 | Threshold calibration (`tools/calibrate_simq.py`) remains blocked until F1 is fixed | Medium |

**Next ticket:** Create a standard-tier ticket to wire SimQ into the kernel startup path
(G1 fix) and the server lifespan (G2 fix). Estimated scope: 2–3 files, no architecture
changes — the `quality_fn` slot was designed for this.
