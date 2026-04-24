Below is a phase-by-phase implementation blueprint for adding the missing RPG-core logic into `src_v2`.

This assumes the updated checklist is the source of truth, and that V2 must preserve intended legacy semantics unless a divergence is explicitly documented and tested. The checklist now covers RPG gameplay, combat, movement, strategic cognition, social contracts, progression, world state, deterministic substrate, CLI, replay, logging, API, and infrastructure fallback concerns. The plan also follows the V2 principle that authoritative mutation must stay singular, bounded, deterministic, and truthfully reported.

---

# Phase 0 — Porting control and proof infrastructure

## Phase description

Create the control layer that prevents the port from becoming a vague rewrite. This phase does not add gameplay. It creates the ledger, test taxonomy, oracle structure, divergence documentation, and CI gates that define when a checklist item may be marked complete.

## Phase technical

Implement a parity ledger that maps every checklist row to:

- legacy evidence,
- V2 evidence,
- status,
- proof type,
- test path,
- divergence note,
- support boundary.

Add pytest markers for:

- `legacy_characterization`,
- `v2_contract`,
- `differential`,
- `intentional_divergence`,
- `regression`,
- `certification`.

## Phase important notes

Do this first. If you skip this, later phases will create false-green completion claims. The checklist is already too large to track manually with confidence.

## Phase high-level checklist

- [ ] Machine-readable parity ledger exists.
- [ ] Every checklist item can be linked to V2 proof.
- [ ] Divergences are explicit.
- [ ] Missing logic is not silently marked complete.
- [ ] CI can fail on unsupported green marks.

## Tasks

### Task 0.1 — Build parity ledger schema

**Task description:**
Create a structured ledger file for every checklist item.

**Task technical:**
Use YAML, JSON, or CSV. Include item ID, subsystem, checklist text, status, evidence, proof type, notes, and owner.

**Affected files assumption:**

- `docs/v2_parity_ledger.yaml`
- `tools/parity/build_ledger.py`
- `tools/parity/validate_ledger.py`
- `tests_v2/parity/test_ledger_integrity.py`

**Task checklist:**

- [ ] Every checklist item has stable ID.
- [ ] Every item has one valid status.
- [ ] Invalid status fails validation.
- [ ] Checked item without proof fails validation.
- [ ] Divergence without note fails validation.

---

### Task 0.2 — Add test taxonomy and pytest markers

**Task description:**
Separate proof types so a test can be understood as characterization, parity, contract, regression, or divergence.

**Task technical:**
Add pytest markers and enforce marker use for `tests_v2/parity`.

**Affected files assumption:**

- `pytest.ini`
- `tests_v2/conftest.py`
- `tests_v2/parity/`
- `docs/testing/v2_test_taxonomy.md`

**Task checklist:**

- [ ] All parity tests use proof-type markers.
- [ ] Unknown markers fail CI.
- [ ] Differential tests are distinguishable from V2-only contract tests.
- [ ] Intentional divergence tests must assert the divergence, not just `pass`.

---

### Task 0.3 — Create legacy oracle fixture framework

**Task description:**
Create a standard way to store legacy behavior outputs for comparison.

**Task technical:**
Use JSON fixtures generated from legacy `src` where feasible. V2 tests load oracle files and compare deterministic outputs.

**Affected files assumption:**

- `tests_v2/oracles/`
- `tests_v2/parity/helpers/oracle_loader.py`
- `tools/parity/generate_legacy_oracle.py`

**Task checklist:**

- [ ] Missing required oracle fails the test.
- [ ] Oracle has schema version.
- [ ] Oracle includes seed/config metadata.
- [ ] Oracle comparison is deterministic.
- [ ] Oracle update requires explicit command.

---

### Task 0.4 — Add divergence register

**Task description:**
Document every intentional gameplay difference between legacy `src` and `src_v2`.

**Task technical:**
Each divergence must include reason, affected systems, expected new behavior, tests, and migration risk.

**Affected files assumption:**

- `docs/v2_intentional_divergences.md`
- `tests_v2/parity/test_divergence_register.py`

**Task checklist:**

- [ ] Every intentional divergence has a test.
- [ ] Every divergence references checklist item IDs.
- [ ] Divergence reason is concrete.
- [ ] Unsupported logic is not mislabeled as divergence.

---

# Phase 1 — Entity, registry, and deterministic substrate

## Phase description

Implement the foundational contracts: entity construction, registries, deterministic RNG, spatial hash, serialization, and copy/isolation behavior. Every later RPG system depends on this.

## Phase technical

Build a V2-native equivalent of legacy `EntityBuilder`, registry loading, deterministic seed/domain use, and entity model initialization. Avoid importing legacy runtime orchestration directly.

## Phase important notes

Do not start advanced combat or strategy until this phase is stable. Bad entity defaults poison every downstream test.

## Phase high-level checklist

- [ ] Entities initialize with correct aspects.
- [ ] Registries load deterministically.
- [ ] RNG domain separation works.
- [ ] Spawn/loadout data is data-driven.
- [ ] Entity copy/serialization preserves gameplay state.

## Tasks

### Task 1.1 — Implement V2 entity construction contract

**Task description:**
Create or complete a V2 entity builder that produces heroes, monsters, NPCs, world bosses, and neutral objects with valid aspect state.

**Task technical:**
Builder should initialize identity, combat, progression, inventory, mind, social, position, faction, role, home/leash, and lifecycle fields.

**Affected files assumption:**

- `src_v2/core/entity.py`
- `src_v2/core/entity_builder.py`
- `src_v2/core/state.py`
- `src_v2/core/aspects/`
- `tests_v2/entities/test_entity_builder_contract.py`

**Task checklist:**

- [ ] Default entity has valid required aspects.
- [ ] Hero has hero role, faction, class, inventory, and progression state.
- [ ] Monster has tier, faction, leash/home behavior fields.
- [ ] Builder output is deterministic for same seed.
- [ ] Builder-created entity can serialize and deep-copy safely.

---

### Task 1.2 — Implement registry loading contract

**Task description:**
Load V2 gameplay data from registries instead of hardcoding behavior in systems.

**Task technical:**
Support item registry, skill registry, class registry, quest templates, spawn configs, loot tables, breakthroughs, traits, and NPC loadouts.

**Affected files assumption:**

- `src_v2/core/registry/`
- `src_v2/data/items/`
- `src_v2/data/classes/`
- `src_v2/data/skills/`
- `src_v2/data/spawn/`
- `src_v2/data/loot/`
- `tests_v2/registry/test_registry_loading.py`

**Task checklist:**

- [ ] All core registry files load.
- [ ] Duplicate IDs fail loudly.
- [ ] Missing references fail loudly.
- [ ] Class skill IDs resolve.
- [ ] Spawn configs reference valid loadouts.
- [ ] Loot tables reference valid item IDs.

---

### Task 1.3 — Implement deterministic RNG domain law

**Task description:**
Ensure all gameplay randomness is deterministic and domain-separated.

**Task technical:**
RNG calls should include domain, seed, entity ID or world ID, tick, and local nonce where needed.

**Affected files assumption:**

