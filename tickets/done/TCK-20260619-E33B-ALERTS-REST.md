---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260619-E33B-ALERTS-REST
phase: done
date: 2026-06-20
tags: [macro-economy, alerts, rest-api, phase-3]
---

# TCK-20260619-E33B-ALERTS-REST

## Title
Epic 3.3B · Economic Alert Events + REST Endpoint

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`EconomyHealthMonitor` (E33A) samples metrics but emits nothing. This ticket adds 4 alert event kinds and a REST endpoint to query current economic health per region.

**Requires:** TCK-20260619-E33A-HEALTH-MONITOR

## Scope

### 1. Add alert event kinds to `src/observability/events.py`

```python
DEFLATION_RISK = "DEFLATION_RISK"
INFLATION_SPIRAL = "INFLATION_SPIRAL"
ECONOMIC_COLLAPSE = "ECONOMIC_COLLAPSE"   # region zero-transaction for 200 ticks
GOLD_HOARDING = "GOLD_HOARDING"           # Gini > 0.8
```

### 2. Wire alert evaluation in `EconomyHealthMonitor.sample()`

After computing snapshot: check alert conditions and emit events via `StateUpdate(events_add=[...])`.

### 3. REST endpoint `GET /api/v1/economy/health`

In new `src/api/routes/economy.py`:
```
GET /api/v1/economy/health
→ {
    tick: N,
    regions: {
      "region_1": {gini: 0.45, transaction_velocity: 12.3, alert: null},
      "region_2": {gini: 0.82, transaction_velocity: 0.0, alert: "GOLD_HOARDING"},
    }
  }
```

## Acceptance Criteria
- 2000-tick run with rapid gold creation emits ≥1 `INFLATION_SPIRAL` event
- `test_inflation_spiral_alert_emitted` passes
- `GET /api/v1/economy/health` returns per-region health state

## Related Tickets
- TCK-20260619-E33-MACRO-ECONOMY (parent epic)
- TCK-20260619-E33A-HEALTH-MONITOR (required)
- TCK-20260619-E33C-GOLD-SINK (blocked on this — needs INFLATION_SPIRAL to trigger sinks)

## Related Code Areas
- `src/observability/events.py` (add alert event kinds)
- `src/engine/economy_health_monitor.py` (wire alert emission)
- `src/api/routes/economy.py` (new)

## Test Summary
```bash
pytest tests/unit/economy/test_economy_health_monitor.py -x -v
pytest tests/integration/scenarios/test_macro_economy.py::test_inflation_spiral_alert_emitted -x -v -m slow
```
## Implementation Notes

- Alert events are `SimulationEvent` subclasses (not `WorldEvent`) — `event_category="economy"`. `StateUpdate.events_add` does not exist; alerts are dispatched via `kernel._event_listeners` callbacks.
- `EconomyHealthMonitor.check_alerts(snapshot, tick, region_id)` added as a pure static method. Returns `list[SimulationEvent]`. Only INFLATION_SPIRAL (gini>0.7) and GOLD_HOARDING (gini>0.8) emitted in E33B; ECONOMIC_COLLAPSE and DEFLATION_RISK defined but deferred to E33C (velocity=stub=0.0).
- Kernel wires alerts inside the existing `if self._metric_recorder:` try/except block, after `record_economy_snapshot()`.
- REST endpoint `GET /api/v1/economy/health` reads `manager.latest_state` via `get_engine_manager()`, groups alive entities by `e.region_id` (None→"global"), computes per-region Gini, evaluates alerts, returns shaped dict via `EconomyPresenter`.
- No raw `AuthoritativeState` or Pydantic models exposed from API; `EconomyPresenter.present_health()` returns plain dict.
- 12 unit tests + 1 slow integration test written.

## Files Changed
- `src/observability/events.py` (modified — 4 alert SimulationEvent subclasses added)
- `src/economy/health_monitor.py` (modified — check_alerts() static method, threshold constants, imports)
- `src/engine/kernel.py` (modified — alert dispatch wired after record_economy_snapshot)
- `src/api/presenters/economy.py` (created — EconomyPresenter)
- `src/api/routes/economy.py` (created — GET /api/v1/economy/health)
- `src/api/server.py` (modified — economy router registered)
- `tests/unit/economy/test_economy_alerts.py` (created — TC-B01 through TC-B08)
- `tests/unit/api/test_economy_route.py` (created — TC-B06 through TC-B11)
- `tests/integration/scenarios/test_macro_economy.py` (created — TC-B09)
- `docs/parity_ledger/town_resource.yaml` (modified — TOWN-178 added)

## Completion Summary
Added 4 economy alert `SimulationEvent` subclasses (`DEFLATION_RISK`, `INFLATION_SPIRAL`, `ECONOMIC_COLLAPSE`, `GOLD_HOARDING`) to `src/observability/events.py`. Added `EconomyHealthMonitor.check_alerts()` static method that emits `INFLATION_SPIRAL` (gini>0.7) and `GOLD_HOARDING` (gini>0.8); ECONOMIC_COLLAPSE/DEFLATION_RISK defined but deferred to E33C (velocity=stub=0.0). Wired alert dispatch in kernel PERSISTENCE phase hook via `_event_listeners`. Created `GET /api/v1/economy/health` endpoint with `EconomyPresenter` that groups alive entities by `navigation.region_id`, computes per-region Gini, and returns shaped read model. Registered economy router in `server.py`. 25 tests pass (23 unit + 1 slow integration `test_inflation_spiral_alert_emitted`). Parity entries TOWN-177 updated, TOWN-178 added.
