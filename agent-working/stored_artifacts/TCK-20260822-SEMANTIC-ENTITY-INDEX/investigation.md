---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260822-SEMANTIC-ENTITY-INDEX
artifact_type: investigation
tags: [engine, performance, determinism]
---

# Investigation — TCK-20260822-SEMANTIC-ENTITY-INDEX

## Note on Context Scan

`mcp__knowledge-search__search_docs` returned `{"error": "index not found", "action": "run make knowledge-index"}`
and `graphify query` failed with `error: graph file not found:
.claude/worktrees/hud-design-system-foundation-epic/graphify-out/graph.json`. The fallback
`python3 tools/knowledge_search.py query ... --top-k 5` also returned `knowledge index not found —
run make knowledge-index`. All three mandated semantic-search tools are unavailable in this
worktree (the index/graph artifacts were not built here). Per the ticket instructions this is
skipped silently and the investigation proceeds directly to source reads — but this is a real gap:
whoever runs Implement on this ticket should run `make knowledge-index` first if the tools remain
unavailable, since this investigation could not benefit from any indexed prior-art the raw
`tickets/done/`/`stored_artifacts/` scan below might have missed.

## Current Behavior

### WorldIndexService — the established lazy, pull-based lifecycle (`src/engine/world_index.py`)

- `WorldIndexService.get_indexes(state, dirty)` (lines 83–116) is the entire lifecycle: it is called
  lazily, from inside query methods (`SpatialQueryService.nearest_resource_node` etc.,
  `src/engine/spatial_query.py:14-16`), not from any kernel phase.
- On call: if `state.world_indexes` exists and `existing.tick == state.tick`, it is returned as-is
  (world_index.py:86-92) — a tick-scoped cache hit.
- Otherwise it rebuilds per-domain, but only for domains `CacheInvalidationPolicy.should_invalidate(domain, dirty)`
  says are dirty (world_index.py:94-99); domains not flagged dirty reuse the *existing* sub-index
  object rather than rebuilding it. This is a partial, per-dimension incremental rebuild, not a
  full rebuild every tick and not a per-mutation incremental update either — it is granularity at
  "rebuild this one dimension's index from scratch this tick" (`_build_resource_index` etc. are
  full re-scans of `state.resource_nodes`/`state.entities`/etc., world_index.py:119-161), just
  scoped by dirty domain rather than always running for every domain.
- The result is attached to state via `object.__setattr__(state, "world_indexes", new_indexes)`
  (world_index.py:111) — never through `StateUpdate`/`replace()`. This is a non-authoritative
  derived cache write, explicitly the pattern the ticket's Scope section requires
  (`object.__setattr__` following the `world_indexes`/`_node_map_cache` pattern).
- `CacheInvalidationPolicy.invalidated_indexes()` (world_index.py:17-33) maps `DirtySet` fields
  (`resource_node_ids`, `building_ids`, `movement_entities`/`lifecycle_entities`, `ground_item_ids`,
  `corpse_ids`, `region_ids`) to named index domains.

### Kernel phase-write reality — confirms the ticket's own correction (`src/engine/kernel.py`)

- `_phase_persistence()` (kernel.py:1060–1074) does **not** touch `self._state` at all. It only:
  computes `tick_hash` via `CanonicalStateHasher.get_hash(self._state)` when replay/audit conditions
  hold (line 1064), emits a `TICK_END` `TraceEvent` to the replay writer (lines 1066–1072), and calls
  `self._replay.on_tick_end(...)` (line 1074). No `object.__setattr__`, no field write, no state
  replacement of any kind occurs in this method.
- The actual state commit happens in `_phase_advancement()` (kernel.py:714–748):
  `self._state = ApplyPath.apply_generation(self._state, update, next_tick=..., ...)` (lines 726–734)
  is where `self._state` is reassigned to the new authoritative generation. Immediately after, this
  same method is where derived/runtime cache attributes are already being attached via
  `object.__setattr__` on the *new* state object — `object.__setattr__(self._state, "_opt_profile", ...)`
  and `object.__setattr__(self._state, "_force_full_scan", ...)` (kernel.py:741-742) — i.e. the
  established pattern for "stamp a non-authoritative extra onto the freshly-generated state" already
  lives in `_phase_advancement`, not `_phase_persistence`.
