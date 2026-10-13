---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL
artifact_type: plan
tags: []
---

# Plan (draft; build only after baseline v1 is recorded and R1-R4 are ruled)

1. `service_prices.py`: keep EAT_PRICE_GOLD (5), REST_PRICE_GOLD (10); replace INN_MEAL_HUNGER with the ruled R1 relief; drop the "free meals stay on" wording.
2. `building_services.service_delta`: build ONE atomic transfer per service: EAT `ResourceTransferIntent(source_kind="TOWN_SERVICE", gold_cost=EAT_PRICE_GOLD, gold_delta=0, biological_upd=BiologicalUpdate(hunger_delta=-relief, last_meal_tick_set=tick), is_group_required=True)`; REST `gold_cost=REST_PRICE_GOLD` with `combat_upd=CombatUpdate(hp_delta=5)` and the readiness effect kept on the update only if the transfer is accepted (readiness_delta rides on the transfer's attributes? check `_service_result`: it carries biological/combat/attributes/etc., not readiness; so REST's `readiness_delta=10` needs either a field on the intent or the ruled behaviour that the bed's readiness is also gated: investigate `ResourceTransferIntent` fields, add one only if needed (state-model change: ask rpg-planner)). A subject that cannot pay in full gets nothing and the action ends with a typed refusal reason.
3. `core_actions.eat_update`: delete the free `hunger_delta=-40` branch; with nothing carried return a typed failure (R2) so the task ends. `can_use_inn_meal` stays the diet gate for the inn.
4. `scorers.EatScorer`/`FatigueScorer`: offer the inn only when `entity.inventory.gold >= price` (read the same constants); a subject that cannot pay falls to `_hunger_without_open_way` (decision 27).
5. Parity/divergence: new divergence entry (Intentional Gameplay Change + Bug Fix; the Bible 03 atomic conservation law and SURV-06 "no engine charity"); update SURV-06 text where it says "still on"; docs/parity_ledger entry; remove the V1 known-red entry from `tools/test_architecture/rpg_gate_known.yaml`.
6. Tests: see test_plan.md.
7. Gates: code health 0 new/0 worse, mypy clean, lint-imports 17/0, pin test (no new src file expected), full measurement per the investigation.
