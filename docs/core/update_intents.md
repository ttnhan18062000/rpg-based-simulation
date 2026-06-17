---
status: active
layer: core
authority: P1
audience: agent
last_verified: 2026-06-13
---

# Update Intent Pipeline

## Purpose

An update intent is a frozen, typed record expressing a desired durable state change. Intents are produced during read-only decision logic and applied exclusively via the authoritative apply path. The pipeline is:

```
Read-only workers → StateUpdate fragments → merge → compact → ApplyPath.apply_generation()
```

No code path other than `ApplyPath.apply_generation()` (`src/engine/apply.py`) may apply a `StateUpdate` to produce a new `AuthoritativeState`.

Compliance IDs: AUTH-005, AUTH-006, AUTH-007, INFRA-122, TOWN-001, TOWN-002, TOWN-131, TOWN-156–163. Source: `src/core/updates.py`, `src/core/update_models/`.

## RPG meaning

In a simulation where many agents reason concurrently, unauthorized mutation is the root cause of non-determinism and conservation violations. A warrior worker must not directly subtract gold from a chest it references — it must emit a `ResourceTransferIntent` proposing the transfer. The authoritative apply path validates conservation before committing.

Intents exist to decouple intent expression (decision logic) from intent application (authoritative path). Decision logic remains pure: it reads frozen state, produces typed proposals, and is never the source of committed durable change. This maps directly to the Immutability Law in `docs/core/state.md`.

## Entity-level intent taxonomy

`EntityUpdate` (updates.py:600–690, Logic IDs: TOWN-001, TOWN-002) is the bundle holding per-entity changes. Each slot maps to one typed sub-intent. All sub-intent types are `frozen=True, slots=True` dataclasses implementing `is_noop()` and `merge()`.

| Field on `EntityUpdate` | Intent type | File / lines | Purpose |
|---|---|---|---|
| `new_position` | `tuple[float, float]` (inline) | updates.py:608 | Raw position override (sets movement dirty) |
| `navigation` | `NavigationUpdate` | updates.py:155–196 | Path, target, movement mode, congestion counters, region ID |
| `combat` | `CombatUpdate` | updates.py:94–153 | HP delta, attacker, outcome, simultaneous intents, wounds, durability |
| `interaction` | `InteractionUpdate` | updates.py:64–81 | Multi-tick harvest progress delta and reset flag |
| `inventory` | `InventoryUpdate` | update_models/inventory.py:8–29 | Items add/remove, gold delta — **result type only; see law below** |
| `resource_transfers` | `List[ResourceTransferIntent]` | update_models/resources.py:12–38 | Atomic transfer proposals with conservation enforcement |
| `identity` | `IdentityUpdate` | updates.py:218–262 | Role, faction, recipes, skills, traits, evolution level, cooldowns |
| `attributes` | `AttributeUpdate` | updates.py:381–413 | Base stat deltas: STR, AGI, VIT, END, INT, SPI, WIS, PER, CHA |
| `biological` | `BiologicalUpdate` | updates.py:349–379 | Sleep debt, hunger, rest pressure, meal/sleep tick stamps |
| `social` | `SocialUpdate` | updates.py:272–347 | Trust, familiarity, fear, grudge, bonds, reputation, contracts, nemesis |
| `quest` | `QuestUpdate` | update_models/quests.py:8–68 | Progress delta, status set, multi-quest container |
| `reward` | `RewardUpdate` | updates.py:445–464 | XP gain and evolution points (non-inventory only) |
| `lifecycle` | `LifecycleUpdate` | updates.py:415–443 | Age delta, permadeath flag, death tick/reason, heir, heirlooms |
| `equipment` | `EquipmentUpdate` | updates.py:38–62 | Slot assignments, durability delta/set per slot |
| `task` | `TaskUpdate` | updates.py:198–216 | Work kind and payload for next tick |
| `strategic` | `StrategicUpdate` | updates.py:466–559 | Blockers, leads, directives, projects, concerns, hypotheses, beliefs, overload |
| `stamina_update` | `StaminaUpdate` | updates.py:561–578 | Current stamina delta/set, max stamina set |
| `wound_update` | `WoundUpdate` | updates.py:580–597 | New wounds, wound heals by ID, new scars |
| `group_id_set` | `Optional[int]` (inline) | updates.py:629 | Group membership change (None = no change) |
| `self_model_bundle_set` | `Optional[Any]` (inline) | updates.py:630 | Full self-model replacement (from cognition layer) |
| `intent_results` | `List[IntentResult]` | updates.py:631 | Outcomes for UI/feedback (not applied to durable state) |
| `property_updates` | `Dict[str, Any]` | updates.py:632 | Generic entity property overrides |

