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
