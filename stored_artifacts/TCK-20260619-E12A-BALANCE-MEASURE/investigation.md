---
ticket_id: TCK-20260619-E12A-BALANCE-MEASURE
phase: investigation
date: 2026-06-20
---

# Investigation: Balance Measurement Pass

## Infrastructure Available

### MetricsService.extract_metrics(state) → WorldMetrics
- `total_gold`: float — sum across all entity inventories  
- `quest_status_counts`: Dict[str, int] — keys: ACTIVE, COMPLETED, FAILED, EXPIRED

### kernel.state at any tick
- `state.entities` → EntityState[] (HP, gold, inventory)
- `state.resource_nodes` → ResourceNodeState[] (amounts — proxy for harvesting)

### Not tracked by existing infrastructure
- Harvesting event count (HARVEST_RESOURCE action is processed but not logged as SimulationEvent)
- Crafting event count (REQUEST_CRAFT same)
- Routes scored with blockers / total routes scored

### Blocker model
- `AdventureRouteOption.blockers: Tuple[str, ...]` — strings only, no severity field
- Implication: E12B graduated penalty would require adding a severity enum or proxy classification

## Measurement Approach

Write `tools/balance_measure.py` that:
1. Loads `urban_political` via WorldRepository + WorldCompiler (seed=42)
2. Monkey-patches `AdventureRouteScorer.score()` to count `routes_total` and `routes_with_blockers`
3. Monkey-patches `economy.py` `Economy.process()` to count HARVEST_RESOURCE and REQUEST_CRAFT actions
4. Runs 1000 ticks, samples per-100-tick window
5. Computes all D04 target metrics
6. Prints structured JSON report

## urban_political World
- Settlement-heavy, 27 entities at seed=202 (generation_seed), faction pressure, trade routes
- Modules: frontier_village_core + trading_company_hub (6 merchants) + bandit_road_trade_pressure
- P0-HUNGER-SATIATION done: hunger urgency calibrated, food opportunities available
- P0-ENTITY-INIT done: entities initialized with diverse attributes
- E11 done: personality traits seeded and active

## Expected Metric Ranges (hypothesis before measurement)

| Metric | Expected range | Basis |
|---|---|---|
| Harvesting rate (events/entity/100t) | 0.2–2.0 | D08 showed basic economic activity in urban_political |
| Quest completion rate | 0.1–0.5 per 100t | D08 F4 showed quest activity |
| Gold accumulation | > 0 by tick 1000 | D08 showed trade activity |
| Attrition at tick 1000 | < 40% | D03 showed moderate combat |
| Blocker frequency | unknown — this is the key question | |
