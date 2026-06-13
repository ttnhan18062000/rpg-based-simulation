# Investigation — TCK-20260613-DOC-ENGINE-RUNTIME-DETAILS

Ticket: TCK-20260613-DOC-ENGINE-RUNTIME-DETAILS
Date: 2026-06-13
Investigator: agent

---

## Topic 1: State Update Compaction

### Source files read
- `src/core/updates.py` — `StateUpdate`, `EntityUpdate`, all sub-intent types, `merge_many()`, `compact()`
- `src/engine/compactor.py` — `StateUpdateCompactor`, `CompactionMetrics`
- `src/engine/pipeline.py` — `AuthoritativeApplyPipeline.refine()` (pipeline entry point)
- `docs/core/update_intents.md` — existing merge semantics doc

### What compaction actually is (two-layer system)

There are **two distinct compaction operations** that must both be documented:

**Layer 1 — `StateUpdate.merge_many()` (updates.py:884):**
Merges N `StateUpdate` fragments from concurrent workers into a single `StateUpdate` in one pass (Logic ID: TOWN-204). This is not strictly compaction — it is aggregation — but it is the prerequisite. Per-entity bundles are merged by calling `EntityUpdate.merge()` per entity ID. Per-world records are merged similarly. Sets are unioned. Single-value fields use last-write-wins.

**Layer 2 — `StateUpdateCompactor.compact_with_metrics()` (compactor.py:37):**
This is the true compaction step, called at the very start of `AuthoritativeApplyPipeline.refine()` (pipeline.py:96) — Phase 1 of the 17-phase pipeline, labelled "Trust & Validity". It operates **before** any pipeline phase runs. It:
1. Drops entity updates where `EntityUpdate.is_noop()` is True (zero-effect removal)
2. Prunes top-level set fields that match current entity state (kind_set, active, new_position)
3. Prunes redundant `property_updates` entries matching current entity values
4. Prunes no-op sub-components by calling `is_noop()` on each of the 16 sub-intent types
5. Under `AGGRESSIVE` compaction level (Milestone 17 Law): additionally strips cosmetic properties (cosmetic_fx, chat_bubble, last_animation) and tiny stamina deltas (abs < 0.1)
6. Returns `CompactionMetrics` with raw/compacted entity update counts, property_prunings, subcomponent_prunings

There is also a lighter `StateUpdate.compact()` method (updates.py:1038) that only strips is_noop entity updates without the state-comparison pruning. This is used in some sub-contexts.

### Merge rules per field type

Three rules, confirmed exactly in source:
- **Delta sum**: All numeric delta fields — `hp_delta`, `readiness_delta`, `age_delta`, `sleep_debt_delta`, `evolution_points_delta`, `trust_delta[k]`, `trauma_delta`, `resource_updates[k]`, etc.
- **Set last-write-wins**: Optional override fields — `alive_set`, `movement_mode_set`, `reputation_set`, `death_tick_set`, `current_project_id_set`, `weather_set`, `hazard_level_set`, etc. Pattern: `other.field if other.field is not None else self.field`
- **List concatenation**: All list fields — `simultaneous_intents`, `resource_transfers`, `wounds_add`, `bond_updates`, `entities_add`, `modifiers_add`, etc. Some lists use set-dedup before concatenation (e.g., `recipes_learned`, `traits_add` use `list(set(...))` to avoid duplicates).

### "Fingerprint equivalence invariant"

The phrase "fingerprint equivalence" is confirmed in `tests/perf/test_apply_compaction_perf.py:76`:
```python
assert raw_state.fingerprint() == compacted_state.fingerprint()
```
This asserts that applying a raw `StateUpdate` (with redundant no-ops) produces the same `AuthoritativeState.fingerprint()` as applying the compacted version. The fingerprint is the `state_hash` field from `AuthoritativeState.fingerprint()` (which delegates to `CanonicalStateHasher.get_hash()` — a SHA-256 of canonical sorted JSON). The invariant is: **compaction never changes what the apply path commits**; it only reduces the work done to get there.

### Pipeline position

Compaction runs as the very first operation inside `AuthoritativeApplyPipeline.refine()` (pipeline.py:96), before any of the 17 pipeline phases execute. It is called with the raw merged `StateUpdate` produced by the kernel's resolution sort. This is critical: downstream phases see only already-compacted updates.

### Forbidden operations during compaction

Compaction is a pure filter — `StateUpdateCompactor` accesses `state.entities` (read-only) and `update.entity_updates` (read-only). It has no IO, no side effects, and no external calls. It may not produce new update content.

### What update_intents.md already covers

`docs/core/update_intents.md` already documents: the three merge rules, `merge_many()`, `StateUpdate.compact()`, and the intent lifecycle. The new compaction doc must cross-link to it and NOT duplicate the merge rule tables. It should focus on the `StateUpdateCompactor` (the richer compaction layer) and the fingerprint invariant, which update_intents.md does not cover.

---

## Topic 2: Candidate Selection

