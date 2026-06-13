---
ticket_id: TCK-20260613-DOC-CORE-DIRTY-STATE
phase: plan
date: 2026-06-13
---

# Implementation Plan: TCK-20260613-DOC-CORE-DIRTY-STATE

## Scope Summary

Create two new logic-contract docs in `docs/core/` covering the dirty-flag dependency model and the update intent pipeline. Update `docs/core/README.md` to list both. Run index and registry regeneration after. No source code changes.

---

## Ordered Steps

### Step 1 — Write `docs/core/dirty_state_and_dependency.md`

**File produced:** `docs/core/dirty_state_and_dependency.md` (new)

**Sources consumed (read-only):**
- `src/core/dirty.py` — already fully read in investigation
- `docs/core/state.md` — must not contradict the Immutability Law
- `tests/perf/test_dirty_set_integrity.py`, `tests/perf/test_dirty_parity.py` — cited in Regression tests section

**Required sections (in order):**

1. **Frontmatter block** — `status: active`, `layer: core`, `authority: P1`, `audience: agent`, `last_verified: 2026-06-13`.

2. **Purpose** — What "dirty" means in the tick pipeline: a flag indicating that an entity's domain state changed this tick and downstream systems must re-evaluate it. The primary motivation is optimization: skip clean entities, avoid full-entity recompute every tick.

3. **Dirty flag taxonomy** — Table of 9 entity-domain sets (`movement`, `combat`, `inventory`, `strategic`, `social`, `lifecycle`, `biological`, `attributes`, `town`) and 8 world-object sets (`group_ids`, `region_ids`, `resource_node_ids`, `building_ids`, `chest_ids`, `ground_item_ids`, `corpse_ids`, `camp_ids`). Note that `town` is derived (not directly settable via `mark_entity()`) and world sets have no expansion rules.

4. **Dependency expansion graph** — Verbatim from `DirtyDependencyGraph.expand()` (dirty.py:408–457). Full table:

   | Source flag   | Implies flag | Reason |
   |---|---|---|
   | `movement`    | `strategic`  | Positional changes affect pathfinding proximity scoring |
   | `movement`    | `social`     | Movement produces encounters requiring social evaluation |
   | `inventory`   | `strategic`  | Item changes trigger capacity, shop, and goal re-evaluation |
   | `combat`      | `lifecycle`  | HP loss triggers near-death and death checks |
   | `combat`      | `social`     | Combat affects group morale, fear, fleeing decisions |
   | `combat`      | `strategic`  | Combat outcome changes goal validity |
   | `biological`  | `strategic`  | Hunger/sleep pressure shifts goal priorities |
   | `biological`  | `lifecycle`  | Biological extremes can cause death |
   | `attributes`  | `strategic`  | Attribute changes can unlock or block goals |
   | `attributes`  | `lifecycle`  | Attribute changes affect max-HP derived from vitality |

   Explicitly state non-propagating terminals: `social`, `lifecycle`, `town` do not expand further. World sets are passed through unchanged.

5. **Dirty flag lifecycle within a tick** — How flags are set (workers and pipeline phases produce `StateUpdate` fragments → `DirtySet.from_update()` or `DirtySetBuilder.mark_from_update()` derives flags → `DirtyDependencyGraph.expand()` adds derived flags → attached to `StateUpdate.dirty_set` → accumulated across sub-phases via `DirtySet.merge()`). How flags are consumed (`CandidateSelector.entities()` returns only dirty-domain entity IDs for each pipeline phase). How flags are cleared (flags do not persist across ticks; each tick builds a fresh `DirtySet`).

6. **CandidateSelector domain routing** — Table mapping pipeline domain names to the DirtySet fields they read, including compound domains (`interactions`, `groups`, `shop`, `capacity`, `redirection`, `all`). Source: dirty.py:460–506 and dirty.py:14–39.

