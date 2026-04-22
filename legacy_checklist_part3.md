### Progression / classes / skills / attributes / rewards

#### `unit/ai/test_legend_legacy.py`

- [ ] `test_narrative_memory_logging`: Narrative memory logging.
- [ ] `test_bravery_modifiers`: Bravery modifiers.
- [x] `test_regional_suppression`: Regional suppression.

#### `unit/combat/test_combat_rewards.py`

- [ ] `test_kill_reward_emission_in_apply`: Kill reward emission in apply.
- [ ] `test_no_reward_on_non_lethal_hit`: No reward on non lethal hit.

#### `unit/core/aspects/test_progression.py`

- [ ] `test_undead_no_level_up`: Undead no level up — Undead should have a train_rate of 0.0 and never level up..
- [x] `test_milestone_level_up`: Milestone level up — Reaching a milestone like level 5 grants extra stats..
- [ ] `test_veterancy_multipliers`: Veterancy multipliers — Veterancy Ranks should boost stats via StatsProxy..
- [ ] `test_innate_talents_training`: Innate talents training — Talented attributes gain 2x points, weak attributes gain 0.5x..
- [ ] `test_combat_veterancy_points`: Combat veterancy points — Combat yields veterancy points..

#### `unit/core/aspects/test_skill_scaling.py`

- [ ] `test_physical_skill_scaling`: Physical skill scaling.
- [ ] `test_magical_skill_scaling`: Magical skill scaling.
- [ ] `test_elemental_skill_scaling`: Elemental skill scaling.

#### `unit/core/gameplay/test_attribute_synergy.py`

- [ ] `test_luck_impacts_crit_rate_significantly`: Luck impacts crit rate significantly — Verify that Luck has a meaningful impact on critical hit rate..
- [ ] `test_luck_impacts_loot_modifier`: Luck impacts loot modifier — Verify that Luck/Perception provides a loot rarity multiplier..
- [ ] `test_per_based_hidden_discovery`: Per based hidden discovery — Verify that hidden entities are only visible with sufficient Perception..

#### `unit/core/gameplay/test_breakthroughs.py`

- [ ] `test_breakthrough_is_added`: Breakthrough is added.
- [ ] `test_breakthrough_applies_bonus`: Breakthrough applies bonus.

#### `unit/core/gameplay/test_class_gear.py`

- [ ] `test_warrior_prefers_defensive_gear`: Warrior prefers defensive gear — Verify that a Warrior weights defensive stats higher than a Mage..
- [ ] `test_hero_starting_gear_integrity`: Hero starting gear integrity — Verify that each hero class has the correct starting gear defined..

### World / entities / snapshot / determinism / engine authority

#### `core/test_snapshot_integrity.py`

- [x] `test_snapshot_immutability_enforced`: Snapshot immutability enforced.
- [x] `test_snapshot_entities_are_deep_copied`: Snapshot entities are deep copied.
- [x] `test_snapshot_entities_are_frozen`: Snapshot entities are frozen.

#### `integration/engine/test_determinism.py`

- [x] `test_simulation_determinism`: Simulation determinism — Verify that two identical simulations with the same seed produce the same result..
- [x] `test_different_seeds_different_hashes`: Different seeds different hashes — Verify that different seeds produce different world states..

#### `integration/engine/test_mutation_purity.py`

- [x] `test_aibrain_statelessness`: Aibrain statelessness.

#### `unit/core/gameplay/items/test_inventory_resolution.py`

- [x] `test_add_item_to_slot_authoritative`: Add item to slot authoritative — Verify that adding an item to the authoritative inventory updates the slot correctly..
- [x] `test_remove_item_by_id_authoritative`: Remove item by id authoritative — Verify that removing an item by ID from the authoritative inventory updates the slot correctly..
- [x] `test_inventory_weight_enforcement`: Inventory weight enforcement — Verify that adding an item beyond the authoritative weight limit is rejected..
- [x] `test_inventory_slot_enforcement`: Inventory slot enforcement — Verify that adding an item beyond the authoritative slot limit is rejected..