Additional inline fields on `EntityUpdate` that affect dirtiness but are not sub-intents: `moved_this_tick: bool`, `readiness_delta: float`, `active: Optional[bool]`, `kind_set: Optional[str]`.

## World-level intent taxonomy

`StateUpdate` (updates.py:814–1053) carries world-level change records alongside `entity_updates`. World-level intents key by object ID; `StateUpdate.merge_many()` merges per-object records with minimal intermediate allocation.

| Field on `StateUpdate` | Intent type | Purpose |
|---|---|---|
| `world_updates` | `Dict[str, WorldUpdate]` | Hazard level, suppression, calamity, trauma, retaliation pressure, influence, owner faction, weather, modifiers per region |
| `node_updates` | `Dict[int, ResourceNodeUpdate]` | Harvest node charge delta and cooldown tick |
| `building_updates` | `Dict[int, BuildingUpdate]` | Building HP delta, functional flag, inventory, price modifiers |
| `camp_updates` | `Dict[str, CampUpdate]` | Camp maturity delta and active flag |
| `chest_updates` | `Dict[int, ChestUpdate]` | Chest cooldown set and items set |
| `chest_add_or_update` | `List[ChestState]` | Full chest record upsert |
| `ground_items_add_or_update` / `ground_items_remove` | `List[GroundItemState]` / `List[int]` | Dropped item lifecycle (add/update/remove by ID) |
| `corpses_add_or_update` / `corpses_remove` | `List[CorpseState]` / `List[int]` | Corpse lifecycle |
| `groups_add_or_update` / `groups_remove` | `List[GroupRecord]` / `List[int]` | Group lifecycle |
| `home_storage_updates` | `Dict[int, InventoryUpdate]` | Home storage inventory per entity |
| `resource_updates` | `Dict[str, float]` | Global resource pool deltas |

Additional `StateUpdate` fields that control pipeline behavior rather than intent content: `dirty_set`, `force_full_scan`, `entities_add`, `entities_remove`, `processed_transaction_ids`, `rejection_events`.

## Special intent rules

### `ResourceTransferIntent` — mandatory transfer pathway

`ResourceTransferIntent` (update_models/resources.py:12–38, Logic ID: VERIFIED v2) is the required pathway for all gold and item transfers that cross a conservation boundary. Key fields:

- `source_id`, `source_kind` — identifies the source object (NODE, GROUND_ITEM, CORPSE, CRAFTING, SHOP_BUY, SHOP_SELL)
- `items_add`, `items_remove`, `gold_delta`, `gold_cost`, `price_multiplier` — the transfer ledger
- `xp_reward`, `transfer_kind`, `transaction_id`, `group_id` — classification and deduplication
- Contingent sub-updates (`biological_upd`, `attributes_upd`, `identity_upd`, `combat_upd`, `strategic_upd`, `equipment_upd`, `reward_upd`) — applied only if the transaction succeeds

Workers must always emit `ResourceTransferIntent` for item and gold transfers. Never emit `InventoryUpdate` directly from decision logic. The `ResourceTransactionResolver` in the apply path validates conservation (inputs equal outputs, no creation from nothing) before committing.

`transaction_id` is used for exactly-once processing — `StateUpdate.processed_transaction_ids` tracks which transactions have already been applied to prevent double-application across merged sub-phases.

### `InventoryUpdate` — result type only

`InventoryUpdate` (update_models/inventory.py:8–29) carries items-add, items-remove, and gold delta. Its docstring states: **"RESULT TYPE ONLY. Workers must NOT emit this directly for gold/items; use `ResourceTransferIntent`."**

`InventoryUpdate` is the post-resolution output type written by the `ResourceTransactionResolver` after validating and committing a `ResourceTransferIntent`. It is also used by `BuildingUpdate.inventory` for building inventory changes. Bypassing `ResourceTransferIntent` breaks atomic conservation and is an architectural violation.

### `QuestUpdate` — MULTI sentinel

`QuestUpdate` (update_models/quests.py:8–68) supports a `"MULTI"` sentinel `quest_id` as a container for multi-quest batch updates. The `merge()` method flattens nesting to prevent `MULTI(MULTI(...))` chains. `is_noop()` treats a `"MULTI"` record with empty `multi_updates` as a no-op.

