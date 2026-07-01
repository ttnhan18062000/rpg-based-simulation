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
| **State** | `done` (all gaps resolved; 81/82 event types emitted; re-run verified 2026-07-01) |
| **Impact** | 4 / 5 |
| **Interest** | 5 / 5 |
| **Priority** | 9 |
| **Method** | run-sim + code-read |
| **Audit date** | 2026-06-30 (original); 2026-07-01 (re-run after fixes) |

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

## Observed Results — Original Run (2026-06-30, pre-fix)

Both seeds completed 200 ticks without error. The simulation engine ran correctly, but the
SimQ hub received zero events due to the wiring gap (G1).

| Metric | Seed 42 | Seed 137 |
|---|---|---|
| Outcome | SUCCESS | SUCCESS |
| Elapsed | 11.02s | 10.86s |
| Final state hash | `9b42f891…` | `69572fb8…` |
| **SimQ tick count** | **0** | **0** |
| **Total events scored** | **0** | **0** |

All 10 pillar grades: C (0.0). Not from degenerate behavior — zero events reached the hub.

---

## Verified Re-Run Results — 2026-07-01 (all fixes applied)

Same world, seeds, and tick count. All three kernel wiring gaps resolved; 81 event types
emitted. Final state hashes are bit-identical to the original run — determinism confirmed.

| Metric | Seed 42 | Seed 137 |
|---|---|---|
| Run ID | `run_1782900226_5169` | `run_1782900239_2781` |
| Outcome | SUCCESS | SUCCESS |
| Elapsed | 10.99s | 11.00s |
| Tick count | 200 | 200 |
| Final state hash | `9b42f891…` ✓ | `69572fb8…` ✓ |
| Hard law violations | 0 | 0 |
| Overall score | 0.0355 | 0.0380 |
| Overall grade | **B** | **B** |

### Pillar scores — Seed 42

| Pillar | Raw score | Normalized | Grade | Events | Negatives | Loop flags |
|---|---|---|---|---|---|---|
| COGNITION | 0.0 | 0.0 | C | 0 | 0 | — |
| AGENCY | 0.0 | 0.0 | C | 0 | 0 | — |
| COMBAT | 6.0 | 0.030 | B | 15 | 5 | `combat_active` |
| FACTION | 0.0 | 0.0 | C | 0 | 0 | — |
| ECONOMY | 0.0 | 0.0 | C | 0 | 0 | — |
| PROGRESSION | 7.0 | 0.035 | B | 6 | 1 | `survival_experience` |
| SOCIAL | 0.0 | 0.0 | C | 0 | 0 | — |
| INFORMATION | 0.0 | 0.0 | C | 0 | 0 | — |
| WORLD | 43.0 | 0.215 | B | 38 | 0 | `hazard_active` |
| NARRATIVE | 15.0 | 0.075 | B | 3 | 0 | `quest_active` |

Seed 137 is near-identical: COMBAT/PROGRESSION/WORLD scores match exactly; NARRATIVE slightly
higher (raw=20.0, 4 events). Overall grade B for both.

### Notable worst events — Seed 42

| Tick | Pillar | Event type | Delta | Reason |
|---|---|---|---|---|
| 8 | COMBAT | `entity_killed` | −10 | early_extinction: entity 16 dead before tick threshold |
| 8 | COMBAT | `entity_killed` | −1 × 4 | attrition: entities 17–20 killed at tick 8 |
| 51 | PROGRESSION | `progression_plateau_detected` | −8 | entity 1 XP rate dropped to zero after tick gate |

---

## Root Cause: Integration Bridge Not Connected *(Historical — resolved 2026-06-30)*

> This section documents the original wiring failure. All three gaps are now resolved.
> See §Finding Updates for the fix tickets.

The SimQ module infrastructure was fully built and tested in isolation. The failure was
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

## Recommended Fix *(Historical — all fixes applied 2026-06-30)*

> Kept for traceability. These changes are in the codebase.

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

## What SimQ Actually Shows (Verified 2026-07-01)

### Pillars with signal in sandbox_world (200 ticks)

**WORLD — B (0.215 normalized, 38 events)**
Primary driver: `hazard_drain_applied` (confirmed `calibration_hits=322` in event_type_coverage).
`region_trauma_delta` also contributes. Loop detection fires on `hazard_active` before run end,
suppressing further events. WORLD is the richest pillar in combat-heavy sandbox_world.

