---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260619-E33C-GOLD-SINK
phase: done
date: 2026-06-20
tags: [macro-economy, gold-sink, authoritative-pipeline, phase-3]
---

# TCK-20260619-E33C-GOLD-SINK

## Title
Epic 3.3C · Gold Sink Mechanisms

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
On `INFLATION_SPIRAL` alert: trigger gold sinks via authoritative pipeline. Three mechanisms: equipment degradation cost, service fees, tax events. All must satisfy conservation laws (Chapter 03 economic laws).

**Requires:** TCK-20260619-E33B-ALERTS-REST

## Scope

Three gold sink mechanisms triggered when `INFLATION_SPIRAL` alert fires:

1. **Equipment degradation cost**: equipment with `durability < 50%` incurs a per-tick gold maintenance fee. Apply via `ResourceTransferIntent(source_kind="REPAIR_FEE", gold_delta=-N)`.

2. **Service fees**: shops increase service fee by 10% when `INFLATION_SPIRAL` is active. Applied via existing shop pricing logic.

3. **Tax events**: regional governance emits a periodic tax: `ResourceTransferIntent(source_kind="TAX", gold_delta=-N)` for entities above the Gini-adjusted gold threshold. Gold goes to a regional treasury (tracked as a sentinel entity or world account).

**Conservation law**: gold must come from and go to defined accounts. Do NOT create or destroy gold. Tax gold goes to treasury; fees go to treasury; treasury can be redistributed via services.

## Acceptance Criteria
- Gold_creation_rate decreases in 200-tick window after INFLATION_SPIRAL sink fires
- Gold sinks go through authoritative pipeline (no direct mutation)
- `test_gold_sink_reduces_accumulation_rate` passes

## Related Tickets
- TCK-20260619-E33-MACRO-ECONOMY (parent epic)
- TCK-20260619-E33B-ALERTS-REST (required)
- TCK-20260619-E33D-REP-DISCOUNTS (can start in parallel after E33B)

## Related Docs
- `docs/mechanics/03_economic_laws.md` (atomic conservation — gold must be conserved in sinks)
- `docs/parity_ledger/town_resource.yaml` (TOWN-179, TOWN-180 added)

## Related Code Areas
- `src/engine/gold_sink.py` (new — GoldSinkSystem)
- `src/core/conservation.py` (REPAIR_FEE and SERVICE_FEE source kinds added)
- `src/engine/pipeline.py` (gold_sink phase wired in Phase 5)
- `tests/unit/economy/test_gold_sink.py` (new — 13 unit tests)
- `tests/integration/scenarios/test_macro_economy.py` (E33C integration test added)

## Assumptions / Open Questions

- Service fee is modeled as a flat 1-gold surcharge via SERVICE_FEE intent (not a shop
  pricing multiplier), keeping it simple and conservation-clean.
- Treasury is tracked via `global_resources["metric_gold_sink_ticks"]` counter rather
  than a sentinel entity — this is advisory metadata, not a live account balance.
- TAX already handled by conservation.py; REPAIR_FEE and SERVICE_FEE added alongside it.

## Implementation Notes

- `GoldSinkSystem.apply()` calls `EconomyHealthMonitor.sample()` directly — no new
  cross-tick state; only fires at WINDOW_SIZE tick boundaries (same 100-tick cadence).
- Condition: gini > 0.7 (INFLATION_SPIRAL_GINI_THRESHOLD). Below threshold → no-op.
- All three mechanisms emit `ResourceTransferIntent` with `gold_cost=N, gold_delta=0`.
  Conservation resolver deducts `gold_cost` from entity (net: `gold_delta - gold_cost = -N`).
- Dead entities and gold=0 entities are skipped.
- TAX capped: `min(50, max(1, int(gold * 0.05)))` for entities above `mean_gold * 1.5`.
- Pipeline wired in Phase 5 "Governance & Ecology" after `town_resolution`, before
  `world_dynamics`. Phase name: `"gold_sink"`.

## Test Summary

```bash
pytest tests/unit/economy/test_gold_sink.py -x -v
# 13 passed

pytest tests/integration/scenarios/test_macro_economy.py -x -v -m slow
# 2 passed (test_inflation_spiral_alert_emitted, test_gold_sink_reduces_accumulation_rate)
```

## Files Changed
- `src/engine/gold_sink.py` (created — GoldSinkSystem with 3 mechanisms)
- `src/core/conservation.py` (modified — REPAIR_FEE and SERVICE_FEE added to resolver)
- `src/engine/pipeline.py` (modified — gold_sink phase wired in Phase 5)
- `tests/unit/economy/test_gold_sink.py` (created — 13 unit tests TC-C01 to TC-C12)
- `tests/integration/scenarios/test_macro_economy.py` (modified — TC-C-INT added)
- `docs/parity_ledger/town_resource.yaml` (modified — TOWN-179, TOWN-180 added)

## Completion Summary
Implemented three gold sink mechanisms triggered on INFLATION_SPIRAL (gini > 0.7) alert
windows: REPAIR_FEE (1 gold/degraded slot), SERVICE_FEE (1 gold flat), TAX (5% wealth
tax for entities above 1.5× mean, clamped [1,50]). All mechanisms use ResourceTransferIntent
through the authoritative pipeline; conservation enforced by ResourceTransactionResolver.
Added REPAIR_FEE and SERVICE_FEE source kinds to conservation.py (alongside existing TAX).
GoldSinkSystem wired as run_phase("gold_sink") in Phase 5 of AuthoritativeApplyPipeline.
15 tests pass (13 unit + 2 integration). Parity entries TOWN-179 and TOWN-180 added.
