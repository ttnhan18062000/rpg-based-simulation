---
status: active
layer: core
authority: P1
audience: agent
last_verified: 2026-06-13
---

# Dirty State & Dependency Model

## Purpose

The dirty-flag system is the primary optimization layer in the tick pipeline. An entity or world object is "dirty" when its domain state changed during the current tick and downstream systems must re-evaluate it. Without dirty tracking, every pipeline phase would scan the entire entity population on every tick — an O(N) cost regardless of how many entities were actually affected.

`DirtySet` records which entities changed in which domain. `DirtyDependencyGraph.expand()` derives additional implied dirtiness from the raw marks. `CandidateSelector.entities()` is the authoritative read-side: pipeline phases call it to receive only the relevant entity IDs and skip clean entities.

Logic IDs: PERF-005, PERF-006, PERF-007, PERF-008, PERF-015. Source: `src/core/dirty.py`.

## RPG meaning

"Dirty" means that an entity changed in a way that matters to one or more simulation systems. If an entity took damage (`combat` dirty), health checks, group morale evaluations, and goal validity checks must all run for it this tick. If an entity only harvested a resource node (`inventory` dirty), only inventory-driven logic needs to re-evaluate — combat and social systems can skip it.

The model is conservative by design: false positives (marking something dirty that did not need re-evaluation) are safe; false negatives (failing to mark something dirty) produce stale state that silently corrupts downstream decisions.

## Inputs — what sets dirty flags

Dirty flags are derived from `StateUpdate` content at two points in the pipeline:

1. **`DirtySet.from_update(state, update, base_dirty=None)`** — Stateless derivation from a `StateUpdate`. Produces a complete `DirtySet` in one pass. Used when a fresh dirty set is needed from a single update object.

2. **`DirtySetBuilder.mark_from_update(state, update)`** — Incremental accumulation into a mutable builder. Used by the pipeline when accumulating dirtiness across multiple sub-phase `StateUpdate` objects. Call `DirtySetBuilder.build()` to freeze the result.

3. **`DirtySetBuilder.mark_entity(e_id, tags)`** — Direct tag-based marking. Accepted tags: `movement`, `combat`, `inventory`, `strategic`, `social`, `lifecycle`, `biological`, `attributes`. Note: `town` is not a valid tag; town dirtiness is position-derived only (see Edge cases).

Both `from_update()` and `DirtySetBuilder` inspect the same `EntityUpdate` fields and produce the same raw marks before expansion. After raw classification, `DirtyDependencyGraph.expand()` is always called to derive implied flags.

## Core rules — the expansion model

Every `DirtySet` produced by any of the above paths is passed through `DirtyDependencyGraph.expand()` (dirty.py:407–457, Logic ID: PERF-008) before use. Expansion adds derived dirtiness based on causal relationships between domains.

Expansion is idempotent: calling `expand()` on an already-expanded set returns an equivalent set.

## Dirty flag taxonomy

### Entity domain sets (9 fields on `DirtySet`)

| Field | Domain | What it covers |
|---|---|---|
| `movement_entities` | `movement` | Position change (`new_position`) or navigation update |
| `combat_entities` | `combat` | HP delta, damage taken, alive status, wounds |
| `inventory_entities` | `inventory` | Item add/remove, gold delta, resource transfer |
| `strategic_entities` | `strategic` | Goal blockers, leads, directives, projects, beliefs, task updates, interaction, quest |
| `social_entities` | `social` | Trust, familiarity, fear, grudge, bond updates, contracts |
| `lifecycle_entities` | `lifecycle` | Age delta, death, permadeath, heir assignment |
| `biological_entities` | `biological` | Sleep debt, hunger, rest pressure |
| `attribute_entities` | `attributes` | Base stat delta (STR/AGI/VIT/END/INT/SPI/WIS/PER/CHA) or reward XP |
| `town_entities` | `town` | Entity whose current position tile is inside `state.town_tiles` |

`all_dirty_entities` (property, dirty.py:231) returns the union of the 8 non-town entity sets. It excludes `town_entities` because town is a position-derived subset, not an independent domain.

### World object sets (9 fields on `DirtySet`)