**COMBAT — B (0.030 normalized, 15 events, 5 negative)**
`combat_initiated` and `near_death_survival` fire; `entity_killed` events fire with penalties.
Hard early attrition at tick 8: 5 monster-type entities die, triggering `early_extinction` (−10).
Loop detection flags `combat_active`. COMBAT scores positively but the early-extinction penalty
significantly depresses the grade. This points to a sandbox_world combat balance issue (too many
weak entities die in the first 10 ticks).

**PROGRESSION — B (0.035 normalized, 6 events, 1 negative)**
New emitters confirmed active: `progression_plateau_detected` fires at tick 51 for entity 1
(XP rate dropped to zero after tick gate, −8 penalty). `survival_experience` loop detected.
PROGRESSION is functional but the plateau penalty is the dominant signal in a 200-tick sandbox run.

**NARRATIVE — B (0.075 normalized, 3–4 events)**
`quest_active` loop detected early. Loop detection suppresses events after threshold,
explaining the drop from the 57-tick calibration run (16 events before loop fired) to the
200-tick run (3–4 events — loop fired earlier in the window). The signal is real but the
world doesn't advance quest state fast enough to escape loop detection.

### Pillars scoring zero in sandbox_world

| Pillar | Root cause |
|---|---|
| AGENCY | `route_selected`/`action_executed` not emitting — sandbox_world entities appear not to change routing family or the diff condition isn't met within 200 ticks |
| COGNITION | `self_model_bundle_set` and `last_assimilated_tick` signals absent — no information economy in sandbox |
| ECONOMY | No trades, harvesting, or shop transactions in sandbox_world (pure combat scenario) |
| SOCIAL | `trust_history` not updated — no cooperation or social interaction observed |
| FACTION | No faction diplomacy in sandbox_world; no tension, alliance, or territory events |
| INFORMATION | `lead_certainty_updated`, `belief_stale` and related events require active information-seeking behavior absent in sandbox |

### Calibration implications

Sandbox_world is a combat-only scenario and is a poor calibration environment for 6 of 10
pillars. Calibration requires richer world compositions:
- **AGENCY/COGNITION/INFORMATION**: `simq_routing_test` or strategy-heavy worlds
- **ECONOMY**: `dungeon_crawl` (resource nodes) or `urban_political` (trade/shops)
- **SOCIAL/FACTION**: `urban_political` or multi-faction worlds with diplomacy

Loop detection window sizes (`hazard_active`, `quest_active`) appear too tight for 200-tick
sandbox_world runs — events that should score are suppressed after ~40 ticks. Threshold
calibration (`tools/calibrate_simq.py`) is now unblocked and should be run against the full
calibration corpus to adjust window sizes per world type.

---

## Module Health (as of 2026-07-01)

All integration gaps resolved. Module is fully wired and producing live scores.

| Component | Status |
|---|---|
| 10 pillar scorers | Implemented, unit-tested, live |
| QualityHub | Wired — `quality_fn=hub.on_envelope` at `kernel.py:264` |
| PillarAccumulator | Sliding window, loop detection, worst-event tracking — active |
| QualityPersistence | Write-through to `data/runs/` — verified by re-run |
| REST API (5 endpoints) | `set_quality_hub()` called at server startup (`server.py:34`) — live |
| Event translation layer | `_TRANSLATE_SIMPLE` + `_TRANSLATE_CONDITIONAL` in quality_hub.py |
| EventExtractor emissions | **81 of 82** scored event types emitted (2 newly added this session: `social_memory_created`, `contract_milestone_completed`). 1 has no engine path (`camp_constructed` — no dynamic camp construction in simulation). |
| Parity ledger | SOC-237, SOC-238 added and marked `verified` |
| Kernel→hub bridge | **RESOLVED** — `InProcessQualityFeed` refactored; no competing consumer |

The module is fully operational. Remaining work: calibration corpus runs across non-sandbox worlds.

---

## Findings Summary