- **Conclusion**: the ticket's proposal doc (`docs/plans/idea_semantic_entity_index.md:94`, "Updates
  are applied in the `Persistence` phase, after the authoritative pipeline commits") describes a
  phase boundary that does not do what the doc assumes. There is no state-mutating hook inside
  `_phase_persistence` to attach to. If an eager-write lifecycle were chosen, the only structurally
  correct home is `_phase_advancement`, immediately after `ApplyPath.apply_generation` returns the
  new `self._state`, alongside the existing `_opt_profile`/`_force_full_scan` `object.__setattr__`
  calls — not a new "Persistence phase" hook that doesn't exist for state.

### Recommendation 1 — Lifecycle: follow WorldIndexService's lazy pull-based pattern, not an eager write

Evidence-based recommendation: **the new semantic entity index should follow `WorldIndexService`'s
existing lazy, pull-based, `CacheInvalidationPolicy`/`DirtySet`-driven lifecycle**, not a new eager
write.

Reasons:
1. It is the only lifecycle pattern with a real, working precedent in this codebase for exactly this
   kind of derived-projection-over-`AuthoritativeState`, attached the same way the ticket's own Scope
   section mandates (`object.__setattr__` following `world_indexes`/`_node_map_cache`).
2. The "eager write in Persistence phase" idea from `docs/plans/idea_semantic_entity_index.md` is not
   just undesirable but structurally unavailable as literally described — `_phase_persistence` performs
   zero state mutation today (confirmed above). Implementing it as originally proposed would require
   inventing a new state-mutating responsibility inside a phase whose entire current contract is
   "compute a hash and emit a trace event," which is itself a phase-boundary change the ticket's Out of
   Scope section explicitly forbids ("do not restructure `_phase_advancement`/`_phase_persistence` beyond
   what's needed to host the index write").
3. An eager write *could* structurally be added to `_phase_advancement` instead (next to the
   `_opt_profile`/`_force_full_scan` stamps) without restructuring phase boundaries — but doing so
   still means every tick pays a full 5-dimension index rebuild cost unconditionally, whereas the lazy
   pattern only pays the (per-dimension) rebuild cost on the first query after a tick where that
   dimension's backing data actually changed, and pays nothing at all on ticks where the index is never
   queried. Given the index's stated purpose (make strategic/governance-layer queries cheap, not make
   every tick heavier), this is a real, not just tidiness, argument for lazy.
4. AC #3 in the ticket ("After a tick where DirtySet captures a region_id/faction/role change, the
   index reflects the new value on next query without a full rebuild") is written in exactly
   `WorldIndexService`'s vocabulary ("without a full rebuild" == the partial-domain-rebuild behavior
   `get_indexes` already implements) — it reads as an acceptance criterion authored assuming the lazy
   pattern is the answer, not the eager one.

Concrete implication: `CacheInvalidationPolicy.invalidated_indexes()` needs three new domains added
(analogous to `active_resource_node_index`/`building_kind_index`/etc.): one keyed on
`(role, faction)`-relevant entity dirty tags (`strategic_entities`/`attribute_entities`/whatever tags
IdentityComponent changes route through — see Anti-Drift Hazards), one keyed on `region_ids`
(already exists as a DirtySet field, though note the existing phantom-field bug flagged below), and
one for the needs/knowledge dimensions (see Recommendation 2). A `SemanticEntityIndexes` frozen
dataclass parallel to `WorldIndexes`, and a `SemanticEntityIndexService` parallel to
`WorldIndexService`, is the structurally consistent shape.

### Recommendation 2 — `entity_needs` maps to `BiologicalComponent` fields, not an unshipped concept

Evidence:
- `BiologicalComponent` (`src/core/state.py:116-138`) is a shipped, durable, per-entity component with
  `sleep_debt`, `hunger`, `rest_pressure` (all `0.0`–`100.0` pressure scalars), `last_meal_tick`,
  `last_sleep_tick`, `well_rested_until`. This is real, queryable state on every entity today.
