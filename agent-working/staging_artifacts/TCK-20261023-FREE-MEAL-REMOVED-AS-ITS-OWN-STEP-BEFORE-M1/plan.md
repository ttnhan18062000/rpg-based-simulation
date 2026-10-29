---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1
artifact_type: plan
tags: []
---

# Plan (D73, plan only; code after rpg-planner's OK; paired run only after the planner's "host free")

## Scope (the ticket's, one variable: the free meal)
1. `src/engine/service_prices.py`: keep `EAT_PRICE_GOLD=5`, `REST_PRICE_GOLD=10`; replace `INN_MEAL_HUNGER=20` with the ruled total `INN_MEAL_HUNGER=60` (row 73); drop the "free meals stay on" wording.
2. `src/engine/building_services.service_delta`: EAT becomes ONE transfer `ResourceTransferIntent(source_kind="TOWN_SERVICE", gold_cost=EAT_PRICE_GOLD, gold_delta=0, transfer_kind="EAT", biological_upd=BiologicalUpdate(hunger_delta=-60, last_meal_tick_set=tick), is_group_required=True)` and an update with no biological part. REST: refuse (return None) when gold < price; transfer carries `gold_cost=REST_PRICE_GOLD`, `combat_upd=CombatUpdate(hp_delta=5)`; readiness stays on the update (see Questions Q2). `with_service` keeps its held-sleep rule.
3. `core_actions.eat_update`: delete the free -40 branch. With nothing carried, return `NavigationUpdate(failure_reason=<typed code>)` and no readiness cost, so the task ends and the brain re-decides (as `eat_at_corpse_update` does). Check where EAT at an inn is routed: the inn's update merges in `with_service` AFTER eat_update, so eat_update must still succeed when an inn serves the subject: the order of failure vs merge needs care (the typed failure must not fire when `service_building` finds an inn the subject can pay); resolve in code with a test (Q3).
4. `ai/goals/scorers.py`: EatScorer requires gold >= `EAT_PRICE_GOLD` for the inn; FatigueScorer gold >= `REST_PRICE_GOLD` for the inn bed. Both read `service_prices`; a subject that cannot pay falls to the existing no-open-way path.
5. Gate known entry: remove `match: "V1"` from `tools/test_architecture/rpg_gate_known.yaml` (but `tools/test_architecture/rpg_gate_*` is a harness-hash path: whether a known-entry edit moves `harness_hash` and so the gate baseline is a QUESTION for testing-planner/rpg-planner before touching it, Q4).
6. Docs in the same change: new divergence entry in `docs/guidelines/intentional_divergences.md` (Intentional Gameplay Change + Bug Fix; Bible 03 atomic conservation; SURV-06 "no engine charity"; Verification test path; Measured filled from the paired step); SURV-06 text where it says free meals are on; `docs/mechanics/03_economic_laws.md` if it lists the meal; parity ledger entry (town_resource.yaml) status/v2_evidence; correct #407's eat figures that included free meals; roadmap/§12.5 and v1.1 row stay the planner's.
7. Gates: code health ratchet (type new fields, docstrings), mypy, lint-imports, pin tests, `graphify update .` in the main checkout only.

## SimQ criterion (memo row 82, guard 1/2)
The outcome is already carried by typed records: the accepted EAT transfer (`transfer_kind="EAT"`, TOWN_SERVICE) and the rejected transfer (ACTION_EXHAUSTION). No new event type; the paired run's per-type counts (80(C) offline reader) report refused inn transactions vs v1. Report only; no content is tuned.

## Measurement (stated before building)
- Parent (base arm): origin/main at step A merge `d914bace7` (any later main commit changes the parent: must still be exactly d914bace7 or the planner re-bases; F4 #765 and step B already sit under it). Scheme `flat-sha256-v3`: compare fates and counters; digests only arm-to-arm within v3.
- Child arm: the D73 branch tip on top of that parent.
- `tools/rpg_measure paired` (use `--collected` and `--verdict-json` flags merged in #752), 3 gate worlds (frontier_living_world, urban_political, crowded_frontier) x seeds 42-46 first x 5000 ticks, `--self-check`, per-seed extinction STOP (single step). If it moves the world and is a candidate for v1.1, widen to seeds 42-51 as the v1 re-record did (decision 76: behaviour steps keep 5 seeds; the 10-seed rerun is the owner's call when the stop fires, as at D74).
- The cumulative watch from v1 (row 76/86): reading uses R arms (v3 base) for seeds 42-51; pooled test; the v1 -> v1.1 reading is a row of the v1.1 disclosure.
- Gate on the off arm: H1-H7 hold, R1-R5 reported; V1 = 0 on all 15 gate runs; record gate and fingerprints as v1.1 (gate rebaseline plus disclosure delta) ONLY on the planner's/owner's go; this ticket's PR does not touch the recorded baseline.
- Reported tables: starvation split broke vs could-pay, alive at t=1000/1100/2500/5000, free-meal count (must be 0), paid inn meals per run, EAT executions by gold at execution, refused inn transactions, and the N15 re-read (crowded_frontier/46 raider 38, frontier_living_world/44 worker 2).
- One heavy process at a time on the host; scratch under /mnt/data/scratch-rpg-implementer-2/d73 (disk about 11 GB free: trees plus arms about the size of the re-record: trim before running; ask the user before deleting anything).

## Questions for rpg-planner (the plan does not guess)
Q1. Parent: confirm the paired base is exactly `d914bace7` (not current main 2c4869d61, which only adds docs), and that R-arm v3 results are the cumulative-watch base for seeds 42-51.
Q2. REST readiness: approve (a) refuse-up-front plus atomic gold/hp (no state-model change), or (b) add a readiness field to `ResourceTransferIntent` (state-model change).
Q3. EAT with nothing carried and no payable inn: typed failure that ends the task (R2 of the old plan). Confirm, and name the ReasonCode (existing SOURCE_MISSING, or a new NO_FOOD).
Q4. V1 known entry removal edits `tools/test_architecture/rpg_gate_known.yaml`: does that move `harness_hash`/need testing-planner (owner of `tools/test_architecture` paths is outside my row)? Alternative: retire it in the v1.1 record ticket.
Q5. Merchant/undeclared-diet kinds: decision 74 declared species, so `can_use_inn_meal` should no longer be the legacy-any path; confirm no remaining undeclared kind (the 2026-10-14 compile check says all compiled bodies resolve to a diet).