7. **Fallback: `force_full_scan`** — When `StateUpdate.force_full_scan=True` or `dirty_set=None`, `CandidateSelector.entities()` returns all entity IDs from `state.entities`. Used when the full entity pool must be re-evaluated (e.g., world-wide calamity, initial tick).

8. **Dirty set accumulation across sub-phases** — `DirtySet.merge()` is called when sub-phase `StateUpdate` objects are merged via `StateUpdate.merge_many()`. The merged `dirty_set` field (updates.py:993) accumulates dirtiness from all sub-phases within a tick before routing to subsequent phases.

9. **Entity death / lifecycle edge case** — Entities added or removed (via `StateUpdate.entities_add` / `entities_remove`) are simultaneously marked in ALL entity domain sets (dirty.py:353–361). This is the conservative "mark everything dirty" rule for lifecycle events to ensure no downstream system skips a newly spawned or destroyed entity.

10. **Known edge cases and risks** (call out explicitly as a subsection, not inline):
    - **`town` is position-derived, not tag-settable**: `DirtySetBuilder.mark_entity()` accepts tags `movement`, `combat`, `inventory`, `strategic`, `social`, `lifecycle`, `biological`, `attributes` — not `town`. Town dirtiness is derived by tile-checking inside `mark_from_update()`.
    - **`e_upd.task` discrepancy**: `DirtySetBuilder.mark_from_update()` treats `e_upd.task` as a trigger for `strategic` dirtiness (dirty.py:162), but `DirtySet.from_update()` omits `e_upd.task` from the same check (dirty.py:329). Agents using `DirtySet.from_update()` directly (rather than `DirtySetBuilder`) will not mark an entity strategic-dirty when only `task` changes. This is a known pre-existing inconsistency; do not fix it in this ticket — raise a separate bugfix ticket.
    - **`DirtySetLeakError` audit mode**: `AuthoritativeState.validate_dirty_set()` checks post-apply that all mutated entities and world objects appear in the attached `DirtySet`. Fires `DirtySetLeakError` on violation. Only active when `audit_dirty_set=True` is passed to `ApplyPath.apply_generation()`.

11. **What must not bypass dirty tracking** — Any durable state change (entity attribute update, position change, item transfer) must flow through `StateUpdate` so the resulting `DirtySet` captures the change. Directly mutating `AuthoritativeState` fields bypasses dirty tracking and will either be caught by `validate_dirty_set()` (in audit mode) or cause stale processing in subsequent phases.

12. **Regression tests** — Cite with full paths:
    - `tests/perf/test_dirty_set_integrity.py` — correctness of `DirtySet.from_update()`, `DirtySetLeakError`, incremental merge.
    - `tests/perf/test_dirty_parity.py::test_dirty_set_vs_full_scan_parity` — bit-identical state hash between optimized and `force_full_scan=True` paths over 100 ticks (`@pytest.mark.slow`).
    - `tests/integration/pipeline/test_authoritative_apply.py` — `apply_generation()` isolation and determinism.

13. **Extension rules** — When to add a new dirty flag: (a) define a new `Set[int]` field on `DirtySet` and `DirtySetBuilder`; (b) add field inspection in both `DirtySet.from_update()` and `DirtySetBuilder.mark_from_update()` (keep them in sync to avoid the `e_upd.task` class of discrepancy); (c) add expansion edges in `DirtyDependencyGraph.expand()` if the new flag implies downstream dirtiness; (d) add a domain routing entry in `CandidateSelector.entities()`; (e) update `DirtySet.merge()` to include the new field; (f) add a test case to `test_dirty_set_integrity.py`.

**Scope guard:** Do not modify `src/core/dirty.py`. Do not contradict or duplicate `docs/core/state.md`'s Immutability Law section — cross-reference it instead.

**Acceptance criteria for Step 1:**
- File exists at `docs/core/dirty_state_and_dependency.md`.
- Frontmatter keys present: `status`, `layer`, `authority`, `audience`, `last_verified`.
- All 10 expansion edges from `DirtyDependencyGraph.expand()` documented in a table.
- Domain-routing table covers all named domains including compound ones.
- `e_upd.task` discrepancy documented in Known edge cases.
- Regression tests section cites the three test file paths listed above.
- Extension rules section present.

