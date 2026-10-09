---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261009-SELL-IS-A-CHOSEN-ACT-PRICED-BY-MARKET-SYSTEM-EXCH-02
phase: open
date: 2026-10-09
tags: [economy, resource, legality]
---

# TCK-20261009-SELL-IS-A-CHOSEN-ACT-PRICED-BY-MARKET-SYSTEM-EXCH-02

## Title
Selling is a chosen act (SELL) priced by MarketSystem; shop visits no longer auto-sell

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Standing at a shop auto-sold the carried goods (Decision 34 removes that). SELL is now a chosen act executed by `shop_sale.py`, priced by the one market law; the shop visit ends when nothing is left to sell. Two force-full-scan tests that asserted the auto-sell were rewritten, not deleted.

## Scope
- `shop_sale.py`, shop wiring through `service_reach` and `MarketSystem`, `serves.py` + trait `keeps_coin_and_trades` gating SELL and WORK.
- Action-time building services (`building_services.py`, `building_arrival.py`): bed, inn meal, sale, repair land when their action executes (divergence 2.101).
- Divergences 2.100 (sell), 2.103 (people).
- Rewrite of `test_force_full_scan_phase_compliance` shop test and `test_force_full_scan_dirty_set_completeness` equality assertion: decision 34 removed the auto-sell, so the old assertions tested deleted behaviour; each keeps its force-full-scan claim.

## Out of Scope
- Removing the free meal (decision 44, waits for hunting + diet).
- The inn route gate.

## Acceptance Criteria
- [ ] SELL executes as a chosen act and is priced by `MarketSystem.calculate_price` (tests/unit/world/test_sell_is_a_chosen_act.py).
- [ ] Services land with their action (tests/unit/world/test_building_services_land_with_their_action.py) and the executor parity test passes.
- [ ] The shop phase still visits an entity under force_full_scan with an empty dirty set (rewritten integration test, with a default-scan control).

## Related Tickets
- TCK-20261009-WAGE-IS-PAID-FROM-THE-EMPLOYERS-OWN-PURSE-EXCH-02, TCK-20261009-SELL-IS-A-CHOSEN-ACT-PRICED-BY-MARKET-SYSTEM-EXCH-02, TCK-20261009-FIRST-COIN-IS-DECLARED-WORLD-CONTENT-EXCH-02, TCK-20261008-RECIPE-NODES-LAND-ON-TILES-THEIR-REGION-DOES-NOT-OWN-P3 (one batch, one PR)
- TCK-20261009-MINTED-KILL-AND-QUEST-COIN-IS-PAID-BY-A-PAYER-EXCH-02-B (successor)

## Related Docs
- `docs/mechanics/03_economic_laws.md`, `docs/guidelines/intentional_divergences.md` (2.96-2.103), `docs/parity_ledger/town_resource.yaml` (TOWN-200..204)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL/probes/` (chain_ms.py, agg.py, table4.txt)

## Related Code Areas
`src/engine/shop_sale.py`, `src/engine/shop.py`, `src/engine/serves.py`, `src/engine/building_services.py`, `src/engine/building_arrival.py`, `src/engine/town_resolution.py`

## Assumptions / Open Questions
- Free meals stay on (decision 44). SELL and WORK are dormant while an inn exists.
- Region owners are legacy faction buckets (disclosed in the PR).

## Implementation Notes
Batch 2 is one commit on `batch2-on-main` (clean re-apply of the net diff on edda25490). Paired 5-seed x 3-world measurements (arm1 main, arm6 batch 2, arm7 batch 2 with profiles not applied) are in the batch-2 PR notes.

## Test Summary
tests/unit/world/test_sell_is_a_chosen_act.py, tests/unit/world/test_building_services_land_with_their_action.py, tests/unit/kernel/test_building_services_executor_parity.py, tests/unit/world/test_shop_resolves_through_service_reach.py, tests/integration/optimization/test_force_full_scan_*.py

## Files Changed
See the batch-2 PR.

## Completion Summary
Pending (filled at close).
