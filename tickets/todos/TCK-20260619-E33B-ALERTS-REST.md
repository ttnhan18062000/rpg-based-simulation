---
status: open
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260619-E33B-ALERTS-REST
phase: open
date: 2026-06-20
tags: [macro-economy, alerts, rest-api, phase-3]
---

# TCK-20260619-E33B-ALERTS-REST

## Title
Epic 3.3B · Economic Alert Events + REST Endpoint

## Status
OPEN

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
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