### Source files read
- `src/engine/candidate_selector.py` — `MovementCandidateSelector`
- `src/core/dirty.py` — `CandidateSelector`, `get_relevant_entity_ids()`, domain routing table
- `docs/core/dirty_state_and_dependency.md` — existing doc covering dirty-set routing

### Finding: two distinct "candidate selection" mechanisms

The ticket's concept of "candidate selection" refers to two entirely separate mechanisms:

**Mechanism A — Domain-based entity routing via `CandidateSelector` (dirty.py):**
This is the primary candidate selection mechanism used by pipeline phases. It takes a set of domain names, unions the corresponding `DirtySet` entity sets, filters to active entities, and returns a sorted `tuple[int, ...]`. The 15 domain routing mappings confirmed in source:

| Domain string | DirtySet fields read |
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
| `interactions` | `movement_entities ∪ strategic_entities` |
| `groups` | `movement_entities ∪ combat_entities ∪ social_entities` |
| `shop` | `movement_entities ∪ inventory_entities` |
| `capacity` | `strategic_entities` |
| `redirection` | `strategic_entities` |
| `all` | `all_dirty_entities` (union of 8 entity sets) |

Any unknown domain string falls back to all entity IDs in `state.entities`.

This mechanism is already fully documented in `docs/core/dirty_state_and_dependency.md`. The new `candidate_selection.md` must cross-link to it rather than duplicate it.

**Mechanism B — `MovementCandidateSelector` (candidate_selector.py):**
This is the movement-specific candidate sub-selector used within the movement phase. It implements a richer 6-stage filter pipeline beyond dirty-set routing:

1. **Liveness filter**: skip entities where `entity is None` or `not entity.lifecycle.active` or `not entity.combat.alive`
2. **Already-moved guard**: skip if `ent_upd.moved_this_tick` is True (prevents double-movement in same tick)
3. **Target validity**: skip if `nav_target is None` or `entity.navigation.position == nav_target` (already at destination)
4. **Force-full-scan bypass**: if `update.force_full_scan`, classify as urgent and skip remaining checks
5. **Urgency classification** (any one trigger → `urgent_selected`):
   - Target changed in current update (`ent_upd.navigation.target_set is not None`)
   - Entity in `dirty_set.movement_entities`
   - Current tile is statically blocked (WALL, blocked_tiles, building tile)
   - Interaction requires movement (entity has active interaction or `target_node_id`)
   - Strategic project requires movement (entity has `current_project_id`)
6. **Scan-policy gating for non-urgent candidates**:
   - `ScanPolicy.EXACT_DIRTY`: skip all non-urgent (heavy degradation mode)
   - Otherwise: check `combat.readiness >= move_cost` (readiness gating)
   - `MovementMode.WANDER`: apply tick modulo throttle (modulo 6 under THROTTLED, modulo 3 otherwise)

**Budget enforcement**: after both urgent and normal sets are populated, budget is enforced by keeping all urgent candidates and trimming normal candidates. Final set is `sorted()` for deterministic ordering.

**Deduplication**: urgent and normal are disjoint sets; an entity is classified as urgent or normal but not both.

**Ordering guarantee**: return type is `tuple(sorted(final_set))` — always ascending entity ID order.

### Scheduler-level selection (upstream)

Before any pipeline-level candidate selection, `DeterministicScheduler.select_work()` (scheduler.py) selects which entities produce `WorkItem`s in the Collection phase. It filters by: `ent.lifecycle.active`, `ent.combat.readiness >= 100.0`, LOD gating (if enabled), and strategic cadence (`should_run(tick, ent.id, cadence)`). Results are sorted for determinism. This is the "tick-level" selection; the dirty-set routing and `MovementCandidateSelector` are the "phase-level" selection within resolution.

### What dirty_state_and_dependency.md already covers

All domain routing (the 15-entry table), `CandidateSelector.entities()`, `get_relevant_entity_ids()`, and `get_relevant_group_ids()` are fully documented in `docs/core/dirty_state_and_dependency.md`. The new `candidate_selection.md` should focus on: the full selection pipeline concept (tick-level → dirty-set routing → movement-specific sub-selection), the `MovementCandidateSelector` 6-stage filter, budget enforcement, urgency classification, and the skip/defer mechanics. It should cross-link to `dirty_state_and_dependency.md` for domain routing details.

---

## Topic 3: Deterministic Execution

### Source files read
- `src/engine/kernel.py` — 6-phase loop, result sort, audit_mode fingerprinting, `_guard_stability()`
- `src/platform/rng.py` — `DeterministicRNG`, domain separation, `get_float()`/`get_int()` stateless API
- `src/engine/checkpoint.py` — `CanonicalStateHasher`, SHA-256 fingerprint, sorted canonical JSON
- `src/engine/replay_manager.py` — replay emission on REFINED_UPDATE and TICK_END events
- `tests/perf/test_dirty_parity.py` — dirty-set optimized vs force_full_scan parity test
- `tests/perf/test_concurrency_parity.py` — sequential vs concurrent parity test
- `docs/engine/known_limitations.md` — documented non-determinism scope (concurrent worker parity caveat)
- `docs/engine/kernel.md` — existing kernel doc

