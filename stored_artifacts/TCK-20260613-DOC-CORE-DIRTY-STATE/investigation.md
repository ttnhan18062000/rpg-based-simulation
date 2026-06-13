---
ticket_id: TCK-20260613-DOC-CORE-DIRTY-STATE
phase: investigation
date: 2026-06-13
---

# Investigation: Core Dirty State and Update Intent Pipeline

## Current Behavior

### `src/core/dirty.py` (Logic IDs: PERF-005, PERF-006, PERF-007, PERF-008, PERF-015)

The file defines four classes that together implement the dirty-tracking optimization layer:

**`DirtySetLeakError`** (dirty.py:11)
An exception raised when `AuthoritativeState.validate_dirty_set()` detects a state mutation that was not captured in the `DirtySet`. This is the audit-mode enforcement mechanism.

**`DirtySet`** (dirty.py:204–234, Logic ID: PERF-006)
A `frozen=True, slots=True` dataclass tracking which entities and world objects changed during a tick. Contains 18 fields split into two categories:
- **Entity domain sets** (9): `movement_entities`, `combat_entities`, `inventory_entities`, `strategic_entities`, `social_entities`, `lifecycle_entities`, `biological_entities`, `attribute_entities`, `town_entities` — all `Set[int]` (entity IDs).
- **World object sets** (9): `group_ids`, `region_ids`, `resource_node_ids`, `building_ids`, `chest_ids`, `ground_item_ids`, `corpse_ids`, `camp_ids` — typed sets (int or str).

The `all_dirty_entities` property (dirty.py:231) returns the union of all 8 entity-domain sets (excluding `town_entities`, which is a position-derived subset).

`DirtySet.from_update()` (dirty.py:237–376) derives a fresh DirtySet from a `StateUpdate`. It classifies each entity update by its non-None fields, handles incremental merging from a `base_dirty` set, and applies town-tile position logic. It ends by calling `DirtyDependencyGraph.expand()`.

`DirtySet.merge()` (dirty.py:378–399) produces the union of two DirtySets and re-expands via `DirtyDependencyGraph.expand()`.

**`DirtySetBuilder`** (dirty.py:58–202)
A mutable builder that avoids excessive object creation when accumulating dirty marks from multiple `StateUpdate` objects incrementally. Used by the pipeline when applying multiple sub-phase updates. Its `mark_entity()` method (dirty.py:101–110) accepts `List[str]` tags. Its `mark_from_update()` method (dirty.py:112–180) applies the same field-inspection logic as `DirtySet.from_update()` but accumulates into mutable sets. The `build()` call (dirty.py:182–202) creates the `DirtySet` and passes it through `DirtyDependencyGraph.expand()`.

**`DirtyDependencyGraph`** (dirty.py:402–457, Logic ID: PERF-008)
The expansion logic — the most critical part for documentation. The `expand()` static method takes a raw `DirtySet` and adds derived dirtiness. See the Dirty Dependency Graph section below.

**`CandidateSelector`** (dirty.py:460–506, Logic ID: PERF-007)
The authoritative mechanism for determining which entities a simulation phase should process. Its `entities()` static method accepts a set of domain names and returns a sorted tuple of active entity IDs from the corresponding dirty sets. This is the read-side: pipeline phases call `CandidateSelector.entities()` to skip clean entities. The `get_relevant_entity_ids()` function (dirty.py:14–39) provides legacy domain-level filtering used by older pipeline helpers.

**Fallback rule** (dirty.py:20–21, dirty.py:474–476): If `update.force_full_scan` is `True` or `update.dirty_set` is `None`, all entity IDs from `state.entities` are returned regardless of domain.

### `src/core/updates.py` (Compliance: AUTH-005, AUTH-006, AUTH-007, INFRA-122, TOWN-001, TOWN-002)

This file defines the entire update intent taxonomy plus the top-level `StateUpdate` container and its compaction/merge logic.

**Key design invariant**: all update types are `frozen=True, slots=True` dataclasses. Every update type implements `is_noop()` and `merge()`. This is the compaction contract — updates can be safely merged by callers before they reach the authoritative apply path.

