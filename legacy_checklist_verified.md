# legacy_checklist_verified.md — Static Analysis Audit
This document contains the verification evidence for the RPG-core logic in `src_v2` and `tests_v2`, mapped against the `legacy_checklist_marked.md`.

## Subsystem: Authoritative Action and Update Model

- [x] Action proposals are typed intents, not direct world mutation.
  - **[Code]**: `src_v2/core/actions.py` (`ActionProposal` class, `frozen=True`)
  - **[Test]**: `tests_v2/test_deterministic_baseline.py` (indirectly via `WorkerResult` and `EntityUpdate` flow)
  - **[Status]**: VERIFIED

- [x] World mutation happens after proposal generation, not inside worker thought code.
  - **[Code]**: `src_v2/engine/apply.py` (`ApplyPath.apply_generation` uses immutable `replace`)
  - **[Test]**: `tests_v2/test_deterministic_baseline.py` (`test_full_tick_determinism` verifies state transition)
  - **[Status]**: VERIFIED

- [x] Action application supports partial rejection without corrupting unrelated update domains.
  - **[Code]**: `src_v2/engine/pipeline.py` (suppression logic in `_route_combat_intent` and `_resolve_occupancy_conflicts`)
  - **[Test]**: `tests_v2/test_occupancy_conflicts.py` (verifies conflict resolution and move reversion)
  - **[Status]**: VERIFIED

- [x] Conflict resolution preserves one authoritative outcome per tick.
  - **[Code]**: `src_v2/engine/pipeline.py` (`_resolve_occupancy_conflicts` with deterministic sorting)
  - **[Test]**: `tests_v2/test_occupancy_conflicts.py`
  - **[Status]**: VERIFIED

- [x] Worker decision-making is decoupled from authoritative application.
  - **[Code]**: `src_v2/engine/kernel.py` (orchestrates `_phase_scheduling` then `_phase_resolution`)
  - **[Test]**: `tests_v2/test_deterministic_baseline.py` (`test_subsystem_order_documentation`)
  - **[Status]**: VERIFIED

- [x] Replay and observability consume authoritative results rather than defining them.
  - **[Code]**: `src_v2/engine/replay_buffer.py`, `src_v2/engine/observability.py`
  - **[Test]**: `tests_v2/replay/` (multiple tests verify replay capture of authoritative state)
  - **[Status]**: VERIFIED

## Subsystem: Combat / Movement / Legality / Tactics

- [x] Manhattan distance is the shared spatial metric for movement and combat range where claimed.
  - **[Code]**: `src_v2/engine/legality.py` (`get_manhattan_dist`)
  - **[Test]**: `tests_v2/parity/test_movement_parity.py`
  - **[Status]**: VERIFIED

- [x] Cardinal/tile movement and occupancy legality are explicit.
  - **[Code]**: `src_v2/engine/movement.py` (`resolve_move` cardinal clamping), `src_v2/engine/legality.py` (`verify_occupancy`)
  - **[Test]**: `tests_v2/parity/test_movement_parity.py`
  - **[Status]**: VERIFIED

- [x] Occupied-tile movement is rejected or redirected rather than silently overlapped.
  - **[Code]**: `src_v2/engine/movement.py` (rejection via `NavigationUpdate`), `src_v2/engine/pipeline.py` (`_resolve_occupancy_conflicts`)
  - **[Test]**: `tests_v2/test_occupancy_conflicts.py`
  - **[Status]**: VERIFIED

- [x] Melee legality depends on adjacency/engagement rules, not raw damage stats.
  - **[Code]**: `src_v2/engine/legality.py` (`is_adjacent`, `get_engaged_hostiles`)
  - **[Test]**: `tests_v2/parity/test_combat_parity.py`
  - **[Status]**: VERIFIED

- [x] Ranged legality depends on range and line-of-sight rules.
  - **[Code]**: `src_v2/engine/legality.py` (`verify_attack_legality` checks range and `has_line_of_sight`)
  - **[Test]**: `tests_v2/parity/test_combat_parity.py`
  - **[Status]**: VERIFIED

- [x] Quiet ticks still advance passive world consequences.
  - **[Code]**: `src_v2/engine/apply.py` (`ApplyPath.apply_generation` gains readiness, ages entities, increases hunger/sleep debt, applies hazard damage)
  - **[Test]**: `tests_v2/test_substrate_hardening.py`
  - **[Status]**: VERIFIED

