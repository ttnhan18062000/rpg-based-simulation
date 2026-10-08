---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL
phase: open
date: 2026-10-07
tags: []
---

# TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL

## Title
EAT beside the inn feeds a subject that cannot pay: `CoreActions.execute_survival("EAT")` cuts hunger by 40 with no building and no gold, and the inn's 5-gold charge clamps at zero, so the meal is free.

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found by Lane A in the SURV-07 five-seed measurement (governor pinned NORMAL). In the gated arm on seed 42, 1500 ticks:
- crowded_frontier: 21 of 21 EAT executions were by a subject holding under 5 gold. Gold went down in only 1 of them.
- urban_political: 11 of 11 were under 5 gold, and gold was unchanged in all 11.

Two things combine:
1. `CoreActions.execute_survival` EAT (core_actions.py) applies hunger -40 with no building and no payment.
2. The inn's town service charges -5 gold through a resource transfer, and `inventory.apply_update` clamps gold at `max(0, ...)`.

A broke subject therefore eats for free. SURV-06 rules this out ("no engine charity"; the inn meal is "for a price"). Baseline survival and SURV-07's gated starvation gain both lean on these free meals. #407's "eat 0 to 24" also includes them.

## Scope
1. Close the free meal: an inn EAT is applied only when the subject can pay the price (`EAT_PRICE_GOLD`), and paying is atomic with the meal. Rule on what core EAT without a building means: under SURV-06 that is eating carried food, which must consume a food item. If no carried-food path exists yet, it must not reduce hunger for free.
2. **Land together with the decision-27 redirect** (`TCK-20261007-A-NEED-WITH-NO-OPEN-WAY-PULLS-TOWARD-THE-STEP-THAT-OPENS-ONE-SURV-07-AMENDMENT`), in one PR. Lane A's gatedA arm shows that closing the free meal alone starves every broke subject: alive at t=1100 fell to 0.2, 5.8 and 0.0.
3. Measure on the 5-seed bar, pinned, on all three worlds. Count EAT executions by gold at execution (free meals must be 0), and give starvation split into broke and could-pay.

## Out of Scope
- The SURV-07 curve and gate (landed separately).
- Shop and blacksmith paths, except where the buy step needs them (`TCK-20261007-SHOP-AND-BLACKSMITH-TOWN-PATHS-NEVER-RAN-IN-A-COMPILED-WORLD`).

## Acceptance Criteria
- [ ] Zero EAT executions that reduce hunger without payment or a consumed food item, shown by a constructed test and by pinned corpus counts.
- [ ] Lands in the same PR as decision 27, and the combined 5-seed result is reported against SURV-07's main.
- [ ] Divergence and parity entries corrected, together with #407's eat figures that included free meals.

