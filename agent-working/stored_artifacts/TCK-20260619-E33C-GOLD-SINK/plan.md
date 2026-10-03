# Plan: TCK-20260619-E33C-GOLD-SINK

## Steps

### Step 1: Extend conservation.py — add REPAIR_FEE and SERVICE_FEE source kinds

**File:** `src/core/conservation.py`

Add `REPAIR_FEE` and `SERVICE_FEE` to the existing `TOWN_SERVICE`/`TAX` block (line 255).
Both follow the same pattern: deduct `gold_cost` from entity inventory, return accepted.
No items_add/items_remove. Includes existing contingent updates (biological, attribute, etc.).

**AC mapped:** Gold sinks go through authoritative pipeline.

### Step 2: Create GoldSinkSystem — src/engine/gold_sink.py

**Logic:**
- `GoldSinkSystem.apply(state, update, cadence)` — called from pipeline Phase 5.
- Only runs at `WINDOW_SIZE` tick boundaries (every 100 ticks), same as EconomyHealthMonitor.
- Calls `EconomyHealthMonitor.sample(state, state.tick)` — returns None if not boundary tick.
- If snapshot is None or gini <= INFLATION_SPIRAL_GINI_THRESHOLD: return update unchanged.
- For each alive entity with gold > 0:
  1. **REPAIR_FEE**: check `entity.equipment.durability`. If any slot < 0.5 (50%),
     emit `ResourceTransferIntent(source_kind="REPAIR_FEE", source_id="gold_sink",
     gold_cost=degraded_slot_count, gold_delta=0, transfer_kind="FEE")`.
     Capped: `gold_cost = min(degraded_slot_count, entity.inventory.gold)`.
  2. **SERVICE_FEE**: emit `ResourceTransferIntent(source_kind="SERVICE_FEE",
     source_id="gold_sink", gold_cost=1, gold_delta=0, transfer_kind="FEE")`.
     Only if entity.inventory.gold >= 1.
  3. **TAX**: compute mean gold across alive entities. If entity.gold > mean * 1.5:
     `tax = min(50, max(1, int(entity.inventory.gold * 0.05)))`.
     Emit `ResourceTransferIntent(source_kind="TAX", source_id="gold_sink",
     gold_cost=tax, gold_delta=0, transfer_kind="FEE")`.
- Append intents to existing entity EntityUpdate.resource_transfers.
- Track treasury: accumulate total `gold_cost` from all intents; add to
  `resource_updates={"metric_treasury_gold": total_collected}` on StateUpdate.
  (ResourceTransactionSystem will resolve which are accepted; for treasury tracking
  we record the total attempted — but to be conservative/accurate, we track via
  `resource_updates` only after the intents are injected, knowing resolver will
  reject on insufficient gold. This is acceptable since INSUFFICIENT_GOLD rejections
  effectively mean no gold moved. The resolver handles this correctly.)

**Conservation note:** The resolver already rejects if entity.gold < gold_cost, so
no gold is created or destroyed. Treasury is credited only for intents that pass.
Since `resource_updates` are applied after intents are resolved, we set a sentinel
`metric_treasury_gold_sink_applied=1.0` to mark that a sink cycle ran. Actual treasury
amount is computable from entity gold diffs. For simplicity we set `resource_updates`
with the gross attempted amount — acknowledged as advisory. The invariant test verifies
actual entity gold reduction matches.

**Revised approach (simpler and correct):** emit intents only — do not separately
track treasury in resource_updates during injection. The treasury credit is implicit
(gold leaving entities goes to the simulated "void" treasury). We track
`metric_gold_sink_ticks` as a counter. This matches the ticket's AC which only
requires gold accumulation rate decreases and the conservation invariant test.

### Step 3: Wire GoldSinkSystem into pipeline.py

**File:** `src/engine/pipeline.py`

In Phase 5 "Governance & Ecology", after `town_resolution` and before `world_dynamics`:
```python
from src.engine.gold_sink import GoldSinkSystem
update = run_phase("gold_sink", update, lambda u: GoldSinkSystem.apply(state, u, cadence))
```

**AC mapped:** Gold sinks go through authoritative pipeline.

### Step 4: Add GoldSinkAppliedEvent to observability events

**File:** `src/observability/events.py`

```python
class GoldSinkAppliedEvent(SimulationEvent):
    """Emitted when gold sink mechanisms apply during INFLATION_SPIRAL window."""
    gini_coefficient: float
    entities_affected: int
    total_gold_drained: int
    event_type: str = "GOLD_SINK_APPLIED"
    event_category: EventCategory = "economy"
    severity: EventSeverity = "INFO"
    source_system: str = "gold_sink_system"
    message: str = ""
```

GoldSinkSystem emits this event via `StateUpdate.world_events_add`-compatible mechanism
— actually via the existing SimulationEvent path. Since world_events_add carries
`WorldEvent` (not `SimulationEvent`), we record the event as a resource_update counter
instead: `metric_gold_sink_ticks += 1`, `metric_gold_sink_last_drain = total_attempted`.

**Simplified:** No new SimulationEvent — just resource_updates counters. This keeps
changes minimal and correct.

### Step 5: Write tests — tests/unit/economy/test_gold_sink.py

11 unit test cases per test_plan.md (TC-C01 through TC-C11).

### Step 6: Add integration test to test_macro_economy.py

`test_gold_sink_reduces_accumulation_rate` — 200-tick run with unequal wealth,
assert at least one gold sink transfer was accepted (entity gold decreased).

### Step 7: Update parity ledger — docs/parity_ledger/town_resource.yaml

Add TOWN-179 (gold sink mechanisms) and TOWN-180 (conservation invariant for sinks).

### Step 8: Copy ticket to inprogress, record monitoring

---

## Scope Guards

- Do NOT modify `ResourceTransactionResolver.resolve()` logic for TAX (already correct).
- Do NOT add TAX/FEE handling to `SHOP_BUY`/`SHOP_SELL` paths.
- Do NOT mutate `AuthoritativeState` directly anywhere.
- Do NOT add new fields to `AuthoritativeState` or `EntityState`.
- Gold sink ONLY fires at WINDOW_SIZE tick boundaries (cadence guard).
- ONLY fires when gini > 0.7 (INFLATION_SPIRAL threshold).

## Deviations

None anticipated.

## AC Mapping

| AC | Step |
|---|---|
| Gold_creation_rate decreases in 200-tick window after sink fires | Step 6 (integration test) |
| Gold sinks go through authoritative pipeline | Steps 1, 2, 3 |
| `test_gold_sink_reduces_accumulation_rate` passes | Step 6 |