- `src_v2/platform/rng.py`
- `src_v2/core/enums.py`
- `tests_v2/platform/test_rng_contract.py`

**Task checklist:**

- [ ] Same seed/domain/entity/tick gives same result.
- [ ] Different domains produce different streams.
- [ ] `next_int` respects inclusive bounds.
- [ ] RNG use is not based on global Python randomness.
- [ ] Replay-visible state is stable under same seed.

---

### Task 1.4 — Implement spatial hash and grid primitive contracts

**Task description:**
Provide deterministic spatial lookup, movement occupancy support, and terrain storage.

**Task technical:**
Spatial hash should support insert, remove, move, radius query, occupant lookup, and deterministic ordering.

**Affected files assumption:**

- `src_v2/platform/spatial_hash.py`
- `src_v2/world/grid.py`
- `src_v2/world/occupancy.py`
- `tests_v2/platform/test_spatial_hash_contract.py`
- `tests_v2/world/test_grid_contract.py`

**Task checklist:**

- [ ] Insert places entity in correct cell.
- [ ] Move removes old cell membership.
- [ ] Remove clears membership.
- [ ] Radius query includes neighboring cells.
- [ ] Query result ordering is deterministic.
- [ ] Grid copy is not shared.

---

### Task 1.5 — Implement serialization and deep isolation law

**Task description:**
Ensure entities and world state can be copied, frozen, serialized, and replayed without hidden mutation.

**Task technical:**
Use immutable/frozen snapshots for AI reasoning. Ensure nested state is isolated.

**Affected files assumption:**

- `src_v2/core/state.py`
- `src_v2/core/snapshot.py`
- `src_v2/core/serialization.py`
- `tests_v2/core/test_snapshot_isolation.py`
- `tests_v2/core/test_serialization_roundtrip.py`

**Task checklist:**

- [ ] Snapshot entities are deep copied.
- [ ] Frozen state rejects mutation.
- [ ] Serialization round-trip preserves gameplay fields.
- [ ] Nested collections are not shared.
- [ ] AI cannot mutate authoritative state through snapshot references.

---

# Phase 2 — Map, movement, pathfinding, leash, and congestion

## Phase description

Implement spatial behavior: movement legality, occupancy, pathfinding, terrain costs, flow fields, congestion, stuck handling, and leash behavior.

## Phase technical

Movement must be proposal-driven. The AI proposes movement; authoritative apply validates legality and updates position.

## Phase important notes

Movement is the base of combat. Do not build kiting, bracketing, or pursuit before movement is authoritative.

## Phase high-level checklist

- [ ] Movement legality is authoritative.
- [ ] Occupied tiles are handled correctly.
- [ ] A\* and flow-field navigation exist.
- [ ] Congestion has yielding/rerouting logic.
- [ ] Mob leash prevents infinite chase.

## Tasks

### Task 2.1 — Implement movement legality oracle

**Task description:**
Centralize tile movement validation.

**Task technical:**
Check bounds, terrain walkability, cardinal movement, occupancy, dead actor, and movement cost.

**Affected files assumption:**

- `src_v2/movement/legality.py`
- `src_v2/actions/move.py`
- `src_v2/engine/apply_path.py`
- `tests_v2/movement/test_movement_legality.py`

**Task checklist:**

- [ ] Cardinal move is valid.
- [ ] Diagonal move is rejected unless explicitly supported.
- [ ] Occupied target is rejected.
- [ ] Dead actor cannot move.
- [ ] Blocked terrain rejects movement.
- [ ] Rejection includes structured reason.

---

### Task 2.2 — Implement A\* pathfinding

**Task description:**
Add deterministic pathfinding for near and medium-range movement.

**Task technical:**
Use Manhattan heuristic, terrain costs, occupied tile avoidance, and max-node budget.

**Affected files assumption:**

- `src_v2/movement/pathfinding.py`
- `src_v2/world/terrain_costs.py`
- `tests_v2/movement/test_astar_contract.py`

**Task checklist:**

- [ ] Same start and goal returns empty path.
- [ ] Adjacent goal returns one step.
- [ ] Wall detour works.
- [ ] Enclosed goal returns no path.
- [ ] Unwalkable goal returns no path.
- [ ] Occupied tile is avoided.
- [ ] Goal tile exception is handled if supported.

---

### Task 2.3 — Implement flow-field navigation

**Task description:**
Add long-range navigation for town, world boss, and fixed destination movement.

**Task technical:**
Cache flow fields by target and terrain version. Add TTL for moving targets.

**Affected files assumption:**

- `src_v2/movement/flow_field.py`
- `src_v2/movement/navigation_service.py`
- `tests_v2/movement/test_flow_field_contract.py`

**Task checklist:**

- [ ] Flow field returns normalized direction.
- [ ] Terrain cost affects vector.
- [ ] Static targets cache.
- [ ] Moving target TTL invalidates cache.
- [ ] Far town navigation uses flow field.
- [ ] Near target uses A\*.

---

### Task 2.4 — Implement congestion and stuck handling

**Task description:**
Handle multi-entity movement conflicts without weakening occupancy.

**Task technical:**
Support yield priority, waiting, safe sidestepping, reroute hysteresis, stuck counters, and oscillation suppression.

**Affected files assumption:**

- `src_v2/movement/congestion.py`
- `src_v2/movement/stuck.py`
- `src_v2/engine/conflict_resolver.py`
- `tests_v2/movement/test_congestion_contract.py`

**Task checklist:**

- [ ] Higher-priority retreat can force yield.
- [ ] Yielding does not step closer to danger.
- [ ] A-B-A-B oscillation is detected.
- [ ] Minor reroutes are suppressed.
- [ ] Stuck threshold changes movement behavior.
- [ ] Occupancy is never bypassed silently.

---

### Task 2.5 — Implement leash and return-to-camp behavior

**Task description:**
Prevent mobs from chasing forever and preserve camp identity.

**Task technical:**
Track home position, leash radius, chase target, chase ticks, return state, and healing while returning.

**Affected files assumption:**

- `src_v2/ai/leash.py`
- `src_v2/ai/states/wander.py`
- `src_v2/ai/states/hunt.py`
- `src_v2/ai/states/return_home.py`
- `tests_v2/movement/test_leash_contract.py`

**Task checklist:**

- [ ] No home means no leash restriction.
- [ ] Leash radius zero means never beyond leash.
- [ ] Beyond leash triggers return-to-camp.
- [ ] Chase beyond threshold is abandoned.
- [ ] Chase timeout gives up.
- [ ] Returning mob heals.
- [ ] Reaching camp resumes normal behavior.

---

# Phase 3 — Combat rulebook and combat consequences

## Phase description

Implement combat legality, damage, ranged rules, contextual bonuses, engagement, opportunity attacks, stamina, wounds, scars, kill rewards, and combat trace output.

## Phase technical

Combat must split into:

1. proposal,
2. legality validation,
3. authoritative application,
4. consequence generation,
5. trace recording.

## Phase important notes

Damage formula parity is not full combat parity. Range, LOS, cover, wounds, stamina, and rewards must be separate contracts.

