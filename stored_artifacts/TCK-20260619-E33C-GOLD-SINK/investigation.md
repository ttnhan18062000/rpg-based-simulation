# Investigation: TCK-20260619-E33C-GOLD-SINK

## Context

Gold sink mechanisms triggered when `INFLATION_SPIRAL` alert fires. Three mechanisms
required: equipment degradation fee, service fee surcharge, tax events. All must satisfy
conservation law (Chapter 03: gold transferred to treasury, never destroyed).

## Key Findings

### Conservation Infrastructure (already in place)

- `src/core/conservation.py` already handles `TOWN_SERVICE` and `TAX` source kinds
  (lines 255-272). They deduct `gold_cost` from entity gold and apply
  `gold_delta - gold_cost` net. Items_add is empty for pure gold sinks.
- `resource_updates` in `StateUpdate` flows via `apply.py` into
  `state.global_resources` — this is the correct place to track treasury accumulation
  (`metric_treasury_gold`).
- `InventoryUpdate.gold_delta` applied in `apply.py` to entity gold.

### Alert Infrastructure (E33B, already in place)

- `InflationSpiralEvent` / `GoldHoardingEvent` dispatched via
  `kernel._event_listeners` callbacks in PERSISTENCE phase.
- The kernel does NOT carry inflation state across ticks — alerts are transient events.
  Gold sink must read `state.pressure_signals` (Dict[str, float]) or `global_resources`
  to check if inflation is "active" this window. Simplest approach: piggyback on the
  EconomyHealthMonitor snapshot already computed in the kernel — check gini directly.

### Gold Sink Injection Point

- `AuthoritativeApplyPipeline.refine()` Phase 5 "Governance & Ecology" →
  `TownResolutionSystem.resolve()` is the natural home for governance-driven fees/taxes.
- Alternative: add a new `run_phase("gold_sink", ...)` call inside Phase 5 or Phase 6
  (after shop/resource_transactions), so it runs AFTER entity updates are formed but
  BEFORE evolution. This avoids modifying TownResolutionSystem.
- Decision: Add `GoldSinkSystem.apply(state, update)` as a new module
  `src/engine/gold_sink.py`, called from pipeline.py Phase 5 after town_resolution.
  Condition: only runs when `EconomyHealthMonitor.sample()` would have flagged
  inflation — checked via `state.pressure_signals["inflation_spiral_active"]` which
  the kernel sets via `resource_updates` after alert dispatch.

### State Communication: Inflation Active Flag

- Kernel already dispatches alert via `_event_listeners`. It can also write
  `resource_updates={"inflation_spiral_active": 1.0}` into a StateUpdate that gets
  folded into `global_resources`. But this requires the kernel to write back to state
  mid-pipeline, which is not the pattern.
- Cleaner approach: `GoldSinkSystem` calls `EconomyHealthMonitor.sample(state, tick)`
  itself (read-only) and only applies sinks when gini > threshold. No cross-tick state
  needed — gini is recomputed from live entity gold each WINDOW_SIZE ticks.
- Even cleaner: pass alert state via `pressure_signals` field on StateUpdate. The kernel
  sets `pressure_signals_set` on the StateUpdate fed to `refine()`. We extend the kernel
  to include `inflation_spiral_active=1.0` in `pressure_signals_set` when an alert fires.
  But this also complicates the kernel.
- **Final decision**: `GoldSinkSystem` calls `EconomyHealthMonitor.sample(state, tick)`,
  checks gini threshold directly, applies sinks if active. This is fully self-contained,
  read-only state access, no cross-cycle state. Consistent with how the health monitor
  is already used.

### Three Mechanisms

1. **Equipment Degradation Cost** (REPAIR_FEE):
   - For each alive entity with equipped items where avg durability < 50%:
     - Fee = 1 gold per degraded slot (capped by entity gold).
     - Emitted as `ResourceTransferIntent(source_kind="REPAIR_FEE", gold_delta=-fee,
       gold_cost=fee, transfer_kind="FEE", source_id="REPAIR_FEE")`.
     - Conservation: fee deducted from entity; tracked in `resource_updates["metric_treasury_gold"]`.
   - Note: `REPAIR_FEE` is a new source_kind not yet in conservation.py.
     Will add alongside `TAX` in the existing elif chain.

2. **Service Fee Surcharge** (SERVICE_FEE):
   - When INFLATION_SPIRAL active: shops increase service fee by 10%.
   - Applied by setting a flag in `state.pressure_signals` — but state is immutable.
   - Simpler: the service fee surcharge is modeled as a per-entity resource transfer
     applied by `GoldSinkSystem` directly. Fee = 1 gold per entity (flat surcharge).
   - `ResourceTransferIntent(source_kind="SERVICE_FEE", gold_delta=-1, gold_cost=1)`.
   - Conservation: fee tracked in treasury.

3. **Tax Event** (TAX):
   - For entities above Gini-adjusted gold threshold (entities with gold > mean*1.5):
     - Tax = floor(entity.gold * 0.05) min 1 gold, max 50 gold.
     - `ResourceTransferIntent(source_kind="TAX", gold_delta=-tax, gold_cost=tax)`.
     - Conservation: tracked in treasury.
   - TAX already handled in conservation.py (lines 255-272).

### New source_kinds needed

- `REPAIR_FEE` — add to conservation.py alongside TAX (same logic: deduct gold_cost).
- `SERVICE_FEE` — add to conservation.py alongside TAX.

### Treasury Tracking

- Each accepted fee/tax adds to `resource_updates["metric_treasury_gold"]` in the
  StateUpdate returned by `GoldSinkSystem.apply()`. This flows into
  `state.global_resources["metric_treasury_gold"]` via `apply.py`.

### Gold Conservation Proof

- Entity gold decreases by fee/tax amount.
- `metric_treasury_gold` increases by same amount.
- Total gold in world = entity gold + treasury gold remains constant. ✓

## Related Files

- `src/core/conservation.py` — add REPAIR_FEE, SERVICE_FEE source kinds
- `src/engine/gold_sink.py` — new GoldSinkSystem
- `src/engine/pipeline.py` — wire gold_sink phase in Phase 5
- `src/observability/events.py` — add GoldSinkAppliedEvent
- `tests/unit/economy/test_gold_sink.py` — unit tests
- `tests/integration/scenarios/test_macro_economy.py` — integration test
- `docs/parity_ledger/town_resource.yaml` — TOWN-179, TOWN-180

## Architecture Compliance

- No direct state mutation — all via ResourceTransferIntent → ResourceTransactionSystem.
- No raw domain models from API.
- Conservation law enforced via existing ResourceTransactionResolver.
- Gold sink logic is read-only on state; writes only via typed StateUpdate.