**`StateUpdate`** (updates.py:814–1053)
The top-level collection of all changes to be applied. Key fields:
- `entity_updates: Dict[int, EntityUpdate]` — per-entity change bundles.
- `dirty_set: Optional[DirtySet]` — carried alongside the update for pipeline routing.
- `force_full_scan: bool` — overrides dirty-set filtering.
- World-level collections: `world_updates`, `node_updates`, `building_updates`, `camp_updates`, `chest_updates`, `home_storage_updates`, `groups_add_or_update`, `groups_remove`, `ground_items_add_or_update`, `corpses_add_or_update`, etc.
- `compact()` (updates.py:1038–1046): removes no-op `EntityUpdate` entries. Called Logic ID: TOWN-204 on `merge_many`.
- `merge_many()` (updates.py:884–1036): merges multiple `StateUpdate` objects with minimal intermediate allocations. Merges DirtySets via `dirty.merge()`.

### `src/core/state.py` (Compliance: AUTH-009)

`AuthoritativeState` (state.py:980–1049): frozen dataclass holding `tick`, `seed`, and all world collections. All collections are wrapped in `ReadOnlyDict` during `to_readonly()` (state.py:1100–1146), which raises `ReadOnlyError` on any mutation attempt — enforcing the read-only phase contract.

`AuthoritativeState.validate_dirty_set()` (state.py:1159–1205): the audit function that verifies all changed entities and world objects appear in the `DirtySet`. Called with `audit_dirty_set=True` flag in `ApplyPath.apply_generation()`.

`EntityState.to_readonly()` (state.py:697–795): converts mutable collections (inventory items, wounds, scars, properties) to tuples and `ReadOnlyDict` to prevent mutation during decision logic phases.

---

## Dirty Dependency Graph

Exact expansion rules from `DirtyDependencyGraph.expand()` (dirty.py:408–457):

| Source Dirty Flag | Implies (adds to) Dirty Flag | Reason / Comment |
|---|---|---|
| `movement` | `strategic` | Positional changes affect pathfinding proximity scoring |
| `movement` | `social` | Movement produces encounters that require social evaluation |
| `inventory` | `strategic` | Item changes trigger capacity, shop, and goal re-evaluation |
| `combat` | `lifecycle` | HP loss triggers near-death and death checks |
| `combat` | `social` | Combat affects group morale, fear, and fleeing decisions |
| `combat` | `strategic` | Combat outcome changes goal validity |
| `biological` | `strategic` | Hunger/sleep pressure shifts goal priorities |
| `biological` | `lifecycle` | Biological extremes can cause death |
| `attributes` | `strategic` | Attribute changes can unlock or block goals |
| `attributes` | `lifecycle` | Attribute changes affect max-HP derived from vitality |

No expansion for: `social`, `lifecycle`, `town`, `biological→social`, `movement→lifecycle`, `movement→inventory`. These relationships are one-way — downstream flags do not propagate further.

**World object dirty flags** (`group_ids`, `region_ids`, `resource_node_ids`, `building_ids`, `chest_ids`, `ground_item_ids`, `corpse_ids`, `camp_ids`) are passed through `expand()` unchanged — they have no dependency expansion rules.

**Domain-to-DirtySet mapping** in `CandidateSelector.entities()` / `get_relevant_entity_ids()`:

| Pipeline Domain | Reads from DirtySet |
|---|---|
| `movement` | `movement_entities` |
| `combat` | `combat_entities` |
| `inventory` | `inventory_entities` |
| `strategic` | `strategic_entities` |
| `social` | `social_entities` |
| `lifecycle` | `lifecycle_entities` |
| `biological` | `biological_entities` |
| `attributes` | `attribute_entities` |
| `town` | `town_entities` |
| `interactions` | `movement_entities` ∪ `strategic_entities` |
| `groups` | `movement_entities` ∪ `combat_entities` ∪ `social_entities` |
| `shop` | `movement_entities` ∪ `inventory_entities` |
| `capacity` | `strategic_entities` |
| `redirection` | `strategic_entities` |
| `all` | `all_dirty_entities` (union of all 8 entity domain sets) |
| *(unknown domain)* | full `state.entities` fallback |

---

## Update Intent Taxonomy

### Entity-level intents (in `EntityUpdate`, updates.py:600–690)

`EntityUpdate` is the bundle holding per-entity changes. Each slot maps to one typed sub-intent:

| Field on `EntityUpdate` | Intent Type | File | Purpose |
|---|---|---|---|
| `new_position` | `tuple[float, float]` (inline) | updates.py | Raw position override |
| `navigation` | `NavigationUpdate` | updates.py:156–196 | Path, target, movement mode, congestion counters |
| `combat` | `CombatUpdate` | updates.py:95–153 | HP delta, attacker, outcome, simultaneous intents, wounds |
| `interaction` | `InteractionUpdate` | updates.py:64–81 | Multi-tick harvest progress and reset |
| `inventory` | `InventoryUpdate` | update_models/inventory.py:8–29 | Items add/remove, gold delta (result type only — see law below) |
| `resource_transfers` | `List[ResourceTransferIntent]` | update_models/resources.py:12–38 | Atomic transfer proposals with conservation enforcement |
| `identity` | `IdentityUpdate` | updates.py:218–262 | Role, faction, recipes, skills, traits, evolution, cooldowns |
| `attributes` | `AttributeUpdate` | updates.py:381–413 | Base stat deltas (STR, AGI, VIT, END, INT, SPI, WIS, PER, CHA) |
| `biological` | `BiologicalUpdate` | updates.py:349–379 | Sleep debt, hunger, rest pressure |
| `social` | `SocialUpdate` | updates.py:273–347 | Trust, familiarity, fear, grudge, bonds, reputation, contracts |
| `quest` | `QuestUpdate` | update_models/quests.py:8–68 | Progress delta, status set, multi-quest container |
| `reward` | `RewardUpdate` | updates.py:445–464 | XP and evolution points (non-inventory only) |
| `lifecycle` | `LifecycleUpdate` | updates.py:415–443 | Age delta, permadeath, death tick/reason, heir |
| `equipment` | `EquipmentUpdate` | updates.py:38–62 | Slot assignments, durability delta/set |
| `task` | `TaskUpdate` | updates.py:198–216 | Work kind and payload for next tick |
| `strategic` | `StrategicUpdate` | updates.py:466–559 | Blockers, leads, directives, projects, concerns, hypotheses, beliefs |
| `stamina_update` | `StaminaUpdate` | updates.py:561–578 | Current stamina, max stamina |
| `wound_update` | `WoundUpdate` | updates.py:580–597 | New wounds, healed wounds, new scars |
| `group_id_set` | `Optional[int]` (inline) | updates.py | Group membership change |
| `self_model_bundle_set` | `Optional[Any]` (inline) | updates.py | Full self-model replacement |
| `intent_results` | `List[IntentResult]` | updates.py | Outcomes for UI/feedback |
| `property_updates` | `Dict[str, Any]` | updates.py | Generic entity properties |

**Total entity-level intent types**: 22 distinct update slots on `EntityUpdate`.

### World-level intents (in `StateUpdate`)

| Field on `StateUpdate` | Intent Type | Purpose |
|---|---|---|
| `world_updates` | `Dict[str, WorldUpdate]` | Hazard, trauma, influence, weather, modifiers per region |
| `node_updates` | `Dict[int, ResourceNodeUpdate]` | Node charges delta, cooldown |
| `building_updates` | `Dict[int, BuildingUpdate]` | Building HP, functional flag, inventory |
| `camp_updates` | `Dict[str, CampUpdate]` | Camp maturity, active flag |
| `chest_updates` / `chest_add_or_update` | `Dict[int, ChestUpdate]` / `List[ChestState]` | Chest cooldown and items |
| `ground_items_add_or_update` / `ground_items_remove` | `List[GroundItemState]` / `List[int]` | Dropped item lifecycle |
| `corpses_add_or_update` / `corpses_remove` | `List[CorpseState]` / `List[int]` | Corpse lifecycle |
| `groups_add_or_update` / `groups_remove` | `List[GroupRecord]` / `List[int]` | Group lifecycle |
| `home_storage_updates` | `Dict[int, InventoryUpdate]` | Milestone 5 home storage |
| `resource_updates` | `Dict[str, float]` | Global resource pool deltas |

### Special intents

**`ResourceTransferIntent`** (`update_models/resources.py:12–38`, Logic ID: VERIFIED v2: ResourceTransferIntent)
The required pathway for all gold and item transfers that cross a conservation boundary. Fields: `source_id`, `source_kind` (NODE, GROUND_ITEM, CORPSE, CRAFTING, SHOP_BUY, SHOP_SELL), `items_add`, `items_remove`, `gold_delta`, `gold_cost`, `price_multiplier`, `xp_reward`, `transfer_kind`, `transaction_id`, `group_id`, and a set of contingent sub-updates (`biological_upd`, `attributes_upd`, `identity_upd`, `combat_upd`, `strategic_upd`, `equipment_upd`, `reward_upd`) applied only on transaction success.

**`InventoryUpdate`** (`update_models/inventory.py:14`)
Docstring: "RESULT TYPE ONLY. Workers must NOT emit this directly for gold/items; use `ResourceTransferIntent`." It is the post-resolution output type written by the `ResourceTransactionResolver`, not an input from decision logic.