## Phase high-level checklist

- [ ] Melee/ranged/AoE legality is explicit.
- [ ] Contextual combat bonuses exist.
- [ ] Combat consequences are persistent.
- [ ] Kill rewards are authoritative.
- [ ] Combat trace is replay-visible.

## Tasks

### Task 3.1 — Implement targeting and range legality

**Task description:**
Centralize targeting checks for melee, ranged, AoE, building, and invalid targets.

**Task technical:**
Use Manhattan distance, weapon range, adjacency, target alive status, faction hostility, LOS, and AoE impact legality.

**Affected files assumption:**

- `src_v2/combat/legality.py`
- `src_v2/combat/range.py`
- `src_v2/combat/line_of_sight.py`
- `tests_v2/combat/test_targeting_legality.py`

**Task checklist:**

- [ ] Melee adjacent target is valid.
- [ ] Melee out-of-range is invalid.
- [ ] Bow range is respected.
- [ ] Wall blocks LOS.
- [ ] Adjacent target remains visible.
- [ ] AoE impact center legality is separate from splash.
- [ ] Invalid target emits structured rejection.

---

### Task 3.2 — Implement combat damage and context modifiers

**Task description:**
Add stable damage calculation plus terrain and tactical modifiers.

**Task technical:**
Include attack, defense, weapon power, skill scaling, high ground, flanking, cover, moved penalty, crit/evasion if supported.

**Affected files assumption:**

- `src_v2/combat/damage.py`
- `src_v2/combat/context.py`
- `src_v2/combat/modifiers.py`
- `tests_v2/combat/test_damage_context.py`

**Task checklist:**

- [ ] Damage formula is deterministic.
- [ ] High ground bonus applies.
- [ ] Flanking bonus applies.
- [ ] Cover affects ranged attacks.
- [ ] Moved penalty applies.
- [ ] HP cannot underflow.
- [ ] Unsupported crit/evasion is documented if not implemented.

---

### Task 3.3 — Implement engagement and opportunity attacks

**Task description:**
Track engagement and punish illegal disengagement.

**Task technical:**
Engagement exists when hostile entities are adjacent. Moving out of engagement can emit an opportunity attack if rules permit.

**Affected files assumption:**

- `src_v2/combat/engagement.py`
- `src_v2/combat/opportunity.py`
- `src_v2/movement/legality.py`
- `tests_v2/combat/test_engagement_opportunity.py`

**Task checklist:**

- [ ] Engagement detects adjacent hostiles.
- [ ] Engagement clears on separation.
- [ ] Non-hostiles do not engage.
- [ ] Disengagement triggers opportunity attack.
- [ ] Staying engaged with same attacker does not trigger.
- [ ] OA result is authoritative.

---

### Task 3.4 — Implement stamina, exhaustion, wounds, and scars

**Task description:**
Add persistent combat consequences beyond HP loss.

**Task technical:**
Stamina drains on attack/movement. Low stamina applies fatigue. Massive hits create wounds. Certain wounds become permanent scars.

**Affected files assumption:**

- `src_v2/combat/stamina.py`
- `src_v2/combat/wounds.py`
- `src_v2/core/aspects/combat.py`
- `src_v2/core/models/life_events.py`
- `tests_v2/combat/test_combat_consequences.py`

**Task checklist:**

- [ ] Attack drains stamina.
- [ ] Low stamina applies exhaustion/fatigue.
- [ ] Massive hit creates wound.
- [ ] Wound affects stats.
- [ ] Scar is permanent.
- [ ] Consequence is replay-visible.

---

### Task 3.5 — Implement combat rewards and traces

**Task description:**
Emit rewards, social effects, and trace records after combat.

**Task technical:**
On lethal hit, create XP/gold/veterancy/reputation/social/quest updates as applicable.

**Affected files assumption:**

- `src_v2/combat/rewards.py`
- `src_v2/combat/trace.py`
- `src_v2/engine/apply_path.py`
- `tests_v2/combat/test_combat_rewards_trace.py`

**Task checklist:**

- [ ] Lethal hit emits reward update.
- [ ] Non-lethal hit emits no kill reward.
- [ ] First kill can create milestone.
- [ ] Ally hit can create betrayal event.
- [ ] Combat trace includes actor, target, damage, legality, outcome.
- [ ] Trace does not define authoritative truth.

---

# Phase 4 — Tactical AI and combat behavior

## Phase description

Implement tactical behavior that chooses among legal combat options: kiting, closing, retreating, cover seeking, bracketing, chokepoints, party roles, anti-stalemate, and action styles.

## Phase technical

Tactical AI should consume immutable snapshots and output proposals. It must not mutate authoritative state.

## Phase important notes

Do not let tactical AI become a workaround for weak combat legality. It must only choose legal actions or emit proposals that are later rejected authoritatively.

## Phase high-level checklist

- [ ] Tactical roles influence behavior.
- [ ] Ranged/melee behavior differs.
- [ ] Cover and chokepoints matter.
- [ ] Anti-stalemate exists.
- [ ] Tactical output is bounded and deterministic.

## Tasks

### Task 4.1 — Implement tactical role profiles

**Task description:**
Add role-based combat priorities for melee, ranged, support, protector, and vanguard entities.

**Task technical:**
Each role modifies utility weights for attack, move, guard, retreat, support, regroup, and protect.

**Affected files assumption:**

- `src_v2/ai/tactical/roles.py`
- `src_v2/ai/tactical/evaluator.py`
- `tests_v2/tactical/test_role_biases.py`

**Task checklist:**

- [ ] Vanguard prefers engagement.
- [ ] Support prefers distance/support actions.
- [ ] Protector biases toward ally protection.
- [ ] Role does not bypass legality.
- [ ] Role choice is deterministic.

---

### Task 4.2 — Implement melee/ranged tactical behavior

**Task description:**
Add core combat positioning behavior.

**Task technical:**
Melee closes distance. Ranged kites when too close, maintains distance when safe, and seeks safe shots.

**Affected files assumption:**

- `src_v2/ai/tactical/positioning.py`
- `src_v2/ai/states/combat.py`
- `tests_v2/tactical/test_melee_ranged_behavior.py`

**Task checklist:**

- [ ] Melee striker closes distance.
- [ ] Ranged skirmisher kites when too close.
- [ ] Ranged skirmisher maintains distance.
- [ ] Safe shot detection works.
- [ ] Low HP retreats.
- [ ] Retreat uses movement legality.

---

### Task 4.3 — Implement cover, chokepoint, and bracketing tactics

**Task description:**
Add tactical awareness of environment and ally positioning.

**Task technical:**
Detect ranged threats, nearby cover, one-tile gaps, and opposite-side ally positions.

**Affected files assumption:**

- `src_v2/ai/tactical/cover.py`
- `src_v2/ai/tactical/chokepoint.py`
- `src_v2/ai/tactical/bracketing.py`
- `tests_v2/tactical/test_environment_tactics.py`

**Task checklist:**

- [ ] Actor seeks cover only against visible ranged threat.
- [ ] Actor identifies 1-tile chokepoint.
- [ ] Actor holds chokepoint when useful.
- [ ] Allies can bracket target from opposite sides.
- [ ] Tactical target position is respected by combat handler.