| Field | Covers |
|---|---|
| `group_ids` | Groups added, removed, or whose members changed |
| `region_ids` | Regions with world updates (hazard, trauma, weather) |
| `resource_node_ids` | Resource nodes with charge or cooldown changes |
| `building_ids` | Buildings with HP, functional flag, or inventory changes |
| `chest_ids` | Chests with cooldown or item changes |
| `ground_item_ids` | Ground items added or removed |
| `corpse_ids` | Corpses added or removed |
| `camp_ids` | Camps with maturity or active flag changes |

World object dirty flags have no expansion rules — they pass through `expand()` unchanged. There is no world-to-entity dependency propagation.

## Dependency graph

The 10 expansion edges from `DirtyDependencyGraph.expand()` (dirty.py:419–437):

| Source flag | Derives flag | Reason |
|---|---|---|
| `movement` | `strategic` | Positional changes affect pathfinding proximity scoring |
| `movement` | `social` | Movement produces encounters requiring social evaluation |
| `inventory` | `strategic` | Item changes trigger capacity, shop, and goal re-evaluation |
| `combat` | `lifecycle` | HP loss triggers near-death and death checks |
| `combat` | `social` | Combat affects group morale, fear, and fleeing decisions |
| `combat` | `strategic` | Combat outcome changes goal validity |
| `biological` | `strategic` | Hunger/sleep pressure shifts goal priorities |
| `biological` | `lifecycle` | Biological extremes can cause death |
| `attributes` | `strategic` | Attribute changes can unlock or block goals |
| `attributes` | `lifecycle` | Attribute changes affect max-HP derived from vitality |

**Terminal flags** (do not expand further): `social`, `lifecycle`, `town`. The graph is acyclic and single-depth — no derived flag implies any further flag.

The expansion implementation (dirty.py:419–437) is written as four compound conditions that handle the four source domains simultaneously:

```
movement  → strategic, social
inventory → strategic
combat    → lifecycle, social, strategic
biological or attributes → strategic, lifecycle
```

## Domain routing

`CandidateSelector.entities(state, update, domains, *, include_inactive=False)` (dirty.py:460–506, Logic ID: PERF-007) is the authoritative mechanism for determining which entities a pipeline phase should process. It returns a `tuple[int, ...]` of sorted active entity IDs.

Pipeline phases pass a set of domain names; `CandidateSelector` unions the corresponding `DirtySet` fields:

| Domain name passed | DirtySet fields read |
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
| *(any unknown domain)* | full `state.entities` fallback |

`get_relevant_entity_ids(state, update, domain)` (dirty.py:14–39) is a legacy helper that provides the same routing logic for older pipeline phases that pass a single domain string. Prefer `CandidateSelector.entities()` for new code.

`get_relevant_group_ids(state, update)` (dirty.py:41–48) provides equivalent filtering for groups.

## Lifecycle — when flags are set and cleared

### Flag production within a tick

1. Workers and pipeline phases produce `StateUpdate` fragments as they resolve their domains.
2. Each fragment's `StateUpdate` is passed to `DirtySetBuilder.mark_from_update()` (incremental path) or `DirtySet.from_update()` (stateless path) to derive raw dirty flags.
3. `DirtyDependencyGraph.expand()` adds derived flags immediately.
4. The resulting `DirtySet` is attached to the `StateUpdate` as `StateUpdate.dirty_set`.
5. When sub-phase `StateUpdate` objects are merged via `StateUpdate.merge_many()`, the dirty sets are merged via `DirtySet.merge()` (updates.py:993). The merged dirty set accumulates dirtiness from all sub-phases.

### Flag consumption

Pipeline phases call `CandidateSelector.entities()` with the appropriate domain set. The returned IDs are the only entities processed by that phase.

### Flag clearance

Dirty flags do not persist across ticks. Each tick builds a fresh `DirtySet` starting from an empty builder or `base_dirty=None`. There is no dirty-state carry-over between ticks.

## Mutation rules

- Any durable state change (position, inventory, attributes, combat results) must be expressed as a `StateUpdate` so the `DirtySet` captures the change.
- Directly mutating `AuthoritativeState` fields bypasses dirty tracking. In audit mode (`audit_dirty_set=True`), this fires `DirtySetLeakError` via `AuthoritativeState.validate_dirty_set()` (state.py:1159–1205). Outside audit mode, the entity is silently absent from subsequent phase candidate sets, producing stale processing.
- The `DirtySet` is a `frozen=True, slots=True` dataclass — it cannot be mutated in place. Use `DirtySetBuilder` for accumulation, then call `build()` once.
- Do not call `DirtyDependencyGraph.expand()` more than once on the same set — the result is idempotent but the double-copy is wasteful. Both `from_update()` and `DirtySetBuilder.build()` call `expand()` internally.

