---
ticket_id: TCK-20260619-E33-MACRO-ECONOMY
phase: investigation
date: 2026-06-20
---

# Investigation: Macro-Economy Health Metrics

## Current State (verified 2026-06-20)

### EconomyHealthMonitor
Does NOT exist. No Gini coefficient, no transaction velocity tracking, no inflation detection.

### Governance phase — `docs/engine/governance_logic.md`
`EconomyHealthMonitor` should run as a governance phase step. Location TBD — check `src/engine/` governance files before implementing.

### SimulationEvent — `src/observability/events.py:L54`
Exists. New alert event kinds (`ECONOMIC_ALERT`, `DEFLATION_RISK`, etc.) need to be added.

### Gold state — `src/core/state.py`
Entity gold is tracked in inventory/biological state. Gini coefficient requires reading gold across all entities — feasible by scanning `state.entities.values()`.

### known_limitations.md — `docs/engine/known_limitations.md`
Documents "reputation discounts unsupported" — E33D closes this gap. Must remove the claim on completion.

### Dynamic pricing
Already exists for calamity/survival pressure. E33 does not replace it — adds macro-level monitoring on top.

## Key Constraint
E33 requires E32 (multi-episode macro trends need campaign continuity) and P0-HUNGER-SATIATION (economic activity must be non-zero). Do not implement until those are complete.

## Gap Summary

| Gap | Size |
|---|---|
| `EconomyHealthMonitor` + metrics | ~80 lines |
| Alert event kinds + emission | ~30 lines |
| REST endpoint `/api/v1/economy/health` | ~40 lines |
| Gold sink mechanisms (degradation/fees/taxes) | ~60 lines |
| Reputation-based shop discounts | ~40 lines |