---

### Task 4.4 — Implement anti-stalemate and action style modifiers

**Task description:**
Prevent repeated combat loops and support personality/action-style effects.

**Task technical:**
Detect repeated movement/combat patterns and temporarily bias actions. Add aggressive/evasive execution style mutation.

**Affected files assumption:**

- `src_v2/ai/tactical/stalemate.py`
- `src_v2/ai/action_styles.py`
- `tests_v2/tactical/test_anti_stalemate.py`
- `tests_v2/ai/test_action_styles.py`

**Task checklist:**

- [ ] Repeated oscillation is detected.
- [ ] Stalemate boosts flee/reposition.
- [ ] Aggressive style modifies proposal appropriately.
- [ ] Evasive style modifies proposal appropriately.
- [ ] Modifier does not mutate state directly.

---

# Phase 5 — Goals, motives, emotion, belief, and routine needs

## Phase description

Implement the non-strategic AI mind loop: perception, attention, beliefs, emotional appraisal, personality, goals, boredom, routine needs, sleep, hunger, and life-stage behavior.

## Phase technical

Use a staged AI pipeline:

1. perception,
2. belief refresh,
3. appraisal,
4. goal scoring,
5. proposal generation.

## Phase important notes

This phase makes entities behave continuously, not only react to combat or strategic projects.

## Phase high-level checklist

- [ ] Goal registry and scoring exist.
- [ ] Beliefs and attention are updated.
- [ ] Emotions affect utility.
- [ ] Routine needs affect behavior.
- [ ] Personality and life stage matter.

## Tasks

### Task 5.1 — Implement goal registry and scorer

**Task description:**
Add canonical goals and deterministic scoring/selection.

**Task technical:**
Support combat, flee, explore, rest, sleep, eat, loot, trade, socialize, town, quest, and strategic goals.

**Affected files assumption:**

- `src_v2/ai/goals/registry.py`
- `src_v2/ai/goals/scorer.py`
- `src_v2/ai/goals/selection.py`
- `tests_v2/ai/test_goal_registry_scoring.py`

**Task checklist:**

- [ ] Built-in goals exist.
- [ ] Goal IDs are unique.
- [ ] Empty candidate list returns `None`.
- [ ] RNG zero selects highest candidate.
- [ ] `top_n` limits weighted selection.
- [ ] Full bag suppresses loot goal.
- [ ] Low HP boosts flee goal.

---

### Task 5.2 — Implement perception, attention, and belief lifecycle

**Task description:**
Maintain apparent state and decaying beliefs.

**Task technical:**
Perception populates attention pool. Belief refresh captures apparent state. Beliefs decay over time.

**Affected files assumption:**

- `src_v2/ai/perception.py`
- `src_v2/ai/attention.py`
- `src_v2/ai/beliefs.py`
- `tests_v2/ai/test_belief_attention.py`

**Task checklist:**

- [ ] Perception phase populates attention pool.
- [ ] Belief refresh captures apparent state.
- [ ] Belief decay reduces stale certainty.
- [ ] Threat estimation uses belief state.
- [ ] Belief updates are authoritative updates or proposal-side updates, not hidden mutation.

---

### Task 5.3 — Implement emotional appraisal and narrative memory effects

**Task description:**
Make trauma, dread, victory, panic, and region fatigue affect behavior.

**Task technical:**
Events create emotional/narrative records. Utility modifiers consume those records.

**Affected files assumption:**

- `src_v2/ai/emotions.py`
- `src_v2/ai/narrative_memory.py`
- `src_v2/core/models/life_events.py`
- `tests_v2/ai/test_emotional_memory.py`

**Task checklist:**

- [ ] Low HP can trigger panic.
- [ ] Trauma region increases dread.
- [ ] Dread increases flee utility.
- [ ] Dread reduces explore utility.
- [ ] Victory memory increases confidence.
- [ ] Emotions decay through typed updates.

---

### Task 5.4 — Implement routine and biological needs

**Task description:**
Add hunger, sleep, rest, nocturnal behavior, and off-hours behavior.

**Task technical:**
Biological decay runs on quiet ticks. Routine service biases goal scoring based on time, needs, location, and personality.

**Affected files assumption:**

- `src_v2/ai/routine.py`
- `src_v2/systems/lifecycle/biological.py`
- `src_v2/ai/goals/routine_modifiers.py`
- `tests_v2/ai/test_routine_needs.py`

**Task checklist:**

- [ ] Biological decay runs on quiet ticks.
- [ ] Sleep utility increases at night.
- [ ] Inn visit can lead to sleeping.
- [ ] Home visit can lead to eating.
- [ ] Sleeping recovers relevant stats.
- [ ] Nocturnal predator gets correct bias.

---

### Task 5.5 — Implement personality, boredom, and life-stage modifiers

**Task description:**
Make repeated behavior, personality, and age/level stage affect decision scoring.

**Task technical:**
Add modifier pipeline over base goal scores.

**Affected files assumption:**

- `src_v2/ai/personality.py`
- `src_v2/ai/score_modifiers.py`
- `src_v2/ai/life_stage.py`
- `tests_v2/ai/test_personality_goal_modifiers.py`

**Task checklist:**

- [ ] Boredom reduces repeated goal utility.
- [ ] Motives bias explore/rest/flee.
- [ ] Life stage changes goal preference.
- [ ] Modifiers compose deterministically.
- [ ] Modifier explanation is replay-visible.

---

# Phase 6 — Inventory, resources, loot, crafting, shops, and economy

## Phase description

Implement the resource economy: inventory slots/weight, ground items, corpse loot, harvesting, treasure chests, shops, blacksmith, equipment, repair, and storage.

## Phase technical

Inventory mutation must happen through authoritative updates. AI can request loot/harvest/trade/craft, but only apply path mutates inventory/world objects.

## Phase important notes

Most duplication bugs happen here. Corpse loot, AI updates, ground items, and inventory additions must converge through one authority path.

## Phase high-level checklist

- [ ] Inventory has slots and weight.
- [ ] Loot/harvest are channeled.
- [ ] Ground items and nodes are authoritative.
- [ ] Shops and blacksmith use real gold/materials.
- [ ] Equipment/storage behavior is stable.

## Tasks

### Task 6.1 — Implement inventory model and item contracts

**Task description:**
Add item types, weight, stack behavior, equipment legality, consumables, and carry burden.

**Task technical:**
Registry-backed item model with inventory constraints.

**Affected files assumption:**

- `src_v2/core/inventory.py`
- `src_v2/core/items.py`
- `src_v2/data/items/`
- `tests_v2/inventory/test_item_inventory_contract.py`

**Task checklist:**

- [ ] Inventory tracks slot count.
- [ ] Inventory tracks weight.
- [ ] Item IDs resolve from registry.
- [ ] Weapon ranges are correct.
- [ ] Consumables are typed.
- [ ] Equipment legality is enforced.

---

### Task 6.2 — Implement channeled loot and corpse recovery

**Task description:**
Looting should take time, be interruptible, and converge authoritatively.

