---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1
artifact_type: test_plan
tags: []
---

# Test plan (D73)
Constructed (tests/unit/engine, new file `test_free_meal_removed.py`):
- A broke subject beside an inn issues EAT: hunger unchanged, gold unchanged, transfer rejected (ACTION_EXHAUSTION), building purse unchanged.
- A subject holding exactly 5 gold: hunger -60, gold -5, building +5, `last_meal_tick_set`, ONE accepted transfer (atomic: no state where hunger fell and gold did not; assert via the resolver, not by hand).
- A subject holding 4 gold: refused, nothing moves (no clamp).
- REST: broke gets no bed, no hp, no readiness; 10 gold pays in full and gets hp +5, readiness +10; held sleep repeat pays once (existing rule).
- EAT with nothing carried, no inn: no hunger change, typed failure, task ends, no readiness burn.
- Carried food and corpse meals unchanged (existing tests stay green: `test_eat_carried_before_travel.py`, corpse-meal tests).
- Scorers: EatScorer/FatigueScorer do not offer the inn to a subject under the price; do offer it at the price; the under-price subject takes `_hunger_without_open_way`.
- Conservation: total coin conserved on a paid meal and on a refused one (Bible 03); `HardLawMonitor` clean.
- Gate: V4 test `test_v4_counts_a_forbidden_meal_through_the_real_kernel.py` stays meaningful (forbidden diet meal still counted); a 1500-tick gate compute shows V1 = 0 and the known entry is removed in the same change (registry lint green) per Q4.
- Existing tests to re-run and update where they assert free meals or 20+40: grep `INN_MEAL_HUNGER`, `hunger_delta=-40`, `EAT_PRICE_GOLD` in tests/ (scope pytest to tests/unit/engine, tests/unit/ai, tests/mechanic_scenarios, tests/integration/observability); no full suite.
- Determinism: two-run digests (paired --self-check spread 0) and cross-hashseed unaffected (no new hash).
- Measurement as in plan.md (paired step after the planner's "host free").
