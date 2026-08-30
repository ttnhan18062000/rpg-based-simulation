---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260822-SEMANTIC-ENTITY-INDEX
artifact_type: test_plan
tags: [engine, performance, determinism]
---

# Test Plan — TCK-20260822-SEMANTIC-ENTITY-INDEX

## Regression Surface

Existing tests that must keep passing (nothing in this ticket's scope should change their behavior —
`WorldIndexService`/`CacheInvalidationPolicy` are read-only precedent, not edit targets):

**unit — world index / spatial query (direct precedent, same file family as any new
`SemanticEntityIndexService`)**
- `tests/unit/domains/optimization/test_world_index_service.py`
- `tests/unit/domains/optimization/test_cache_invalidation_policy.py`
- `tests/unit/perf/test_phase10_cache_invalidation.py`

**static — DirtySet access guard (the new index's query layer must not violate this)**
- `tests/static/test_no_direct_dirtyset_candidate_selection.py`

**unit — DirtySet construction/expansion (if a new DirtySet tag is added for identity/needs
invalidation, this suite is the regression surface for that change)**
- any `tests/unit/**/test_dirty*.py` / `tests/unit/**/test_*dirtyset*.py` covering
  `DirtySetBuilder`, `DirtySet.from_update`, `DirtyDependencyGraph.expand` (locate via
  `pytest --collect-only -q tests/unit -k "dirty"` at implementation time — not enumerated by
  filename here since none was directly read in this investigation pass)

**unit — information providers / cognition (backing data for `knowledge_domain` dimension; must not
regress if this ticket reads `information_providers`/`InformationNeedDetector` read-only)**
- `tests/unit/cognition/test_information_seeking.py`

**integration — force-full-scan / dirty-set completeness (adjacent DirtySet-consumer regression
surface; catches any change that silently breaks full-scan fallback)**
- `tests/integration/optimization/test_force_full_scan_dirty_set_completeness.py`

**quest generation stub (must keep returning `None` — this ticket does not implement `from_entity_need`)**
- `tests/unit/quest/test_quest_generation.py`

## New Tests Required

Per acceptance criteria (`tickets/inprogress/TCK-20260822-SEMANTIC-ENTITY-INDEX.md`):

1. **`test_by_role_class_matches_naive_scan`**
   - Category: unit
   - Verifies: `entity_index.by_role_class(role, class_id)` returns exactly the entity ID set matching
     a naive linear scan over `state.entities` filtering on `entity.identity.role`/`entity.identity.class_id`
     (AC #1). Parametrize over multiple role/class_id combinations, including one with zero matches.
   - Location: `tests/unit/domains/optimization/test_semantic_entity_index.py`

2. **`test_by_region_matches_naive_scan`**, **`test_by_faction_matches_naive_scan`**
   - Category: unit
   - Verifies: same naive-scan-parity pattern as #1 for the `region_id` (via
     `entity.navigation.region_id`) and `faction` (via `entity.identity.faction`) dimensions.
   - Location: `tests/unit/domains/optimization/test_semantic_entity_index.py`

3. **`test_by_entity_needs_matches_naive_scan_against_biological_thresholds`**
   - Category: unit
   - Verifies: the `entity_needs` dimension (resolved by this investigation to mean
     `BiologicalComponent` field thresholds — `hunger`/`sleep_debt`/`rest_pressure`) matches a naive
     scan applying the same threshold to `entity.biological`. Must explicitly assert the index does
     NOT reference `QuestOpportunityGenerator.from_entity_need`'s `need_kind` stub concept (regression
     guard against accidentally building the out-of-scope unshipped structure).
   - Location: `tests/unit/domains/optimization/test_semantic_entity_index.py`

4. **`test_by_knowledge_domain_matches_naive_scan`**
   - Category: unit
   - Verifies: the `knowledge_domain` dimension indexes `state.information_providers` entity IDs by
     each string in `InformationProviderState.knowledge_domains`, matching a naive scan over
     `state.information_providers.items()`.
   - Location: `tests/unit/domains/optimization/test_semantic_entity_index.py`

5. **`test_query_methods_return_only_entity_ids_not_objects`**
   - Category: architecture guard (static/type test)
   - Verifies: every public query method on the new index/service returns `int`/`List[int]`/`Set[int]`/
     `Tuple[int,...]` — never `EntityState`, `IdentityComponent`, or other component/domain objects.
     Follow the pattern of `tests/static/test_no_direct_dirtyset_candidate_selection.py`: either a
     source-scan for forbidden return-type annotations/patterns, or (preferred, stronger) a runtime
     test that calls each query method against a built fixture state and asserts every element of the
     returned collection is an `int` (`isinstance(x, int)` for every entry, and not an `isinstance(x, EntityState)`).
   - Location: `tests/static/test_semantic_entity_index_returns_ids_only.py` (mirrors AC #2's explicit
     "following the pattern of `test_no_direct_dirtyset_candidate_selection.py`" instruction)