**Task technical:**
Add interaction progress state, target corpse/ground item, interruption rules, completion updates, and no-duplication guard.

**Affected files assumption:**

- `src_v2/actions/loot.py`
- `src_v2/systems/loot_system.py`
- `src_v2/world/ground_items.py`
- `tests_v2/inventory/test_loot_channeling.py`

**Task checklist:**

- [ ] Looting progresses over ticks.
- [ ] Looting can be interrupted.
- [ ] Slot pressure aborts loot.
- [ ] Weight pressure aborts loot.
- [ ] Corpse recovery does not duplicate items.
- [ ] Ground item removal is authoritative.

---

### Task 6.3 — Implement harvesting and resource nodes

**Task description:**
Harvesting should require valid nearby nodes and produce yields through authority path.

**Task technical:**
Resource nodes have type, yield, depletion, respawn if supported, and harvest duration.

**Affected files assumption:**

- `src_v2/actions/harvest.py`
- `src_v2/world/resource_nodes.py`
- `src_v2/systems/harvest_system.py`
- `tests_v2/inventory/test_harvest_contract.py`

**Task checklist:**

- [ ] Nearby node is required.
- [ ] Harvest has duration.
- [ ] Node yield decreases.
- [ ] Inventory receives yield.
- [ ] Slot/weight pressure aborts.
- [ ] Invalid node emits rejection.

---

### Task 6.4 — Implement shop, blacksmith, repair, and crafting

**Task description:**
Add economy interactions that consume and produce inventory/gold truth.

**Task technical:**
Shop buys/sells bounded by inventory/gold. Blacksmith crafts/repairs using recipes/materials.

**Affected files assumption:**

- `src_v2/town/shop.py`
- `src_v2/town/blacksmith.py`
- `src_v2/core/recipes.py`
- `tests_v2/town/test_shop_blacksmith_contract.py`

**Task checklist:**

- [ ] Shop cannot buy without gold.
- [ ] Shop cannot sell missing item.
- [ ] Blacksmith requires recipe materials.
- [ ] Crafting consumes materials.
- [ ] Crafting adds item.
- [ ] Missing material emits blocker if strategic system is enabled.

---

### Task 6.5 — Implement equipment, treasure chests, and home storage

**Task description:**
Add gear ranking, auto-equip, chest lifecycle, and storage.

**Task technical:**
Equipment power depends on class weights. Chests have availability and respawn tick. Home storage has capacity and deep-copy safety.

**Affected files assumption:**

- `src_v2/core/equipment.py`
- `src_v2/world/chests.py`
- `src_v2/town/home_storage.py`
- `tests_v2/inventory/test_equipment_chests_storage.py`

**Task checklist:**

- [ ] Better gear replaces worse gear.
- [ ] Worse gear is not auto-equipped.
- [ ] Non-equipment is ignored.
- [ ] Chest starts available.
- [ ] Chest becomes unavailable after loot.
- [ ] Chest respawns after threshold.
- [ ] Home storage add/remove/full behavior works.
- [ ] Home storage copy is deep.

---

# Phase 7 — Town, buildings, services, and local hubs

## Phase description

Implement town as a real gameplay loop: travel, guild, inn, home, class hall, shop, blacksmith, building interaction, and service-driven strategic updates.

## Phase technical

Buildings should be explicit gameplay objects with typed interaction handlers. Avoid generic proximity triggers that hide semantics.

## Phase important notes

Town is not UI. It is a recovery, information, progression, economy, and strategy hub.

## Phase high-level checklist

- [ ] Town return is real travel/state.
- [ ] Guild emits quests/intel/leads.
- [ ] Inn/home/class hall have distinct effects.
- [ ] Building interactions are explicit.
- [ ] Town services integrate with strategy.

## Tasks

### Task 7.1 — Implement town return and building registry

**Task description:**
Make town a navigable gameplay destination with explicit building records.

**Task technical:**
Town contains buildings with type, position, service handler, and availability.

**Affected files assumption:**

- `src_v2/town/town_state.py`
- `src_v2/town/buildings.py`
- `src_v2/world/world_generation.py`
- `tests_v2/town/test_town_building_contract.py`

**Task checklist:**

- [ ] Town has explicit center/region.
- [ ] Buildings are world objects.
- [ ] Return-to-town requires movement or state transition.
- [ ] Building type determines interaction.
- [ ] Invalid building interaction is rejected.

---

### Task 7.2 — Implement guild service

**Task description:**
Guild should produce quests, rumors, intel, and resource/material hints.

**Task technical:**
Guild service emits strategic leads, candidate zones, quest offers, and source metadata.

**Affected files assumption:**

- `src_v2/town/guild.py`
- `src_v2/quests/generator.py`
- `src_v2/strategy/knowledge.py`
- `tests_v2/town/test_guild_pipeline.py`

**Task checklist:**

- [ ] Guild visit emits intel.
- [ ] Guild visit can create quest offers.
- [ ] Intel has source identity.
- [ ] Rumors are uncertain, not perfect coordinates.
- [ ] Guild output is visible to strategy/API/replay.

---

### Task 7.3 — Implement inn, home, and class hall services

**Task description:**
Add recovery, sleep, eating, storage, skill learning, and home/class progression.

**Task technical:**
Each service has a separate interaction handler and update type.

**Affected files assumption:**

- `src_v2/town/inn.py`
- `src_v2/town/home.py`
- `src_v2/town/class_hall.py`
- `tests_v2/town/test_recovery_class_hall.py`

**Task checklist:**

- [ ] Inn visit can lead to sleep/recovery.
- [ ] Home visit can lead to eating/storage.
- [ ] Home upgrade resolves maintenance blocker.
- [ ] Class hall checks skill prerequisites.
- [ ] Skill learning resolves capability blocker.

---

### Task 7.4 — Implement building damage and sabotage if retained

**Task description:**
Support combat or sabotage against buildings if the legacy behavior is still in scope.

**Task technical:**
Validate building target, apply damage/sabotage, emit world and strategic consequences.

**Affected files assumption:**

- `src_v2/combat/building_combat.py`
- `src_v2/town/building_damage.py`
- `tests_v2/town/test_building_sabotage.py`

**Task checklist:**

- [ ] Building target validation exists.
- [ ] Sabotage applies authoritative update.
- [ ] Building damage persists.
- [ ] Damage can produce local concern/scar if supported.
- [ ] Unsupported behavior is documented if omitted.

---

# Phase 8 — Quests, progression, skills, classes, and growth

## Phase description

Implement RPG advancement: quests, XP, gold, levels, milestones, veterancy, talents, class gear, skills, breakthroughs, NPC loadouts, and evolution.

## Phase technical

Progression must update derived stats safely and authoritatively. Registry-backed definitions should drive classes, skills, and gear.

## Phase important notes

Progression is not just XP. It affects combat math, strategic capacity, equipment choice, available skills, and entity identity.

## Phase high-level checklist

- [ ] Quest lifecycle is stable.
- [ ] Rewards are authoritative.
- [ ] Leveling and milestones work.
- [ ] Skills/classes are registry-backed.
- [ ] Derived stats recalculate safely.