## Edge cases

### `town` is position-derived, not tag-settable

`DirtySetBuilder.mark_entity()` accepts tags `movement`, `combat`, `inventory`, `strategic`, `social`, `lifecycle`, `biological`, `attributes` — the string `"town"` is not a valid tag. Town dirtiness is derived by tile-checking inside `mark_from_update()` and `DirtySet.from_update()`: when `e_upd.new_position` is set, the tile coordinate `(int(x), int(y))` is looked up in `state.town_tiles`. If present, the entity enters `town_entities`; if absent, it is removed from it (`town.discard(e_id)`). This means an entity can exit town-dirty status mid-tick if it moves out of the town tile set.

### `e_upd.task` discrepancy — known risk

`DirtySetBuilder.mark_from_update()` (dirty.py:162) treats `e_upd.task` as a trigger for `strategic` dirtiness:

```python
if e_upd.strategic or e_upd.task or e_upd.interaction or e_upd.quest:
    self.strategic.add(e_id)
```

`DirtySet.from_update()` (dirty.py:329) omits `e_upd.task` from the same check:

```python
if e_upd.strategic or e_upd.interaction or e_upd.quest:
    strategic.add(e_id)
```

Callers that use `DirtySet.from_update()` directly (rather than `DirtySetBuilder`) will not mark an entity `strategic`-dirty when only `task` changes. This is a pre-existing behavioral inconsistency between the two paths. Do not fix it in this ticket — raise a dedicated bugfix ticket if task-only changes are observed to slip through strategic routing.

### `DirtySetLeakError` audit mode

`AuthoritativeState.validate_dirty_set()` (state.py:1159–1205) verifies post-apply that all mutated entities and world objects appear in the attached `DirtySet`. Fires `DirtySetLeakError` on violation. Audit mode is activated by passing `audit_dirty_set=True` to `ApplyPath.apply_generation()`. It is not active in production runs by default due to overhead.

### `force_full_scan` fallback

When `StateUpdate.force_full_scan=True` or `StateUpdate.dirty_set is None`, both `CandidateSelector.entities()` and `get_relevant_entity_ids()` return all entity IDs from `state.entities` regardless of dirty flags. This is the global re-evaluation path used for initial ticks, calamity events, and any scenario where the full entity pool must be re-evaluated. This routing bypass is unaffected by the dirty set's content — a phase never consults `dirty_set` to decide whether force-full-scan is active, only `update.force_full_scan`/`state._force_full_scan` directly.

For `force_full_scan=False` ticks, the dirty set `AuthoritativeApplyPipeline.refine()` finally returns is exactly what `DirtySetBuilder` computed from real mutations — the dirty set is still computed and attached, it is just not used for filtering. For `force_full_scan=True` ticks, `refine()`'s final "Final dirty set for result application" block (`pipeline.py`) additionally replaces the nine entity/town domain fields of the returned `DirtySet` with the full entity population (`dataclasses.replace(update.dirty_set, movement_entities=all_ids, ..., town_entities=state.town_entity_ids)`), preserving the eight non-entity fields (`group_ids`, `region_ids`, `resource_node_ids`, `building_ids`, `chest_ids`, `ground_item_ids`, `corpse_ids`, `camp_ids`) verbatim. This ensures downstream consumers outside `refine()` — `ReadModelCache.compute_tick_delta`/`.update()`, the `/api/v1/ws` broadcast — also observe full entity coverage, not just the in-pipeline phases that were already correctly widened by the routing bypass above. `Kernel.status.force_full_scan` (a declared `RuntimeStatus` field, populated once at `Kernel.__init__` from the boot-time flag) is what lets `V2EngineManager._update_latest_state` see this correctly in every observability mode, including `OFF`.

### Lifecycle event conservative marking

Entities added via `StateUpdate.entities_add` or removed via `StateUpdate.entities_remove` are simultaneously marked in ALL entity domain sets (dirty.py:353–361): movement, combat, inventory, strategic, social, lifecycle, biological, attribute. This "mark everything" approach ensures no downstream system skips a newly spawned or destroyed entity. A newly spawned entity gets `union_ids` ORed into every entity set before expansion.

## Examples

### Example 1 — entity takes damage during combat phase

