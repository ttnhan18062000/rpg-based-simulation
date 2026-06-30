---
ticket_id: TCK-20260619-E33-MACRO-ECONOMY
phase: test_plan
date: 2026-06-20
---

# Test Plan: Macro-Economy Health Metrics

## Unit Tests (new file: tests/unit/economy/test_economy_health_monitor.py)

### test_gini_coefficient_computed_correctly
- Known gold distribution {A:100, B:0, C:0}; assert Gini ≈ 0.667 (within 0.01)

### test_inflation_spiral_alert_emitted (E33B)
- Inject rapid gold creation; run 2000 ticks; assert INFLATION_SPIRAL event in simulation_events.jsonl

### test_economic_collapse_alert_on_zero_transactions (E33B)
- Zero-transaction region for 200 ticks; assert ECONOMIC_COLLAPSE event

## Integration Tests (new file: tests/integration/scenarios/test_macro_economy.py)

### test_gold_sink_reduces_accumulation_rate (E33C)
- Trigger INFLATION_SPIRAL; assert gold_creation_rate decreases in next 200-tick window

### test_reputation_discount_applies (E33D)
- Entity with high Faction A reputation; assert lower price at Faction A shop vs. neutral entity

## Validation
```bash
pytest tests/unit/economy/test_economy_health_monitor.py -x -v
pytest tests/integration/scenarios/test_macro_economy.py -x -v -m slow
```