### `CombatIntent` — sub-record within `CombatUpdate`

`CombatIntent` (updates.py:83–92) is a single-attack record embedded within `CombatUpdate.simultaneous_intents`. It is not applied independently — it is a sub-record within the combat resolution result, used to record simultaneous attacker contributions. Fields: `attacker_id`, `damage`, `is_opportunity_attack`, `is_lethal`, `splash_radius`, `splash_damage`, `impact_pos`.

## Intent lifecycle

### Creation (read-only decision logic)

Workers receive `AuthoritativeState.to_readonly()` (state.py:1100–1146). This wraps all mutable collections in `ReadOnlyDict`, which raises `ReadOnlyError` on any mutation attempt. Decision logic (workers, pipeline phases, governance layer) produces `StateUpdate` fragments holding intent records but does not apply them.

Workers are the canonical producers of `EntityUpdate` fragments. Pipeline orchestration phases (e.g., governance, scheduling) produce `StateUpdate` fields like `current_mode_set`, `current_policy_set`.

### Merge and compaction

Sub-phase `StateUpdate` fragments are merged via `StateUpdate.merge_many()` (updates.py:884–1036, Logic ID: TOWN-204). This processes N updates in a single pass with minimal intermediate allocation:

- Per-entity bundles: merged by calling `EntityUpdate.merge()` for each entity ID.
- World-level records: per-object merges (`WorldUpdate.merge()`, `ResourceNodeUpdate.merge()`, etc.).
- Dirty sets: accumulated via `DirtySet.merge()` (updates.py:993).
- Transaction IDs: unioned across all sub-phases for deduplication.

`StateUpdate.compact()` (updates.py:1038–1046) then drops `EntityUpdate` entries where `EntityUpdate.is_noop()` returns `True`. This reduces the patch set reaching the apply path.

### Apply (authoritative path only)

`ApplyPath.apply_generation()` (`src/engine/apply.py`) is the sole location where a `StateUpdate` is applied to produce a new `AuthoritativeState`. No other code path may apply intents to durable state.

Apply sequence:
1. Receive merged and compacted `StateUpdate`.
2. Validate transaction IDs for exactly-once processing.
3. Apply entity updates, world updates, lifecycle events.
4. If `audit_dirty_set=True`, call `AuthoritativeState.validate_dirty_set()` post-apply.
5. Return the new `AuthoritativeState`.

Cross-reference: `docs/engine/authoritative_apply_contract.md` for full apply-path internals.

## Merge semantics

`EntityUpdate.merge()` (updates.py:656–690) combines two bundles for the same entity by calling each sub-intent's `merge()`. The three merge rules by field type:

| Rule | Applies to | Examples |
|---|---|---|
| **Delta sum** | Numeric delta fields | `hp_delta`, `xp_gain`, `sleep_debt_delta`, `readiness_delta`, `age_delta`, `trust_delta[k]` |
| **Set last-write-wins** | Optional set/override fields | `alive_set`, `current_project_id_set`, `movement_mode_set`, `reputation_set`, `death_tick_set` |
| **List concatenation** | List fields | `items_add`, `bond_updates`, `wounds_add`, `simultaneous_intents`, `resource_transfers` |

Nested sub-intents recurse: e.g., `social_upd` calls `SocialUpdate.merge()`, which sums delta dicts and concatenates list fields.

All sub-intent types implement `is_noop()` and `merge()`. This is the compaction contract — `StateUpdate.compact()` relies on `is_noop()` to prune zero-effect bundles before they reach apply.

## Mutation rules

**Must use intents:** Any change that survives beyond the current tick or function call must be expressed as a typed intent and applied through `ApplyPath.apply_generation()`. This includes: entity position, inventory, attributes, health, combat results, social relationships, quests, lifecycle events, world state.

**Must not bypass intents:** Directly mutating `AuthoritativeState` fields is an architectural violation. It bypasses dirty tracking, conservation checks, and the determinism guarantee.

**May bypass intents:** Ephemeral, in-tick local state that does not persist to `AuthoritativeState` — intermediate calculation variables, working sets within a single worker, UI feedback signals that do not affect the next tick. `intent_results` on `EntityUpdate` is the conventional carrier for feedback that does not affect durable state.

Cross-reference: `docs/core/state.md` — Immutability Law. The `ReadOnlyDict` / `ReadOnlyError` enforcement is the runtime guard; the intent system is the data-model contract.

## Edge cases

### Conflicting intents for the same field