Combat resolution emits:
```
EntityUpdate(entity_id=42, combat=CombatUpdate(hp_delta=-15, attacker_id=7))
```

`DirtySet.from_update()` classifies this as `combat_entities={42}`.

`DirtyDependencyGraph.expand()` derives:
- `lifecycle_entities={42}` (combat → lifecycle)
- `social_entities={42}` (combat → social)
- `strategic_entities={42}` (combat → strategic)

Lifecycle, social, and strategic phases will all process entity 42 this tick. Movement, inventory, biological, attribute phases will not (entity 42 is absent from those sets).

### Example 2 — entity moves to a new position in town

Movement phase emits:
```
EntityUpdate(entity_id=99, new_position=(12.0, 8.0))
```

Tile `(12, 8)` is in `state.town_tiles`.

`DirtySet.from_update()` classifies this as `movement_entities={99}`, `town_entities={99}`.

`DirtyDependencyGraph.expand()` derives:
- `strategic_entities={99}` (movement → strategic)
- `social_entities={99}` (movement → social)

Town domain, strategic domain, and social domain will all process entity 99. Combat, inventory, lifecycle, biological, attribute phases skip it.

## Source areas

- `src/core/dirty.py` — `DirtySetLeakError`, `DirtySet`, `DirtySetBuilder`, `DirtyDependencyGraph`, `CandidateSelector`, `get_relevant_entity_ids()`, `get_relevant_group_ids()`
- `src/core/state.py` — `AuthoritativeState.validate_dirty_set()`, `AuthoritativeState.to_readonly()`, `state.town_tiles`, `state.town_entity_ids`
- `src/core/updates.py` — `StateUpdate.dirty_set`, `StateUpdate.merge_many()` (dirty set accumulation at updates.py:993)

Cross-reference: `docs/core/state.md` (Immutability Law — why `DirtySet` is frozen), `docs/engine/authoritative_apply_contract.md` (where `audit_dirty_set` is activated).

## Regression tests

| Test file | What it verifies |
|---|---|
| `tests/perf/test_dirty_set_integrity.py` | `DirtySet.from_update()` tracks movement, combat, world objects correctly; `DirtySetLeakError` fires on undeclared mutations; incremental merge correctness via `DirtySet.merge()` |
| `tests/perf/test_dirty_parity.py::test_dirty_set_vs_full_scan_parity` | Bit-identical state hash between dirty-set-optimized path and `force_full_scan=True` reference path over 100 ticks (`@pytest.mark.slow`) |
| `tests/integration/pipeline/test_authoritative_apply.py` | `apply_generation()` isolation (prior state not mutated), deterministic apply order, resource delta correctness |
| `tests/integration/optimization/test_force_full_scan_dirty_set_completeness.py` | `refine()`'s final `DirtySet` covers every entity across all nine entity/town domains under `force_full_scan=True`, even with zero real `EntityUpdate`s that tick; the eight non-entity domains (`building_ids` etc.) already computed by `DirtySetBuilder` survive the override untouched; the override does not fire when `force_full_scan=False`; a `force_full_scan=True`-booted `Kernel`'s WS delta (`ReadModelCache.compute_tick_delta`) `changed` list contains every live entity |

## Extension rules

To add a new dirty flag:

1. Define a new `Set[T]` field on `DirtySet` (dirty.py, near line 211). Use `field(default_factory=set)`.
2. Add the corresponding mutable attribute to `DirtySetBuilder.__init__()` (both the `if base:` branch and the `else:` branch).
3. Add inspection logic in **both** `DirtySet.from_update()` (dirty.py near line 308) **and** `DirtySetBuilder.mark_from_update()` (dirty.py near line 139). Keep them in sync to avoid the `e_upd.task`-class discrepancy.
4. Add expansion edges in `DirtyDependencyGraph.expand()` (dirty.py near line 408) if the new flag implies downstream dirtiness in other domains.
5. Add the new field to the `DirtySet` constructor call inside `DirtySetBuilder.build()` (dirty.py near line 183) and inside `DirtyDependencyGraph.expand()` (dirty.py near line 439).
6. Add a domain routing entry in `CandidateSelector.entities()` (dirty.py near line 479) for the new domain name string.
7. Update `DirtySet.merge()` (dirty.py near line 380) to union the new field from both sides.
8. Add a test case to `tests/perf/test_dirty_set_integrity.py` asserting the new flag is set by the expected `StateUpdate` content and cleared by an empty update.