## Related Tickets
- `TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07` (where it was found)
- `TCK-20261007-A-NEED-WITH-NO-OPEN-WAY-PULLS-TOWARD-THE-STEP-THAT-OPENS-ONE-SURV-07-AMENDMENT` (lands with it)
- `TCK-20260921-BIOLOGICAL-PRESSURE-ACCUMULATION-UNIFORM-ACROSS-ENTITIES` (#407)

## Related Docs
- `docs/world_rules/life-body/survival-needs.md` SURV-06; `docs/mechanics/03_economic_laws.md` (atomic conservation).

## Related Stored Artifacts
- The SURV-07 ticket's five-seed table and EAT-execution probe, once stored.

## Related Code Areas
- `src/engine/domain/core_actions.py` (`execute_survival`), `src/engine/town_resolution.py`, `src/core/inventory.py` (`apply_update` gold clamp), `src/engine/service_prices.py` (arrives with the affordability work).

## Assumptions / Open Questions
- A gold clamp that silently swallows an unpaid charge may also affect other town services (REST costs 10). Check them in the same pass.

## Implementation Notes
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_

## Amendment 2026-10-08 (Decision 29, from rpg-planner; supersedes the AC table above where they differ)

Wild food is part of the land and is never sized to demand. Supply model:

- Coverage: none set. Each biome declares in content data how much wild food its land holds and how fast it regrows (fertility order: forest, grassland, river high; hills lower; desert, mountain, cave little or none). How many it feeds is an outcome.
- Placement: by biome, in wild land outside settlement bounds. Town land holds owned food, off-limits (decision 27). No minimum-walk number.
- Regrowth: a flat data value per biome and node kind through RES-05's ecology process (#426). No seasons.
- Guardrails: conservation (Bible 03), its own item and node kind, `need_paths` counts it. Absolute numbers are anchored to an existing gatherable node kind (anchor and table go to rpg-planner BEFORE measuring).

New acceptance criteria:

1. Occurrence and effect: broke subjects forage, carry and EAT what they gathered; food nodes deplete and regrow (RESOURCE_RECOVERED); free meals stay 0; conservation holds.
2. Starvation among broke subjects, deaths, and alive at t=1000 / t=1100 are REPORTED as the outcome (pinned 5 seeds x 3 worlds, mean (SD), two-run determinism), not gated. If starvation still rises, the divergence says so and names the missing half: earn-then-buy (the shop/blacksmith ticket), not more food.
3. A scenario test for the SURV-06 forage loop (a broke worker walks to wild land, gathers, carries the food back, eats it, and the stripped patch regrows), built from the designer's spec.

Measured before the re-scope (one 8-charge node in `hometown`, main `dcfe5de4d`, pinned 5x3): starvation rose on all three worlds (9.6 to 12.8, 11.0 to 17.6, 6.8 to 15.4); that node sat in town land, which Decision 29 forbids. Rows: `probes/remeasure_one_node_on_dcfe5de4d.jsonl`; travel and broke-population samples: `probes/travel_and_broke_population_samples.jsonl`.

## Investigation notes (2026-10-08, batch d27 + ENV-08 + Decision 33)

- **Does a broke town worker ever forage? Not before ENV-08 content.** `frontier_living_world`, pinned, seeds 42 to 46: no `town_council` subject entered the wild-food region (`near_forest`) in any run. The factions that stood there were `wild_beast_pack`, `goblin_warband`, `merchant_league` (all endure NATURAL_TERRAIN). The goal saw the node (`opening_steps._forage_step` lists it for `town_council`; `EatScorer` utility 47 to 82 at hunger 50 to 60, 143 at 85) and workers walked, but the only road from `hometown` crosses `trading_hometown` (hazard 0.5, 5 HP per tick, dead in 20 ticks; a lone worker staged in it: HP 95, 90, 85 ... 0). 48 of 61 HAZARD deaths in five seeds were `town_council` humans, mostly there. `trading_hometown` hazard is constant (0.5, calamity 0.0, trauma 0 to 1) and no scoring or pathing code is hazard-aware.
- **The 8 `town_council` "gathers" on seed 43 were an inheritance** (a `CHEST`/`AUTO` heir transfer from `LifecycleSystem` at tick 529 to a worker at (30,15) in `hometown`), not a gather. Receive is dropped as a candidate way to eat: rare, needs a death and an heir, zero in the two worlds with no food.
- **Retraction recorded**: I wrongly reported that a forager "never leaves the node". The re-trace shows the worker gathers one charge per 44 ticks, eats from carry when hungry, leaves when the node is depleted (`SOURCE_DEPLETED` ends the held INTERACT, 2.85), idles by the inn and returns when the node regrows. The earlier long stay was my SPC-S16 staging: a staged `ENTITY_MOVE` whose target is the node tile never ends and keeps harvesting (11 berries, no eating, starvation death); no live task kind is known to do that.
- **ENV-08 derivation**: see divergence 2.90 (180 thickets, 1 to 13 steps from the region edge; first gather 33 ticks, then 44; p10 starting HP 78; the integer drain `int(level * 10)` has 1 HP per tick as its smallest nonzero step, which leaves 19 HP after one gather and kills at two).
- **Inn-meal attempts by broke subjects**: none. `EatScorer` offers the inn only when gold is at least 5. The rejected paid transfers per run (1 to 7 by 1 to 4 subjects, `TAX`/`FEE` and `SERVICE_FEE`, `ACTION_EXHAUSTION`) are the 10-gold rest at the inn: `FatigueScorer` targets the inn regardless of gold. P3 finding, not fixed here (rough rest per SURV-06 is the fallback).
- **highland_traverse**: a second region with the id `near_forest` (module `nomadic_herd`, plain terrain, hazard 1.5, no thicket) borders only `wolf_den`; no settlement or building within 70 tiles, so it is not a near edge and is unchanged; the duplicate region id is a separate P3 content ticket.
- **Decision 31 feasibility (read-only)**: gather works after ENV-08 only in `frontier_living_world`; hunting needs animals, which only that world has (5 wolves in the wolf den, 5 spiders at the old mine); `town_council` kills 5 spiders per run there (seed 42) and none in the other two worlds; a corpse holds only the victim's own inventory (`apply_plan.py:346`), animals carry nothing, `loot_table` is unused at runtime; per-item fill needs a schema field (any `food` category item fills 30). Shops (1, 2, 2) and inns (1, 2, 2) exist in all three measured worlds, but all 14 `town_council` start with 0 gold and earn 5 to 40 gold per run; the earn step is a stub. Price law: `ShopService.buy_item` prices with `DynamicPriceService` alone while `MarketSystem.calculate_price` (region and building modifiers, buy factor) is authoritative per Bible 03 (rpg-planner's ruling); routing `buy_item` through it belongs to the earn-then-buy build.

## Test Summary (batch head)
- `tests/unit/worldbuilding/test_wild_food_node.py` 88 passed; `tests/mechanic_scenarios/test_forage_loop_wild_food.py` (LB-S17) 5 passed; `tests/mechanic_scenarios/test_near_wild_is_survivable_deep_wild_is_not.py` (SPC-S16) 4 passed; engine, ai, actions, content units 708 passed; worldbuilding, worldassembly, content, resource, world and economy sweep 1326 passed plus the timing-dependent `test_corpus_diversity` grade-stability tests, which fail in the same number on main and on this branch under load (12 and 11 failures plus one error each).
- Placement rule proof: for all 24 resolved worlds at seeds 42 and 43 the compiled state with the rule on and off is identical once the food node is removed (hand run; `test_the_placement_rule_changes_only_the_food_node` pins three worlds).
- Gates: ratchet 0 new 0 worse, mypy clean, import-linter 17 kept 0 broken.
- Pinned 5x3 (1500 ticks): divergence 2.89 to 2.91 carry the tables. The 5000-tick headline measurement is in the stored artifacts and the divergence once it finishes.

## Parked (owner ruling 2026-10-08)
The batch landed WITHOUT this change: free meals stay on until a second way to eat works in all three measured worlds (earn, or wild land in `crowded_frontier` and `urban_political`). The removal is on local branch `d27-free-meal-removal` (stacked on the batch; its diff is exactly the removal and its tests). Evidence for why it waits: `agent-working/stored_artifacts/TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL/removal_evidence_divergence_2_89_as_drafted.md` is on that branch; the pinned 5000-tick rows are in `probes/pinned_5x3_5000_ticks_base_main_39e65eb5a_vs_batch_with_hunger_low.jsonl` (starvation wave in ticks 1000 to 2000; `urban_political` 0.0 alive at tick 2500, `crowded_frontier` 1.0 at tick 5000 with the removal on).