### Core guarantee and scope

Guarantee (confirmed from kernel.py `_guard_stability()`, `CanonicalStateHasher`, and test assertions):
> Same world seed + same initial `AuthoritativeState` + same `RuntimeProfile` → identical `AuthoritativeState` after each tick, as measured by `CanonicalStateHasher.get_hash()`.

**In scope**: entity decisions (worker outputs), resource transfers, combat outcomes, world evolution, movement, governance transitions, lifecycle events.

**Explicitly NOT in scope** (from known_limitations.md:28 and inference):
- Wall-clock time (Kernel uses `time.perf_counter_ns()` for phase cost measurement only — not for simulation logic)
- Log message ordering and telemetry event ordering (EventExtractor, observability layer)
- Worker thread scheduling order in concurrent mode — known_limitations.md:28 states "bit-identical parity vs original src is only officially ratified for the Sequential execution mode"
- Run IDs and artifact filenames (use `random.randint` on init — not seeded from world seed)

### Rules that maintain determinism

**Rule 1 — No stateful RNG in hot paths:**
`DeterministicRNG.get_float(domain, tick, entity_id, sub_id)` and `get_int(domain, tick, entity_id, a, b, sub_id)` are stateless: they compute a composite seed `base_seed ^ (domain.value << 48) ^ (tick << 32) ^ (entity_id << 16) ^ sub_id` and construct a fresh `random.Random(seed)` per call. This means a draw is order-independent — calling it for entity 42 at tick 5 always returns the same value regardless of what other entities drew before it.

The deprecated `next_float()` / `next_int()` methods use a stateful per-domain RNG stream and are forbidden in concurrent contexts (clearly marked DEPRECATED in source).

Domain separation: each `Domain` enum value XOR-shifts the base seed into a distinct space. SPAWN draws never collide with COMBAT draws even with the same base seed.

**Rule 2 — Result sort before resolution:**
`kernel.py:449`: `self._final_results.sort(key=lambda r: (r.class_priority, -r.local_priority, r.entity_id))`. Worker results (produced concurrently) are sorted by class priority, then descending local priority, then ascending entity_id before the resolution pass. This collapses non-deterministic worker completion order into a deterministic processing sequence.

**Rule 3 — Canonical state hash uses sorted key iteration:**
`CanonicalStateHasher.to_canonical_data()` explicitly sorts all dict keys (`sorted(state.entities.keys())`, `sorted(state.regions.items())`, etc.) and calls `json.dumps(data, sort_keys=True)`. No dict iteration order is assumed.

**Rule 4 — Authoritative state is frozen / immutable:**
`AuthoritativeState` is a frozen dataclass. Workers receive `state.readonly_view()` which wraps collections in `ReadOnlyDict`. No worker can mutate state during the Collection phase. The `_guard_stability()` method in audit_mode re-fingerprints the state after Scheduling and Collection and raises `ProtocolViolationError` on any hash change.

**Rule 5 — Entity ordering in candidate sets is always sorted:**
Both `CandidateSelector.entities()` and `MovementCandidateSelector.select()` return `tuple(sorted(...))`. No `set` iteration is used as the final ordering step.

**Rule 6 — DirtySet modifiers_add deduplication is sorted:**
`WorldUpdate.merge()` (updates.py:773): `modifiers_add=list(set(self.modifiers_add + other.modifiers_add))`. This uses `set()` for dedup — but the result feeds into the apply path, not into a sort-dependent operation.

### How divergence is diagnosed

In `audit_mode=True`:
- `_guard_stability()` fires `ProtocolViolationError` immediately when state hash changes during a non-mutating phase (Scheduling or Collection). The error message includes the expected and actual hash, and the phase name.
- `audit_dirty_set=True` activates `AuthoritativeState.validate_dirty_set()` post-apply, which fires `DirtySetLeakError` on undeclared mutations.

For replay divergence (comparing two runs):
- Each tick emits a `TICK_END` TraceEvent containing `tick_hash` (from `CanonicalStateHasher.get_hash()`) to the replay buffer.
- Divergence is detected by comparing tick hashes between two replay traces. The first tick where hashes differ is the divergence point.
- The `REFINED_UPDATE` replay event (emitted just before advancement) includes the full `refined_update` and pre-apply fingerprint, enabling per-field diffing.

### What kernel.md already covers

`docs/engine/kernel.md` covers: the 6-phase sequence, Law of Ticks (deterministic entity order), the Stability Guard (fingerprinting in audit_mode), Hard Law Compliance Guard, and result sort note ("sorted by ID"). The new `deterministic_execution.md` should cover what kernel.md omits: the RNG model (domain separation, stateless vs stateful API), the `CanonicalStateHasher` (how the hash is computed and what it covers), the exact forbidden operations, how to diagnose divergence, the sequential-only parity caveat, and extension rules. Cross-link to kernel.md rather than re-explaining the 6-phase loop.
