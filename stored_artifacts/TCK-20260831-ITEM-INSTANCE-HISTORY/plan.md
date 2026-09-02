---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260831-ITEM-INSTANCE-HISTORY
artifact_type: plan
tags: [resource]
---

# Implementation Plan — TCK-20260831-ITEM-INSTANCE-HISTORY

## Summary

Add `ItemInstance` as a new, additive, typed durable record tracking per-physical-item ownership
history — modeled as a top-level `AuthoritativeState` collection (`item_instances: Dict[int,
ItemInstance]`), following the exact structural precedent of `ground_items`/`corpses`/`chests`/
`buildings` (int-keyed, counter-generated), not the `camps`/`regions` str-keyed precedent the
source schema doc suggested. Deterministic id generation reuses the **existing durable-counter
pattern already proven for `next_entity_id`/`next_node_id`** (`src/core/state.py:1249-1250`,
applied only in `src/engine/apply.py:293-294` inside `ApplyPath.apply_generation`) rather than
inventing a new offset scheme or copying the `corpse_id = 1000000 + e_id` 1:1-derivation trick,
which does not generalize to items not tied to exactly one entity. Every significant item keeps
its ordinary `ItemStack` entry in `InventoryComponent.items` unchanged — `ItemInstance` is a
strictly additive sidecar, never a replacement, so `src/core/conservation.py` and
`InventoryService.apply_update`'s merge-by-`item_id` logic (`src/core/inventory.py:134-215`) are
untouched and `test_inventory_stacking` passes unmodified. `significance_flag`'s trigger criteria
is resolved per this ticket's own AC #5: **no automatic classifier is built**. A `significant:
bool` parameter is added to a new scaffolding entry point (`ItemInstanceService
.maybe_create_instance`); no production call site is wired to pass `significant=True` in this
ticket — this mirrors the already-DONE `TCK-20260831-CLAN-STATE-SCHEMA` precedent of shipping
inert, testable scaffolding with the actual business-logic trigger decision deferred. Owner
transfer is a typed `ItemInstanceUpdate` routed through `StateUpdate.item_instance_updates`,
applied only inside `ApplyPath.apply_generation` — the sole writer of `AuthoritativeState`
(`apply_partial`/`apply_passive` are thin wrappers delegating to it, `src/engine/apply.py:429-438`),
so there is no concurrent-writer *race* for the apply step itself. Separately,
`StateUpdate.merge`/`merge_many` (`src/core/updates.py:971-1152`, read directly to confirm) is a
hand-enumerated field-by-field merge invoked repeatedly per tick — by `AuthoritativeApplyPipeline`
(`src/engine/pipeline.py:188,227,257,267,291`, each `update = run_phase(..., lambda u:
u.merge(...), ...)`) and by `world_dynamics.py:124,150,185,191,199` (`update =
update.merge(...)`) — so Step 4 below explicitly extends `merge_many` for the three new fields
(a gap the first review round of this plan missed), and Step 6 below resolves the
same-tick-id-collision hazard `maybe_create_instance` would otherwise have using the exact
stateful-allocator precedent already proven by `EntityGenerator._last_id`
(`src/systems/world_systems/generator.py:28-32`, `src/world/spawn.py:63,119`). TOWN-128 is
re-verified as unaffected (it
describes `item_id`/`ItemKind` type identity, not instance identity) and gets its long-standing
`test_path: null` P0 gap closed with a real test, without inventing a new adjacent parity entry
that isn't needed. `ENABLE_ITEM_INSTANCE_HISTORY` is registered default-OFF per this batch's
DEV-002 convention, gating the scaffolding function itself via the exact `flags.get(...) != "ON"`
pattern already used by `GuildNeedScorer` (`src/ai/goals/scorers.py:253-255`).

## Steps

### Step 1 — Add `ItemInstance` typed model and `AcquiredMethod` enum
**Files:** `src/core/models/inventory.py`
**Change:** In the same module that defines `ItemStack`/`InventoryComponent`
(`src/core/models/inventory.py:23-34,36-57`, confirmed the only real `ItemStack` definition in
the codebase per investigation.md), add:
```python
class AcquiredMethod(str, Enum):
    LOOT = "LOOT"
    CRAFTED = "CRAFTED"
    GIFT = "GIFT"
    INHERITED = "INHERITED"

@dataclass(frozen=True, slots=True)
class ItemInstance:
    """A durable per-physical-item ownership record. Additive sidecar to ItemStack — never
    replaces the ItemStack entry in InventoryComponent.items. See docs/mechanics/03_economic_laws.md
    (once updated) for the governing law."""
    instance_id: int
    item_id: str
    owner_history: List[str]
    acquired_tick: int
    acquired_method: AcquiredMethod