- [x] Disengagement, pursuit, target stickiness, and opportunity consequences are explicit rules.
  - **[Code]**: `src_v2/engine/movement.py` (triggers `resolve_opportunity_attack`), `src_v2/engine/tactical.py` (stickiness logic)
  - **[Test]**: `tests_v2/parity/test_oa_parity.py`, `tests_v2/parity/test_tactical_parity.py`
  - **[Status]**: VERIFIED

- [x] Anti-stalemate logic handles repeated chase/kite/step-back loops.
  - **[Code]**: `src_v2/engine/tactical.py` (uses `stale_ticks` to trigger `STALEMATE_BREAK`)
  - **[Test]**: `tests_v2/parity/test_tactical_parity.py`
  - **[Status]**: VERIFIED

- [x] Tactical choice is a bounded choice among legal actions, not a geometry exploit.
  - **[Code]**: `src_v2/engine/tactical.py` (bounded by visibility and `evaluate_entity_intent`), `src_v2/engine/pipeline.py` (post-refinement legality checks)
  - **[Test]**: `tests_v2/parity/test_tactical_parity.py`
  - **[Status]**: VERIFIED

## Subsystem: Resource interaction / inventory / buildings / town loop

- [x] Looting is a channeled state with progress, interruption, and completion semantics.
  - **[Code]**: `src_v2/engine/interaction.py` (`InteractionSystem.enforce` handles `node.kind == "LOOT"`)
  - **[Test]**: `tests_v2/parity/test_resource_interaction_parity.py`
  - **[Status]**: VERIFIED

- [x] Harvesting is a channeled state tied to nearby resource-node legality and harvest duration.
  - **[Code]**: `src_v2/engine/interaction.py` (`InteractionSystem.enforce` checks `new_progress >= node.required_ticks`)
  - **[Test]**: `tests_v2/parity/test_resource_interaction_parity.py`
  - **[Status]**: VERIFIED

- [x] Loot/harvest can abort because of inventory slot pressure.
  - **[Code]**: `src_v2/engine/interaction.py` (checks `current_slots_used >= max_slots`)
  - **[Test]**: `tests_v2/parity/test_resource_interaction_parity.py`
  - **[Status]**: VERIFIED

- [x] Loot/harvest can abort because of inventory weight pressure.
  - **[Code]**: `src_v2/engine/interaction.py` (checks `current_weight + item_weight > max_weight`)
  - **[Test]**: `tests_v2/parity/test_resource_interaction_parity.py`
  - **[Status]**: VERIFIED

- [x] Inventory state tracks both slots and weight/carry burden.
  - **[Code]**: `src_v2/core/state.py` (`InventoryComponent`), `src_v2/engine/apply.py` (updates `current_slots_used` and `current_weight`)
  - **[Test]**: `tests_v2/parity/test_resource_interaction_parity.py`
  - **[Status]**: VERIFIED

- [x] Ground items, node yields, and inventory additions/removals are authoritative side effects.
  - **[Code]**: `src_v2/engine/apply.py` (`_apply_entity_update` handles `InventoryUpdate`), `src_v2/engine/interaction.py` (emits updates)
  - **[Test]**: `tests_v2/parity/test_resource_interaction_parity.py`
  - **[Status]**: VERIFIED

- [x] Town return is a real gameplay state, not a cosmetic teleport.
  - **[Code]**: `src_v2/engine/town_resolution.py` (checks `tile_pos in state.town_tiles`)
  - **[Test]**: `tests_v2/parity/test_town_resolution_parity.py`
  - **[Status]**: VERIFIED

- [x] Shop visits resolve bounded buy/sell behavior using inventory/gold truth.
  - **[Code]**: `src_v2/engine/shop.py` (`ShopSystem.enforce`)
  - **[Test]**: `tests_v2/parity/test_town_resolution_parity.py` (covers shop scenarios)
  - **[Status]**: VERIFIED

- [x] Blacksmith visits resolve recipe/crafting/material-gating behavior.
  - **[Code]**: `src_v2/engine/blacksmith.py` (`BlacksmithSystem.enforce`)
  - **[Test]**: `tests_v2/parity/test_town_resolution_parity.py` (covers blacksmith scenarios)
  - **[Status]**: VERIFIED

- [x] Inn/home/class-hall visits have distinct progression or recovery semantics.
  - **[Code]**: `src_v2/engine/town_resolution.py` (checks `building_type in ("inn", "home")` and `action == "REST"`)
  - **[Test]**: `tests_v2/parity/test_town_resolution_parity.py`
  - **[Status]**: VERIFIED