## Tasks

### Task 8.1 — Implement quest lifecycle model

**Task description:**
Support quest creation, progress, completion, serialization, copy isolation, and no double-completion.

**Task technical:**
Quest records include kind, target, progress, goal, reward, source, and completion state.

**Affected files assumption:**

- `src_v2/quests/models.py`
- `src_v2/quests/progress.py`
- `tests_v2/quests/test_quest_lifecycle.py`

**Task checklist:**

- [ ] Quest starts at progress zero.
- [ ] Progress ratio is correct.
- [ ] Completion returns true once.
- [ ] Completed quest does not mutate on advance.
- [ ] Quest copy is isolated.
- [ ] Serialization handles target positions correctly.

---

### Task 8.2 — Implement quest generation

**Task description:**
Generate hunt, explore, gather, liberate, bounty, and dynamic quests.

**Task technical:**
Use templates, level bands, duplicate prevention, region difficulty, and reward scaling.

**Affected files assumption:**

- `src_v2/quests/generator.py`
- `src_v2/data/quests/`
- `tests_v2/quests/test_quest_generation.py`

**Task checklist:**

- [ ] Generation respects level.
- [ ] Duplicate quest IDs are skipped.
- [ ] Gold scales with level.
- [ ] Explore quest gets valid target position.
- [ ] Liberate quest is generated when region/camp state supports it.
- [ ] Max active quest limit is enforced.

---

### Task 8.3 — Implement XP, level, veterancy, and milestone progression

**Task description:**
Add core growth behavior after combat, questing, training, and survival events.

**Task technical:**
XP grants level, milestones grant bonuses, veterancy adds combat multipliers, undead/no-growth exceptions are respected.

**Affected files assumption:**

- `src_v2/progression/leveling.py`
- `src_v2/progression/veterancy.py`
- `src_v2/progression/milestones.py`
- `tests_v2/progression/test_leveling_veterancy.py`

**Task checklist:**

- [ ] XP can level entity.
- [ ] Level-up respects cap.
- [ ] Milestone level grants extra stats.
- [ ] Undead do not level up if that rule is retained.
- [ ] Combat grants veterancy.
- [ ] Derived stats recalculate after level change.

---

### Task 8.4 — Implement attributes, talents, skills, and breakthroughs

**Task description:**
Add attribute ownership, training rates, skill scaling, prerequisites, and breakthroughs.

**Task technical:**
Attributes affect combat, XP multiplier, loot, perception, strategic capacity, and skill scaling.

**Affected files assumption:**

- `src_v2/progression/attributes.py`
- `src_v2/progression/skills.py`
- `src_v2/progression/breakthroughs.py`
- `tests_v2/progression/test_attributes_skills_breakthroughs.py`

**Task checklist:**

- [ ] Talent modifies training rate.
- [ ] Weakness modifies training rate.
- [ ] Physical skill scaling works.
- [ ] Magical skill scaling works.
- [ ] Elemental skill scaling works.
- [ ] Breakthrough can be added.
- [ ] Breakthrough applies bonus.
- [ ] Stat recomputation is stable.

---

### Task 8.5 — Implement classes, class gear, NPC loadouts, and evolution

**Task description:**
Make class and entity type matter in equipment, skills, stats, and transformation.

**Task technical:**
Use class registry and NPC loadout registry. Evolution can replace kind, stats, and gear.

**Affected files assumption:**

- `src_v2/progression/classes.py`
- `src_v2/data/classes/`
- `src_v2/data/npc_loadouts/`
- `src_v2/progression/evolution.py`
- `tests_v2/progression/test_classes_loadouts_evolution.py`

**Task checklist:**

- [ ] Hero class has correct starting gear.
- [ ] Class has skill chain.
- [ ] Warrior values defensive gear more than mage.
- [ ] NPC tier maps to canonical equipment.
- [ ] Race/tier maps to semantic kind.
- [ ] Goblin can evolve at cap.
- [ ] Evolution refreshes equipment.

---

# Phase 9 — Social relationships, contracts, groups, and lived consequences

## Phase description

Implement private relationships, public reputation, betrayal, social learning, contracts, obligations, recruitment, haggling, groups, party roles, and persistent lived consequences.

## Phase technical

Separate public reputation from private social memory. Social records must affect future behavior, not merely exist.

## Phase important notes

Do not build contract records without consequences. A social contract that does not change behavior is just flavor text.

## Phase high-level checklist

- [ ] Relationships update from evidence.
- [ ] Public and private reputation differ.
- [ ] Betrayal affects future recruitment.
- [ ] Contracts produce obligations/consequences.
- [ ] Groups/parties affect tactics.

## Tasks

### Task 9.1 — Implement relationship and reputation model

**Task description:**
Add private bonds and public reputation.

**Task technical:**
Track familiarity, trust, debt, fear, grudge, reputation, heroism, notoriety, and salience.

**Affected files assumption:**

- `src_v2/social/relationships.py`
- `src_v2/social/reputation.py`
- `src_v2/core/models/social.py`
- `tests_v2/social/test_relationship_reputation.py`

**Task checklist:**

- [ ] Familiarity increases from interaction.
- [ ] CHA affects familiarity gain.
- [ ] Trust changes from evidence.
- [ ] Public reputation is separate from private bond.
- [ ] Low reputation affects caution.
- [ ] Social updates are authoritative.

---

### Task 9.2 — Implement betrayal, turning points, and narrative consequences

**Task description:**
Make betrayal and life events persist and influence future behavior.

**Task technical:**
Events create turning points, memory records, social deltas, and future appraisal modifiers.

**Affected files assumption:**

- `src_v2/social/events.py`
- `src_v2/social/life_events.py`
- `src_v2/ai/narrative_memory.py`
- `tests_v2/social/test_betrayal_turning_points.py`

**Task checklist:**

- [ ] Hitting ally creates betrayal event.
- [ ] Betrayal shifts bond.
- [ ] Near-death creates turning point.
- [ ] First kill can create reputation milestone.
- [ ] Betrayal trauma affects recruitment.
- [ ] Private trauma can override public reputation.

---

### Task 9.3 — Implement recruitment, haggling, and offer evaluation

**Task description:**
Support recruitment offers, counteroffers, acceptance, rejection, and recruiter evaluation.

**Task technical:**
Evaluation uses trust, debt, greed, risk, capability fit, prior trauma, urgency, and payout.

**Affected files assumption:**

- `src_v2/social/recruitment.py`
- `src_v2/social/offers.py`
- `src_v2/strategy/contracts.py`
- `tests_v2/social/test_recruitment_negotiation.py`

**Task checklist:**

- [ ] Recruiter generates reasonable offer.
- [ ] Trusted fair offer is accepted.
- [ ] Greedy candidate counteroffers.
- [ ] Urgent recruiter can accept counter.
- [ ] Betrayal lowers willingness.
- [ ] Offer evaluation is deterministic under same state.

---

### Task 9.4 — Implement social contracts and obligations

**Task description:**
Make contracts persistent strategic/social objects with consequences.

**Task technical:**
Contracts include parties, role, obligation, terms, status, outcome, and consequence updates.