`EntityUpdate.merge()` resolves conflicts by the merge rule for the field type. For set fields, the later merge wins. For delta fields, both contributions accumulate. If two pipeline phases produce incompatible set-field values (e.g., two phases both set `movement_mode_set`), the one merged last wins. Phase sequencing is the caller's responsibility — `merge_many()` processes updates in the order supplied.

### Invalid intent targets

An `EntityUpdate` keyed to a non-existent entity ID may be dropped silently or raise during apply, depending on the apply-path implementation. Callers should validate that target entities exist before emitting updates if the entity may die between resolution and apply (e.g., concurrent combat producing an `EntityUpdate` for an entity whose lifecycle phase removed it).

### Dropped intents (no-ops)

`StateUpdate.compact()` drops `EntityUpdate` entries where `EntityUpdate.is_noop()` is `True`. Any intent that produces `is_noop() == True` for all sub-fields is silently discarded. Callers must not rely on a no-op intent reaching apply — if a side effect is needed even for a logically empty update, use a non-noop sentinel field.

### `force_full_scan` and dirty-set bypass

A `StateUpdate` with `force_full_scan=True` causes downstream `CandidateSelector.entities()` calls to return all entities regardless of dirty flags. The `StateUpdate` itself is still applied normally — `force_full_scan` only affects routing, not application.

## Source areas

- `src/core/updates.py` — All entity-level and world-level intent types, `StateUpdate`, `EntityUpdate.merge()`, `StateUpdate.merge_many()`, `StateUpdate.compact()`
- `src/core/update_models/inventory.py` — `InventoryUpdate` (result type only)
- `src/core/update_models/resources.py` — `ResourceTransferIntent`
- `src/core/update_models/quests.py` — `QuestUpdate`, MULTI sentinel
- `src/core/state.py` — `AuthoritativeState.to_readonly()`, `ReadOnlyDict`, `ReadOnlyError`
- `src/engine/apply.py` — `ApplyPath.apply_generation()` (sole application site)

Cross-reference: `docs/engine/authoritative_apply_contract.md` (apply-path internals), `docs/engine/authoritative_mutation_pipeline_contract.md` (mutation rules), `docs/core/state.md` (Immutability Law).

## Regression tests

| Test file | What it verifies |
|---|---|
| `tests/perf/test_dirty_set_integrity.py` | `DirtySet.from_update()` correctly derives dirty flags from `StateUpdate` content |
| `tests/integration/pipeline/test_authoritative_apply.py` | `apply_generation()` isolation (prior state not mutated), determinism, resource delta correctness |
| `tests/integration/pipeline/test_phase5_idempotency.py` | Exactly-once transaction processing via `processed_transaction_ids` |
| `tests/perf/test_apply_compaction_perf.py` | `StateUpdate.compact()` behavior under load |
| `tests/architecture/test_phase18_import_boundaries.py` | `src/core/` never imports `src/domains/`; layer isolation |

## Extension rules

To add a new intent type:

1. Define a new `frozen=True, slots=True` dataclass in `src/core/updates.py` or an appropriate `src/core/update_models/` file.
2. Implement `is_noop()` — must return `True` when the instance has no effect on durable state. A default-constructed instance must always satisfy `is_noop() == True`.
3. Implement `merge(self, other) -> Self` with rules that match field semantics:
   - Numeric deltas: sum both sides.
   - Optional set/override fields: last-write-wins (`other.field if other.field is not None else self.field`).
   - List fields: concatenate (`self.field + other.field`).
   - Document any field that does not follow the standard rules.
4. Add a slot to `EntityUpdate` (for entity-scoped intents) or a field to `StateUpdate` (for world-scoped intents).
5. Update `EntityUpdate.merge()` (updates.py:656) to call the new sub-intent's `merge()`.
6. Update `EntityUpdate.is_noop()` (updates.py:634) to include the new slot.
7. Update `StateUpdate.compact()` (updates.py:1038) if the new slot can produce no-op entity bundles that should be pruned.
8. Update the dirty-flag derivation in `DirtySet.from_update()` and `DirtySetBuilder.mark_from_update()` to classify the new field into the appropriate entity domain set (see `docs/core/dirty_state_and_dependency.md` — Extension rules).
9. Document the new intent in this file (entity-level or world-level taxonomy table, plus a special intents subsection if it has non-standard rules).
10. Add tests asserting: `is_noop()` on a default-constructed instance, `merge()` commutativity (or document why it is not commutative), and that the apply path applies the intent correctly.