original evidence: `unit/core/gameplay/items/test_inventory_resolution.py`
`src_v2` evidence: `src_v2/core/state.py` (`InventoryComponent`), `src_v2/engine/apply.py`
divergence note: v2 utilizes a flattened `InventoryComponent` in the authoritative state, with enforcement during the resolution phase.
proof path: `tests_v2/core/test_authoritative_state_contract.py`

#### `integration/engine/test_snapshot_safety.py`

- [x] `test_entity_deep_copy_isolation`: Entity deep copy isolation — Verify that Entity.copy() provides absolute isolation for nested mutable structures..
- [x] `test_snapshot_actor_isolation`: Snapshot actor isolation — Verify that resolving an actor from a Snapshot ensures mutation safety..
- [ ] `test_aspect_model_rebuild_integrity`: Aspect model rebuild integrity — Ensure that deep copies correctly initialize models and don't lose data..
- [ ] `test_lived_structure_isolation`: Lived structure isolation — Verify isolation for Phase 3 routine and attachment structures..

#### `unit/core/entities/test_entity_serialization.py`

- [ ] `test_entity_to_full_schema_no_crash`: Entity to full schema no crash.
- [ ] `test_entity_to_full_schema_minimal`: Entity to full schema minimal.

#### `unit/core/models/test_snapshot_purity.py`

- [x] `test_simulation_model_collection_freeze_list`: Simulation model collection freeze list — Verify that lists in SimulationModel become immutable after freeze..
- [x] `test_simulation_model_collection_freeze_dict`: Simulation model collection freeze dict — Verify that dicts in SimulationModel become immutable MappingProxy after freeze..
- [x] `test_world_state_freeze_guards`: World state freeze guards — Verify that WorldState prevents mutations after freeze..
- [x] `test_snapshot_deep_purity`: Snapshot deep purity — Verify that Snapshot entities and their nested aspects are recursively frozen..
- [x] `test_action_proposal_guard_integration`: Action proposal guard integration — Verify the ActionProposalGuard context manager properly freezes the snapshot..

#### `unit/systems/test_town_service.py`

- [x] `test_inn_rest_recovery`: Inn rest recovery — Verify that staying at an inn recovers health and resets the 'rest' requirement..
- [x] `test_shop_transaction_gold_check`: Shop transaction gold check — Verify that a hero cannot buy an item if gold is insufficient..
- [x] `test_blacksmith_crafting_materials_check`: Blacksmith crafting materials check — Verify that crafting fails if required materials are missing from the inventory..

original evidence: `unit/systems/test_town_service.py`
`src_v2` evidence: `src_v2/engine/town_resolution.py`, `src_v2/engine/shop.py`, `src_v2/engine/blacksmith.py`
divergence note: v2 moves town service logic into specialized systems within the authoritative resolution phase.
proof path: `tests_v2/parity/test_town_resolution_parity.py`

#### `unit/core/test_deep_freeze.py`

- [x] `test_deep_freeze_nested_collections`: Deep freeze nested collections — Verify that freeze() recursively converts nested collections to immutable types..
- [x] `test_deep_freeze_idempotency`: Deep freeze idempotency — Verify that calling freeze() multiple times is safe..

#### `unit/core/test_domain_invariants.py`

- [ ] `test_combat_aspect_invariants`: Combat aspect invariants.
- [ ] `test_progression_aspect_invariants`: Progression aspect invariants.
- [ ] `test_freeze_calls_validate`: Freeze calls validate.
- [ ] `test_nested_freeze_invariants`: Nested freeze invariants.

#### `unit/core/test_invariants.py`

- [ ] `test_speed_delay_invariants`: Speed delay invariants — Test that speed_delay never returns NaN or out-of-bounds values..
- [ ] `test_stats_invariants`: Stats invariants — AOA Stabilization: Test CombatAspect invariants (formerly Stats)..
- [ ] `test_damage_calc_math`: Damage calc math — Test the core damage calculation logic in isolation..
- [ ] `test_recalc_level_consistency`: Recalc level consistency — Ensure level-based stat recalculation remains consistent across aspects..
- [ ] `test_combat_damage_invariants`: Combat damage invariants — Ensure HP reduction application doesn't cause overflow or invalid states..

#### `unit/systems/test_calamity_evolution.py`

- [x] `test_calamity_evolution`: Calamity evolution.