6. **`test_index_reflects_dirty_set_change_without_full_rebuild`**
   - Category: unit (behavioral, mocked rebuild counters)
   - Verifies: AC #3 — after a tick where `DirtySet` captures a `region_id`/`faction`/`role` change on
     one entity, the index (a) reflects the new value on the next query, and (b) does not trigger a
     full rebuild of unrelated dimensions (assert via a rebuild-call counter/spy on the per-dimension
     builder methods, mirroring
     `test_world_index_invalidates_resource_index_when_resource_node_dirty`'s existing pattern in
     `tests/unit/domains/optimization/test_world_index_service.py`).
   - Location: `tests/unit/domains/optimization/test_semantic_entity_index.py`

7. **`test_incremental_index_bit_identical_to_full_rebuild`**
   - Category: unit
   - Verifies: AC #3's "bit-identical to a from-scratch rebuild" clause — build the index
     incrementally across N ticks with mutations, then separately force a full rebuild from the final
     `AuthoritativeState`, and assert every dimension's query results are identical between the two.
   - Location: `tests/unit/domains/optimization/test_semantic_entity_index.py`

8. **`test_delete_and_rebuild_index_matches_incremental_across_all_dimensions`**
   - Category: unit
   - Verifies: AC #4 — deleting the index entirely (simulating `object.__setattr__(state,
     "semantic_entity_indexes", None)` or equivalent) and rebuilding from `AuthoritativeState` produces
     identical query results to the incrementally-maintained version, across all 5 dimensions in one
     combined assertion (not just per-dimension in isolation, to catch cross-dimension interaction bugs).
   - Location: `tests/unit/domains/optimization/test_semantic_entity_index.py`

9. **`test_semantic_index_excluded_from_canonical_state_hash`**
   - Category: unit (determinism guard, addresses the Risk flagged in investigation.md)
   - Verifies: `CanonicalStateHasher.get_hash(state)` (or `AuthoritativeState.to_canonical_dict()`) is
     identical whether or not the semantic entity index has been built/attached to `state` — confirms
     the index is a true non-authoritative derived cache per `docs/engine/performance_contract.md`'s
     "optimization must not change semantic outcome" law, mirroring how `world_indexes` is presumed
     (not directly verified in this investigation pass) to be excluded today.
   - Location: `tests/unit/domains/optimization/test_semantic_entity_index.py`

## Scoped Pytest Commands

```bash
# New + directly adjacent optimization/world-index suite
pytest tests/unit/domains/optimization/ tests/static/test_no_direct_dirtyset_candidate_selection.py -v

# Perf/cache-invalidation regression surface
pytest tests/unit/perf/test_phase10_cache_invalidation.py -v

# DirtySet-consumer integration regression surface
pytest tests/integration/optimization/ -m "not slow"

# Information-seeking / knowledge_domain backing-data regression surface
pytest tests/unit/cognition/test_information_seeking.py tests/unit/quest/test_quest_generation.py -v
```

Never: `pytest tests/`. All commands above are scoped to the optimization/index domain plus the
directly-adjacent DirtySet and information-provider consumers this ticket's five index dimensions
read from.

## Anti-Drift Test Guards

- **`test_semantic_index_never_written_via_stateupdate`**: static/source-scan test asserting no file
  under `src/engine/` (or wherever the new index service lands) constructs a `StateUpdate`/`replace()`
  call that writes to the new index fields — the only legal write path is `object.__setattr__` on an
  already-constructed `AuthoritativeState`, per the ticket's Scope section and the `WorldIndexService`
  precedent. Guards against a future edit accidentally promoting the index to authoritative state.
- **`test_paid_information_scan_unchanged`**: a guard (can be an existing regression test in
  `tests/unit/cognition/test_information_seeking.py` or a light new assertion) confirming
  `src/engine/pipeline_phases/paid_information.py`'s O(N)/O(M) nested scan is byte-for-byte unchanged
  by this ticket — catches accidental scope creep into the explicitly out-of-scope retrofit tickets
  (`TCK-20260822-PAID-INFO-INDEX-RETROFIT`, `TCK-20260822-GUARD-SCAN-INDEX-RETROFIT`).
- **`test_from_entity_need_still_returns_none`**: guard against silently "completing" the
  `QuestOpportunityGenerator.from_entity_need` stub as a side effect of building the `entity_needs`
  dimension — already covered by the existing `tests/unit/quest/test_quest_generation.py` stub test,
  but explicitly re-list it in the ticket's regression run so a CI diff would flag it if the stub's
  `return None` line changes.
- **`test_cache_invalidation_policy_unrelated_domains_unaffected`**: when new domains are added to
  `CacheInvalidationPolicy.invalidated_indexes()`/`should_invalidate()` for the semantic dimensions,
  assert the existing spatial domains (`resources`, `buildings`, `entities`, `ground_items`, `corpses`,
  `regions`) keep returning identical results for the same `DirtySet` inputs as before this ticket —
  regression guard against accidentally changing spatial-index invalidation behavior while extending
  the policy class for semantic dimensions.
- **`test_no_phase_boundary_restructuring`**: a lightweight guard (can be a diff-review checklist item
  rather than a runtime test, but call it out explicitly in Verify) confirming `_phase_persistence`'s
  body in `src/engine/kernel.py` is unchanged by this ticket (line count / no new `object.__setattr__`
  calls added there) — since Recommendation 1 concluded the lazy pattern requires no kernel phase hook
  at all, any diff touching `_phase_persistence` or `_phase_advancement`'s existing control flow is a
  signal the implementation drifted from the investigated/recommended lifecycle.