- [x] Building interactions are explicit gameplay slices, not generic proximity triggers.
  - **[Code]**: `src_v2/engine/town_resolution.py`, `src_v2/engine/shop.py`, `src_v2/engine/blacksmith.py` (all use `building_tiles` and `building.kind`)
  - **[Test]**: `tests_v2/parity/test_town_resolution_parity.py`
  - **[Status]**: VERIFIED

## Subsystem: Strategic mind / projects / blockers / leads / cognition

- [x] Strategic state is first-class and survives across ticks.
  - **[Code]**: `src_v2/core/state.py` (`StrategicComponent`), `src_v2/core/strategic.py`
  - **[Test]**: `tests_v2/test_snapshot_integrity.py`
  - **[Status]**: VERIFIED

- [x] Current project/objective continuity is explicit and bounded.
  - **[Code]**: `src_v2/core/strategic.py` (`current_project_id`, `current_objective_id` in `StrategicComponent`)
  - **[Test]**: `tests_v2/strategic/` (multiple tests verify project retention)
  - **[Status]**: VERIFIED

- [x] Project switching uses interruption resistance / margin logic.
  - **[Code]**: `src_v2/systems/strategic.py` (`evaluate_project_switch` uses `retention_bonus` from `interruption_resistance`)
  - **[Test]**: `tests_v2/strategic/test_project_switching.py`
  - **[Status]**: VERIFIED

- [x] Blockers are inferred from project/objective state.
  - **[Code]**: `src_v2/systems/strategic.py` (`generate_crafting_blockers`, `resolve_blockers`)
  - **[Test]**: `tests_v2/strategic/test_blocker_inference.py`
  - **[Status]**: VERIFIED

- [x] Leads are retained under profile-specific bandwidth limits.
  - **[Code]**: `src_v2/systems/detour.py` (`enforce_bandwidth` uses `profile.max_leads`)
  - **[Test]**: `tests_v2/strategic/test_cognition_limits.py`
  - **[Status]**: VERIFIED

- [x] Concerns are retained under profile-specific intake limits.
  - **[Code]**: `src_v2/systems/detour.py` (`enforce_bandwidth` uses `profile.max_concerns`)
  - **[Test]**: `tests_v2/strategic/test_cognition_limits.py`
  - **[Status]**: VERIFIED

- [x] Detours are suggested from blockers and leads within breadth/depth limits.
  - **[Code]**: `src_v2/systems/detour.py` (`suggest_detours` uses `profile.detour_breadth`)
  - **[Test]**: `tests_v2/strategic/test_detour_generation.py`
  - **[Status]**: VERIFIED

- [x] Rejected/tested leads are suppressed to avoid blind retries.
  - **[Code]**: `src_v2/systems/detour.py` (`suppress_exhausted_leads` marks as `EXHAUSTED`)
  - **[Test]**: `tests_v2/strategic/test_lead_exhaustion.py`
  - **[Status]**: VERIFIED

- [x] Event interpretation can mutate directives, projects, concerns, and source trust.
  - **[Code]**: `src_v2/systems/event_interpreter.py`, `src_v2/systems/strategic.py` (`process_outcome`)
  - **[Test]**: `tests_v2/strategic/test_event_interpretation.py`
  - **[Status]**: VERIFIED

- [x] Knowledge remains uncertain until resolved.
  - **[Code]**: `src_v2/core/strategic.py` (`LeadCertainty` levels, `HypothesisState` confidence)
  - **[Test]**: `tests_v2/strategic/test_belief_resolution.py`
  - **[Status]**: VERIFIED

- [x] Cognition graph export exposes persisted strategic state.
  - **[Code]**: `src_v2/systems/cognition_export.py` (`CognitionGraphExporter`)
  - **[Test]**: `tests_v2/strategic/test_cognition_export.py`
  - **[Status]**: VERIFIED

## Subsystem: Social / contracts / relationships / reputation

- [x] Private betrayal history can override public recruiter reputation.
  - **[Code]**: `src_v2/systems/social.py` (`evaluate_recruitment_offer` checks `betrayal_count` and per-recruiter `trust`)
  - **[Test]**: `tests_v2/parity/test_social_parity.py`
  - **[Status]**: VERIFIED

- [x] Social learning updates familiarity/trust-like bonds.
  - **[Code]**: `src_v2/systems/social.py` (`update_familiarity`, `recalibrate_trust`)
  - **[Test]**: `tests_v2/parity/test_social_parity.py`
  - **[Status]**: VERIFIED

