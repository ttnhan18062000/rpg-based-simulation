---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL
artifact_type: investigation
tags: []
---

# Investigation (2026-10-13, main b396080cc; M0 step 4, the free-meal removal; plan only, build after baseline v1)

## What feeds a subject for nothing today (measured by the gate's V1, read in code)
1. `src/engine/domain/core_actions.py:67`, `eat_update`: an EAT action with no carried food returns `BiologicalUpdate(hunger_delta=-40.0, last_meal_tick_set=tick)` and NO transfer. Gate: only `can_use_inn_meal(entity)` (False for a declared diet without prepared food). So any undeclared or prepared diet that issues EAT with nothing carried eats 40 for free, anywhere. V1 measured it as merchants (group `undeclared`): 3 to 10 hunger-drop ticks per world per run.
2. `src/engine/building_services.py:60-74`, `service_delta` for EAT at an inn: the effects (`hunger_delta=-INN_MEAL_HUNGER`, 20) ride on the entity's update; the price rides on a separate transfer built with `gold_delta=-EAT_PRICE_GOLD` and NO `gold_cost`. `conservation._service_result` rejects only when `target_inventory.gold < intent.gold_cost` (0 here), and `inventory.apply_update` clamps gold at `max(0, ...)`. So a broke subject at the inn is fed (the update's hunger lands even when the transfer is clamped to 0 paid). REST is the same shape (`readiness +10`, `hp +5`, `gold_delta=-10`).
   - Together: today an inn EAT is 40 (core, free) + 20 (inn effect) = 60 hunger, for at most 5 gold, none if broke.
3. `EatScorer` (scorers.py:107) still offers the inn to any subject in reach, whether or not it can pay (the comment names this "a recorded flaw until the animals' own ways exist, owner decision 44"). `FatigueScorer` targets the inn's 10-gold rest regardless of gold (found earlier, P3).

## What already exists
- The paid-or-not-served pattern for other services: `_service_result` rejects when the subject holds less than `intent.gold_cost` (reason ACTION_EXHAUSTION) and applies `biological_upd` ONLY when accepted, so a transfer built with `gold_cost=EAT_PRICE_GOLD` and `biological_upd=<the meal's relief>` is atomic and refuses a broke subject with no new resolver code.
- `carried_meal` (CARRIED_FOOD) and `corpse_meal` (CORPSE_FOOD) are the other ways to eat and already go through typed transfers (V1 sees them).
- The parked patch `step4_full_payment_refusal.patch` adds `SERVICE_PRICES` + `can_pay_for` in `service_delta` (refuse before building the update). It is correct for REST and EAT but it does not make payment atomic with the meal for a subject that spends its gold between the check and the resolve in the same tick, and it leaves the -40 path alone.

## Open rulings needed before the build (owner or rpg-planner)
R1. What the inn meal gives. Today 60 (40 core + 20 inn). With the free -40 gone, is an inn meal 40 (the old core relief, "a meal"), 60 (today's total) or 20 (today's inn part)? The baseline v1 and all survival tuning (D36 staged starvation, hunger rates) were measured with 60-per-inn-EAT plus 40-per-free-EAT, so this changes the world. Recommendation: keep the TOTAL the inn gives today (60) so a paying subject's hunger economy does not move; only the free path and the unpaid inn disappear.
R2. EAT with no building and nothing carried (eat_update fallthrough): it must not reduce hunger. What does the action do instead: end the task with a typed failure reason (like `eat_at_corpse_update` returns `SOURCE_MISSING`/`SOURCE_DEPLETED`) so the brain re-decides, rather than burning the readiness cost for nothing? Recommendation: yes, a typed `NO_FOOD` style failure reason on NavigationUpdate.failure_reason (check the enum for an existing code).
R3. Undeclared-diet kinds (merchants, and the kinds with no `diet`): `can_use_inn_meal` keeps the legacy "eats any food" for an undeclared diet. After the removal a merchant with no carried food and no coin starves like anyone. Merchants carry goods and coin? V1 shows them eating for free with empty inventory and 0 gold. Expect merchant starvation to appear in the 5000-tick runs; is that the intended outcome (they must trade to eat)? This is a world-semantic change the divergence must name.
R4. `EatScorer`/`FatigueScorer` affordability: offer the inn only to a subject that holds the price (`EAT_PRICE_GOLD`, `REST_PRICE_GOLD`); otherwise `NeedAccess` already routes a hungry no-way subject to opening steps (forage; earn-then-buy and ask are stubs). Is landing the removal before the earn-then-buy step acceptable (the earlier measurement: closing the free meal alone starves every broke subject: urban_political 0.0 alive by t=2500)? The ticket text said it lands WITH the decision-27 redirect (landed in #536, so that part is done) but the earlier owner ruling (2026-10-08) was that free meals stay on until a second way works in all three worlds. Planner says it lands after baseline v1 and is measured alone against v1; I need the owner's confirmation that the starvation wave this causes in `urban_political` and `crowded_frontier` is accepted as the measured result and not a blocker.

## Measurement plan
Pinned (PinnedNormalGovernor, audit mode, sequential executor), 5 seeds x 3 worlds, 1500 and 5000 ticks, two-run digests; compare against baseline v1 per the gate (the gate's own harness gives V1/V8 and the O rows). Report starvation by group, alive at t=1000/1100/2500/5000, free-meal count (V1 must go to 0), paid inn meals per run, and EAT executions by gold at execution. V1's known-red entry is removed by this ticket's closer.