```
Follows the exact `@dataclass(frozen=True, slots=True)` convention already used for `ItemStack`/
`InventoryComponent`/`EquipSlot`/`ItemKind` in this same file. `owner_history: List[str]` matches
the ticket's own Scope-bullet-1 literal type (`owner_history: List[str]`) — entries are
`str(entity_id)`, not raw ints; this is a deliberate divergence from `EntityState.id: int`
elsewhere, dictated by the ticket's own explicit AC #1 field contract, not an oversight. No
defaults on `instance_id`/`item_id`/`owner_history`/`acquired_tick`/`acquired_method` — callers
must supply all fields explicitly (no silent `LOOT` default that could look like invented
criteria).
**Do NOT touch:** `ItemStack` (lines 23-34) or `InventoryComponent` (lines 36-57) themselves —
zero field changes to either class. Do not add anything to `ItemStack.properties`.
**Verify:** `test_item_instance_typed_state_location_not_untyped_dict` (new).

### Step 2 — Add `item_instances` collection and `next_item_instance_id` counter to `AuthoritativeState`
**Files:** `src/core/state.py`
**Change:** Add `ItemInstance, AcquiredMethod` to the existing re-export line
(`src/core/state.py:16`, which already re-exports `ItemKind, EquipSlot, ItemStack,
InventoryComponent` from `models/inventory.py`). Add a new top-level field to `AuthoritativeState`
next to the other `Dict[int, X]` world-object collections (`src/core/state.py:1140-1148`, which
holds `entities: Dict[int, EntityState]` through `regions: Dict[str, RegionState]`):
`item_instances: Dict[int, ItemInstance] = field(default_factory=dict)`. This is an **int-keyed**
collection — following the real precedent of `ground_items`/`corpses`/`chests`/`buildings`/
`groups` (all int-keyed, all counter/offset-generated, mid-sim-spawnable objects), **not** the
`camps`/`regions` str-keyed precedent, because those two are declarative worldgen-authored named
identifiers, not counter-generated mid-sim objects — `ItemInstance` is structurally the latter.
This deliberately overrides the source schema doc's `instance_id: str` suggestion
(`docs/brainstorm/rpg_expected_schemas.html:778`) in favor of actual code precedent, per this
ticket's own investigation finding.

Add the id counter next to the existing `next_node_id: int = 1000` / `next_entity_id: int = 1`
fields (`src/core/state.py:1249-1250`): `next_item_instance_id: int = 1`. Mirror the existing
self-healing logic in `__post_init__` (`src/core/state.py:1225-1240`, which repairs
`next_entity_id`/`next_node_id` against `max(existing_int_keys) + 1` on load) with an identical
block for `item_instances`/`next_item_instance_id`:
```python
if self.item_instances:
    int_i_keys = [k for k in self.item_instances.keys() if isinstance(k, int)]
    if int_i_keys and self.next_item_instance_id <= max(int_i_keys):
        object.__setattr__(self, "next_item_instance_id", max(int_i_keys) + 1)
```
This is the same durable-counter pattern already proven for `next_entity_id`/`next_node_id` —
reused wholesale rather than inventing a third id scheme, resolving investigation.md's flagged
"no production mid-sim id-minting precedent for a brand-new collection" gap by reusing the
counter pattern instead of the narrower `corpse_id = 1000000 + e_id` offset-derivation
(`src/engine/apply_plan.py:320`), which only works for objects 1:1-derived from an existing
entity id — `ItemInstance` is not.
**Do NOT touch:** `ground_items`/`corpses`/`chests`/`camps`/`regions` field definitions or their
own self-healing blocks. Do not change `next_node_id`/`next_entity_id` defaults or logic.
**Verify:** `test_item_instance_typed_state_location_not_untyped_dict` (new, extended to assert
the collection exists on `AuthoritativeState` and is int-keyed).

### Step 3 — Add `ItemInstanceUpdate` typed update record
**Files:** `src/core/update_models/inventory.py`
**Change:** In the same module that defines `InventoryUpdate` (`src/core/update_models/
inventory.py:8-27`, the dedicated item-shaped update module — distinct from where
`ChestUpdate`/`CampUpdate`/`BuildingUpdate` live directly in `src/core/updates.py:742,824,839`;
`ItemInstance` follows the more specific `InventoryUpdate` precedent since it is item-shaped, not
world-object-shaped), add:
```python
@dataclass(frozen=True, slots=True)
class ItemInstanceUpdate:
    """RESULT TYPE ONLY. Appends a new owner to an existing ItemInstance's owner_history.
    Law: only ApplyPath may consume this — no direct mutation of a live ItemInstance.

    CONTRACT (see plan.md Step 4, 'ItemInstanceUpdate.merge() — resolved'): StateUpdate.merge_many
    combines item_instance_updates by plain last-write-wins dict overwrite per instance_id, NOT
    by combining owner_history_append values. At most one ItemInstanceUpdate per instance_id per
    tick is supported today. Proposing two updates for the same instance_id within the same tick
    will silently keep only the last one merged — acceptable only because this ticket ships zero
    real production call sites that mint or transfer ItemInstances. A future ticket must add real
    per-instance merge semantics (e.g. concatenating owner_history_append in order) before any
    production caller can propose more than one transfer per instance per tick.
    """
    instance_id: int
    owner_history_append: Optional[str] = None

    def is_noop(self) -> bool:
        return self.owner_history_append is None