**`QuestUpdate`** (`update_models/quests.py:8–68`)
Supports a `"MULTI"` sentinel `quest_id` as a container for multi-quest batch updates. The `merge()` method flattens nesting to prevent `MULTI(MULTI(...))` chains. The `is_noop()` check treats `"MULTI"` with empty `multi_updates` as a no-op.

**`CombatIntent`** (updates.py:83–92)
A single-attack record embedded within `CombatUpdate.simultaneous_intents`. Not applied independently — it is a sub-record within the combat resolution result.

---

## Intent Lifecycle

### Where intents are created

Intents are created exclusively during **read-only decision logic**:

- **Workers** (concurrent sub-phase workers): Read `AuthoritativeState.to_readonly()`, produce `StateUpdate` proposals. They must not call any method that mutates a live state object. `ReadOnlyDict` raises `ReadOnlyError` on any attempt.
- **Pipeline phases** (e.g., combat resolution, movement resolution): Each phase produces a `StateUpdate` fragment covering its domain.
- **Governance layer**: Produces `StateUpdate` fields like `current_mode_set`, `current_policy_set`.

### Where intents are applied

Intents are applied exclusively in **`ApplyPath.apply_generation()`** (`src/engine/apply.py`), as documented in `docs/engine/authoritative_apply_contract.md`:

1. Sub-phase `StateUpdate` fragments are merged via `StateUpdate.merge_many()`.
2. The merged update is compacted via `StateUpdate.compact()` (removes no-op entity entries).
3. `ApplyPath.apply_generation()` applies the compacted update to produce a new `AuthoritativeState`.
4. If `audit_dirty_set=True`, `AuthoritativeState.validate_dirty_set()` is called post-apply.

The `DirtySet` is derived from the merged `StateUpdate` (via `DirtySet.from_update()`) and attached as `StateUpdate.dirty_set` before the apply call. It is then used by subsequent pipeline phases to route entity processing.

### Compaction semantics

`StateUpdate.compact()` (updates.py:1038–1046): iterates `entity_updates` and drops entries where `EntityUpdate.is_noop()` returns `True`. This reduces the number of entity patches that reach `ApplyPath`.

`EntityUpdate.merge()` (updates.py:656–690): merges two `EntityUpdate` objects for the same entity by calling each sub-intent's `merge()` method. Sub-intent merge rules:
- **Deltas** are summed (e.g., `hp_delta`, `xp_gain`, `sleep_debt_delta`).
- **Set fields** prefer the later value (last write wins, e.g., `alive_set`, `current_project_id_set`).
- **Lists** are concatenated (e.g., `items_add`, `bond_updates`, `wounds_add`).
- **Nested updates** recurse (e.g., `social_upd` calls `SocialUpdate.merge()`).

`StateUpdate.merge_many()` (updates.py:884–1036, Logic ID: TOWN-204): merges N updates in a single pass with minimal intermediate allocation. For world-level updates, per-object merges are applied to minimize object creation.

---

## Existing Doc Coverage

### `docs/core/state.md`
Covers:
- The Immutability Law (frozen dataclasses, `ReadOnlyDict`).
- The frozen lifecycle: Snapshot → Deliberation → Refinement → Transition.
- Component composition pattern and anatomy.
- Serialization and canonical protocol (`to_canonical_dict()`, `_canonical_cache`).
- Regional state and trauma.
- Performance: shallow copying, zero-allocation ReadOnly caching, fingerprinting.

Does NOT cover:
- The dirty-flag system (`DirtySet`, `DirtyDependencyGraph`, `CandidateSelector`).
- The update intent taxonomy and lifecycle.
- Compaction semantics.
- The `InventoryUpdate` restriction rule.
- `ResourceTransferIntent` conservation law.
- The `force_full_scan` fallback path.

### `docs/core/README.md`
Lists four files: `state.md`, `entities.md`, `attributes_and_classes.md`, `items_and_inventory.md`. Does not mention `dirty_state_and_dependency.md` or `update_intents.md` (both to be created).

### `src/core/update_models/README.md`
One line: "Canonical typed representations of state transitions and intents." Contains no detail.

---

## Test Coverage

### Tests that directly verify dirty-state and mutation boundaries