- `QuestOpportunityGenerator.from_entity_need(entity_id, need_kind, ticks_unsatisfied, tick)`
  (`src/domains/world_emergence/services.py:252-259`) — the function the idea doc's E23 use case
  ("Entities with unsatisfied needs for N ticks" → QuestOpportunityGenerator trigger) actually maps to
  — is a **stub**: `"""Stub — diplomatic_errand from long-unsatisfied entity need. Returns None until
  Phase 5."""` / `return None`. It is never called from any pipeline phase (repo-wide grep for
  `from_entity_need` finds only its own definition and its unit test,
  `tests/unit/quest/test_quest_generation.py:226`, which exercises the stub's `None` return, not real
  behavior). There is no per-entity `need_kind` enum, no durable "ticks unsatisfied per need kind"
  tracker anywhere in `src/core/state.py` or `src/domains/world_emergence/`.
- `InformationNeedDetector` (`src/engine/domain/cognition_extras.py:36-98`) is a real, shipped
  mechanism, but it is not a per-entity "needs" state — it is a pure function that scans
  `entity.self_model.knowledge.unknowns` (`UnknownFact.priority`/`seeking_project_id`) and returns a
  `StrategicUpdate` that creates an `INFORMATION_SEEKING` `ProjectState`. Its durable trace is the
  presence of an active `INFORMATION_SEEKING` project on `entity.strategic.projects` — which is exactly
  what `paid_information.py`'s own O(N) scan (`src/engine/pipeline_phases/paid_information.py:92-101`)
  already walks to find "seekers." That is the natural backing data for the **`knowledge_domain`**
  dimension (which entities are seeking / which providers serve which domains — see below), not for
  `entity_needs`.