```
**Do NOT touch:** `InventoryUpdate` itself (lines 8-27) — zero field changes.
**Verify:** `test_transfer_significant_item_appends_owner_history_via_apply_pipeline` (new),
`test_item_instance_update_merge_many_single_transfer_per_tick_contract` (new, see Step 4).

### Step 4 — Add new `StateUpdate` fields AND wire them into `merge`/`merge_many`/`is_noop`
**Files:** `src/core/updates.py`
**Change:** Import `ItemInstance` alongside the existing `from src.core.state import ItemStack,
EquipSlot, AttributeComponent, LifeStage` (`src/core/updates.py:17`), and `ItemInstanceUpdate`
alongside the existing `from src.core.update_models.inventory import InventoryUpdate`
(`src/core/updates.py:21`). Add three new fields to `StateUpdate`
(`src/core/updates.py:892-944`), placed next to the structurally-nearest existing pair
(`ground_items_add_or_update`/`ground_items_remove`, lines 903-904, and `next_node_id_set`/
`next_entity_id_set`, lines 930-931):
```python
item_instances_add_or_update: List[ItemInstance] = field(default_factory=list)
item_instance_updates: Dict[int, ItemInstanceUpdate] = field(default_factory=dict)
next_item_instance_id_set: Optional[int] = None
```
No `item_instances_remove` field — explicitly deferred (see Scope Guards; removal/lifecycle of
orphaned `ItemInstance` records on sale/destruction is out of this ticket's AC scope).

**`is_noop()` (`src/core/updates.py:946-970`, confirmed by direct read — the boolean chain ends
`... and not self.faction_updates)` on line 970):** insert `and not
self.item_instances_add_or_update and not self.item_instance_updates and
self.next_item_instance_id_set is None` into that same chain, matching how every other field
already extends it (e.g. the existing `self.next_node_id_set is None and self.next_entity_id_set
is None` terms at line 964).

**`merge_many()` (`src/core/updates.py:977-1152`, confirmed by direct read — this is the actual
bug this Finding targets, since `merge()` at 971-975 just delegates to `merge_many([other])`):**
this method is a hand-enumerated field-by-field accumulator with four sections that must each get
a new line for the three new fields, mirroring the *exact* existing precedent used for the
structurally-nearest fields:
1. **Dict-copy section** (`:989-999`, `new_entity_updates = dict(self.entity_updates)` etc.): add
   `new_item_instance_updates = dict(self.item_instance_updates)`.
2. **Non-dict-collection-copy section** (`:1002-1023`, `new_ground_items_add_or_update =
   list(self.ground_items_add_or_update)` at :1007 is the direct precedent): add
   `new_item_instances_add_or_update = list(self.item_instances_add_or_update)`.
3. **Single-value seed section** (`:1026-1037`, `node_id = self.next_node_id_set` /
   `ent_id = self.next_entity_id_set` at :1028-1029 are the direct precedent): add
   `item_inst_id = self.next_item_instance_id_set`.
4. **Inside the `for other in valid_others:` loop** (`:1039-1105`):
   - Dict-merge sub-section (`:1040-1065`; `quest_status_updates.update(...)` at :1086 — actually
     inside the lists/sets sub-section but is a plain-overwrite dict merge, the exact pattern
     needed here — is the direct precedent, not the `entity_updates`/`building_updates`
     `.merge()`-per-key pattern at :1042/1048, which requires the value type to implement its own
     `.merge()`): add
     ```python
     for iid, upd in other.item_instance_updates.items():
         new_item_instance_updates[iid] = upd
     ```
     This is a **plain last-write-wins overwrite per `instance_id`**, not a `.merge()`-per-key
     call — see the "`ItemInstanceUpdate.merge()` — resolved" note below for why this is
     sufficient and does not need `ItemInstanceUpdate` to grow its own `.merge()` method.
   - Lists/sets extend sub-section (`:1067-1091`; `new_ground_items_add_or_update.extend(
     other.ground_items_add_or_update)` at :1073 is the direct precedent): add
     `new_item_instances_add_or_update.extend(other.item_instances_add_or_update)`.
   - Single-value last-non-None-wins sub-section (`:1093-1105`; `if other.next_node_id_set is not
     None: node_id = other.next_node_id_set` / `if other.next_entity_id_set is not None: ent_id =
     other.next_entity_id_set` at :1096-1097 are the direct precedent): add
     ```python
     if other.next_item_instance_id_set is not None: item_inst_id = other.next_item_instance_id_set
     ```
5. **Final `replace(self, ...)` call** (`:1107-1152` — this is the exact spot Finding 1 identifies
   as the drop point: any field not listed here silently reverts to `self`'s original value on
   merge): add
   ```python
   item_instances_add_or_update=new_item_instances_add_or_update,
   item_instance_updates=new_item_instance_updates,
   next_item_instance_id_set=item_inst_id,
   ```

**`ItemInstanceUpdate.merge()` — resolved, not left open:** the reviewer asked whether
`ItemInstanceUpdate` needs its own `.merge()` (to combine two same-tick transfers of the same
`instance_id`'s `owner_history`) or whether `merge_many`'s plain dict-key overwrite is enough. It
is **not enough in general** — a naive `new_item_instance_updates[iid] = upd` overwrite would
silently drop an earlier same-tick transfer's `owner_history_append` if two phases proposed a
transfer for the same `instance_id` in the same tick (second write wins, first is lost, with no
error). However, per this ticket's own scaffolding scope (Step 6: zero real production call sites
mint or transfer any `ItemInstance` in this ticket), this dead code path cannot actually be
exercised by production code today. Resolution: adopt plain dict-key overwrite (as implemented
above, matching the `quest_status_updates`/`information_providers_update` precedent) and pair it
with an explicit, tested contract — **at most one `ItemInstanceUpdate` per `instance_id` per tick
is supported until a future ticket adds real multi-transfer-per-tick merge semantics to
`ItemInstanceUpdate`**. This contract is documented in `ItemInstanceUpdate`'s docstring (Step 3)
and enforced by a new test in Step 8,
`test_item_instance_update_merge_many_single_transfer_per_tick_contract`, which merges two
`StateUpdate`s carrying `ItemInstanceUpdate`s for the *different* `instance_id`s (proving the
common case is not dropped) and separately documents+asserts the known last-write-wins behavior
for the *same*-`instance_id` case (proving the limitation is a known, tested boundary, not a
silent gap). Building a real per-instance merge (e.g. concatenating owner_history_append values in
order) is explicitly deferred — not required by any AC, and would be premature complexity for a
code path with no real caller yet.

**Other writers to `StateUpdate` and to `merge`/`merge_many` (enumeration required — shared
resource):** `StateUpdate` instances are constructed by every semantic worker in `src/engine/`,
`src/systems/`, `src/domains/`, etc., and merged by two confirmed call sites during a single tick:
`AuthoritativeApplyPipeline.refine()` in `src/engine/pipeline.py` (chains `update =
run_phase(..., lambda u: u.merge(...), ...)` across many phases, e.g. lines 188, 227, 257, 267,
291) and `src/engine/world_dynamics.py` (lines 124, 150, 185, 191, 199, `update =
update.merge(...)`). Adding three new fields with `field(default_factory=...)`/`None` defaults to
the dataclass itself is purely additive — no existing writer's constructor call needs updating
(Python dataclasses fill unspecified fields from defaults). But **the `merge_many` rewrite above is
exactly what makes those additive fields safe to merge** — before this fix, any phase's
`item_instances_add_or_update`/`item_instance_updates`/`next_item_instance_id_set` would have been
silently dropped the moment a second phase's update got merged into the accumulator in the same
tick (the bug Finding 1 identified), since `merge_many`'s `replace(self, ...)` call only carries
forward fields it explicitly lists. No other existing field's merge behavior changes — this step
only adds new lines for the three new fields, never edits an existing field's merge line.
**Do NOT touch:** Any existing `StateUpdate` field, its default, `is_noop()`'s existing boolean
terms, or any existing field's merge/copy/extend/overwrite line in `merge_many`.
**Verify:** `test_transfer_significant_item_appends_owner_history_via_apply_pipeline` (new),
`test_item_instance_update_merge_many_single_transfer_per_tick_contract` (new).

### Step 5 — Wire `ApplyPath.apply_generation` to commit `item_instances`/`next_item_instance_id`
**Files:** `src/engine/apply.py`
**Change:** `ApplyPath.apply_generation` (`src/engine/apply.py:189-419`) is the **sole writer** of
`AuthoritativeState` — `apply_partial` (`:430-432`) and `apply_passive` (`:434-438`) are thin
wrappers that both delegate straight into `apply_generation`, so there is exactly one commit path
and no concurrent-writer race to resolve for this new state. Add, near the existing corpse
reconstruction block (`:245-250`, which merges `plan.new_corpses` into `new_corpses`):
```python
new_item_instances = dict(prior_state.item_instances)
for inst in update.item_instances_add_or_update:
    new_item_instances[inst.instance_id] = inst