---

### Step 2 — Write `docs/core/update_intents.md`

**File produced:** `docs/core/update_intents.md` (new)

**Sources consumed (read-only):**
- `src/core/updates.py` — already fully read in investigation
- `src/core/update_models/inventory.py`, `src/core/update_models/resources.py`, `src/core/update_models/quests.py` — already read in investigation
- `docs/engine/authoritative_apply_contract.md` — cross-reference (do not duplicate)

**Required sections (in order):**

1. **Frontmatter block** — same keys: `status: active`, `layer: core`, `authority: P1`, `audience: agent`, `last_verified: 2026-06-13`.

2. **Purpose** — What an update intent is: a frozen, typed record expressing a desired durable state change, produced during read-only decision logic and applied exclusively via the authoritative apply path. Intents exist to prevent unauthorized mutation from read-only decision logic (the `ReadOnlyDict` / `ReadOnlyError` enforcement is the runtime guard; intents are the data-model contract).

3. **Intent taxonomy — entity-level** — Table of all 22 slots on `EntityUpdate` (updates.py:600–690):

   | Field | Intent type | Location | Purpose |
   |---|---|---|---|
   | `new_position` | `tuple[float, float]` (inline) | updates.py | Raw position override |
   | `navigation` | `NavigationUpdate` | updates.py:156–196 | Path, target, movement mode, congestion counters |
   | `combat` | `CombatUpdate` | updates.py:95–153 | HP delta, attacker, outcome, wounds |
   | `interaction` | `InteractionUpdate` | updates.py:64–81 | Multi-tick harvest progress and reset |
   | `inventory` | `InventoryUpdate` | update_models/inventory.py:8–29 | **Result type only — see law below** |
   | `resource_transfers` | `List[ResourceTransferIntent]` | update_models/resources.py:12–38 | Atomic transfer proposals with conservation enforcement |
   | `identity` | `IdentityUpdate` | updates.py:218–262 | Role, faction, recipes, skills, traits, evolution, cooldowns |
   | `attributes` | `AttributeUpdate` | updates.py:381–413 | Base stat deltas (STR/AGI/VIT/END/INT/SPI/WIS/PER/CHA) |
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

4. **Intent taxonomy — world-level** — Table of 10 world-level fields on `StateUpdate`:

   | Field | Intent type | Purpose |
   |---|---|---|
   | `world_updates` | `Dict[str, WorldUpdate]` | Hazard, trauma, influence, weather, modifiers per region |
   | `node_updates` | `Dict[int, ResourceNodeUpdate]` | Node charges delta, cooldown |
   | `building_updates` | `Dict[int, BuildingUpdate]` | Building HP, functional flag, inventory |
   | `camp_updates` | `Dict[str, CampUpdate]` | Camp maturity, active flag |
   | `chest_updates` / `chest_add_or_update` | `Dict[int, ChestUpdate]` / `List[ChestState]` | Chest cooldown and items |
   | `ground_items_add_or_update` / `ground_items_remove` | `List[GroundItemState]` / `List[int]` | Dropped item lifecycle |
   | `corpses_add_or_update` / `corpses_remove` | `List[CorpseState]` / `List[int]` | Corpse lifecycle |
   | `groups_add_or_update` / `groups_remove` | `List[GroupRecord]` / `List[int]` | Group lifecycle |
   | `home_storage_updates` | `Dict[int, InventoryUpdate]` | Home storage (milestone 5) |
   | `resource_updates` | `Dict[str, float]` | Global resource pool deltas |