**Affected files assumption:**

- `src_v2/social/contracts.py`
- `src_v2/strategy/obligations.py`
- `src_v2/social/contract_consequences.py`
- `tests_v2/social/test_contract_consequences.py`

**Task checklist:**

- [ ] Contract creates obligations.
- [ ] Honoring contract improves relevant social state.
- [ ] Breaking contract creates persistent consequence.
- [ ] Outcome updates all members.
- [ ] Contract role affects tactical utility.
- [ ] Contract state survives serialization.

---

### Task 9.5 — Implement groups, parties, and cohesion

**Task description:**
Support purpose-driven cooperation, not just proximity clustering.

**Task technical:**
Groups have leader, members, shared goal, anchor, cohesion, tactical intent, and dissolution rules.

**Affected files assumption:**

- `src_v2/social/groups.py`
- `src_v2/ai/tactical/group_tactics.py`
- `src_v2/core/state.py`
- `tests_v2/social/test_group_party_contract.py`

**Task checklist:**

- [ ] Same faction/cluster can form group.
- [ ] Group requires at least two living members.
- [ ] Leader selected by level or priority.
- [ ] Dead leader dissolves or reassigns group.
- [ ] Distance affects cohesion.
- [ ] Shared group goal biases decisions.
- [ ] Contract can instantiate party group.

---

# Phase 10 — Strategic cognition, uncertainty, projects, and world reasoning

## Phase description

Implement high-level cognition: directives, projects, objectives, blockers, leads, concerns, candidate zones, hypotheses, uncertainty, source trust, event interpretation, continuity, and bounded capacity.

## Phase technical

Strategic state must be bounded and persisted, but never become a mutation shortcut. Strategy proposes updates; apply path commits them.

## Phase important notes

Strategic intelligence without real world/social inputs is fake. This phase should come after world, combat, social, town, and quest basics exist.

## Phase high-level checklist

- [ ] Strategic state is first-class.
- [ ] Capacity bounds are enforced.
- [ ] Project/objective continuity works.
- [ ] Uncertainty and source trust work.
- [ ] Strategic graph/export is non-authoritative.

## Tasks

### Task 10.1 — Implement bounded cognition profile

**Task description:**
Derive cognition capacity from attributes, personality, stamina, and traits.

**Task technical:**
Profile includes planning budget, judgment stability, evidence quality, social bandwidth, detour depth, lead retention, and interruption resistance.

**Affected files assumption:**

- `src_v2/strategy/cognition_capacity.py`
- `src_v2/ai/profile_builder.py`
- `tests_v2/strategy/test_cognition_capacity.py`

**Task checklist:**

- [ ] Same entity state produces same profile.
- [ ] Profile derivation does not use RNG.
- [ ] Profile builder does not mutate entity.
- [ ] Low/high profile produce different active slice size.
- [ ] Capacity metrics are replay-visible.

---

### Task 10.2 — Implement project and objective continuity

**Task description:**
Support project retention, switching, active objective preservation, and resumption.

**Task technical:**
Use interruption resistance, switch margin, project locks, persistence boost, and major-threat override.

**Affected files assumption:**

- `src_v2/strategy/projects.py`
- `src_v2/strategy/objectives.py`
- `src_v2/strategy/evaluator.py`
- `tests_v2/strategy/test_project_objective_continuity.py`

**Task checklist:**

- [ ] Current project retained below margin.
- [ ] Rival project wins above margin.
- [ ] Higher resistance increases switch margin.
- [ ] Project lock prevents switching.
- [ ] Major threat can override threshold.
- [ ] Suspended objective resumes correctly.

---

### Task 10.3 — Implement blockers, detours, and lead handling

**Task description:**
Infer blockers and suggest bounded detours from known leads.

**Task technical:**
Blockers can be knowledge, resource, capability, social, route, threat, or obligation blockers. Detours obey breadth/depth limits.

**Affected files assumption:**

- `src_v2/strategy/blockers.py`
- `src_v2/strategy/detours.py`
- `src_v2/strategy/leads.py`
- `tests_v2/strategy/test_blockers_detours_leads.py`

**Task checklist:**

- [ ] High judgment diagnoses accurately.
- [ ] Low judgment can misdiagnose.
- [ ] Detour breadth is capped.
- [ ] Detour depth is capped.
- [ ] Tested leads are suppressed.
- [ ] Exhausted leads remain visible as tested.

---

### Task 10.4 — Implement uncertainty, hypotheses, and source trust

**Task description:**
Make knowledge uncertain until confirmed and make source reliability affect future behavior.

**Task technical:**
Rumors produce candidate zones/hypotheses. Confirmation/refutation adjusts certainty and source trust.

**Affected files assumption:**

- `src_v2/strategy/uncertainty.py`
- `src_v2/strategy/source_trust.py`
- `src_v2/strategy/hypotheses.py`
- `tests_v2/strategy/test_uncertainty_source_trust.py`

**Task checklist:**

- [ ] Rumor lead has lower certainty.
- [ ] Vague lead does not cheat perfect coordinates.
- [ ] Proximity can resolve uncertain lead.
- [ ] Contradiction lowers certainty.
- [ ] False lead lowers source trust.
- [ ] Source trust changes future weighting.

---

### Task 10.5 — Implement strategic event interpretation and truth surfaces

**Task description:**
Convert world/social/combat events into concerns, directives, projects, and observable cognition graph outputs.

**Task technical:**
Event interpreter consumes turning points, scars, regional threats, betrayal, near-death, and home damage.

**Affected files assumption:**

- `src_v2/strategy/event_interpreter.py`
- `src_v2/strategy/directives.py`
- `src_v2/strategy/cognition_graph.py`
- `src_v2/api/schemas/cognition.py`
- `tests_v2/strategy/test_event_interpretation_graph.py`

**Task checklist:**

- [ ] Near-death creates survival concern.
- [ ] Betrayal mutates directive.
- [ ] Regional danger pivots project.
- [ ] Home damage affects attached entities more.
- [ ] Cognition graph export is deterministic.
- [ ] Export does not mutate state.
- [ ] API/replay/graph fields stay aligned.

---

# Phase 11 — World regions, hazards, calamities, and macro systems

## Phase description

Implement world-scale simulation: regions, difficulty tiers, POIs, local scars, hazards, influence, war, strongholds, camps, raids, calamities, world bosses, and bounty quests.

## Phase technical

World systems should run on quiet ticks too. They must feed gameplay and strategy, not just metrics.

## Phase important notes

This phase turns the world from a map into an active pressure system.

## Phase high-level checklist

- [ ] Regions and POIs exist.
- [ ] Difficulty affects spawn and rewards.
- [ ] Local scars/hazards influence behavior.
- [ ] War/territory systems affect world state.
- [ ] Calamity/world boss creates gameplay pressure.

## Tasks

### Task 11.1 — Implement region topology and POIs

**Task description:**
Create deterministic regions with terrain, difficulty, locations, and ownership.

**Task technical:**
Use region centers, Voronoi or equivalent assignment, terrain identity, difficulty zones, and POI templates.