for instance_id, upd in update.item_instance_updates.items():
    if upd.is_noop():
        continue
    existing = new_item_instances.get(instance_id)
    if existing is not None and upd.owner_history_append is not None:
        new_item_instances[instance_id] = replace(
            existing, owner_history=list(existing.owner_history) + [upd.owner_history_append]
        )
```
Add, next to the existing counter-resolution lines (`:293-294`, `new_next_node = update
.next_node_id_set if update.next_node_id_set is not None else getattr(prior_state,
"next_node_id", 1000)`):
```python
new_next_item_instance = update.next_item_instance_id_set if update.next_item_instance_id_set is not None else getattr(prior_state, "next_item_instance_id", 1)
```
Pass both into the final `AuthoritativeState(...)` constructor call (`:363-419`, where every other
reconstructed collection — `entities=new_entities`, `chests=new_chests`, `next_node_id=
new_next_node`, etc. — is explicitly listed): add `item_instances=new_item_instances,
next_item_instance_id=new_next_item_instance,`.

Owner-history append is append-only by construction (`list(existing.owner_history) +
[upd.owner_history_append]` never drops prior entries), directly satisfying AC #3's "typed
StateUpdate through the authoritative apply pipeline only" — no other code path may ever call
`replace(some_item_instance, owner_history=...)`; this block in `ApplyPath.apply_generation` is
the only place that constructs a mutated `ItemInstance`.
**Do NOT touch:** The existing `new_corpses`/`new_ground_items`/`new_chests`/counter-resolution
logic for any other collection. Do not add `item_instances`/`next_item_instance_id` handling
anywhere outside `apply_generation` (e.g. no shortcut mutation inside `InventoryService` or any
semantic worker).
**Verify:** `test_transfer_significant_item_appends_owner_history_via_apply_pipeline` (new),
`test_item_instance_id_generation_is_deterministic` (new).

### Step 6 — Add `ItemInstanceService` as a per-tick stateful id allocator (caller-supplied flag only)
**Files:** `src/core/inventory.py`
**Change:** **Finding 2 fix**: the original draft of this step made `maybe_create_instance` a
stateless `@staticmethod` that read `state.next_item_instance_id` directly off the frozen
snapshot on every call — if two call sites minted an `ItemInstance` in the same tick, both would
read the identical id and collide. Resolved via **option (a)**: mirror the exact stateful
per-tick counter precedent already proven for entity ids. Confirmed by direct read of
`src/systems/world_systems/generator.py:28-32` (`self._last_id = 0` in `__init__`; the id-minting
method does `self._last_id += 1; return self._last_id`) and `src/world/spawn.py:63,119`
(`generator._last_id = state.next_entity_id - 1` seeded once per `process_spawns` call, then
`next_entity_id_set=generator._last_id + 1 if entities_add else None` proposed once at the end —
every mint within that one call increments the same in-memory counter, never re-reading
`state.next_entity_id`). Option (b) (test-guard a single-call-per-tick contract instead of
threading state) was considered and rejected: there is no way to make "at most one call per tick"
genuinely enforceable at runtime without threading some state across calls, which is exactly what
the allocator below already does at negligible extra cost — so (a) is strictly better here, not
just simpler.

Add a new class alongside the existing `InventoryService` (`src/core/inventory.py:134-215`,
`apply_update`):
```python
class ItemInstanceService:
    """Per-tick stateful id allocator for ItemInstance minting, mirroring EntityGenerator._last_id
    (src/systems/world_systems/generator.py:28-32). Callers MUST construct exactly one
    ItemInstanceService(state) per tick/phase invocation and reuse that same instance across every
    maybe_create_instance() call within that invocation — never re-instantiate mid-tick — so that
    two mints in the same tick never read the same next_item_instance_id and collide. At the end
    of the phase, propose next_item_instance_id_set=<instance>.last_id + 1 in the StateUpdate only
    if at least one instance was actually minted (mirrors src/world/spawn.py:119's
    `next_entity_id_set=generator._last_id + 1 if entities_add else None`)."""

    def __init__(self, state: "AuthoritativeState"):
        self._last_id = state.next_item_instance_id - 1

    @property
    def last_id(self) -> int:
        return self._last_id

    def maybe_create_instance(
        self,
        item_id: str,
        significant: bool,
        owner_entity_id: int,
        tick: int,
        acquired_method: AcquiredMethod,
        state: "AuthoritativeState",
    ) -> Optional[ItemInstance]:
        """Pure construction only — does not mutate state. Caller must route the result through
        StateUpdate.item_instances_add_or_update + next_item_instance_id_set (using this
        instance's .last_id, see class docstring), applied only by ApplyPath.apply_generation.
        Returns None when `significant` is False (ordinary ItemStack path, unaffected) or when
        ENABLE_ITEM_INSTANCE_HISTORY is not ON. Does NOT increment/consume an id in either
        None-returning case."""
        if not significant:
            return None
        flags = getattr(state, "feature_flags", None) or {}
        if flags.get("ENABLE_ITEM_INSTANCE_HISTORY", "OFF") != "ON":
            return None
        self._last_id += 1
        return ItemInstance(
            instance_id=self._last_id,
            item_id=item_id,
            owner_history=[str(owner_entity_id)],
            acquired_tick=tick,
            acquired_method=acquired_method,
        )