| Test file | What it verifies |
|---|---|
| `tests/perf/test_dirty_set_integrity.py` | `DirtySet.from_update()` tracks movement, combat, world objects correctly; `DirtySetLeakError` fires on undeclared mutations; incremental merge correctness via `DirtySet.merge()`. |
| `tests/perf/test_dirty_parity.py` | Bit-identical state hashes between DirtySet-optimized path and `force_full_scan=True` reference path over 100 ticks (marked `@pytest.mark.slow`). |
| `tests/integration/pipeline/test_authoritative_apply.py` | `ApplyPath.apply_generation()` isolation (prior state not mutated), deterministic apply order, resource update correctness. |

### Tests that verify mutation boundary enforcement (read-only)

| Test file | What it verifies |
|---|---|
| `tests/architecture/test_phase18_import_boundaries.py` | `src/core/` never imports `src/domains/` (layer isolation). |
| `tests/architecture/test_phase18_cognition_migration_linter.py` | `EntityState` has no flat cognitive fields — all cognitive state must live inside `CognitionModel`. |
| `tests/architecture/test_phase19_hot_path_safety_contract.py` | `src/engine/` and hot-path observability files do not import heavy post-run analyzers. |
| `tests/architecture/test_phase19_observability_boundaries.py` | Observability boundary doc exists with required terminology; hot path does not import `observability.anomaly`, `.cognition`, `.reporting`. |

### Tests that exercise StateUpdate through the pipeline

| Test file | Relevance |
|---|---|
| `tests/integration/pipeline/test_phase5_idempotency.py` | Verifies exactly-once transaction processing via `processed_transaction_ids`. |
| `tests/perf/test_apply_compaction_perf.py` | Verifies `StateUpdate.compact()` behavior under load. |
| `tests/perf/bench_apply_path.py` | Performance benchmark for apply path. |

### Note on architecture tests and mutation boundaries

None of the files in `tests/architecture/` directly test the `DirtySet` or `StateUpdate` classes by import — the dirty-set tests live in `tests/perf/` (which is semantically correct: they verify optimization correctness, not purely architecture rules). The architecture tests focus on import boundaries and structural invariants.

---

## Risks and Open Questions

1. **`navigation` is not a dirty tag in `DirtySetBuilder.mark_entity()`** (dirty.py:101–110): `mark_entity()` accepts tags `movement`, `combat`, `inventory`, `strategic`, `social`, `lifecycle`, `biological`, `attributes` — but not `town`. Town dirtiness is derived from position tile-checking in `mark_from_update()`, not from tags. This is correct but should be called out explicitly in the doc.

2. **`e_upd.task` dirtiness**: In `DirtySet.from_update()` (dirty.py:329), `e_upd.task` is present on `EntityUpdate` but is NOT checked in `from_update()`. Only `e_upd.strategic`, `e_upd.task`, `e_upd.interaction`, and `e_upd.quest` together trigger `strategic.add(e_id)` in `DirtySetBuilder.mark_from_update()` (dirty.py:162) but in `DirtySet.from_update()` (dirty.py:329) the check is `e_upd.strategic or e_upd.interaction or e_upd.quest` — `e_upd.task` is missing. This is a subtle behavioral discrepancy between `DirtySetBuilder` and `DirtySet.from_update()`. Worth calling out in the doc as a known edge case.

3. **`entities_add` / `entities_remove`** handling (dirty.py:353–361): Added or removed entities are added to ALL entity domain sets simultaneously. This is a conservative "mark everything dirty" approach for lifecycle events. The doc should note this.

4. **`DirtySet.merge()` does not include `biological_entities` or `attribute_entities`** (dirty.py:378–399): The `merge()` method appears to omit `biological_entities` and `attribute_entities` from the union (they are not listed in the returned `DirtySet` constructor call — lines 380–398). However, `DirtyDependencyGraph.expand()` is called on the result, which may re-derive biological/attribute from other flags. This requires careful documentation — the merge is not simply a union of all fields without expansion.

   Checking: Looking at lines 380–399, the `DirtySet` constructor in `merge()` does include `biological_entities=self.biological_entities | other.biological_entities` and `attribute_entities=self.attribute_entities | other.attribute_entities`. Actually, these fields ARE included (lines 396–397). The concern is resolved — both are merged correctly.

5. **`force_full_scan` semantics**: When `force_full_scan=True`, the dirty set is bypassed entirely. The doc should explain when this is set (explicit flag in `Kernel` constructor, or carried on a `StateUpdate`).

6. **`StateUpdate.dirty_set` carriage**: The dirty set is attached to the `StateUpdate` object and merges forward as sub-phase updates are merged together (updates.py:993). This means the dirty set accumulates across sub-phases within a single tick, which is correct but non-obvious.