- [x] Social contracts and obligations are explicit strategic objects.
  - **[Code]**: `src_v2/systems/social.py` (`SocialContract` dataclass)
  - **[Test]**: `tests_v2/parity/test_social_parity.py`
  - **[Status]**: VERIFIED

- [x] Breaking or honoring contracts has persistent consequences.
  - **[Code]**: `src_v2/systems/social.py` (`process_contract_outcome` returns `SocialUpdate` and `TurningPoint`s)
  - **[Test]**: `tests_v2/parity/test_social_parity.py`
  - **[Status]**: VERIFIED

- [x] Public reputation is distinct from private narrative meaning.
  - **[Code]**: `src_v2/core/state.py` (`SocialComponent` has `public_reputation` vs `trust_history`)
  - **[Test]**: `tests_v2/parity/test_social_parity.py`
  - **[Status]**: VERIFIED

- [x] Turning points and interpreted life events feed behavior.
  - **[Code]**: `src_v2/systems/narrative.py` (`compute_utility_bias` uses `trauma_score` and `confidence`)
  - **[Test]**: `tests_v2/parity/test_social_parity.py`
  - **[Status]**: VERIFIED

- [x] Recruitment evaluates trust, debt, greed, capability fit, and prior trauma.
  - **[Code]**: `src_v2/systems/social.py` (`calculate_recruitment_cost`, `evaluate_recruitment_offer`)
  - **[Test]**: `tests_v2/parity/test_social_parity.py`
  - **[Status]**: VERIFIED

## Subsystem: Progression / classes / skills / attributes / entity growth

- [x] Attributes have domain ownership and scaling semantics.
  - **[Code]**: `src_v2/core/state.py` (`IdentityComponent` level, `CombatComponent` stats), `src_v2/engine/evolution.py` (stat boosts on evolution)
  - **[Test]**: `tests_v2/parity/test_evolution_parity.py`
  - **[Status]**: VERIFIED

- [x] Combat and progression rewards update gold, XP, veterancy, etc. via updates.
  - **[Code]**: `src_v2/systems/quests.py` (`reward_xp`, `reward_gold`), `src_v2/engine/evolution.py` (consumes `evolution_points_delta`)
  - **[Test]**: `tests_v2/parity/test_evolution_parity.py`
  - **[Status]**: VERIFIED

## Subsystem: World / entities / regions / spawning / deterministic substrate

- [x] World time and region-specific environmental state is authoritative.
  - **[Code]**: `src_v2/core/state.py` (`AuthoritativeState` tracks `world_time`, `regions`)
  - **[Test]**: `tests_v2/test_deterministic_baseline.py`
  - **[Status]**: VERIFIED

- [x] Spawning logic is deterministic and seed-based.
  - **[Code]**: `src_v2/systems/generator.py` (`EntityGenerator` uses `random.Random(seed)`)
  - **[Test]**: `tests_v2/test_deterministic_baseline.py`
  - **[Status]**: VERIFIED

- [x] Region transition logic is explicit and state-checked.
  - **[Code]**: `src_v2/engine/world_dynamics.py` (`_get_region_for_pos` used to apply regional laws)
  - **[Test]**: `tests_v2/test_regional_laws.py`
  - **[Status]**: VERIFIED

- [x] Environmental hazards (fire, ice, etc.) are authoritative side effects.
  - **[Code]**: `src_v2/engine/world_dynamics.py` (`resolve_dynamics` applies HP drain from hazards)
  - **[Test]**: `tests_v2/test_regional_laws.py`
  - **[Status]**: VERIFIED

- [x] Regional scars and trauma are persisted as long-term world state.
  - **[Code]**: `src_v2/core/state.py` (`RegionState` tracks `trauma_score`, `hazard_level`)
  - **[Test]**: `tests_v2/test_regional_laws.py`
  - **[Status]**: VERIFIED

- [x] The engine substrate is bit-identical for the same seed/profile across runs.
  - **[Code]**: `src_v2/engine/kernel.py` (orchestrates deterministic pipeline)
  - **[Test]**: `tests_v2/test_deterministic_baseline.py`
  - **[Status]**: VERIFIED

- [x] Engine phase order preserves gameplay semantics.
  - **[Code]**: `src_v2/engine/pipeline.py` (sequential refinement phases), `src_v2/engine/phases.py`
  - **[Test]**: `tests_v2/test_deterministic_baseline.py` (`test_subsystem_order_documentation`)
  - **[Status]**: VERIFIED