Recommendation: **`entity_needs` maps to `BiologicalComponent` thresholds** (e.g., `hunger` /
`sleep_debt` / `rest_pressure` crossing a configurable threshold, mirroring how `HardLawMonitor` or
`AI goals/scorers.py`'s `SleepScorer`/`EatScorer` already read these same fields for urgency scoring).
This is exactly what the ticket's own Out of Scope line already anticipates and forecloses the
alternative for: *"Building an InformationNeed-style concept if entity_needs is resolved to mean
BiologicalComponent fields only — do not speculatively build unshipped structures."* Building against
`QuestOpportunityGenerator.from_entity_need`'s `need_kind`/`ticks_unsatisfied` stub would require
inventing the very unshipped `need_kind` taxonomy and durable "ticks unsatisfied" tracker that stub
exists to gesture at but that Phase 5 has not built — out of scope here per the ticket's own text.

`knowledge_domain` maps to `AuthoritativeState.information_providers: Dict[int, InformationProviderState]`
(`src/core/state.py:1154`; `InformationProviderState.knowledge_domains: Tuple[str, ...]`,
`src/domains/information/providers.py:37-58`) — index provider entity IDs by each domain string in
their `knowledge_domains` tuple. This is real, shipped, durable state (registered by E42B) and is the
literal backing data the idea doc's E42 use case ("route InformationNeeds to providers") describes.

### `role`/`class_id`/`faction`/`region_id` — all shipped, durable, per-entity fields

- `IdentityComponent` (`src/core/state.py:471-500`): `role: int = 0` (EntityRole enum),
  `faction: int = 0` (Faction enum), `class_id: str = "NOVICE"` — all durable, all present on every
  entity today (`object.__setattr__(res, "role", id_comp.role)` etc. at apply.py:512-521 show these
  are carried through `ApplyPath`'s canonical-state construction unchanged).
- `NavigationComponent.region_id: Optional[str] = None` (`src/core/state.py:376-377`, comment: "Phase 3
  Hardening: Cache region_id to avoid O(N) scans") — already an explicit prior optimization of the same
  shape this ticket is doing at a different granularity; a real precedent that per-entity `region_id`
  caching is an accepted pattern here.

### Consumer call sites this ticket's Out-of-Scope defers, but which motivate the dimensions

- `src/engine/pipeline_phases/paid_information.py:88-101`: `for entity in sorted(state.entities.values(), key=lambda e: e.id): ... for proj in entity.strategic.projects.values(): if proj.kind == INFORMATION_SEEKING ...` then `for pid in sorted(providers.keys()): ...` — an O(N) then O(M) nested scan, sorted for determinism, exactly as `docs/plans/idea_semantic_entity_index.md`'s status-review note describes. Confirmed unconditional (no `scan_policy`/`DirtySet` gating anywhere in this file). Retrofitting this call site is explicitly out of scope for this ticket (`TCK-20260822-PAID-INFO-INDEX-RETROFIT`).

## Mechanics / Engine Constraints

- `docs/engine/performance_contract.md` §"Optimization MUST NOT change the semantic outcome..." (line
  55): any optimization that changes `AuthoritativeState`'s hash vs. a baseline is a failure. The index
  must be provably derivable/rebuildable to bit-identical query results from `AuthoritativeState` alone
  (AC #4 already encodes this) and must never itself be hashed as part of authoritative state (it must
  stay off the `CanonicalStateHasher` path the way `world_indexes` already is — verify this at
  implementation time by confirming `to_canonical_dict()` on `AuthoritativeState` does not serialize
  `world_indexes`/derived caches; not confirmed in this investigation pass, flagged as a risk below).
- §7 (`scan_policy`: `FULL`/`THROTTLED`/`EXACT_DIRTY` governed by `DirtySet`, line 79) is the
  engine-wide precedent for "bypass O(N) scans under pressure using `DirtySet`" — this is the same
  family of mechanism `CacheInvalidationPolicy` already implements for `WorldIndexService`, and the new
  index should extend that same family, not invent a parallel one.
- Determinism: query methods must return only `List[int]`/`Set[int]` entity IDs (AC #2), matching the
  existing `WorldIndexes` pattern (`Dict[str, Tuple[int,...]]`, tuples not lists, for deterministic
  ordering) and `CandidateSelector.entities()`'s own `tuple(sorted(...))` return convention
  (`src/core/dirty.py:503,506`). Any new index's internal storage should use tuples/frozensets with
  sorted iteration at the query boundary, following that convention.

## Docs Requiring Update

- `docs/engine/performance_contract.md`: this ticket adds a new derived-index mechanism (semantic
  entity index over role/class/region/faction/needs/knowledge dimensions) parallel to the existing
  spatial `WorldIndexService`/`CacheInvalidationPolicy` machinery this doc already documents (§7
  scan_policy/DirtySet, and the general "optimization must not change semantic outcome" law at line
  55) — the doc needs a new subsection describing the semantic index's lifecycle (lazy,
  `CacheInvalidationPolicy`-driven, per this investigation's Recommendation 1) so the contract stays
  the authoritative description of how derived read models over `AuthoritativeState` are allowed to
  work.

The `docs/plans/idea_semantic_entity_index.md` doc (path: `docs/plans/idea_semantic_entity_index.md`)
is not a "must update to reflect new implemented behavior" doc in the Format-1 sense — it is a
`maturity: idea` planning doc, already carries an extensive 2026-08-22 status-review correction block
at its top, and its role once this ticket ships is to be graduated/retired rather than edited to match
final behavior; that transition (marking it superseded, or moving it out of `docs/plans/`) is better
handled as part of this ticket's Finalize/close step once the actual implementation is known, not
speculatively written into this investigation. Flagging it here so Finalize does not forget it, without
listing it as a machine-parsed doc-to-update bullet since its required edit (a "superseded by
TCK-20260822-SEMANTIC-ENTITY-INDEX" marker, not new technical content) will not itself be `git status`
observable in the same way a technical doc update is unless planner explicitly schedules it.

No `docs/mechanics/` chapter needs updating: this ticket is a performance-layer, non-authoritative,
derived-projection change (Mechanics Bible chapters document simulation *laws*, not read-model
implementation details) — it changes no formula, no entity attribute, no combat/economic/strategic
law. `docs/mechanics/01_entity_anatomy.md` (which documents `role`/`class_id`/biological pressures as
concepts) is not required to change either: it documents what these fields *mean*, and this ticket
does not alter their meaning, only adds a faster way to query entities grouped by their existing
values.

## Parity Ledger Overlap

No `docs/parity_ledger/*.yaml` entry currently references `WorldIndexService`, `SpatialQueryService`,
`world_index.py`, or a semantic/entity index by name or by `PERF-0xx` Logic ID (repo-wide grep across
`docs/parity_ledger/*.yaml` for `PERF-007`/`PERF-010`/`PERF-011`/`spatial_query`/`CacheInvalidationPolicy`
returns zero hits). The closest adjacent entries are in `docs/parity_ledger/strategic_cognition.yaml`
around the `information_providers_update`/`LeadContradictionSystem` entry (~line 2608-2625,
`v2_evidence` cites `src/core/updates.py — StateUpdate.information_providers_update field`), which
covers *how* provider reliability degrades on failed leads — a related but distinct concern from this
ticket's read-side indexing of `information_providers` by `knowledge_domains`.

Since this ticket is a purely non-authoritative, derived, always-rebuildable read-model addition (no
behavior/formula change to any authoritative mutation path), it does not itself require a new parity
ledger entry under the "when a behavior changes, update the parity ledger" rule — there is no
behavior change to a simulation law here. If planner/implementer choose to add a `P2` entry anyway for
traceability of the new `SemanticEntityIndexService` mechanism (mirroring how `WorldIndexService` itself
does *not* have a dedicated parity ledger entry today — confirmed by the same zero-hit grep), that is
a reasonable optional addition but not a required one; no P0 entries are touched.

## Prior Work

- **`TCK-20260517-WORLD-INDEX-SERVICE`** (`tickets/done/`, `stored_artifacts/TCK-20260517-WORLD-INDEX-SERVICE/`):
  direct precedent. Its investigation.md documents the exact same problem shape (ad-hoc caches attached
  via `object.__setattr__` by AI scorers) and proposes exactly the lazy `WorldIndexes`/
  `CacheInvalidationPolicy`/`WorldIndexService` pattern now implemented in `src/engine/world_index.py`.
  This ticket's semantic entity index is the same design pattern applied to five new dimensions
  (role/class, region, faction, needs, knowledge) instead of spatial ones. Its `test_plan.md`
  (`tests/unit/domains/optimization/test_world_index_service.py`, `test_cache_invalidation_policy.py`)
  is the direct template to mirror for this ticket's own test files.
- **`TCK-20260517-STATIC-DIRTYSET-GUARD`** (`tickets/done/`): established
  `tests/static/test_no_direct_dirtyset_candidate_selection.py`, which forbids `.dirty_set`/`dirty_set.`
  substring usage inside `src/engine/pipeline_phases/`, `src/systems/`, `src/ai/` outside
  `CandidateSelector`/`src/core/dirty.py` helpers. The new semantic index's query layer must not
  introduce direct `DirtySet` field access from those directories either — it should route through
  `CacheInvalidationPolicy`-style helpers the same way `WorldIndexService` does (which lives in
  `src/engine/world_index.py`, outside the three guarded directories, same as the semantic index would
  if placed alongside it).
- **`TCK-20260518-READ-MODEL-CACHE`** (`tickets/done/`): a separate non-authoritative read-model caching
  ticket (API/presentation-layer `ReadModelCache`, distinct subsystem from `WorldIndexService`) — not
  directly reusable code, but confirms the "non-authoritative derived cache, rebuildable from
  authoritative state, never bypasses the authoritative path" pattern is a recurring, sanctioned shape
  in this codebase across multiple layers (engine-internal spatial index, engine-internal semantic
  index now, and API read-model cache).
- The `docs/plans/idea_semantic_entity_index.md` doc's own 2026-08-22 status-review block (already
  read in full above) already did most of the "is this still relevant" legwork and reached the same
  conclusions this investigation independently re-verified from source: E42/E53 shipped without the
  `ProviderLocator`/`TerritorialObserver` seams, the O(N)/O(N×M) scan is live and unconditional at
  `paid_information.py:92,112`, and `scan_policy`/`DirtySet` do not currently gate that call site.

## Risks and Open Questions

- **Both ticket-flagged open questions are now resolved by this investigation** (lifecycle → lazy
  `WorldIndexService`-style; `entity_needs` → `BiologicalComponent` fields), per Recommendations 1 and 2
  above. Planner should treat these as settled inputs, not re-open them without new evidence.
- **Open, not resolved here**: whether `role`+`class_id` should be one combined dimension key
  (`(role, class_id)` tuple, matching the idea doc's `by_role_class(role, class_id)` query signature) or
  two separate indexable dimensions that get joined at query time. `IdentityComponent` stores both as
  independent scalar fields (`state.py:473,482`), so either is buildable; this is a planner-level design
  choice, not a blocked question — flagging so planner makes it explicitly rather than by accident.
- **Open, not resolved here**: which `DirtySet` tag(s) should invalidate the role/class/faction
  dimension. `DirtySetBuilder`/`DirtySet.from_update` (`src/core/dirty.py`) has no dedicated
  "identity_entities" or "role_entities" tag — role/faction/class_id changes would currently need to be
  inferred from some existing tag (most plausibly `attribute_entities`, since `e_upd.attributes` is the
  closest existing tag to "identity-shaped" changes, or a new tag would need to be added to `DirtySet`
  itself). Confirm at implementation time whether any current call site actually mutates
  `role`/`faction`/`class_id` via `EntityUpdate`, and via which `EntityUpdate` field, before choosing
  the invalidation tag — this investigation did not trace every caller that could mutate identity
  fields.
- **Risk**: whether `world_indexes` (and by extension any new `semantic_entity_indexes` attached the
  same way) is excluded from `CanonicalStateHasher.get_hash()`/`AuthoritativeState.to_canonical_dict()`
  was asserted above as a requirement but not directly verified by reading
  `CanonicalStateHasher`/`to_canonical_dict()` in this pass — implementer/planner must confirm this
  before relying on the "index writes never affect the state hash" property AC #4's bit-identical
  rebuild requirement implicitly depends on.
- **Known adjacent bug, explicitly not to fix here** (already flagged in
  `docs/plans/idea_semantic_entity_index.md`'s status-review block and re-confirmed structurally
  plausible from reading `world_index.py:17-33` + `:83-116`): `CacheInvalidationPolicy.invalidated_indexes()`
  adds `"region_index"` to its output whenever `dirty.region_ids` is populated, and
  `should_invalidate("regions", ...)` checks for that key, but `WorldIndexes` has no `region_index`
  field and `WorldIndexService.get_indexes()` never calls `should_invalidate("regions", ...)` — dead/
  phantom code. Do not let this ticket's new region-dimension work get tangled with fixing that
  pre-existing bug; they are adjacent but separate (tracked for a future ticket per the idea doc).

## Anti-Drift Hazards

- **Scope creep into consumer retrofits**: `paid_information.py` and faction/military code are the
  obvious "let's just wire it up while we're here" targets — explicitly out of scope
  (`TCK-20260822-PAID-INFO-INDEX-RETROFIT`, `TCK-20260822-GUARD-SCAN-INDEX-RETROFIT`). This ticket
  builds and tests the index in isolation; it does not touch any existing O(N) scan call site.
  `Related Code Areas` lists `src/domains/information/providers.py` and `src/engine/apply.py` — those
  should be read-only references for this ticket (to model `InformationProviderState`/`IdentityComponent`
  shape), not edit targets.
- **Scope creep into building the unshipped `InformationNeed`/`need_kind` concept**: the ticket's Out of
  Scope line already forecloses this; Recommendation 2 above is the evidence backing that foreclosure —
  do not let "but wouldn't `entity_needs` be more useful if it also covered X" resurrect the stub.
- **Scope creep into fixing the phantom `region_index` bug** in `CacheInvalidationPolicy` — tempting
  because the new region dimension sits right next to it, but it is a pre-existing, independently
  tracked issue.
- **Scope creep into restructuring Kernel phases** — the ticket's Out of Scope line already forecloses
  rewriting `_phase_advancement`/`_phase_persistence` boundaries; Recommendation 1 above means no phase
  restructuring is needed at all (the lazy pattern requires no kernel phase hook whatsoever, since
  `WorldIndexService` itself has none — it's called from query sites, not from any kernel phase).
- **Returning live objects instead of IDs**: AC #2's static/type test
  (mirroring `tests/static/test_no_direct_dirtyset_candidate_selection.py`'s file-scan-for-forbidden-pattern
  shape) must actually catch a query method that returns `EntityState`/component objects instead of
  `int`/`Set[int]`/`List[int]` — easy to accidentally violate by, e.g., returning
  `Dict[str, EntityState]` instead of `Dict[str, Tuple[int,...]]` the way `WorldIndexes.buildings_by_kind`
  correctly returns IDs, not `BuildingState` objects (world_index.py:71).
