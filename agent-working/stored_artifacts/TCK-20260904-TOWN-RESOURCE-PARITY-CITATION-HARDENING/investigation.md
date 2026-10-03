---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260904-TOWN-RESOURCE-PARITY-CITATION-HARDENING
artifact_type: investigation
tags: [economy]
---

# Investigation — TCK-20260904-TOWN-RESOURCE-PARITY-CITATION-HARDENING

Confirmed all 13 stale entries' `v2_evidence` source paths (unlike `test_path`) are real and exist —
this gap is isolated to `test_path` citations only, not a broader ledger-accuracy problem.

Per-entry replacement search, each confirmed by running the actual test before citing it (not
guessed):

- `TOWN-001` (typed intents, not direct mutation) ->
  `tests/unit/core/test_authoritative_state_contract.py::test_mutation_tripwire_during_decision`
- `TOWN-004` (mutation after proposal generation) ->
  `tests/integration/kernel/test_simulation_kernel_contract.py::test_authoritative_phase_list`
- `TOWN-007` (decision decoupled from application) ->
  `tests/integration/kernel/test_simulation_kernel_contract.py::test_kernel_tick_execution_order`
- `TOWN-008` (replay/observability consume, not define) ->
  `tests/unit/kernel/test_replay_contract.py::test_replay_is_non_authoritative`
- `TOWN-009` (looting channeled state) -> `tests/unit/resource/test_loot_channeling.py`
- `TOWN-010` (harvesting channeled state) -> `tests/unit/resource/test_harvest_channeling.py`
- `TOWN-013` (inventory slots + weight) ->
  `tests/unit/resource/test_inventory_hardening.py::
  test_inventory_stack_size_enforcement,test_inventory_weight_preservation_delta`
- `TOWN-014` (ground items/node yields/inventory side effects) ->
  `tests/unit/resource/test_resource_conservation_regression.py::
  test_harvest_conservation_full_inventory,test_loot_conservation_full_inventory,
  test_corpse_conservation_full_inventory`
- `TOWN-015` (town return real state) ->
  `tests/unit/world/test_town_building_contract.py::test_town_navigation_proximity`
- `TOWN-016` (shop buy/sell) -> `tests/unit/world/test_economy_contract.py::test_shop_buy_and_sell`,
  kept the already-correct `test_macro_economy.py::test_reputation_discount_applies` citation
- `TOWN-017` (blacksmith crafting) ->
  `tests/unit/world/test_economy_contract.py::test_blacksmith_crafting`
- `TOWN-019` (inn/home/class-hall) ->
  `tests/unit/world/test_building_interaction_contract.py::test_building_interaction_inn_rest_recovery`
  (inn) + `tests/unit/world/test_recovery_class_hall.py::
  test_class_hall_inn_rest_recovery,test_home_upgrade_blocker` (class-hall, home)
- `TOWN-020` (building interactions explicit, not proximity) -> same inn test +
  `tests/unit/world/test_town_services.py::
  test_guild_service_routes_via_interaction_kind,test_unrelated_interaction_kind_not_routed`
  (the latter specifically proves routing requires an explicit matching kind)

All 38 cited tests run and pass (1 unrelated pre-existing skip in the same files, not part of any
cited assertion).