```
The flag-check mirrors the exact existing pattern in `GuildNeedScorer.score`
(`src/ai/goals/scorers.py:253-255`: `flags = getattr(state, "feature_flags", None) or {}`; `if
flags.get("ENABLE_GUILD_QUEST_GENERATION", "OFF") != "ON": return ...`). `significant: bool` is a
**caller-supplied parameter only** — this function contains no rarity/tier/item_id/value
heuristic of any kind. **This is the ticket's AC #5 resolution**: zero production call sites pass
`significant=True` in this ticket (matches the already-DONE `TCK-20260831-CLAN-STATE-SCHEMA`
precedent of shipping inert, testable scaffolding). Actually minting the returned `ItemInstance`
into durable state (via `StateUpdate.item_instances_add_or_update`/`next_item_instance_id_set`) is
the caller's responsibility, following the Proposal → Refine → Apply law
(`docs/engine/authoritative_mutation_pipeline_contract.md` §1) — this function never touches
`AuthoritativeState` directly. Because zero production call sites exist yet, no code in this
ticket actually instantiates `ItemInstanceService` outside of tests — the tests below construct it
directly, exactly as `test_item_inventory_contract.py` constructs `ApplyPath.apply_generation()`
inputs directly per investigation.md's noted precedent.
**Do NOT touch:** `InventoryService.apply_update` (`:134-215`) — zero changes to the merge logic
non-significant items rely on. Do not add any auto-classification logic (rarity thresholds,
item_id allowlists, value thresholds) anywhere in this function or elsewhere. Do not make
`maybe_create_instance` a `@staticmethod` again — that would silently reintroduce the Finding 2
collision.
**Verify:** `test_only_significant_items_receive_item_instance` (new),
`test_significance_flag_requires_explicit_caller_input` (new),
`test_item_instance_id_generation_is_deterministic` (new, extended per Step 8 to also prove two
sequential `maybe_create_instance()` calls on the same `ItemInstanceService` instance within one
tick produce distinct, non-colliding ids).

### Step 7 — Register `ENABLE_ITEM_INSTANCE_HISTORY` feature flag
**Files:** `src/domains/optimization/feature_flags.py`
**Change:** Add to `FeatureFlagManager.__init__`'s `self._flags` dict
(`src/domains/optimization/feature_flags.py:13-128`), following the exact comment convention used
for this batch's two sibling tickets (`ENABLE_CREATURE_TERRITORY_LIFECYCLE`, lines 116-120;
`ENABLE_HABIT_BIAS_ACTION_STYLE`, lines 121-127):
```python
# New gameplay behavior (TCK-20260831-ITEM-INSTANCE-HISTORY): registers the
# ItemInstance ownership-history scaffolding (ItemInstanceService.maybe_create_instance,
# src/core/inventory.py). DEV-002 default-OFF policy applies -- brand-new mechanic, no
# production call site passes significant=True yet (significance_flag trigger criteria is an
# explicit open design decision, not invented by this ticket -- see ticket AC #5), no corpus
# profile turns this on and no SHADOW-validation history exists.
"ENABLE_ITEM_INSTANCE_HISTORY": FeatureMode.OFF,
```
**Do NOT touch:** Any other flag entry or its default.
**Verify:** `test_only_significant_items_receive_item_instance` (asserts default-OFF means no
instance is created even when `significant=True` is passed, until a future ticket flips the
flag).

### Step 8 — New tests
**Files:** `tests/unit/resource/test_item_instance_history.py` (new file, grouped with the
existing inventory-contract tests per test_plan.md's stated location preference)
**Change:** Implement all new tests named in `test_plan.md`'s "New Tests Required" section:
`test_item_instance_typed_state_location_not_untyped_dict`,
`test_only_significant_items_receive_item_instance`,
`test_significant_item_merge_does_not_collapse_instances`,
`test_transfer_significant_item_appends_owner_history_via_apply_pipeline`,
`test_item_instance_id_generation_is_deterministic`,
`test_significance_flag_requires_explicit_caller_input`. Follow the existing
`ApplyPath.apply_generation()` test-construction pattern already used by
`tests/unit/resource/test_item_inventory_contract.py` (per investigation.md) for any test that
exercises the apply pipeline. Do not modify `test_inventory_stacking` in
`tests/unit/resource/test_item_inventory_contract.py` — it must be run as-is to prove AC #2's
second half.

Additionally, per this plan's Finding 1/Finding 2 fixes (Steps 4 and 6), implement two more tests
not present in the original test_plan.md draft — both required to make those fixes verifiable
rather than merely asserted:
- `test_item_instance_update_merge_many_single_transfer_per_tick_contract` (Step 4): construct two
  `StateUpdate`s, each carrying an `item_instance_updates` entry for a *different* `instance_id`,
  call `.merge_many()`, and assert both survive in the result (proves the Finding 1 fix — before
  the fix, both would have been silently dropped since `merge_many`'s old `replace(...)` call
  never listed the field at all). Separately, in the same test or an adjacent one, merge two
  `StateUpdate`s proposing an `ItemInstanceUpdate` for the *same* `instance_id` and assert the
  documented last-write-wins outcome (only the second survives) — this documents/locks in the
  known single-transfer-per-instance-per-tick contract from `ItemInstanceUpdate`'s docstring
  (Step 3) rather than leaving it as an untested assumption.
- Extend `test_item_instance_id_generation_is_deterministic` (Step 6): in addition to its
  originally-planned replay-determinism assertion, also construct one `ItemInstanceService(state)`
  and call `maybe_create_instance(...)` twice within the same test (simulating two mints in one
  tick), asserting the two returned `ItemInstance`s have distinct, sequentially-incrementing
  `instance_id`s — proving the Finding 2 fix actually prevents the same-tick collision it was
  written to prevent.

**Verify:** All eight new tests pass (the original six plus the two above); `pytest
tests/unit/resource/ -m "not slow"` (full scoped regression command from test_plan.md) passes
including all pre-existing tests unmodified.
**Do NOT touch:** Any existing test file in the Regression Surface listed in `test_plan.md`.

### Step 9 — TOWN-128 parity ledger: re-verify + close the `test_path: null` gap
**Files:** `docs/parity_ledger/town_resource.yaml`
**Change:** Re-verify TOWN-128 (`docs/parity_ledger/town_resource.yaml:1325-1335`, "Item
identity/kind is preserved through pickup, stacking, selling, crafting, and dropping") as
**unaffected** by this ticket — confirmed in investigation.md by reading the entry in its
TOWN-126/127/128 triad context: "identity/kind" means `item_id`/`ItemKind` type identity, the same
axis as quantity (TOWN-126) and weight (TOWN-127), not per-instance uniqueness. **No new adjacent
entry is added** — the simpler of the ticket's own AC #4 either/or options, chosen because no
concrete confusion risk was found between the two identity concepts (item_id-type vs.
instance-uniqueness) that a new entry would meaningfully prevent; `ItemInstance`'s own typed
model (Step 1) is itself the durable record distinguishing the two, no separate doc entry is
needed to keep them apart. Update TOWN-128's `v2_evidence` to note the re-verification date and
that `ItemInstance` was confirmed not to alter `item_id`/`kind` on the underlying `ItemStack`.
Set `test_path: tests/unit/resource/test_item_instance_history.py::
test_town_128_item_kind_identity_unaffected_by_item_instance` — this closes the pre-existing P0
`test_path: null` gap flagged in investigation.md, satisfying the Authoritative Mechanics Rule's
"P0 entries require a passing test_path" for TOWN-128 specifically (not its siblings — see Scope
Guards).
**Do NOT touch:** TOWN-126 or TOWN-127's own `test_path: null` gap — pre-existing, out of this
ticket's scope, not caused or worsened by this ticket.
**Verify:** `test_town_128_item_kind_identity_unaffected_by_item_instance` (new) passes; use
`tools/parity_ledger_writer.py` (the schema-validating writer) for this edit, never a raw
Edit/ad-hoc script against the YAML file, per this repo's own parity-ledger-corruption-avoidance
convention.

### Step 10 — Documentation updates (Document-Update phase)
**Files:** `docs/core/items_and_inventory.md`, `docs/mechanics/03_economic_laws.md`
**Change:** Add a new subsection to `docs/core/items_and_inventory.md` describing `ItemInstance`
(fields, typed state location `AuthoritativeState.item_instances`, the
`significant`-caller-supplied-flag design, deferred trigger criteria). While in this doc, flag —
but do not silently rewrite as part of this ticket's own scope — the **pre-existing** divergence
investigation.md found: the doc's current `rarity: Rarity`/`ItemTemplate`/"Legendary Items"
content (`docs/core/items_and_inventory.md:27-150`) describes a system that does not exist in the
real `src/core/items.py` `ItemDefinition` (no `rarity` field on any of the ~15 registered items).
This divergence predates this ticket and is unrelated to it, but is directly adjacent to the new
`ItemInstance` section being added here, so Document-Update should correct it in the same pass
rather than let readers conflate the doc's fictional `rarity` field with `ItemInstance`'s real
`significance_flag` gap. Add a new subsection to `docs/mechanics/03_economic_laws.md` recording
the owner-history-append law (append-only, via `ItemInstanceUpdate` through `ApplyPath
.apply_generation` only) — this chapter currently has zero mentions of item identity/instance
concepts (confirmed by investigation.md's grep), so this is the first Mechanics Bible treatment
of the concept, not an edit to existing text.
**Do NOT touch:** `docs/brainstorm/rpg_expected_schemas.html` — confirmed by investigation.md to
already accurately describe the intended shape; this ticket implements what it states, does not
change it.
**Verify:** No test verifies documentation content directly; Document-Update phase's own
completion check plus `make knowledge-index-update` (required per project CLAUDE.md whenever
`docs/` files change).

## Scope Guards

- Do not add any per-instance field to `ItemStack.properties` or any other untyped dict anywhere
  in `EntityState`/`AuthoritativeState` — the exact anti-pattern this ticket's own AC #1 and this
  repo's Durable State Rule forbid.
- Do not modify `InventoryService.apply_update`'s existing merge-by-`item_id` behavior
  (`src/core/inventory.py:134-215`) — `test_inventory_stacking` must pass with zero
  modification.
- Do not touch `src/domains/progression/possession.py`'s `PossessionUnderstandingService` —
  explicitly Out of Scope in the ticket, confirmed unrelated by investigation.md.
- Do not invent `significance_flag` trigger criteria anywhere (no rarity threshold, no
  hardcoded `item_id` list like the existing `ancient_fragment` check at
  `src/domains/progression/possession.py:90-92`, no value/weight heuristic). `significant` stays
  a caller-supplied boolean only.
- Do not wire any production call site (loot generation, crafting, quest rewards, gifting) to
  pass `significant=True` — deferred to a future ticket per this ticket's own scope.
- Do not add `item_instances_remove` to `StateUpdate` or any removal/lifecycle handling for
  orphaned `ItemInstance` records (e.g. on sale/destruction/drop of the backing `ItemStack`) —
  not required by any AC, explicitly deferred.
- Do not implement the `item_ownership_transferred` WorldEvent
  (`docs/brainstorm/rpg_expected_schemas.html:978`) — not required by any AC; the owner_history
  append via `ItemInstanceUpdate` alone satisfies AC #3.
- Do not touch TOWN-126 or TOWN-127's own pre-existing `test_path: null` gap.
- Do not fix `docs/core/items_and_inventory.md`'s pre-existing `rarity`/`ItemTemplate`
  divergence as new code (e.g. do not add a `rarity` field to `ItemDefinition`) — it is a stale
  doc, not a code gap; only the doc gets corrected, in Step 10.
- Do not change `AuthoritativeState.camps`/`regions` (str-keyed) or reuse their key convention
  for `item_instances` — `item_instances` is int-keyed per Step 2's precedent decision.

## Dependency Map

- Step 1 (model) has no dependencies — first step.
- Step 2 (state collection + counter) depends on Step 1 (`ItemInstance`/`AcquiredMethod` must
  exist to import).
- Step 3 (`ItemInstanceUpdate`) depends on Step 1 (imports nothing from Step 2, independent of
  it — can run in parallel with Step 2).
- Step 4 (`StateUpdate` fields + `merge`/`merge_many`/`is_noop` wiring) depends on Steps 1–3
  (imports `ItemInstance` and `ItemInstanceUpdate`; the `merge_many` rewrite only touches lines
  already present in `src/core/updates.py`, no new dependency beyond the import).
- Step 5 (`ApplyPath.apply_generation` wiring) depends on Steps 2 and 4 (`prior_state
  .item_instances`/`next_item_instance_id` and `update.item_instances_add_or_update`/
  `item_instance_updates`/`next_item_instance_id_set` must all exist and merge correctly).
- Step 6 (`ItemInstanceService` stateful allocator) depends on Steps 1 and 2 (`ItemInstance`,
  `state.next_item_instance_id`, `state.feature_flags`) — no dependency on Step 4/5 since it only
  constructs `ItemInstance` objects, it never touches `StateUpdate` or `AuthoritativeState`
  directly.
- Step 7 (feature flag registration) is independent — can run any time before Step 6's tests.
- Step 8 (tests) depends on Steps 1–7 (exercises every new symbol, including the Step 4
  `merge_many` fix and the Step 6 stateful-allocator fix).
- Step 9 (parity ledger) depends on Step 8 (needs the real test path to exist before it can be
  cited as `test_path`).
- Step 10 (docs) depends on Steps 1–9 (documents the settled design) — can run last, or in
  parallel with Step 9 once Steps 1–8 land, since it does not depend on the parity ledger
  decision.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — `ItemInstance` typed record (instance_id, item_id, owner_history, acquired_tick, acquired_method), defined typed state location, NOT in `ItemStack.properties`/untyped dict | Steps 1, 2 | `test_item_instance_typed_state_location_not_untyped_dict` |
| AC #2 — only explicitly-flagged-significant items get an `ItemInstance`; all other items keep the unmodified `ItemStack` merge path; `test_inventory_stacking()` passes unmodified | Steps 1, 2, 3, 4, 5, 6, 7 | `test_only_significant_items_receive_item_instance`, `test_significant_item_merge_does_not_collapse_instances`, existing `test_inventory_stacking` (unmodified) |
| AC #3 — transferring a significant item appends the new owner to `owner_history` via a typed `StateUpdate` through the authoritative apply pipeline only | Steps 3, 4, 5 | `test_transfer_significant_item_appends_owner_history_via_apply_pipeline` |
| AC #4 — TOWN-128 re-verified as unaffected, or a new adjacent entry added | Step 9 | `test_town_128_item_kind_identity_unaffected_by_item_instance` |
| AC #5 — `significance_flag` trigger criteria flagged as an explicit open design decision requiring sign-off, not invented ad hoc | Step 6 (caller-supplied `significant: bool`, no auto-classifier), this plan's Summary/Open Questions | `test_significance_flag_requires_explicit_caller_input` |

## Anti-Drift Notes

- **Dual-representation risk (investigation.md, "Risks and Open Questions")**: a significant
  item's `ItemStack` entry in `InventoryComponent.items` must never be removed or replaced by
  `ItemInstance` — `src/core/conservation.py` (lines 142, 167, 204, 307, 318) and
  `InventoryService.can_add_items`/`apply_update` are entirely `item_id`/`quantity`-driven and
  blind to `ItemInstance`. Step 6's scaffolding only ever *adds* an `ItemInstance` sidecar
  alongside the caller's normal `ItemStack` addition — it never substitutes for it.
- **Merge-collision risk**: equipment items have `stack_size=1` today
  (`src/core/items.py:41-48` per investigation.md), so two significant items of the same
  `item_id` can coexist in one inventory without anything blocking it. `InventoryService
  .apply_update`'s merge logic operates purely on `ItemStack` (`item_id`/`quantity`) and has no
  awareness of `ItemInstance` at all — this is by design (Step 6 never touches `apply_update`),
  but means two same-`item_id` significant items' `ItemStack` quantities could still merge into
  one `ItemStack` entry while their two separate `ItemInstance` records remain distinct and
  correctly un-collapsed in `AuthoritativeState.item_instances`. `test_significant_item_merge_does
  _not_collapse_instances` must assert this exact separation, not merely that instances exist.
- **Determinism**: `ItemInstanceService.maybe_create_instance` must never call
  `random.Random()`/`uuid.uuid4()` — `instance_id` comes exclusively from the `ItemInstanceService`
  instance's own `_last_id` counter (seeded once from `state.next_item_instance_id` at
  construction, per Step 6's fix), and the caller is responsible for proposing
  `next_item_instance_id_set=<service>.last_id + 1` in the same `StateUpdate` only when at least
  one instance was minted (mirroring how `src/world/spawn.py:119` proposes `next_entity_id_set`
  from `generator._last_id`). Only `ApplyPath.apply_generation` commits the counter increment into
  durable state.
- **Same-tick id collision (Finding 2, fixed in Step 6)**: a `@staticmethod` reading
  `state.next_item_instance_id` directly, as the first draft of this plan specified, would have
  let two same-tick mints read the identical id and collide. `ItemInstanceService` is now a
  stateful per-tick allocator, constructed once per tick/phase and reused across every mint in
  that phase — mirroring `EntityGenerator._last_id` exactly (`src/systems/world_systems/
  generator.py:28-32`, `src/world/spawn.py:63,119`, both confirmed by direct read). Re-instantiating
  `ItemInstanceService` more than once within the same tick's minting sequence would reintroduce
  the same collision this fix is meant to prevent — this is why the class docstring states the
  constraint explicitly, not just this plan.
- **Cross-phase merge drop risk (Finding 1, fixed in Step 4)**: `StateUpdate.merge`/`merge_many`
  (`src/core/updates.py:971-1152`) is a hand-enumerated field-by-field merge with no reflection —
  a field left out of the final `replace(self, ...)` call is silently dropped whenever two phases'
  updates are merged in the same tick, which happens routinely (`AuthoritativeApplyPipeline.refine()`
  in `src/engine/pipeline.py` and `world_dynamics.py` both call `.merge()`/`.merge_many()` multiple
  times per tick, confirmed by direct read of both files). Step 4 explicitly extends all four
  `merge_many` sections (dict-copy, list-copy, single-value-seed, and the final `replace(...)`
  call) for the three new fields — do not add a fourth `StateUpdate` field to this ticket (or any
  future one) without checking whether it also needs the same four-section treatment.
- **`item_instance_updates` same-instance-same-tick limitation is a documented, tested boundary,
  not a silent gap**: `merge_many`'s plain dict-key overwrite means a second same-tick
  `ItemInstanceUpdate` for the same `instance_id` overwrites (does not combine with) the first.
  This is acceptable only because zero production call sites propose any `ItemInstanceUpdate` in
  this ticket (Step 6). `ItemInstanceUpdate`'s docstring (Step 3) and
  `test_item_instance_update_merge_many_single_transfer_per_tick_contract` (Step 8) make this an
  explicit, enforced contract rather than an unstated assumption — a future ticket wiring a real
  transfer call site must either respect "one transfer per instance per tick" or add real
  per-instance merge semantics to `ItemInstanceUpdate` first.
- **Single-writer guarantee**: `ApplyPath.apply_generation` (`src/engine/apply.py:189-419`) is
  confirmed the sole constructor of `AuthoritativeState` — `apply_partial`/`apply_passive` both
  delegate into it (`:429-438`). This means Step 5's new reconstruction block has no concurrent
  writer to race against for the *apply* step; the cross-phase *merge* step (addressed separately
  above) is a distinct hazard that Step 4 now also covers. The existing "Proposal → Refine →
  Apply" law already prevents any worker from mutating `item_instances` directly.
- **`significant` is not a business-logic feature**: Step 6 and Step 7 ship inert scaffolding.
  Zero production call sites pass `significant=True`, and `ENABLE_ITEM_INSTANCE_HISTORY` defaults
  OFF. This is intentional and matches the already-DONE `TCK-20260831-CLAN-STATE-SCHEMA`
  precedent — do not treat this as an incomplete feature during Architecture-Verify; the actual
  trigger-criteria decision is explicitly out of scope pending human sign-off.
- **`docs/core/items_and_inventory.md`'s `rarity` content is not a real anchor** — confirmed by
  investigation.md that no `rarity`/`ItemTemplate` exists in `src/core/items.py`. Do not let this
  stale doc content leak into Step 6's design as if it were real.

## Open Questions

None remaining that block implementation. Specifically:

- **AC #5 (significance_flag trigger criteria) is resolved, not deferred as unresolved**: the
  decision is "caller-supplied `significant: bool` parameter only, no automatic classifier of any
  kind, zero production call sites wired in this ticket." This is a final Plan-phase decision, not
  a placeholder — Architecture-Verify should not block on it as an incomplete feature.
- **TOWN-128 (AC #4) is resolved**: re-verify as unaffected, no new adjacent parity entry, close
  the pre-existing `test_path: null` gap with a real test. See Step 9.
- **`item_ownership_transferred` WorldEvent** (`docs/brainstorm/rpg_expected_schemas.html:978`,
  flagged by investigation.md as "scored by zero pillars today"): explicitly deferred, not
  required by any AC. Not built in this ticket. If a future ticket wants it, it would emit
  alongside Step 5's `ItemInstanceUpdate` application inside `ApplyPath.apply_generation`.
- **TOWN-126/127's own `test_path: null` gap**: pre-existing, unrelated, explicitly out of this
  ticket's scope (see Scope Guards).
- **Finding 1 (StateUpdate.merge()/merge_many() drops the three new fields) is resolved**: Step 4
  now explicitly extends all four sections of `merge_many` (dict-copy, list-copy, single-value-seed,
  final `replace(...)`) for `item_instances_add_or_update`/`item_instance_updates`/
  `next_item_instance_id_set`. See Step 4 and the "Cross-phase merge drop risk" Anti-Drift Note.
- **Finding 2 (same-tick id collision in `maybe_create_instance`) is resolved**: Step 6 now uses a
  stateful `ItemInstanceService` per-tick allocator (option (a)), mirroring `EntityGenerator
  ._last_id`, instead of a stateless `@staticmethod` reading `state.next_item_instance_id`
  directly. See Step 6 and the "Same-tick id collision" Anti-Drift Note.
- **`ItemInstanceUpdate.merge()` sub-question is resolved**: no dedicated `.merge()` method is
  added to `ItemInstanceUpdate`. `merge_many` uses plain dict-key overwrite, paired with a
  documented+tested "at most one transfer per instance per tick" contract (Step 3's docstring,
  Step 4's "`ItemInstanceUpdate.merge()` — resolved" note, and
  `test_item_instance_update_merge_many_single_transfer_per_tick_contract` in Step 8) — acceptable
  because zero production call sites propose any `ItemInstanceUpdate` in this ticket.
