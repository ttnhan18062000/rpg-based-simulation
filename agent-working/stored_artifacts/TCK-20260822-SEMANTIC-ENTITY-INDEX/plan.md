---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260822-SEMANTIC-ENTITY-INDEX
artifact_type: plan
tags: [engine, performance, determinism]
---

# Implementation Plan — TCK-20260822-SEMANTIC-ENTITY-INDEX

## Summary

Build a `SemanticEntityIndexes` frozen dataclass + `SemanticEntityIndexService`, structurally
parallel to `WorldIndexes`/`WorldIndexService` (`src/engine/world_index.py`), covering five
dimensions over live entity state: `role`+`class_id`, `region_id`, `faction`, `entity_needs`
(`BiologicalComponent` threshold crossings), and `knowledge_domain`
(`AuthoritativeState.information_providers`). The index follows `WorldIndexService`'s existing
lazy, pull-based, tick-cached, per-domain-partial-rebuild lifecycle — called from query methods,
attached to `AuthoritativeState` via `object.__setattr__`, never via `StateUpdate`/`replace()` —
per investigation Recommendation 1. `entity_needs` maps to `BiologicalComponent` fields per
investigation Recommendation 2 (not the unshipped `QuestOpportunityGenerator.from_entity_need`
stub). `CacheInvalidationPolicy.invalidated_indexes()`/`should_invalidate()` gain three new
domains for the semantic dimensions.

This plan additionally resolves, with direct source evidence, the two risks the investigation
left open:

1. **`CanonicalStateHasher` exclusion is already structurally guaranteed, no code change needed.**
   `CanonicalStateHasher.to_canonical_data()` (`src/engine/checkpoint.py:66-107`) is a **hand-written
   allow-list** — it builds its output dict by explicitly naming each field it wants
   (`tick`, `seed`, `world_time`, `movement_count`, `maturity`, `last_calamity_tick`, `town_center`,
   then `entities`/`regions`/`local_scars`/`resource_nodes`/`buildings`/`corpses`/`ground_items`/
   `chests`/`groups`/`home_storage`/`camps`/`global_resources`/`periodic_due_ticks`/`work_debt`/
   `blocked_tiles`/`town_tiles`/`building_tiles`/`rng_checkpoint`) rather than iterating
   `dataclasses.fields(state)` generically. It never references `world_indexes` or any `_*_cache`
   field today. `AuthoritativeState.world_indexes` is declared `field(default=None, repr=False,
   compare=False)` (`src/core/state.py:1111`) — same pattern as `_node_map_cache` (line 1115),
   `_opt_profile` (line 1145), etc. As long as the new `semantic_entity_indexes` field on
   `AuthoritativeState` is declared the same way (`repr=False, compare=False`) and is **never added**
   to `CanonicalStateHasher.to_canonical_data()`'s explicit field list, it is automatically excluded
   from the hash — this is a scope guard (see Step 1 and Scope Guards), not a code change to
   `checkpoint.py`.
2. **DirtySet currently has zero tag coverage for `IdentityUpdate`/role/faction changes — confirmed,
   not just suspected.** `DirtySet.from_update`'s per-entity loop (`src/core/dirty.py:305-343`) checks
   `e_upd.new_position`, `e_upd.combat`, `e_upd.inventory or e_upd.resource_transfers`,
   `e_upd.strategic or e_upd.interaction or e_upd.quest`, `e_upd.social`, `e_upd.lifecycle`,
   `e_upd.biological`, `e_upd.attributes or e_upd.reward` — there is **no branch that reads
   `e_upd.identity` at all**. `IdentityUpdate.role_set`/`faction_set`
   (`src/core/updates.py:222-223`) — the fields `EntityUpdate.identity` carries — currently drive
   zero `DirtySet` tags. This plan adds a new dedicated `identity_entities: Set[int]` field (Step 2)
   rather than overloading the existing `attribute_entities` tag, because `attribute_entities` already
   has a real consumer outside `dirty.py` — `src/engine/phase_graph.py:141` gates whether phases
   declaring `"attributes"` in `input_domains` run at all — and folding identity changes into it would
   silently increase how often those unrelated phases run. A new field is purely additive: it has no
   existing readers to perturb.
   `class_id` (`IdentityComponent.class_id`, `src/core/state.py:482`) has **no update path at all** —
   grepped across `src/core/updates.py`/`src/core/state.py`/`src/engine/apply.py`: it is set once at
   entity construction (`state.py:825`) and carried through unchanged by `ApplyPath`
   (`apply.py:521: object.__setattr__(res, "class_id", id_comp.class_id)`), never written by any
   `IdentityUpdate`/`EntityUpdate` field. So the `identity_entities` tag firing on `e_upd.identity`
   being non-`None` is sufficient — no separate `class_id` invalidation path is needed, since
   `class_id` cannot change post-creation in current shipped code.

## Steps

### Step 1 — Add `SemanticEntityIndexes` dataclass and derived-cache field on `AuthoritativeState`

**Files:** `src/engine/semantic_entity_index.py` (new), `src/core/state.py`

**Change:**
- Create `src/engine/semantic_entity_index.py`, mirroring `WorldIndexes`
  (`src/engine/world_index.py:64-76`). Define a frozen dataclass `SemanticEntityIndexes`:
  ```python
  @dataclass(frozen=True)
  class SemanticEntityIndexes:
      tick: int
      by_role_class: Dict[Tuple[int, str], Tuple[int, ...]]   # (role, class_id) -> entity ids
      by_region: Dict[str, Tuple[int, ...]]                    # region_id -> entity ids
      by_faction: Dict[int, Tuple[int, ...]]                   # faction -> entity ids
      by_need: Dict[str, Tuple[int, ...]]                      # need name (e.g. "hunger") -> entity ids over threshold
      by_knowledge_domain: Dict[str, Tuple[int, ...]]          # domain string -> provider entity ids
  ```
  `role`/`class_id` are combined into a single `(role, class_id)` tuple key on one dimension
  (`by_role_class`), per the ticket's own AC #1 query signature
  (`entity_index.by_role_class(role, class_id)`) — resolving the investigation's flagged open design
  choice in favor of the ticket's literal AC wording rather than two separately-joined dimensions.
