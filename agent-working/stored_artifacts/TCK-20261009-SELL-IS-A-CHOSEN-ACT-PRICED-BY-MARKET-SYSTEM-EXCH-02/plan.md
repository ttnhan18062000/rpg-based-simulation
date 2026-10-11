---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261009-SELL-IS-A-CHOSEN-ACT-PRICED-BY-MARKET-SYSTEM-EXCH-02
artifact_type: plan
tags: [economy, resource, legality]
---

# plan — TCK-20261009-SELL-IS-A-CHOSEN-ACT-PRICED-BY-MARKET-SYSTEM-EXCH-02

## Approach
- `shop_sale.py`, shop wiring through `service_reach` and `MarketSystem`, `serves.py` + trait `keeps_coin_and_trades` gating SELL and WORK.
- Action-time building services (`building_services.py`, `building_arrival.py`): bed, inn meal, sale, repair land when their action executes (divergence 2.101).
- Divergences 2.100 (sell), 2.103 (people).
- Rewrite of `test_force_full_scan_phase_compliance` shop test and `test_force_full_scan_dirty_set_completeness` equality assertion: decision 34 removed the auto-sell, so the old assertions tested deleted behaviour; each keeps its force-full-scan claim.

## Scope guards
- Removing the free meal (decision 44, waits for hunting + diet).
- The inn route gate.
