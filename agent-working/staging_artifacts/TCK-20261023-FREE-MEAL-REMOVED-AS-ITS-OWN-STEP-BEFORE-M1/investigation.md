---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1
artifact_type: investigation
tags: []
---

# Investigation (2026-10-28, origin/main 2c4869d61, contains step A d914bace7; D73, the free-meal removal as its own step)

Context Scan done: search_docs, graphify query (can_use_inn_meal, EatScorer, service_building), then code reads. Supersedes the 2026-10-13 plan on branch
`free-meal-removal-step4` (edbd11407, stacked on b396080cc), which is stale (branched before v1) but whose R1-R4 questions are now ruled (below).

## Binding rulings
- Memo row 73 (owner, 2026-10-13): a paid inn meal removes **60** hunger for **5 gold** (today's total); rest keeps its effects at **10 gold**; payment is atomic and refused unless the full price is held, no clamp. An undeclared diet is declared in content first (SURV-05): done (decision 74, species step). A post-removal starvation wave is measured with the earn path live and brought to the owner.
- Row 44: nothing free for any kind; animals have hunting/raw meat (landed). Row 31/34: other ways (gather, hunt, earn, receive) exist; wages landed (EXCH-02).
- Rows 87/89 and roadmap §12.5: D73 is its own paired step against its parent, after HUNGER B, A and F4; its record is v1.1 (if neutral, last world-changing tip plus neutral proof, recorded anyway). Full stop rules (row 76/86: single step keeps the per-seed extinction STOP). It retires the V1 known entry (expires 2026-12-31). Re-read the repaired cases against v1 disclosure rows (N15 raider 38 changes shape: V3 reappearing is NEW at v1.1).
- Row 92: v3 digests. Base = R arms (957caf8f6, v3) are NOT D73's parent; the parent is the step A merge d914bace7 (v3 scheme, same as R's line). A paired proof compares fates and counters; digests compare only within v3.
- Row 54/§12.3: gate H1-H7 hold on the off arm, R1-R5 reported. Roadmap freeze not yet started (record phase not dispatched), so src changes may merge.

## What feeds a subject for nothing today (code read at 2c4869d61)
1. `src/engine/domain/core_actions.py:58 eat_update`: with no carried food and a usable inn diet, EAT returns `hunger_delta=-40, last_meal_tick_set` with NO transfer: free, anywhere, no building needed.
2. `src/engine/building_services.py:60 service_delta` EAT (inn within reach): the update carries `hunger_delta=-INN_MEAL_HUNGER` (20) while the price rides as a separate transfer `gold_delta=-5` with `gold_cost` 0. `conservation._service_result` (core/conservation.py:254) refuses only `gold < gold_cost` (0), and pays `min(gold, ...)`; inventory clamps gold at 0. So a broke subject still gets the update's hunger. An inn EAT is 40 + 20 = 60 today for at most 5 gold. REST: `readiness_delta=+10`, `hp +5` on the update, `gold_delta=-10` charge, same clamp.
3. `EatScorer` (ai/goals/scorers.py:118) offers the inn to any in-reach subject whether or not it can pay (comment names it a recorded flaw until animals' own ways exist: that condition is now met). `FatigueScorer` targets the inn rest regardless of gold (P3 found earlier).
4. V1 (gate) counts the hunger drop as unbacked when no accepted transfer moved items or gold; the known entry covers exactly this.

## What already exists (reuse)
- `_service_result` already gives the atomic pattern: a TOWN_SERVICE transfer with `gold_cost=N` is rejected (ACTION_EXHAUSTION) below N, debits N, credits the building, and applies `biological_upd`, `combat_upd` etc. ONLY on accept. So: EAT charge = `gold_cost=EAT_PRICE_GOLD, gold_delta=0, biological_upd=BiologicalUpdate(hunger_delta=-60, last_meal_tick_set=tick)`; no new resolver code. Check: the `paid` line `min(gold, cost - gold_delta)` then equals the full price on accept, so the building credit is exact.
- REST gap: the intent has `combat_upd` (hp +5) but no readiness field, and `readiness_delta=10` sits on the update, so an atomic rest needs either (a) `service_delta` refusing up front when `entity.inventory.gold < REST_PRICE_GOLD` (reads the same constants; the subject can only lose gold between check and resolve by another same-tick spend, which the per-tick resolver orders), or (b) a new intent field (state-model change). Recommendation (a) for readiness plus `gold_cost`/`combat_upd` on the transfer for hp, so the price check is atomic for everything the intent carries; confirm with rpg-planner.
- Carried food and corpse meals already pass typed transfers (V1 sees them), unchanged.
- The parked patch `probes/step4_full_payment_refusal.patch` (`SERVICE_PRICES`, `can_pay_for`) predates all this; use as reference only.

## Behaviour changes D73 makes (what the paired step measures)
a. Broke subject at an inn: today fed (60), after: nothing; EAT with no carried food and no building: today 40, after: typed failure (end task so the brain re-decides; check ReasonCode for an existing code; on a task that ends instead of burning `readiness_delta=-100`).
b. Paying subject: hunger economy unchanged (60 for 5 gold, row 73), but via ONE accepted transfer instead of update plus transfer.
c. Scorer: EatScorer offers the inn only if gold >= EAT_PRICE_GOLD; else `_hunger_without_open_way` (decision 27). FatigueScorer same for the 10-gold rest (rough rest per SURV-06 is the fallback).
d. Expected world effect: starvation among broke subjects (the ticket notes: earlier removal alone starved urban_political to 0.0 alive by t=2500 BEFORE wild food, forage, hunting, wages existed). Now ways exist; the size of any wave is the measured outcome and goes to the owner if it crosses a stop line (row 73 says so).

## Q5 evidence (2026-10-28, d73 branch off main 2c4869d61): no undeclared diet is left in a compiled world
`tests/unit/worldbuilding/test_every_compiled_body_has_a_declared_diet.py` (TCK-20261014-EVERY-COMPILED-LIVING-BODY-RESOLVES-TO-A-DECLARED-DIET-OR-THE-WORLD-DOES-NOT-COMPILE) compiles every data world through `require_declared_diet`: a body with no species, an unknown species or a body model with no diet raises a content error at compile. Run on this branch: 6 passed, 0 skipped. So `can_use_inn_meal`'s legacy "no body = eats anything" branch is unreachable from a compiled world (hand-built test entities only), and the gate worlds contain no undeclared kind.

## Build findings (2026-10-28)
- The planner's Q2 condition was real: a probe (scratch d73/probe_rest.py) showed a REST transfer rejected at 0 gold keeps the update's readiness +10 (only hp, riding on the transfer, was rolled back). Ruled (b): contingent `readiness_delta` on `ResourceTransferIntent`, `readiness_update` on `TransactionResult`, merged on accept in `economy._merge_contingent_updates`. The new default-zero field is not part of any hashed or carried state (intents are transient).
- `SleepScorer` was NOT gated on gold: an unpaid rest at the inn yields only the base rest effect, the bed's hp and readiness need the payment now, so nothing is free and the walk is unchanged. Gating it moved sleep-project tests and would be a second variable. Deviation from the draft plan item 4; disclosed in divergence 2.142.
- Carried food plus an inn in reach: both the carried meal and the inn meal still apply in the same EAT (unchanged on main); now the inn part costs 5 gold.
- `test_death_ledger.py::test_the_ledger_reads_the_states_and_writes_nothing_back` failed once in a 4-worker run of the whole affected scope and passes alone and in `tests/unit/observability -n 4`: an order-dependent flake, not touched.