- In `src/core/state.py`, add one new field to `AuthoritativeState` immediately after
  `world_indexes: Any = field(default=None, repr=False, compare=False)` (state.py:1111):
  `semantic_entity_indexes: Any = field(default=None, repr=False, compare=False)`. Use the same
  `Any`/`repr=False`/`compare=False` shape as `world_indexes` — this is what keeps it out of
  dataclass `__eq__`/`__repr__` and (per the resolved risk above) out of `CanonicalStateHasher`.
  Do **not** add it to `AuthoritativeState.to_readonly()`'s `replace(...)` call (state.py:1221-1250)
  unless the `world_indexes` precedent requires it — check: `world_indexes=self.world_indexes` IS
  passed through at state.py:1249, so add `semantic_entity_indexes=self.semantic_entity_indexes` to
  that same `replace()` call, matching the precedent exactly.
- Do NOT add `semantic_entity_indexes` to `CanonicalStateHasher.to_canonical_data()`
  (`src/engine/checkpoint.py:66-107`) — its exclusion from the hash is achieved by omission, not by
  an explicit exclusion list. This is enforced by Step 6's test, not by editing checkpoint.py.

**Do NOT touch:** `WorldIndexes`, `WorldIndexService`, `CacheInvalidationPolicy`'s existing spatial
domains (edit only additively in Step 3) — those stay read-only precedent per the investigation's
Anti-Drift Hazards.

**Verify:** New file imports cleanly; `AuthoritativeState()` constructs with
`semantic_entity_indexes=None` by default (no test yet — this step is a prerequisite for Step 4's
tests to exist against).

---

### Step 2 — Add `identity_entities` DirtySet tag for role/faction invalidation

**Files:** `src/core/dirty.py`, `src/engine/pipeline.py`

**Change:** This is the fix for Risk 2 above (DirtySet currently has zero coverage for identity
changes) and a hard prerequisite for AC #3's role/faction incremental-invalidation behavior. Four
places in `src/core/dirty.py` construct/reconstruct `DirtySet` objects field-by-field
(confirmed by reading each) plus one in `pipeline.py` — all four dirty.py sites and the pipeline.py
site must be updated together or the new field silently reverts to an empty set partway through the
pipeline:

1. **`DirtySet` dataclass** (`dirty.py:205-229`): add `identity_entities: Set[int] =
   field(default_factory=set)` alongside `attribute_entities` (line 219).
2. **`DirtySet.from_update`** (`dirty.py:237-374`): in the `base_dirty is None`/`else` branches
   (lines 244-282), add an `identity = set()` / `identity = set(base_dirty.identity_entities)`
   initializer alongside `attributes`. In the per-entity loop (lines 305-343), add a new branch
   after the `e_upd.attributes or e_upd.reward` check (line 342-343):
   ```python
   if e_upd.identity:
       identity.add(e_id)
   ```
   (`e_upd.identity` is `Optional[IdentityUpdate]`; `IdentityUpdate.__bool__`/truthiness follows the
   same pattern as `e_upd.combat`/`e_upd.social` — a non-`None` `IdentityUpdate` object is truthy).
   Add `identity_entities=identity | union_ids` to the final `DirtySet(...)` construction
   (lines 356-373).
3. **`DirtySet.merge`** (dirty.py, the `merge` method after `from_update`): add
   `identity_entities=self.identity_entities | other.identity_entities` to its `DirtySet(...)`
   construction.
4. **`DirtyDependencyGraph.expand`** (`dirty.py:402-457`): add `identity = set(dirty.identity_entities)`
   at the top (line ~417 area) and `identity_entities=identity` to the final `DirtySet(...)`
   construction (lines 439-457). Do NOT add any new dependency-implication edges (e.g. do not make
   identity changes imply `strategic`/`lifecycle` the way biological/attributes do at lines 434-437)
   — no existing consumer requires that inference and adding it would be speculative scope beyond
   what AC #3 needs.