5. **Special intents** — Dedicated subsection for the three special-case types:

   a. **`ResourceTransferIntent`** (`update_models/resources.py:12–38`, Logic ID: VERIFIED v2): The required pathway for all gold and item transfers that cross a conservation boundary. Fields: `source_id`, `source_kind` (NODE, GROUND_ITEM, CORPSE, CRAFTING, SHOP_BUY, SHOP_SELL), `items_add`, `items_remove`, `gold_delta`, `gold_cost`, `price_multiplier`, `xp_reward`, `transfer_kind`, `transaction_id`, `group_id`, and a set of contingent sub-updates applied only on transaction success. Always use `ResourceTransferIntent` when transferring resources — never emit `InventoryUpdate` directly from decision logic.

   b. **`InventoryUpdate` — result type restriction**: Docstring says "RESULT TYPE ONLY. Workers must NOT emit this directly for gold/items; use `ResourceTransferIntent`." It is the post-resolution output written by the `ResourceTransactionResolver`, not an input intent. Bypassing this rule breaks atomic conservation.

   c. **`QuestUpdate` — MULTI sentinel**: Supports a `"MULTI"` sentinel `quest_id` as a container for multi-quest batch updates. `merge()` flattens nesting to prevent `MULTI(MULTI(...))` chains. `is_noop()` treats `"MULTI"` with empty `multi_updates` as a no-op.

   d. **`CombatIntent`** (updates.py:83–92): A single-attack record embedded within `CombatUpdate.simultaneous_intents`. Not applied independently — it is a sub-record within the combat resolution result.

6. **Intent lifecycle** — Three phases:

   a. **Creation (read-only decision logic)**: Workers receive `AuthoritativeState.to_readonly()`. Any attempt to mutate via `ReadOnlyDict` raises `ReadOnlyError`. Decision logic (workers, pipeline phases, governance layer) produces `StateUpdate` fragments holding intent records.

   b. **Merge and compaction**: Sub-phase `StateUpdate` fragments are merged via `StateUpdate.merge_many()` (updates.py:884–1036, Logic ID: TOWN-204). `StateUpdate.compact()` (updates.py:1038–1046) then drops `EntityUpdate` entries where `is_noop()` is `True`. This reduces the set of entity patches reaching apply. The `DirtySet` accumulated from sub-phase merges is attached to the final merged `StateUpdate`.

   c. **Apply (authoritative path only)**: `ApplyPath.apply_generation()` (`src/engine/apply.py`) is the sole location where a `StateUpdate` is applied to produce a new `AuthoritativeState`. No other code path may apply intents to durable state. If `audit_dirty_set=True`, `validate_dirty_set()` is called post-apply.

7. **Merge semantics** — How `EntityUpdate.merge()` (updates.py:656–690) combines two bundles for the same entity:
   - **Delta fields** are summed (e.g., `hp_delta`, `xp_gain`, `sleep_debt_delta`).
   - **Set fields** last-write-wins (e.g., `alive_set`, `current_project_id_set`).
   - **List fields** are concatenated (e.g., `items_add`, `bond_updates`, `wounds_add`).
   - **Nested updates** recurse (e.g., `social_upd` calls `SocialUpdate.merge()`).
   All sub-intent types implement `merge()` and `is_noop()` — this is the compaction contract.

8. **Durable state rule** — What must not bypass intents: any change that survives beyond the current tick or function call must be expressed as a typed intent and applied through `ApplyPath.apply_generation()`. Do not store durable meaning in `reason` strings, free-form `metadata`, or temporary local variables. (Cross-reference `docs/core/state.md` — Immutability Law.)

9. **What may bypass intents** — Ephemeral, in-tick local state that does not persist to `AuthoritativeState`: intermediate calculation variables, working sets within a single worker, UI feedback signals that do not affect the next tick.

10. **Edge cases**:
    - **Conflicting intents for the same field**: `EntityUpdate.merge()` resolves conflicts by the merge rule for that field type (last-write-wins for set fields, sum for deltas). If two pipeline phases produce incompatible set-field values, the later merge wins. Callers must sequence phases accordingly.
    - **Invalid intent targets**: An `EntityUpdate` keyed to a non-existent entity ID is dropped silently or raises during apply (behavior is apply-path-specific — document that targets must be validated before emission if the entity may be dead).
    - **Dropped intents**: `StateUpdate.compact()` drops no-op entity entries. Any intent that produces `is_noop() == True` for all sub-fields is silently discarded. This is correct behavior — callers should not rely on a no-op intent reaching apply.
    - **`force_full_scan` and `dirty_set=None`**: A `StateUpdate` with `force_full_scan=True` bypasses all dirty-set routing downstream. Used for global re-evaluation events.