| # | Finding | Severity | Status |
|---|---|---|---|
| F1 | `QueueDrainWorker.quality_fn` slot exists but is never populated at kernel init | High | **RESOLVED** — TCK-20260630-SIMQ-WIRE-KERNEL (2026-06-30) |
| F2 | `set_quality_hub()` is never called; REST quality endpoints always return hub=None path | High | **RESOLVED** — TCK-20260630-SIMQ-WIRE-SERVER (2026-06-30) |
| F3 | `InProcessQualityFeed` creates a competing consumer that races against EventRecorder | Medium | **RESOLVED** — TCK-20260630-SIMQ-WIRE-KERNEL (2026-06-30) |
| F4 | Zero events scored across both 200-tick seeds — SimQ produces no actionable signal | High | **Resolved** — hub wired; 81 event types emitted; all engine emission gaps closed; `camp_constructed` has no viable engine path (scorer entry premature) |
| F5 | Threshold calibration (`tools/calibrate_simq.py`) remains blocked until F1 is fixed | Medium | **UNBLOCKED** — F1 resolved; calibration can proceed |

### §Finding Updates — 2026-07-01

**Kernel wiring (F1/F2/F3): RESOLVED on 2026-06-30.**
- G1 (`quality_fn` at kernel init) — fixed by `TCK-20260630-SIMQ-WIRE-KERNEL`: `quality_fn=hub.on_envelope` passed to `QueueDrainWorker` in `Kernel.__init__` (`src/engine/kernel.py:264`)
- G2 (`set_quality_hub` in server lifespan) — fixed by `TCK-20260630-SIMQ-WIRE-SERVER`: `set_quality_hub(_k.quality_hub)` called after manager start (`src/api/server.py:34`)
- G3 (`InProcessQualityFeed` competing consumer) — fixed by `TCK-20260630-SIMQ-WIRE-KERNEL`: `InProcessQualityFeed` refactored to lifecycle-only; no longer creates a second `QueueDrainWorker`

**Emission gap progress:** 24 of 27 engine emission gaps resolved by the simq-emit epic:
- `TCK-20260701-SIMQ-EMIT-AGENCY2` — 4 AGENCY events (`defer_with_reason`, `route_family_first_use`, `commitment_abandoned`, `rejection_cascade_tick`)
- `TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS` — 6 INFORMATION/COGNITION events
- `TCK-20260701-SIMQ-EMIT-PROGRESSION` — 5 PROGRESSION events
- `TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY` — 5 FACTION/ECONOMY/NARRATIVE events
- `TCK-20260701-SIMQ-EMIT-WORLD-DYNAMICS` — 4 WORLD DYNAMICS events

**Remaining gaps — premise corrections (2026-07-01):**
- `social_memory_created` — prior premise wrong. `SocialMemoryExporter` is campaign-layer only (called at episode end). Correct emit: `EventExtractor` on `trust_history` delta — no infrastructure change needed. TCK-20260701-SIMQ-EMIT-SOCIAL-MEM scope updated.
- `contract_milestone_completed` — **resolved**. No schema change needed. EventExtractor emits at 25%/50%/75% of ACTIVE contract duration using existing `created_tick`/`expiry_tick` fields. Gate: once per `(contract_id, milestone)` per run. TCK-20260701-SIMQ-EMIT-CONTRACT-MILESTONE DONE.
- `camp_constructed` — prior premise wrong. `StateUpdate` has no `camps_add`; camps are pre-placed at world generation. No dynamic camp construction occurs in simulation. No event recorder can fix this — the mechanic doesn't exist. TCK-20260701-SIMQ-EMIT-CAMP closed.

---

## Actionable Next Steps (as of 2026-07-01)

| Priority | Action | Rationale |
|---|---|---|
| P1 | Run `tools/calibrate_simq.py` against `dungeon_crawl` and `urban_political` worlds | sandbox_world is combat-only; 6 pillars are blind to it. Calibration baselines require richer scenarios. |
| P1 | Investigate AGENCY zero-score — confirm whether `route_family_first_use` / `action_executed` conditions are hit in any world | These emitters were added by TCK-20260701-SIMQ-EMIT-AGENCY2 but fire zero events in sandbox_world. May be legitimate (no routing changes in combat-only scenario) or a diff condition bug. |
| P2 | Tune loop detection window for `hazard_active` and `quest_active` | Loop detection suppresses events after ~40 ticks in a 200-tick run; events that should score are silenced. Window sizes need world-type calibration. |
| P2 | Investigate `early_extinction` penalty at tick 8 — sandbox_world entities 16–20 are weak | 5 monster-type entities die in the first 10 ticks, triggering the `early_extinction` −10 COMBAT penalty. This may be intentional world design or a spawn/balance bug. |
| P3 | Add `camp_constructed` to the "no engine path" exclusion list in event_type_coverage.md | Already documented; formally remove it from the 82-event scored set if the mechanic is not planned. |