5. **`src/engine/pipeline.py`'s force-full-scan block** (pipeline.py:352-366): this is a second,
   independent writer that directly constructs a `replace()` call setting every `DirtySet` field to
   `all_ids` when `update.force_full_scan` is true. Add `identity_entities=all_ids` to that
   `replace(update.dirty_set, ...)` call (alongside the existing `attribute_entities=all_ids` at
   line 365-366). Missing this would mean a force-full-scan tick fails to invalidate the role/faction
   dimension — a real correctness gap, not cosmetic, and exactly what
   `tests/integration/optimization/test_force_full_scan_dirty_set_completeness.py` (already in the
   test plan's regression surface) is positioned to catch.
6. **`DirtySet.all_dirty_entities` property** (`dirty.py:230-233`): this is a **sixth** touch point,
   distinct from the five construction sites above — a hand-written union property, not a
   constructor, so a new field added to the dataclass does not automatically appear in it:
   ```python
   @property
   def all_dirty_entities(self) -> Set[int]:
       return (self.movement_entities | self.combat_entities | self.inventory_entities |
               self.strategic_entities | self.social_entities | self.lifecycle_entities |
               self.biological_entities | self.attribute_entities)
   ```
   Add `| self.identity_entities` to this union (a 9th term). `all_dirty_entities` is read by five
   other call sites beyond `dirty.py` itself, all of which silently misbehave on an identity-only
   change (no `movement`/`combat`/`inventory`/`strategic`/`social`/`lifecycle`/`biological`/
   `attribute` field touched, only `identity_entities`) if this union is left unfixed:
   - `AuthoritativeState.validate_dirty_set` (`src/core/state.py:1268`, reads `dirty_set.all_dirty_entities`
     at state.py:1276) — invoked from `ApplyPath.apply` (`src/engine/apply.py:422-423`) only when
     `audit_dirty_set is True`. In audit mode, an identity-only `EntityUpdate` would produce an entity
     whose live state differs from `prior_state` but whose id is absent from `all_dirty_entities`,
     raising a false `DirtySetLeakError` (`src/core/dirty.py` — imported at state.py:1268-1269). Fixing
     the union resolves this with no other change needed.
   - `ReadModelInvalidationPolicy.get_dirty_entity_ids` (`src/api/read_model_cache.py:21-28`, returns
     `set(dirty_set.all_dirty_entities)` at line 28) and `ReadModelCache.compute_tick_delta`
     (`read_model_cache.py:118+`, consumes that id set to decide which entities' WS delta payload to
     rebuild/broadcast). `faction` is one of the fields in `StatePresenter.present_entity_slim`'s wire
     payload per parity ledger entry INFRA-388 — without the union fix, a faction-only change would
     never appear in the dirty id set and its WS delta would silently never broadcast. This step's
     fix is the only change needed; no edit to `read_model_cache.py` itself.
   - `ApplyPlan.plan()`'s `invalidate_read_model` flag (`src/engine/apply_plan.py:72`:
     `invalidate_read_model=update.dirty_set is not None and bool(getattr(update.dirty_set,
     "all_dirty_entities", set()))`) — reads the same property; fixed for free once the union is fixed.
   - `HardLawMonitor.check_entities` (`src/observability/hard_law_monitor.py:70`, `dirty_ids =
     dirty_set.all_dirty_entities`) — scoped attribute/property checks on dirty entities would skip
     identity-only-dirty entities without this fix; fixed for free.
   - `CandidateSelector`'s `'all'`-domain branch (`src/core/dirty.py:494`: `elif d == "all": candidates
     |= ds.all_dirty_entities`) — fixed for free.

   This fix is independent of `attribute_entities`/`phase_graph.py:141`: `all_dirty_entities` has no
   relationship to per-domain `input_domains` phase-gating (that gating reads `ds.attribute_entities`
   directly, not the union property), so adding `identity_entities` to this union does not reintroduce
   the phase-cadence risk this plan already avoids by using a dedicated tag instead of overloading
   `attribute_entities` (see Summary item 2 and the "Do NOT touch" note below).

**Do NOT touch:** `attribute_entities`'s existing branch/semantics (the `e_upd.attributes or
e_upd.reward` check, dirty.py:342) — do not fold identity into it. Do NOT touch
`src/engine/phase_graph.py:141`'s `"attributes"` domain-skip logic — it must keep reading only
`ds.attribute_entities`, unaffected by this change, since `identity_entities` is a new, separate tag
with no phase-graph consumer in this ticket's scope. Do not add `identity_entities` to any of
`ReadModelInvalidationPolicy`, `ApplyPlan.plan()`, `HardLawMonitor.check_entities`, or
`CandidateSelector` individually — sub-item 6's single fix to the `all_dirty_entities` union property
is what fixes all four of those call sites; do not additionally special-case `identity_entities` in
any of their own bodies, which would be redundant and risks double-counting.

**Verify:**
- `tests/perf/test_dirty_set_integrity.py`, `tests/perf/test_dirty_parity.py` — regression surface
  for any new `DirtySet` field, must still pass.
- `tests/integration/optimization/test_force_full_scan_dirty_set_completeness.py` — must still pass
  with `identity_entities` now included in the force-full-scan field list.
- New test: `test_identity_update_sets_identity_entities_tag` (unit, in
  `tests/unit/domains/optimization/test_semantic_entity_index.py` or a `dirty.py`-adjacent test file)
  asserting an `EntityUpdate` with a non-noop `IdentityUpdate(role_set=...)` produces a `DirtySet`
  with that entity id in `identity_entities`, and that an `EntityUpdate` with only
  `attributes`/`biological` set does NOT populate `identity_entities`.
- New test: `test_identity_only_update_appears_in_all_dirty_entities` (unit, same file family as
  above, directly adjacent to `test_identity_update_sets_identity_entities_tag`) — construct an
  `EntityUpdate` with only `identity=IdentityUpdate(role_set=...)` (or `faction_set=...`) and no other
  domain field set, derive its `DirtySet` via `DirtySet.from_update`, and assert the entity id is
  present in `dirty_set.all_dirty_entities` (sub-item 6's union property) — this is the direct
  regression guard for the architecture-review finding that `all_dirty_entities` previously omitted
  `identity_entities`.
- Re-verify (do not modify unless it fails) `tests/unit/api/test_read_model_cache.py::
  test_compute_tick_delta_changed_includes_only_dirty_and_alive_entities` under an identity-only
  `EntityUpdate` (faction change, no other domain touched) — confirm the resulting delta includes the
  entity, proving `ReadModelInvalidationPolicy.get_dirty_entity_ids`/`ReadModelCache.compute_tick_delta`
  now see the identity-only change through the fixed `all_dirty_entities` union. If the existing test
  fixture does not already exercise an identity-only update, add a parametrized case rather than
  writing a new test file.
- Re-verify `AuthoritativeState.validate_dirty_set`'s audit-mode path (`state.py:1268`, invoked from
  `ApplyPath.apply` at `apply.py:422-423` when `audit_dirty_set=True`) with an identity-only update:
  apply an `EntityUpdate(identity=IdentityUpdate(faction_set=...))` through `ApplyPath.apply(...,
  audit_dirty_set=True)` and assert no `DirtySetLeakError` is raised. This is the direct regression
  guard for the false-leak-error failure mode the architecture review flagged.

---

### Step 3 — Extend `CacheInvalidationPolicy` with three semantic-index domains

**Files:** `src/engine/semantic_entity_index.py` (or `src/engine/world_index.py` if co-locating —
see note below)

**Change:** `CacheInvalidationPolicy` (`src/engine/world_index.py:11-42`) is a shared resource:
`WorldIndexService.get_indexes` (world_index.py:83-116) already calls
`CacheInvalidationPolicy.should_invalidate("resources"/"buildings"/"entities"/"ground_items"/
"corpses", dirty)` for the five existing spatial domains. This step adds three new domain strings
without touching any existing branch:
- `"identity"` → invalidated when `dirty.identity_entities` is non-empty (backs `by_role_class` and
  `by_faction` — both driven by `IdentityComponent`/`IdentityUpdate`, sharing the same dirty tag from
  Step 2).
- `"region"` → invalidated when `dirty.region_ids` is non-empty. **Do NOT reuse or touch the existing
  `"region_index"` string** already present in `CacheInvalidationPolicy.invalidated_indexes()`
  (world_index.py:31: `if dirty.region_ids: invalidated.add("region_index")`) — that string is the
  known pre-existing phantom-field bug (`WorldIndexes` has no `region_index` field, and
  `WorldIndexService.get_indexes()` never calls `should_invalidate("regions", ...)`). Use a distinctly
  named string, e.g. `"semantic_region_index"`, for this ticket's new domain so the two are never
  conflated and the phantom bug's eventual fix (a separate future ticket) does not collide with this
  addition.
- `"needs"` → invalidated when `dirty.biological_entities` is non-empty (reuses the existing
  `biological_entities` tag — already correctly populated by `e_upd.biological`, dirty.py:341-342 —
  since `entity_needs` is resolved to mean `BiologicalComponent` fields; no new dirty tag needed for
  this dimension).
- `"knowledge"` → invalidated when `dirty is None` (always rebuild if no dirty info) or... note:
  `information_providers` mutations are not currently tracked by any `DirtySet` field (confirmed:
  `DirtySet` has no `information_provider_ids`/similar tag, and this ticket's Out of Scope forbids
  inventing new unshipped tracking beyond what AC #3 requires for role/region/faction). Since AC #3
  only requires "region_id/faction/role" to demonstrate incremental invalidation (the ticket's own
  wording), the `knowledge` domain may conservatively always invalidate (`should_invalidate("knowledge",
  dirty)` returns `True` unconditionally) rather than inventing new DirtySet plumbing for a dimension
  AC #3 doesn't test. Document this conservative choice inline as a code comment.

Implement `CacheInvalidationPolicy.should_invalidate()`'s three new `if domain == ...` branches
(world_index.py:38+) additively, after the existing `"regions"` branch, without modifying any
existing `if domain ==` branch's return logic.

**Do NOT touch:** the existing `"resources"`/`"buildings"`/`"entities"`/`"ground_items"`/`"corpses"`/
`"regions"` branches, or the phantom `"region_index"` entry in `invalidated_indexes()` — leave both
exactly as-is (see Scope Guards).

**Verify:** New test `test_cache_invalidation_policy_unrelated_domains_unaffected` (from test_plan.md
Anti-Drift Test Guards) — asserts existing spatial domains return identical results for the same
`DirtySet` inputs as before this ticket.

---

### Step 4 — Implement `SemanticEntityIndexService.get_indexes()` with per-dimension partial rebuild

**Files:** `src/engine/semantic_entity_index.py`

**Change:** Mirror `WorldIndexService.get_indexes()` (`src/engine/world_index.py:83-116`) exactly:
tick-scoped cache hit check (`existing.tick == state.tick`), then per-dimension reuse-or-rebuild
gated by `CacheInvalidationPolicy.should_invalidate(domain, dirty)` from Step 3, then
`object.__setattr__(state, "semantic_entity_indexes", new_indexes)` — never `StateUpdate`/`replace()`.

Per-dimension builder methods, each a full re-scan of `state.entities` (matching
`_build_resource_index`'s full-rescan-but-dirty-gated shape, world_index.py:119+):
- `_build_role_class_index(state)`: iterate `state.entities.values()`, bucket by
  `(entity.identity.role, entity.identity.class_id)` (`IdentityComponent.role`/`class_id`,
  `src/core/state.py:472,482`; `EntityState.identity`, `src/core/state.py:674`). Sort entity ids
  within each bucket, store as `Tuple[int, ...]` per the "tuples not lists" determinism convention
  (`CandidateSelector.entities()`'s `tuple(sorted(...))`, `src/core/dirty.py:503,506` — cited in
  investigation).
- `_build_region_index(state)`: bucket by `entity.navigation.region_id`
  (`NavigationComponent.region_id`, `src/core/state.py:376-377`; `EntityState.navigation`,
  `src/core/state.py:686`). Skip entities where `region_id is None`.
- `_build_faction_index(state)`: bucket by `entity.identity.faction`
  (`IdentityComponent.faction`, `src/core/state.py:473`).
- `_build_needs_index(state)`: for each entity, check `entity.biological.hunger`/`sleep_debt`/
  `rest_pressure` (`BiologicalComponent`, `src/core/state.py:115-124`) against **per-field** module-
  level threshold constants — not one shared magic number. Use the Mechanics-Bible-documented Penalty
  Thresholds where they exist, and the existing source-code precedent constant where the Bible is
  silent:
  - `HUNGER_NEED_THRESHOLD = 95.0` — cites `docs/mechanics/01_entity_anatomy.md:76`: "**Hunger** |
    `+0.1` | 100.0 | **95.0**: Starvation (+2 HP damage/tick)". This is the Bible's documented Penalty
    Threshold for hunger; use it verbatim rather than an invented value.
  - `SLEEP_DEBT_NEED_THRESHOLD = 98.0` — cites `docs/mechanics/01_entity_anatomy.md:77`: "**Sleep
    Debt** | `+0.05` | 100.0 | **98.0**: Fatigue (+1 HP damage/tick)". Same rationale as hunger.
  - `REST_PRESSURE_NEED_THRESHOLD = 70.0` — the Mechanics Bible's biological-pressures table
    (`01_entity_anatomy.md:71-78`) documents Penalty Thresholds only for Hunger and Sleep Debt, not
    `rest_pressure` (the table's third row, Stamina, is a different field with a different, unnumbered
    "Exhaustion Threshold" and is not `rest_pressure`). In the absence of a Bible-documented value for
    `rest_pressure`, use the existing shipped precedent: `bio.rest_pressure > 70.0` is already the
    urgency/forced-rest cutoff used in two live call sites — `src/domains/combat_engagement/
    perception.py:95` (`if rest_pressure > 70.0:`) and `src/systems/world_systems/routine.py:49` (`if
    bio.rest_pressure > 70.0:`), and matches `work_queue.py:84`'s `bio.rest_pressure > 80.0` family of
    checks in spirit (same pressure-scalar convention, just a different consumer's own cutoff). `70.0`
    is the value two independent existing consumers already treat as the "forced rest" cutoff, so this
    index reuses it rather than inventing a new number — do not invent a fourth different constant for
    this field.
  Bucket entity id under `"hunger"`/`"sleep_debt"`/`"rest_pressure"` key for each field that crosses
  its own threshold (three independent per-field comparisons, not one shared cutoff applied to all
  three). Do NOT reference `QuestOpportunityGenerator.from_entity_need` or any `need_kind` concept
  anywhere in this method — this is the exact scope boundary Recommendation 2 and the ticket's Out of
  Scope line establish.
- `_build_knowledge_domain_index(state)`: iterate `state.information_providers.items()`
  (`AuthoritativeState.information_providers: Dict[int, InformationProviderState]`,
  `src/core/state.py:1154`); for each provider, bucket its entity_id under every string in
  `InformationProviderState.knowledge_domains: Tuple[str, ...]`
  (`src/domains/information/providers.py:37-58`).

**Do NOT touch:** `src/engine/pipeline_phases/paid_information.py` — read-only reference for
`InformationProviderState`/seeker-scan shape only, per the ticket's explicit Out of Scope
(`TCK-20260822-PAID-INFO-INDEX-RETROFIT` is the separate retrofit ticket). Do not call this new
service from `paid_information.py` in this ticket.

**Verify:**
- `test_by_role_class_matches_naive_scan`
- `test_by_region_matches_naive_scan`
- `test_by_faction_matches_naive_scan`
- `test_by_entity_needs_matches_naive_scan_against_biological_thresholds`
- `test_by_knowledge_domain_matches_naive_scan`
(all in `tests/unit/domains/optimization/test_semantic_entity_index.py` per test_plan.md)

---

### Step 5 — Public query methods returning only entity IDs

**Files:** `src/engine/semantic_entity_index.py`

**Change:** Add a thin query-facing class or module-level functions (e.g. `SemanticEntityQuery` or
static methods on `SemanticEntityIndexService`) that call `get_indexes()` internally and expose:
- `by_role_class(state, dirty, role: int, class_id: str) -> Tuple[int, ...]`
- `by_region(state, dirty, region_id: str) -> Tuple[int, ...]`
- `by_faction(state, dirty, faction: int) -> Tuple[int, ...]`
- `by_need(state, dirty, need: str) -> Tuple[int, ...]`
- `by_knowledge_domain(state, dirty, domain: str) -> Tuple[int, ...]`

Every method signature and return type must be `Tuple[int, ...]` (or `Set[int]`/`List[int]` — pick
one and use it consistently; `Tuple[int, ...]` matches `WorldIndexes`' own convention, e.g.
`buildings_by_kind: Dict[str, Tuple[int, ...]]`, world_index.py:71) — never `EntityState`,
`IdentityComponent`, or other component/domain objects. This directly satisfies AC #1's
`entity_index.by_role_class(role, class_id)` signature.

**Do NOT touch:** Do not add any method that returns a component object "for convenience" (e.g. no
`by_role_class_full(...) -> List[EntityState]`) — AC #2 forbids this categorically, not just for the
primary methods.

**Verify:**
- `test_query_methods_return_only_entity_ids_not_objects` (static/architecture guard, in
  `tests/static/test_semantic_entity_index_returns_ids_only.py`, mirroring
  `tests/static/test_no_direct_dirtyset_candidate_selection.py`'s pattern) — AC #2.

---

### Step 6 — Determinism guard: exclusion from `CanonicalStateHasher`

**Files:** `tests/unit/domains/optimization/test_semantic_entity_index.py` (test-only step; no
production code change — see Step 1's citation of why no `checkpoint.py` edit is needed)

**Change:** Add `test_semantic_index_excluded_from_canonical_state_hash`: build a state, compute
`CanonicalStateHasher.get_hash(state)`, then attach a built `SemanticEntityIndexes` via
`object.__setattr__(state, "semantic_entity_indexes", indexes)`, recompute the hash, and assert
equality. This is a regression guard, not a fix — Step 1 already established (by reading
`checkpoint.py:66-107`) that the hash is an explicit allow-list that will never pick up the new
field unless someone later edits `to_canonical_data()` to add it, which this test would catch.

**Do NOT touch:** `src/engine/checkpoint.py` itself — no production change in this step.

**Verify:** `test_semantic_index_excluded_from_canonical_state_hash` (AC-adjacent; underwrites AC #3
and #4's "bit-identical" language by proving the index write path cannot perturb the hash other
tests compare against).

---

### Step 7 — Incremental-vs-rebuild bit-identity and delete-and-rebuild tests

**Files:** `tests/unit/domains/optimization/test_semantic_entity_index.py`

**Change:** No new production code in this step (Steps 1-5 already implement the mechanics this step
tests). Add:
- `test_index_reflects_dirty_set_change_without_full_rebuild` — mutate one entity's `role` via a
  `StateUpdate`/`EntityUpdate(identity=IdentityUpdate(role_set=...))`, derive the resulting
  `DirtySet` (Step 2's new `identity_entities` tag fires), call `get_indexes()` again, and assert (a)
  the `by_role_class` result reflects the new role and (b) a rebuild-call spy shows only the
  `"identity"` domain's builder method was invoked, not `_build_region_index`/`_build_needs_index`/
  `_build_knowledge_domain_index`. Mirrors
  `test_world_index_invalidates_resource_index_when_resource_node_dirty` in
  `tests/unit/domains/optimization/test_world_index_service.py`.
- `test_incremental_index_bit_identical_to_full_rebuild` — build the index incrementally across N
  ticks with mutations across all 5 dimensions, then force a full rebuild
  (`object.__setattr__(state, "semantic_entity_indexes", None)` then `get_indexes(state, dirty=None)`
  — `dirty=None` means `should_invalidate` returns `True` unconditionally per
  `CacheInvalidationPolicy.should_invalidate`'s existing `if dirty is None: return True` guard,
  world_index.py:37), and assert every dimension's query results are identical (AC #3's
  "bit-identical to a from-scratch rebuild" clause).
- `test_delete_and_rebuild_index_matches_incremental_across_all_dimensions` — same shape as above but
  a single combined assertion across all 5 dimensions at once (AC #4), catching cross-dimension
  interaction bugs a per-dimension check might miss.

**Do NOT touch:** production code in this step — pure test additions verifying Steps 1-5's already-
implemented behavior.

**Verify:** the three tests above, all AC #3/#4.

---

### Step 8 — Anti-drift regression guards

**Files:** `tests/static/` (new or extended file), `tests/unit/domains/optimization/
test_semantic_entity_index.py`

**Change:** No production code. Add the four anti-drift tests from test_plan.md's "Anti-Drift Test
Guards" section:
- `test_semantic_index_never_written_via_stateupdate` — source-scan test (same shape as
  `tests/static/test_no_direct_dirtyset_candidate_selection.py`) asserting no file under
  `src/engine/` (or wherever `SemanticEntityIndexService` lands) constructs a `StateUpdate`/
  `replace()` call writing to `semantic_entity_indexes`.
- `test_paid_information_scan_unchanged` — light assertion (can extend
  `tests/unit/cognition/test_information_seeking.py`) confirming
  `src/engine/pipeline_phases/paid_information.py`'s scan is byte-for-byte unchanged.
- `test_from_entity_need_still_returns_none` — re-list `tests/unit/quest/test_quest_generation.py`'s
  existing stub test in this ticket's regression run (no new test body needed if the existing test
  already covers this — confirm it does, not duplicate it).
- `test_no_phase_boundary_restructuring` — diff-review checklist item for Verify: confirm
  `src/engine/kernel.py`'s `_phase_persistence`/`_phase_advancement` bodies are unchanged by this
  ticket (no new `object.__setattr__` calls added there, no line-count drift). This ticket's lazy
  lifecycle (Recommendation 1) requires zero kernel phase hooks, so any diff touching either phase's
  control flow is a drift signal.

**Do NOT touch:** `src/engine/kernel.py` — zero changes in this entire plan touch this file.

**Verify:** all four guards pass; `_phase_persistence`/`_phase_advancement` diff is empty.

---

### Step 9 — Docs: `docs/engine/performance_contract.md` update and `idea_semantic_entity_index.md` supersession marker

**Files:** `docs/engine/performance_contract.md`, `docs/plans/idea_semantic_entity_index.md`

**Change:** Add a new subsection to `performance_contract.md` (parallel to the existing spatial
`WorldIndexService`/`CacheInvalidationPolicy` documentation) describing:
- The `SemanticEntityIndexes`/`SemanticEntityIndexService` mechanism and its 5 dimensions.
- Its lifecycle: lazy, pull-based, `CacheInvalidationPolicy`-driven, tick-cached, per-domain partial
  rebuild — explicitly NOT an eager Persistence-phase write (cite Recommendation 1's reasoning:
  `_phase_persistence` performs zero state mutation).
- That it is excluded from `CanonicalStateHasher` by omission (Step 1/6).
- The new `identity_entities` `DirtySet` tag (Step 2) and its role.

In `docs/plans/idea_semantic_entity_index.md`, add a marker at the top noting it is superseded by
`TCK-20260822-SEMANTIC-ENTITY-INDEX` (per investigation's "Docs Requiring Update" section) — this is
a status marker edit, not a technical rewrite; do not delete or move the file in this step (that
decision, if any, belongs to Finalize).

**Do NOT touch:** any `docs/mechanics/` chapter — investigation confirms none require updates (no
formula/law change). Do NOT create a new `docs/parity_ledger/*.yaml` entry — investigation confirms
none is required (non-authoritative, no behavior/formula change); optional P2 entry only, and this
plan does not schedule it as a required step.

**Verify:** `make knowledge-index-update` (per project CLAUDE.md "After Work" rule, since
`docs/engine/performance_contract.md` was modified).

## Scope Guards

- Do NOT fix the pre-existing `"region_index"` phantom-field bug in `CacheInvalidationPolicy.
  invalidated_indexes()`/`WorldIndexes` (world_index.py:31, world_index.py:83-116's missing
  `should_invalidate("regions", ...)` call). Step 3 uses a distinctly-named `"semantic_region_index"`
  string specifically to avoid colliding with or masking this bug.
- Do NOT retrofit `src/engine/pipeline_phases/paid_information.py` or any faction/military conflict
  call site to use the new index. Those are `TCK-20260822-PAID-INFO-INDEX-RETROFIT` and
  `TCK-20260822-GUARD-SCAN-INDEX-RETROFIT`.
- Do NOT build `QuestOpportunityGenerator.from_entity_need`'s `need_kind` taxonomy or any
  `InformationNeed`-style durable "ticks unsatisfied" tracker. `entity_needs` is `BiologicalComponent`
  thresholds only.
- Do NOT restructure `Kernel._phase_advancement`/`_phase_persistence` boundaries or add any
  `object.__setattr__` call inside either method. The lazy lifecycle requires no kernel hook.
- Do NOT overload the existing `attribute_entities` DirtySet tag for identity changes — Step 2 adds a
  dedicated `identity_entities` tag instead, specifically to avoid perturbing
  `src/engine/phase_graph.py:141`'s existing `"attributes"`-domain phase-skip behavior.
- Do NOT special-case `identity_entities` individually inside `ReadModelInvalidationPolicy`,
  `ApplyPlan.plan()`, `HardLawMonitor.check_entities`, or `CandidateSelector` — Step 2 sub-item 6's
  single fix to `DirtySet.all_dirty_entities` (dirty.py:230-233) is the one place all four of those
  consumers are fixed from; adding a redundant per-consumer special case is out of scope and risks
  double-counting.
- Do NOT invent an unsourced magic-number threshold for `_build_needs_index`'s per-field cutoffs —
  Step 4 uses the Mechanics-Bible-documented Penalty Thresholds for `hunger` (95.0,
  `docs/mechanics/01_entity_anatomy.md:76`) and `sleep_debt` (98.0,
  `docs/mechanics/01_entity_anatomy.md:77`), and the existing shipped `rest_pressure > 70.0` precedent
  (`src/domains/combat_engagement/perception.py:95`, `src/systems/world_systems/routine.py:49`) for
  the one field the Bible does not document. Do not substitute a different, uncited number for any of
  the three.
- Do NOT add `semantic_entity_indexes` to `CanonicalStateHasher.to_canonical_data()`
  (`src/engine/checkpoint.py`) — its exclusion is by omission, and adding it would break AC #3/#4's
  bit-identical/hash-stability guarantees.
- Do NOT edit `WorldIndexes`, `WorldIndexService`, or any of `CacheInvalidationPolicy`'s five existing
  spatial `if domain ==` branches — read-only precedent.
- Do NOT touch `src/domains/information/providers.py` or `src/engine/apply.py` beyond reading them for
  shape reference — investigation lists both as read-only reference areas.

## Dependency Map

- Step 1 (dataclass + state field) has no dependencies — first step.
- Step 2 (DirtySet `identity_entities` tag) is independent of Step 1; can be done in parallel/either
  order, but Step 4/7's incremental-invalidation tests depend on both Step 1 and Step 2 existing.
- Step 3 (CacheInvalidationPolicy domains) depends on Step 2 (needs `dirty.identity_entities` to
  exist) and conceptually on Step 1 (index domain names should match the dataclass shape), though it
  can be written before Step 4.
- Step 4 (`SemanticEntityIndexService.get_indexes`) depends on Steps 1 and 3.
- Step 5 (query methods) depends on Step 4.
- Step 6 (hash-exclusion test) depends on Step 1 only.
- Step 7 (incremental/rebuild bit-identity tests) depends on Steps 1-4.
- Step 8 (anti-drift guards) depends on Steps 1-5 existing (source to scan) but is otherwise
  independent test-only work.
- Step 9 (docs) depends on Steps 1-5 being implemented (describes final shape); can be done last.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1: `entity_index.by_role_class(role, class_id)` returns exactly the matching entity ID set, verified against naive linear-scan | Steps 1, 4, 5 | `test_by_role_class_matches_naive_scan` |
| AC #2: query methods return only `List[int]`/`Set[int]` entity IDs, never component objects | Step 5 | `test_query_methods_return_only_entity_ids_not_objects` |
| AC #3: after a tick where DirtySet captures a region_id/faction/role change, index reflects new value on next query without full rebuild, bit-identical to from-scratch rebuild | Steps 2, 3, 4, 7 | `test_index_reflects_dirty_set_change_without_full_rebuild`, `test_incremental_index_bit_identical_to_full_rebuild` |
| AC #4: deleting and rebuilding the index from AuthoritativeState produces identical query results to incrementally-maintained version, across all 5 dimensions | Steps 4, 7 | `test_delete_and_rebuild_index_matches_incremental_across_all_dimensions` |
| AC #5: ticket documents chosen lifecycle (lazy) and entity_needs field mapping, with rationale | This plan's Summary + investigation.md Recommendations 1/2 + Step 9 doc update | Reviewed at Finalize; `docs/engine/performance_contract.md` new subsection |

## Anti-Drift Notes

- The investigation's Recommendation 1 (lazy lifecycle) and Recommendation 2 (`entity_needs` =
  `BiologicalComponent`) are treated as settled inputs per the investigation's own "Risks and Open
  Questions" section — do not re-litigate without new evidence.
- The `"region_index"` phantom-field bug sits directly adjacent to Step 3's new region domain. Use a
  distinct string name (`"semantic_region_index"`, not `"region_index"`) to keep the two from ever
  being confused in a future diff or fix.
- `class_id` has no runtime update path today (confirmed by grep across `updates.py`/`state.py`/
  `apply.py`) — do not add one as part of building the `by_role_class` index; only `role` needs
  `identity_entities`-driven invalidation in practice, though the tag correctly fires on any
  `IdentityUpdate` including a hypothetical future `class_id_set`.
- `attribute_entities` must not be touched or reused for identity invalidation — `phase_graph.py:141`
  depends on its current, narrower meaning.
- `paid_information.py`, `military_conflict.py`, and any other consumer call site are read-only
  reference material for understanding `InformationProviderState`/scan shape — never edit targets in
  this ticket.
- The four `DirtySet`-construction sites in `dirty.py` (dataclass field, `from_update`, `merge`,
  `DirtyDependencyGraph.expand`) plus `pipeline.py`'s force-full-scan block, plus the
  `all_dirty_entities` union property (dirty.py:230-233, Step 2 sub-item 6) are **six** separate
  places that must all be updated together for Step 2 — missing any one silently drops the new
  `identity_entities` tag partway through the pipeline, or (specifically for the union property)
  leaves it tracked internally but invisible to every external consumer that reads
  `all_dirty_entities` instead of the field directly. `test_force_full_scan_dirty_set_completeness.py`
  is the specific regression test positioned to catch a missed `pipeline.py` update;
  `test_identity_only_update_appears_in_all_dirty_entities` (Step 2) is the specific regression test
  positioned to catch a missed union-property update.
- `DirtySet.all_dirty_entities` (dirty.py:230-233) is a hand-written union property, not something
  that follows automatically from adding a field to the `DirtySet` dataclass — this was the original
  architecture-review finding for this plan (an identity-only change was invisible to
  `validate_dirty_set`'s audit-mode leak check, `ReadModelCache`'s WS delta broadcast decision,
  `ApplyPlan`'s `invalidate_read_model` flag, `HardLawMonitor.check_entities`, and `CandidateSelector`'s
  `'all'` domain — five downstream consumers, all fixed by the single union-property edit in Step 2
  sub-item 6). Any future new `DirtySet` field must apply the same check: does it also need adding to
  `all_dirty_entities`, not just the dataclass and the four/five construction sites.
- `_build_needs_index`'s three per-field thresholds (Step 4) are individually sourced, not one shared
  constant: `hunger`=95.0 and `sleep_debt`=98.0 come from the Mechanics Bible's documented Penalty
  Thresholds (`docs/mechanics/01_entity_anatomy.md:76-77`); `rest_pressure`=70.0 has no Bible entry (the
  Bible's third pressure row, Stamina, is a distinct field with its own unrelated "Exhaustion
  Threshold") and instead reuses the value two existing live consumers
  (`perception.py:95`, `routine.py:49`) already use as their own forced-rest/urgency cutoff. Do not
  collapse these back into one shared magic number in implementation — the original architecture-review
  finding was specifically about an uncited, unsourced 70.0 applied uniformly to all three fields.
- Both risks investigation.md flagged as open (`CanonicalStateHasher` exclusion; DirtySet tag
  coverage for identity/role/faction changes) were resolved during planning by direct source reads —
  see Summary items 1-2, cited with `file:line` evidence. They are treated as settled inputs, not
  re-opened without new evidence. The investigation's one flagged "planner-level design choice, not
  blocked" item (combined `(role, class_id)` key vs. two separately-joined dimensions) is likewise
  resolved, in Step 1, in favor of a combined key — matching the ticket's own AC #1 query signature
  (`entity_index.by_role_class(role, class_id)`) literally.

## Deviations (recorded during Implement)

1. **Step 2's `identity_entities` fix had to cover two additional construction sites the plan text
   did not name: `DirtySetBuilder` (`src/core/dirty.py`) and `apply_plan.py`'s per-entity tag
   computation.** The plan enumerated "four places in `dirty.py`" (the `DirtySet` dataclass,
   `DirtySet.from_update`, `DirtySet.merge`, `DirtyDependencyGraph.expand`) plus `pipeline.py`'s
   force-full-scan block. Reading the actual call graph during implementation showed
   `DirtySet.from_update`/`merge` are **not** the path the live authoritative apply pipeline uses to
   build its per-tick `DirtySet`: `AuthoritativeApplyPipeline.refine()` (`src/engine/pipeline.py:57,
   261-262, 296-297, 314-315, 329-330, 352-353`) and `ApplyPath.apply_generation`
   (`src/engine/apply.py:234, 252-253, 262-263`) both build the real `DirtySet` via the separate
   `DirtySetBuilder` class (`mark_entity`/`mark_from_update`/`build()`), driven by string tags. In
   `apply_generation`'s case those tags come from `src/engine/apply_plan.py`'s
   `ApplyPlanBuilder.build_plan()` (lines 336-345), which inspects the `changes` dict
   `_compute_entity_changes` returns and appends a string tag per changed component — with no
   `"identity"` tag before this change, despite `changes["identity"]` already being populated
   correctly by `IdentityPatch.apply()` (`src/engine/patches.py:218-226`) whenever a role/faction
   change is present. Without extending `DirtySetBuilder.__init__`/`mark_entity`/`mark_from_update`/
   `build()` to carry an `identity` set, and without adding `if "identity" in changes:
   tags.append("identity")` to `apply_plan.py`, the new `identity_entities` tag would never be
   populated by the real authoritative apply path (`ApplyPath.apply_generation`, invoked from
   `Kernel._phase_advancement`) — only by the lower-level `DirtySet.from_update`/`merge` helpers,
   which are exercised directly by some tests but are not what production ticks call. This is the
   same "must fix every construction site or the tag silently reverts to empty" principle the plan
   itself already applied to `dirty.py`'s four sites plus `pipeline.py`; it was simply missed for
   `DirtySetBuilder`/`apply_plan.py` because the plan's source citations focused on
   `DirtySet.from_update` as if it were the sole production path. Files touched beyond the plan's
   explicit list: `src/engine/apply_plan.py` (one new line, additive, mirroring the existing
   `if "attributes" in changes: tags.append("attribute")` pattern). `src/engine/apply.py` itself was
   **not** touched — the existing generic `for e_id, tags in plan.dirty_tags_by_entity.items():
   dirty_builder.mark_entity(e_id, tags)` loop already forwards whatever tags `apply_plan.py`
   computes, so no change to `apply.py`'s control flow was needed, consistent with the plan's Scope
   Guard forbidding edits to `apply.py`.
   Verified by `tests/unit/domains/optimization/test_semantic_entity_index.py::
   test_identity_only_update_does_not_raise_dirty_set_leak_error`, which drives an identity-only
   `EntityUpdate` through the real `ApplyPath.apply_generation(..., audit_dirty_set=True)` path (not
   just `DirtySet.from_update` in isolation) and asserts no `DirtySetLeakError`.

2. **`CacheInvalidationPolicy.invalidated_indexes()`'s new `"semantic_region_index"` entry broke a
   pre-existing test's exact-cardinality assertion; the assertion, not the production code, was
   updated.** `tests/unit/domains/optimization/test_cache_invalidation_policy.py::
   test_region_dirty_invalidates_region_index` asserted `len(invalidated) == 1` for
   `DirtySet(region_ids={"north_woods"})`. Adding the plan-mandated, distinctly-named
   `"semantic_region_index"` domain (deliberately kept separate from the existing phantom
   `"region_index"` string per the plan's own instruction) means a region-dirty `DirtySet` now
   populates *two* entries in `invalidated_indexes()`'s output set, not one — both triggered by the
   same `dirty.region_ids` condition. The test's behavioral assertions
   (`should_invalidate("regions", dirty) is True`) are unchanged and still pass; only the literal
   `len(invalidated)` cardinality needed updating from `1` to `2`, with an added assertion that
   `"semantic_region_index"` is present and a new `should_invalidate("region", dirty) is True` check.
   This is a substance-preserving update to a stale cardinality assertion, not a gate-integrity
   workaround — the underlying `should_invalidate()` behavior for every pre-existing domain is
   unchanged, which the new `test_cache_invalidation_policy_unrelated_domains_unaffected` anti-drift
   guard (Step 3's Verify requirement) independently confirms.

3. **Known limitation, left undone per the plan's explicit Scope Guard, not silently dropped:**
   unlike `world_indexes`, `semantic_entity_indexes` is not carried forward across ticks in
   `ApplyPath.apply_generation`'s new-state construction (`src/engine/apply.py:406` carries
   `world_indexes=getattr(prior_state, "world_indexes", None)` but has no analogous line for the new
   field). This means that in real production ticks, the first `get_indexes()` query after tick
   advancement always sees `existing=None` and does a full 5-dimension rebuild rather than reusing
   the previous tick's cache with per-dimension partial invalidation — the partial-rebuild mechanism
   itself is fully implemented and tested (Step 4/7's tests construct the "previous tick's index"
   directly on the state object, the same way `tests/unit/domains/optimization/
   test_world_index_service.py`'s own precedent test does, bypassing `apply.py` entirely), but it
   only benefits repeated queries *within* the same tick until a follow-up ticket wires the
   cross-tick carry-forward. Not fixed here because `src/engine/apply.py` is explicitly listed in
   this plan's Scope Guards as a read-only reference file. Documented in
   `docs/engine/performance_contract.md`'s new "Semantic Entity Indexes" subsection under "Known
   limitation" so it is not lost.