**Affected files assumption:**

- `src_v2/world/regions.py`
- `src_v2/world/poi.py`
- `src_v2/world/world_generation.py`
- `tests_v2/world/test_region_topology.py`

**Task checklist:**

- [ ] Region contains uses expected metric.
- [ ] Difficulty tier maps from distance/zone.
- [ ] Every region owns territory.
- [ ] `find_region_at` returns nearest region.
- [ ] Empty region list returns none.
- [ ] Expected POI types exist.

---

### Task 11.2 — Implement difficulty-scaled spawning

**Task description:**
Make regional difficulty affect spawned enemy level, stats, gold, and tier.

**Task technical:**
Spawn generator consumes region difficulty and spawn config.

**Affected files assumption:**

- `src_v2/systems/generator.py`
- `src_v2/world/spawn_config.py`
- `tests_v2/world/test_difficulty_scaling.py`

**Task checklist:**

- [ ] Tier 1 is baseline.
- [ ] Tier 4 has higher stats than tier 1.
- [ ] Tier determines level range.
- [ ] Gold scales with difficulty.
- [ ] Boss difficulty is capped if legacy rule retained.
- [ ] Default spawn is tier 1.

---

### Task 11.3 — Implement local scars, hazards, and regional consequences

**Task description:**
Make traumatic or dangerous places persist and influence future behavior.

**Task technical:**
Local scars include kind, location, salience, decay/permanence, and strategic/emotional effect.

**Affected files assumption:**

- `src_v2/world/local_scars.py`
- `src_v2/world/hazards.py`
- `src_v2/strategy/place_threat.py`
- `tests_v2/world/test_scars_hazards.py`

**Task checklist:**

- [ ] Death/combat can create local scar.
- [ ] Scar can trigger dread or concern.
- [ ] Heroes can detect nearby scar.
- [ ] Regional danger influences strategic pivot.
- [ ] Scar state serializes and replays.

---

### Task 11.4 — Implement influence, war, territory, and strongholds

**Task description:**
Add faction-level world consequences.

**Task technical:**
Influence shifts on deaths/events. War states transition. Conquest creates strongholds. Strongholds apply debuffs.

**Affected files assumption:**

- `src_v2/world/influence.py`
- `src_v2/world/war.py`
- `src_v2/world/strongholds.py`
- `tests_v2/world/test_strategy_systems.py`

**Task checklist:**

- [ ] Monster death shifts influence.
- [ ] Hero death shifts influence.
- [ ] War declaration works.
- [ ] Territory conquest works.
- [ ] Territory liberation works.
- [ ] Stronghold applies debuff.

---

### Task 11.5 — Implement calamity, world boss, camps, and raids

**Task description:**
Add macro threats that create quests, pressure, and long-term consequences.

**Task technical:**
Calamity system tracks world maturity, spawn intervals, boss state, bounty creation, camp reinforcements, and raids.

**Affected files assumption:**

- `src_v2/world/calamity.py`
- `src_v2/world/camps.py`
- `src_v2/world/raids.py`
- `src_v2/quests/bounty.py`
- `tests_v2/world/test_calamity_raids.py`

**Task checklist:**

- [ ] World maturity increases.
- [ ] Calamity spawns on interval.
- [ ] World boss has legendary stats/loadout.
- [ ] Boss creates bounty quest.
- [ ] Camp reinforcements occur.
- [ ] Raid mobs use raid behavior.
- [ ] Killing boss grants fame/title/reward.

---

# Phase 12 — Replay, inspection, observability, and certification

## Phase description

Make all implemented gameplay provable, replayable, inspectable, and truthfully certified.

## Phase technical

Replay, API, CLI inspector, logs, metrics, and reports should reflect authoritative state. They must not define or mutate gameplay truth.

## Phase important notes

This is the final trust layer. Do not use it to hide missing gameplay. Certification must say what is preserved, divergent, unsupported, and unchecked.

## Phase high-level checklist

- [ ] Replay includes new gameplay surfaces.
- [ ] API/inspector expose supported state.
- [ ] Logs/metrics are truthful.
- [ ] Certification report is scoped.
- [ ] Unsupported logic is visible.

## Tasks

### Task 12.1 — Extend replay and fingerprints

**Task description:**
Include new gameplay state in deterministic replay and fingerprinting.

**Task technical:**
Add inventory, quests, social, strategy, world, combat trace, region, and progression fields.

**Affected files assumption:**

- `src_v2/replay/recorder.py`
- `src_v2/replay/fingerprint.py`
- `tests_v2/replay/test_replay_fidelity.py`

**Task checklist:**

- [ ] Same seed gives same replay-visible state.
- [ ] Different seeds diverge.
- [ ] Replay includes inventory.
- [ ] Replay includes quests.
- [ ] Replay includes social/strategy.
- [ ] Replay includes world objects and combat traces.

---

### Task 12.2 — Extend API schemas and inspector

**Task description:**
Expose supported gameplay state through API and CLI inspection.

**Task technical:**
Add schemas for cognition, inventory, social, quests, combat trace, region, and progression.

**Affected files assumption:**

- `src_v2/api/schemas/`
- `src_v2/api/routes/`
- `src_v2/cli/inspector.py`
- `tests_v2/api/test_gameplay_schema.py`
- `tests_v2/cli/test_inspector_gameplay.py`

**Task checklist:**

- [ ] API serializes new gameplay state.
- [ ] Inspector does not crash on missing optional fields.
- [ ] Empty cognition/social/quest state is handled.
- [ ] API schema matches replay fields where required.
- [ ] Presentation does not mutate state.

---

### Task 12.3 — Extend logs, metrics, and runtime truth

**Task description:**
Make logs and metrics reflect gameplay and runtime pressure honestly.

**Task technical:**
Add structured events for rejections, phase errors, replay pressure, queue pressure, combat outcomes, strategy shifts, and unsupported feature attempts.

**Affected files assumption:**

- `src_v2/observability/logging.py`
- `src_v2/observability/metrics.py`
- `src_v2/runtime/status.py`
- `tests_v2/observability/test_runtime_truth.py`

**Task checklist:**

- [ ] Logs remain valid JSON.
- [ ] Logs include timestamp, level, component, message.
- [ ] Rejections are aggregated.
- [ ] Runtime pressure is not decorative.
- [ ] Unsupported behavior is visible, not silent.
- [ ] Metrics do not rely on broker-only paths.

---

### Task 12.4 — Generate certification and support-boundary report

**Task description:**
Produce machine-readable and human-readable reports showing what V2 actually supports.

**Task technical:**
Certification consumes parity ledger, test results, conformance results, divergence register, and unsupported items.

**Affected files assumption:**

- `src_v2/certification/report.py`
- `tools/parity/generate_report.py`
- `docs/reports/v2_parity_report.md`
- `tests_v2/certification/test_parity_report_truth.py`

**Task checklist:**

- [ ] Report lists preserved items.
- [ ] Report lists intentional divergences.
- [ ] Report lists unsupported items.
- [ ] Report lists unchecked items.
- [ ] Allowed failures remain visible.
- [ ] Green report cannot hide missing proof.