11. **Regression tests** — Cite with full paths:
    - `tests/perf/test_dirty_set_integrity.py` — verifies that `DirtySet.from_update()` correctly derives dirty flags from `StateUpdate` content.
    - `tests/integration/pipeline/test_authoritative_apply.py` — `apply_generation()` isolation, determinism, and resource delta correctness.
    - `tests/integration/pipeline/test_phase5_idempotency.py` — exactly-once transaction processing via `processed_transaction_ids`.
    - `tests/perf/test_apply_compaction_perf.py` — `StateUpdate.compact()` behavior under load.
    - `tests/architecture/test_phase18_import_boundaries.py` — core never imports domains; layer isolation.

12. **Extension rules** — When adding a new intent type: (a) define a new `frozen=True, slots=True` dataclass in `src/core/updates.py` or `src/core/update_models/`; (b) implement `is_noop()` and `merge()` with rules matching the field semantics (delta sum vs set last-write-wins vs list concat); (c) add a slot to `EntityUpdate` or a field to `StateUpdate` as appropriate; (d) update `EntityUpdate.merge()` to call the new sub-intent's `merge()`; (e) update `StateUpdate.compact()` if the new slot can produce no-ops; (f) document the new intent in this file; (g) add a test asserting `is_noop()` on a default-constructed instance and `merge()` commutativity (or document why it is not commutative).

**Scope guard:** Do not document the authoritative apply path internals in detail — that is `docs/engine/authoritative_apply_contract.md`. Cross-reference it. Do not cover `self_model.md` (lives in `src/cognition/`, covered by TCK-20260613-DOC-COGNITION-SUBSYSTEM). Do not modify `docs/core/state.md`.

**Acceptance criteria for Step 2:**
- File exists at `docs/core/update_intents.md`.
- Frontmatter keys present: `status`, `layer`, `authority`, `audience`, `last_verified`.
- All 22 entity-level and 10 world-level intent slots documented in tables.
- `InventoryUpdate` result-type restriction stated explicitly.
- `ResourceTransferIntent` mandatory pathway stated explicitly.
- Lifecycle section covers creation, merge/compaction, and apply-path-only application.
- Merge semantics (delta/set/list rules) stated.
- Regression tests section cites the five test file paths listed above.
- Extension rules section present.

---

### Step 3 — Update `docs/core/README.md`

**File modified:** `docs/core/README.md`

**Change:** Add two new entries to the `## Files` list. Existing four entries (`state.md`, `entities.md`, `attributes_and_classes.md`, `items_and_inventory.md`) must remain unchanged. Current content (lines 13–18) is:

```markdown
## Files
- [Authoritative State](../core/state.md): Lifecycle of the frozen state container.
- [Entities](../core/entities.md): Entity composition and component mapping.
- [Attributes & Classes](../core/attributes_and_classes.md): Derived stats and breakthrough milestones.
- [Items & Inventory](../core/items_and_inventory.md): Slot-based inventory and item templates.
```

Append (after the last existing entry):

```markdown
- [Dirty State & Dependency Model](../core/dirty_state_and_dependency.md): Dirty flag system, dependency expansion graph, and pipeline routing.
- [Update Intent Pipeline](../core/update_intents.md): Typed update intent taxonomy, lifecycle (create → merge → apply), and compaction semantics.
```

Do not change the frontmatter of `README.md` (currently `status: authoritative`, `authority: P0`).

**Scope guard:** No other change to `README.md`. Do not modify any other file.

