# Test Plan: TCK-20260619-E33C-GOLD-SINK

## Scope

Test the three gold sink mechanisms (REPAIR_FEE, SERVICE_FEE, TAX) for:
- Correct activation under INFLATION_SPIRAL condition (gini > 0.7)
- No activation when gini below threshold
- Conservation invariant (total gold constant)
- Authoritative pipeline path (ResourceTransferIntent)
- Treasury tracking (metric_treasury_gold)

## Test File

`tests/unit/economy/test_gold_sink.py`

## Test Cases

### TC-C01: repair_fee_applied_to_degraded_equipment
- Entity with equipped item durability < 50% and gini > 0.7
- GoldSinkSystem.apply() returns StateUpdate with resource_transfer for REPAIR_FEE
- Entity gold reduced by fee amount

### TC-C02: repair_fee_not_applied_above_durability_threshold
- Entity with all equipment durability >= 50% and gini > 0.7
- No REPAIR_FEE transfer emitted

### TC-C03: service_fee_applied_under_inflation
- Alive entity with gold > 0 and gini > 0.7
- SERVICE_FEE transfer emitted

### TC-C04: tax_applied_to_wealthy_entities
- Entity with gold above mean*1.5 and gini > 0.7
- TAX transfer emitted, amount = floor(gold * 0.05) clamped [1, 50]

### TC-C05: tax_not_applied_to_poor_entities
- Entity with gold below mean*1.5
- No TAX transfer emitted for that entity

### TC-C06: no_sinks_when_gini_below_threshold
- gini = 0.3 (healthy economy)
- No sink transfers emitted

### TC-C07: conservation_invariant
- Multiple entities with varied gold, gini > 0.7
- After GoldSinkSystem.apply() accepted intents: sum(entity gold) + treasury_delta = constant
- Verified by summing all gold_cost from intents

### TC-C08: sink_not_applied_to_dead_entities
- Dead entity (combat.alive=False) should not receive any sink transfer

### TC-C09: sink_respects_entity_gold_floor
- Entity with gold=0 receives no sink transfer (gold_cost check in resolver rejects)

### TC-C10: conservation_resolver_handles_repair_fee
- Unit test ResourceTransactionResolver with source_kind="REPAIR_FEE"
- Accepted when entity has sufficient gold
- Rejected (INSUFFICIENT_GOLD) when entity gold < gold_cost

### TC-C11: conservation_resolver_handles_service_fee
- source_kind="SERVICE_FEE", similar validation

### Integration: test_gold_sink_reduces_accumulation_rate
- 200-tick run with high gini (1 rich, 9 poor entities)
- Assert gold_sink transfers accepted in the run
- (per AC from ticket)
- Located in tests/integration/scenarios/test_macro_economy.py

## Run Command

```bash
pytest tests/unit/economy/test_gold_sink.py -x -v
pytest tests/integration/scenarios/test_macro_economy.py::test_gold_sink_reduces_accumulation_rate -x -v -m slow
```
