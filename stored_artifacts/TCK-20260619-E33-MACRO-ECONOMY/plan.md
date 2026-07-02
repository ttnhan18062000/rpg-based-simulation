---
ticket_id: TCK-20260619-E33-MACRO-ECONOMY
phase: plan
date: 2026-06-20
---

# Plan: Macro-Economy Health Metrics — Epic Scope

## Child Ticket Sequence

```
E33A (EconomyHealthMonitor + metrics)
  └──► E33B (alert events + REST endpoint)
         └──► E33C (gold sink mechanisms — triggered by INFLATION_SPIRAL)
                └──► E33D (reputation discounts)
```

E33C requires E33B (needs INFLATION_SPIRAL alert to trigger sinks). E33D is independent of C but benefits from an active economy (run after E33A).

## Child Ticket Summary

| Ticket | Scope | Key Deliverable |
|---|---|---|
| E33A | `EconomyHealthMonitor` governance step: Gini coefficient, transaction velocity, average price index per region per tick-window | `src/engine/economy_health_monitor.py` (new) |
| E33B | Alert event kinds (DEFLATION_RISK, INFLATION_SPIRAL, ECONOMIC_COLLAPSE, GOLD_HOARDING); emit to simulation_events.jsonl; REST `GET /api/v1/economy/health` | New event kinds + `src/api/routes/economy.py` |
| E33C | Gold sink mechanisms via authoritative pipeline: equipment degradation cost, service fees, tax events — triggered on INFLATION_SPIRAL alert | Authoritative pipeline extension |
| E33D | Reputation-based shop discounts: entity with high faction rep gets lower price at faction shops; close known_limitations.md gap | Shop pricing + known_limitations.md update |

## Acceptance Path

1. E33A: 2000-tick run produces `metric_windows.jsonl` with Gini + transaction velocity per region
2. E33B: ≥1 `ECONOMIC_ALERT` event; GET `/api/v1/economy/health` returns per-region state
3. E33C: gold_creation_rate decreases in 200-tick window after INFLATION_SPIRAL sink fires
4. E33D: entity with high rep gets discount; `known_limitations.md` updated