**Acceptance criteria for Step 3:**
- Both new doc links appear in `## Files` list.
- Existing four entries unmodified.
- `README.md` frontmatter unchanged.

---

### Step 4 — Frontmatter validation

**No files written. Command only.**

Run the validation script from `test_plan.md`:

```bash
python3 -c "
import yaml, pathlib

for doc in ['docs/core/dirty_state_and_dependency.md', 'docs/core/update_intents.md']:
    text = pathlib.Path(doc).read_text()
    if not text.startswith('---'):
        print(f'FAIL {doc}: no frontmatter')
        continue
    end = text.index('---', 3)
    fm = yaml.safe_load(text[3:end])
    required = {'status', 'layer', 'authority', 'audience', 'last_verified'}
    missing = required - fm.keys()
    if missing:
        print(f'FAIL {doc}: missing keys {missing}')
    else:
        print(f'OK   {doc}')
"
```

Both files must print `OK`. If either prints `FAIL`, fix the frontmatter before proceeding.

**Acceptance criteria for Step 4:**
- Both docs print `OK` from the validation script.
- No `FAIL` output.

---

### Step 5 — Run knowledge-index-update and docs-registry

**No files written. Commands only.**

```bash
make knowledge-index-update
make docs-registry
```

Both must complete without errors. These regenerate the agent context search index and `docs/REGISTRY.yaml`.

**Acceptance criteria for Step 5:**
- `make knowledge-index-update` exits 0.
- `make docs-registry` exits 0.
- No error output from either command.

---

## Explicit Scope Guards (What NOT to Touch)

| Do NOT modify | Reason |
|---|---|
| `src/core/dirty.py` | Source code is authoritative; doc describes it, not the other way around |
| `src/core/updates.py` | Same — no code changes in this ticket |
| `docs/core/state.md` | Already covers Immutability Law; cross-reference, do not duplicate |
| `docs/engine/authoritative_apply_contract.md` | Apply path detail lives there; cross-reference only |
| `docs/engine/authoritative_mutation_pipeline_contract.md` | Out of scope for this ticket |
| Any `tests/` file | Documentation ticket — no test changes |
| `docs/core/README.md` frontmatter | Only the `## Files` list changes |
| The `e_upd.task` discrepancy in `dirty.py` | Document it as a known edge case; do not fix it |

---

## Acceptance Criteria → Step Mapping

| Acceptance Criterion (from ticket) | Verified by Step |
|---|---|
| `docs/core/dirty_state_and_dependency.md` created with full dependency graph | Step 1 |
| `docs/core/update_intents.md` created with intent taxonomy and lifecycle | Step 2 |
| Both docs have `## Regression tests` sections citing concrete test paths | Steps 1, 2 |
| Both docs have `## Extension rules` sections | Steps 1, 2 |
| `docs/core/README.md` updated to list the two new docs | Step 3 |
| Both docs have correct frontmatter (5 required keys) | Step 4 |
| `make knowledge-index-update` runs without error | Step 5 |
| `make docs-registry` runs without error | Step 5 |

---

## Unresolved Questions Blocking Implementation

**None.** All content needed to write both docs was resolved during investigation:

- The full 10-edge dependency graph is extracted from `dirty.py:408–457` (investigation.md lines 68–84).
- All 22 entity-level and 10 world-level intent types are enumerated from `updates.py` and `update_models/` (investigation.md lines 111–156).
- The `InventoryUpdate` restriction, `ResourceTransferIntent` mandatory pathway, and `QuestUpdate` MULTI semantics are documented (investigation.md lines 159–170).
- The intent lifecycle (creation → merge/compaction → apply) is traced end-to-end (investigation.md lines 175–204).
- The `e_upd.task` discrepancy is identified and scoped as a documentation risk note only (investigation.md lines 272–273; test_plan.md lines 67–69).
- All test file paths for regression citations are confirmed in investigation.md lines 239–261.
- The `docs/core/README.md` current content is confirmed (4 existing entries to be preserved; 2 new entries to be appended).
