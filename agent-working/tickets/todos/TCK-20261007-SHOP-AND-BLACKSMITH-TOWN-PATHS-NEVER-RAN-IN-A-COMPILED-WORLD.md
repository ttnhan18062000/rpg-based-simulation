---
status: active
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261007-SHOP-AND-BLACKSMITH-TOWN-PATHS-NEVER-RAN-IN-A-COMPILED-WORLD
phase: open
date: 2026-10-07
tags: [economy, world, bug]
---

# TCK-20261007-SHOP-AND-BLACKSMITH-TOWN-PATHS-NEVER-RAN-IN-A-COMPILED-WORLD

## Title
`ShopSystem` and `BlacksmithSystem` enforcement never runs in a compiled world: `state.building_tiles` is empty, so `building_type == "shop"` and `== "blacksmith"` can never match

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by `rpg-implementer-2` while making the inn's town services reachable (`TCK-20260921-BIOLOGICAL-PRESSURE-ACCUMULATION-UNIFORM-ACROSS-ENTITIES`), and first reported by Lane A on #404. In every one of the 24 compiled corpus worlds (and in every compile without a context) `AuthoritativeState.building_tiles` is EMPTY; buildings live in `state.buildings` and their footprints in `blocked_tiles`. `src/engine/shop.py:56` and `src/engine/blacksmith.py:130` look the building up with `state.building_tiles.get(tile_pos)`, so the shop price floor, the auto-sell of materials and the blacksmith wholesale recipe learning have never run in a compiled world. The biology ticket fixed the same lookup for `town_resolution.py` through `src/engine/service_reach.py` (building map plus orthogonal reach) and deliberately did NOT switch these two on.

## Why not switched on in the biology ticket
Enabling the shop path broke a plain buy: `tests/unit/world/test_economy_contract.py::test_shop_buy_and_sell` ends with gold 1000 instead of 990, because the price-floor sanitizer (`MarketSystem.calculate_price` against `ShopAction.buy`'s own price, after the #387 multiplier removal) drops the intent. Blacksmith would grant every adjacent walker the wholesale recipe set. Both are economy behavior changes that need their own measurement.

## Scope
1. Decide whether the shop price floor and the blacksmith wholesale learning are intended to run in play; reconcile `ShopAction.buy`'s price with `MarketSystem.calculate_price`.
2. Resolve the building through `service_reach` (or fill `building_tiles` at compile; see readers below) and measure before and after on one tree.

## Out of Scope
The inn's town services (done in the biology ticket).

## Acceptance Criteria
- [ ] The shop and blacksmith paths run in a compiled world, or the dead enforcement is removed on purpose.
- [ ] `test_shop_buy_and_sell` passes with the enforcement on, or is changed for a stated reason.
- [ ] Before and after measured on one tree and recorded as a divergence entry.

## Related Tickets
- `TCK-20260921-BIOLOGICAL-PRESSURE-ACCUMULATION-UNIFORM-ACROSS-ENTITIES`
- `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING`

## Related Docs
`docs/guidelines/intentional_divergences.md` 2.75 and 2.79.

## Related Stored Artifacts
`agent-working/stored_artifacts/TCK-20260921-BIOLOGICAL-PRESSURE-ACCUMULATION-UNIFORM-ACROSS-ENTITIES/`

## Related Code Areas
Readers of `building_tiles` (grep on 7aa6f997b plus the biology branch): `src/engine/shop.py:56`, `src/engine/blacksmith.py:130`, `src/engine/legality.py:85-87`, `:389-392`, `:405-408` (occupancy checks; they fall back to a scan when the map is empty), `src/engine/spatial_query.py:100` (comment), `src/engine/executor.py:55` (read-only copy), `src/engine/apply.py:491` (pass-through), `src/domains/campaigns/survivor_placement.py:62,74` (forces the fallback scan). `src/worldbuilding/compiler.py` never fills it. Only the shop and blacksmith lookups depend on it for behavior; the legality readers already have a fallback.

## Assumptions / Open Questions
Whether the compile path should fill `building_tiles` (one place, fixes both readers) or each reader should use the building map is open; the biology ticket chose the building map for `town_resolution`.

## Implementation Notes
(not started)

## Test Summary
(not started)

## Files Changed
(not started)

## Completion Summary
(not started)

## Progress 2026-10-08 (batch 2, branch `batch2-earning-chain`)
- Shop half done: `ShopSystem.enforce` finds the shop through `service_reach`; `ShopService.buy_item` prices a purchase with `MarketSystem.calculate_price` (Bible 03 section 4, rpg-planner ruling); four tests re-pinned to that price; new tests in `tests/unit/world/test_shop_resolves_through_service_reach.py`. With empty shop purses (every building starts with 0 gold and 0 stock) the path runs and rejects: one auto-sell attempt in the three measured worlds (seed 42, 1500 ticks), rejected `LIQUIDITY_EXHAUSTED`. Sell pricing keeps its two documented laws (static 50 percent; `ShopSystem.get_sell_price` with the trauma surcharge) until the earn build needs one.
- Blacksmith: LEFT UNWIRED ON PURPOSE (ruling 2026-10-08, option b). Wiring the wholesale learning would give every entity standing beside a smithy all 46 recipes for free: 4, 4 and 3 distinct entities per run (crowded_frontier, frontier_living_world, urban_political, seed 42, 1500 ticks), all with 0 gold, so they would meet crafting blockers; one is a `goblin_warband` member. It is a fiction call for the designer and is recorded in the code comment in `src/engine/blacksmith.py`.
