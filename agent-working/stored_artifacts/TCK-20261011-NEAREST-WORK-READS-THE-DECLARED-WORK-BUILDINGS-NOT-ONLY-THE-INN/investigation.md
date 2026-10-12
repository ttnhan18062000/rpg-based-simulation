---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261011-NEAREST-WORK-READS-THE-DECLARED-WORK-BUILDINGS-NOT-ONLY-THE-INN
artifact_type: investigation
tags: []
---

# investigation — TCK-20261011-NEAREST-WORK-READS-THE-DECLARED-WORK-BUILDINGS-NOT-ONLY-THE-INN

## What exists (read on rpg-nearest-work, fe1270233)
- **Decision layer:** `ai/goals/opening_steps.py::_earn_then_buy_step` calls `work_shift.nearest_work(state, entity)`, which is `nearest_serving(..., "inn", accept=inn purse >= WAGE_GOLD)` (WAGE_GOLD 6). Inn kind and an inn-purse check are hard-coded; `LeashService.way_in_range` then filters it.
- **Action layer (Lane B, batch 3):** `building_services.SERVICE_KINDS["WORK"] = {"inn"}` (declared in code, not content) and `TREASURY_WORK_KINDS = frozenset()` (empty: "built and tested but not reachable in play"). `work_shift.work_update` holds a 200-tick shift (`SHIFT_TICKS`), then emits one `WAGE` `ResourceTransferIntent` of 6 from the building's purse; for a kind in `TREASURY_WORK_KINDS` it sets `treasury_pays` and the holder faction so `conservation._wage_result` lets the owning treasury top up a short purse (`can_pay`, one typed `TreasuryTransfer`). The wage is paid once by transaction id.
- **Upkeep today:** `town_resolution.TownResolutionSystem.resolve` step 4, on `is_tax_tick` (`state.tick % (cadence.town_resolution * 2) == 0`, so the "period" is that cadence), for every non-wrecked building in an owned region: `_meet_upkeep` compares a flat `MAINTENANCE_COST = 5` with the building purse, tops up any shortfall from the holder treasury (`key`), closes the building (`functional_set=False`) when neither can pay, and reopens it when it can. Nothing in the decision layer ever causes a non-inn WORK shift, so the treasury top-up in `_wage_result` is unreachable in play.
- **Durable state:** `BuildingState` (core/state.py:1288) has `id, kind, position, hp, max_hp, functional, inventory, price_modifiers, place_id` and a cached `to_canonical_dict`. Built in `worldbuilding/compiler.py:631` (and perf scenarios), changed only by `BuildingUpdate` (hp_delta, functional_set, inventory, price_modifiers_set) applied in `apply_plan.py:225`; checkpointed through `to_canonical_dict` (`checkpoint.py:115`).
- **Content:** `BuildingDefinition` (content/schema.py:299) has `hp, max_hp, service_profile_id, themes, starting_gold, starting_stock`; no maintenance declaration. data/content/world/buildings.yaml lists shop, town_hall, blacksmith, inn, and more.

## Gap against the ruling (designer 2026-10-11, extends memo row 61 / D58)
1. No content declaration of maintenance shifts; `MAINTENANCE_COST` is an independent constant.
2. No per-period counter, so nothing can say "this building needs no more shifts".
3. `nearest_work` sees only inns, and `WORK`/`TREASURY_WORK_KINDS` are code constants.
4. The solvency check (`_meet_upkeep`) compares a flat 5, not shifts x WAGE_GOLD.

## Open questions for rpg-planner (the design needs these answers before code)
Q1. Does an inn's own-purse shift also count toward its maintenance shifts (so a shift is a shift everywhere: one wage, one counter), and is it then capped at "shifts needed"? Or does the inn keep today's uncapped kitchen work and only treasury-backed buildings carry the counter? Proposed: every WORK shift at a building with a declared need counts and the need caps the shifts offered, inn included (one rule, D58 same-pay rule); the inn's maintenance need is 1 shift a period, so inn work falls from "any time its purse covers a wage" to "once a period"; this is the largest behaviour change and needs your call.
Q2. Which building kinds are WORK buildings? Proposed: any kind with `maintenance_shifts` above 0 in content (WORK set derived from the content band, `SERVICE_KINDS["WORK"]` and `TREASURY_WORK_KINDS` retired), so no kind name appears in code (D56).
Q3. The default band: 1 shift for an ordinary building, 2 for a large one (town_hall, blacksmith?), as a coarse D50 band declared per kind in buildings.yaml. Who sets the numbers (designer)? Proposed values: ordinary 1, town_hall 3, others per their max_hp band.
