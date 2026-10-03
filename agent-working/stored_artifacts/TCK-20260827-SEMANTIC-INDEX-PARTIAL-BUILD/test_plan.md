---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260827-SEMANTIC-INDEX-PARTIAL-BUILD
artifact_type: test_plan
tags: [engine, performance, determinism]
---

# Test Plan — TCK-20260827-SEMANTIC-INDEX-PARTIAL-BUILD

## Regression Surface

Existing tests that must keep passing **unmodified** (explicit AC requirement — behavior preservation
for TCK-20260822-SEMANTIC-ENTITY-INDEX's AC #1-4):

**Unit — semantic index / cache invalidation (primary surface):**
- `tests/unit/domains/optimization/test_semantic_entity_index.py` — all 12 tests, especially:
  - `test_index_reflects_dirty_set_change_without_full_rebuild` (rebuild-call-spy pattern this
    ticket's new tests should reuse)
  - `test_incremental_index_bit_identical_to_full_rebuild`
  - `test_delete_and_rebuild_index_matches_incremental_across_all_dimensions`
  - `test_semantic_index_excluded_from_canonical_state_hash`
  - `test_identity_only_update_does_not_raise_dirty_set_leak_error` (calls
    `ApplyPath.apply_generation` directly — first real regression surface for the `apply.py` edit)
- `tests/unit/domains/optimization/test_cache_invalidation_policy.py` — all tests, especially
  `test_empty_dirty_invalidates_nothing` (asserts `knowledge` always-invalidates even for an empty
  `DirtySet` — must NOT change) and `test_cache_invalidation_policy_unrelated_domains_unaffected`.
- `tests/unit/domains/optimization/test_dirty_dependency_graph.py` (identity passthrough coverage).

**Unit — spatial index (adjacent system, same `CacheInvalidationPolicy` module):**
- `tests/unit/perf/test_phase10_cache_invalidation.py`
- `tests/unit/perf/test_phase10_dirty_work_scheduler.py`

**Integration — apply path / determinism (the `apply.py` edit's real regression surface):**
- `tests/perf/test_dirty_set_integrity.py`
- `tests/perf/test_dirty_parity.py`
- `tests/integration/kernel/test_checkpoint_reproducibility.py`
- `tests/unit/test_dirty_refresh.py`
- `tests/unit/engine/` (broad sweep — `apply.py`/`state.py` are widely depended upon)
- `tests/unit/core/` (broad sweep — `state.py`'s `semantic_entity_indexes` field and
  `to_readonly()`'s `replace(...)` call are both here)

**Static / anti-drift guards:**
- `tests/static/test_semantic_entity_index_returns_ids_only.py`
- `tests/static/test_semantic_entity_index_no_stateupdate_write.py`
- `tests/static/test_no_direct_dirtyset_candidate_selection.py`

**Adjacent domains that currently use local hoists instead of the index (must show zero behavior
change — this ticket does not touch their call sites):**
- `tests/unit/cognition/test_information_seeking.py::TestPaidInformationTransaction`
- `tests/unit/domains/faction/test_siege_model.py`
- `tests/unit/domains/faction/test_military_conflict_phase.py`
- `tests/integration/scenarios/test_faction_campaign.py`

**Parity ledger schema validation (INFRA-395 edit target):**
- `tests/tools/test_parity_ledger_schema.py`

## New Tests Required

Per the ticket's Acceptance Criteria:

1. **`test_semantic_entity_indexes_carried_forward_across_ticks`**
   - Category: unit
   - Verifies: after `ApplyPath.apply_generation(prior_state, update, ...)` where `update.dirty_set`
     has no invalidated semantic-index domains (empty `DirtySet` or one touching only unrelated tags),
     `new_state.semantic_entity_indexes` is not `None` and a subsequent
     `SemanticEntityIndexService.get_indexes(new_state, dirty)` call reuses the prior tick's cached
     per-dimension values by identity (`is`, not `==`) rather than rebuilding — mirrors
     `test_index_reflects_dirty_set_change_without_full_rebuild`'s existing pattern but drives the
     "prior tick" state through the real `apply_generation` path instead of hand-constructing
     `next_state`.
   - Location: `tests/unit/domains/optimization/test_semantic_entity_index.py`

2. **`test_get_indexes_only_rebuilds_dirty_domains_across_ticks`**
   - Category: unit
   - Verifies: when only one invalidation domain is dirty on a given tick (e.g. only `identity`), the
     other 4 dimensions are NOT rebuilt across that tick's queries — via rebuild-call spies on the
     unaffected `_build_*` methods (reuse the exact monkeypatch pattern already used in
     `test_index_reflects_dirty_set_change_without_full_rebuild`), run against a state produced via
     real cross-tick carry-forward (two consecutive `apply_generation` calls), not a hand-built
     `next_state`. This is the test that actually closes the "Known limitation" — it must fail before
     the `apply.py` fix and pass after.
   - Location: `tests/unit/domains/optimization/test_semantic_entity_index.py`

3. **`test_single_dimension_query_does_not_rebuild_unrequested_invalidated_dimension`**
   - Category: unit
   - Verifies: a caller requesting a single dimension through `SemanticEntityQuery` (e.g. `by_region`)
     does not trigger a rebuild of a dimension that is both invalidated AND not requested in that call
     — via rebuild-call spies proving the unrequested-but-invalidated dimension's `_build_*` method is
     not invoked. Concretely: construct a state/dirty combo where `identity` and `needs` are both
     invalidated, call `SemanticEntityQuery.by_region(...)`, and assert
     `_build_role_class_index`/`_build_faction_index`/`_build_needs_index`/`_build_knowledge_domain_index`
     were NOT called while `_build_region_index` WAS (if region was also invalidated) or reused (if
     not). Exact shape (dataclass change vs. `dimensions` parameter) follows planning's decision.
   - Location: `tests/unit/domains/optimization/test_semantic_entity_index.py`

4. **`test_knowledge_domain_still_always_rebuilds_when_requested`** (anti-drift guard for the
   selective-build change)
   - Category: unit
   - Verifies: the "knowledge always-invalidates" deliberate limitation is preserved — when a caller
     DOES request `by_knowledge_domain`, it still always rebuilds regardless of `dirty`, matching
     `test_empty_dirty_invalidates_nothing`'s existing `should_invalidate("knowledge", ...) is True`
     assertion. Guards against the selective-build mechanism accidentally starting to cache/skip
     `knowledge` rebuilds when it IS the requested dimension.
   - Location: `tests/unit/domains/optimization/test_semantic_entity_index.py`

5. **`test_apply_generation_semantic_index_carry_forward_bit_identical_to_full_rebuild`**
   - Category: integration / determinism
   - Verifies: Parity Invariant (`docs/engine/performance_contract.md` §4.1) — two code paths, (a)
     carried-forward + per-dimension-selective `get_indexes()` result after a real
     `apply_generation` call, and (b) a from-scratch rebuild (`semantic_entity_indexes` forced to
     `None` before calling `get_indexes()`), produce byte-identical `SemanticEntityIndexes` for all 5
     dimensions. Mirrors the existing `test_incremental_index_bit_identical_to_full_rebuild` but
     exercises the real cross-tick `apply_generation` carry-forward path instead of a hand-constructed
     state.
   - Location: `tests/unit/domains/optimization/test_semantic_entity_index.py`

6. **`test_semantic_entity_indexes_carry_forward_survives_dirty_set_audit`**
   - Category: architecture guard
   - Verifies: adding the `apply.py` carry-forward line does not trigger a `DirtySet` leak error under
     `audit_dirty_set=True` (same audit mode `test_identity_only_update_does_not_raise_dirty_set_leak_error`
     already exercises) — confirms the new field is correctly excluded from
     `AuthoritativeState.validate_dirty_set`'s leak-detection the same way `world_indexes` already is.
   - Location: `tests/unit/domains/optimization/test_semantic_entity_index.py`

7. **(If planning chooses a `SemanticEntityIndexes` dataclass shape change for selective building)
   `test_semantic_index_no_stateupdate_write_still_holds_for_partial_object`**
   - Category: architecture guard (static)
   - Verifies: whatever new partial/optional-field shape is chosen, the existing
     `tests/static/test_semantic_entity_index_no_stateupdate_write.py` guard still passes without
     modification — no new write path through `StateUpdate`/`replace()` was introduced.
   - Location: `tests/static/test_semantic_entity_index_no_stateupdate_write.py` (existing file, no new
     file needed unless the guard's own scan logic needs extending for a new dataclass shape).

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/unit/domains/optimization/ -m "not slow" -q
.venv/bin/python3 -m pytest tests/static/test_semantic_entity_index_returns_ids_only.py tests/static/test_semantic_entity_index_no_stateupdate_write.py tests/static/test_no_direct_dirtyset_candidate_selection.py -q
.venv/bin/python3 -m pytest tests/unit/perf/test_phase10_cache_invalidation.py tests/unit/perf/test_phase10_dirty_work_scheduler.py -q
.venv/bin/python3 -m pytest tests/perf/test_dirty_set_integrity.py tests/perf/test_dirty_parity.py -q
.venv/bin/python3 -m pytest tests/integration/kernel/test_checkpoint_reproducibility.py tests/unit/test_dirty_refresh.py -q
.venv/bin/python3 -m pytest tests/unit/engine/ tests/unit/core/ -m "not slow" -q
.venv/bin/python3 -m pytest tests/unit/cognition/test_information_seeking.py tests/unit/domains/faction/ tests/integration/scenarios/test_faction_campaign.py -m "not slow" -q
.venv/bin/python3 -m pytest tests/tools/test_parity_ledger_schema.py -q
```

Never `pytest tests/` — always scoped to the domains above (optimization/engine/core primary,
faction/information adjacent-verification, tools for the parity-ledger YAML edit).

## Anti-Drift Test Guards

- `test_cache_invalidation_policy_unrelated_domains_unaffected` (existing) — must keep passing
  unmodified; guards that adding a `dimensions` parameter or `Optional` fields to the selective-build
  mechanism does not change `should_invalidate()`'s per-domain answers for the 6 pre-existing spatial
  domains or the identity/region/needs domains.
- `test_empty_dirty_invalidates_nothing` (existing) — must keep asserting
  `should_invalidate("knowledge", dirty) is True` for an empty `DirtySet`; a regression here would mean
  the selective-build change accidentally started treating "no dimensions requested this call" as
  "nothing needs rebuilding," which would silently stale the knowledge index.
- New test #4 above (`test_knowledge_domain_still_always_rebuilds_when_requested`) — specifically
  guards against the selective-build mechanism conflating "not requested" with "not dirty" for the one
  domain that has no real dirty-tracking today.
- `test_semantic_index_excluded_from_canonical_state_hash` (existing) — must keep passing; guards that
  neither fix accidentally makes `semantic_entity_indexes` (or a new partial-object variant of it)
  reachable from `CanonicalStateHasher.to_canonical_data()`.
- `test_identity_only_update_does_not_raise_dirty_set_leak_error` (existing) plus new test #6 above —
  guard that the `apply.py` carry-forward line does not introduce a `DirtySet` audit-mode leak, the
  same class of regression `world_indexes`' own carry-forward line already avoids.
- Full existing `tests/unit/cognition/test_information_seeking.py::TestPaidInformationTransaction` and
  `tests/unit/domains/faction/test_siege_model.py`/`test_military_conflict_phase.py` suites — guard
  that this ticket, despite touching the same index those two retrofit tickets evaluated and rejected,
  produces zero behavior change in either adjacent call site (neither is touched by this ticket's
  diff).
