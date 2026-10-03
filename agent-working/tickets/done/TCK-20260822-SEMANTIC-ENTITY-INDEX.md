---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260822-SEMANTIC-ENTITY-INDEX
phase: done
date: 2026-08-22
tags: [engine, performance, determinism]
---

# TCK-20260822-SEMANTIC-ENTITY-INDEX

## Title
Build maintained semantic entity index for role/class/region/faction/needs lookups

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Preserves the original intent of a structured, incrementally-maintained index over live entity state (role+class_id, region_id, faction, entity_needs, knowledge_domain) giving strategic/governance layers O(1)/O(k) lookups instead of O(N) scans, as a non-authoritative derived projection that is always rebuildable and returns only entity IDs. Corrected by investigation: the closest precedent, WorldIndexService, uses a lazy pull-based tick-cached rebuild driven by CacheInvalidationPolicy against DirtySet -- not the eager single-point-in-Persistence-phase write the proposal specifies -- and Kernel._phase_persistence today does not touch state at all (the real state commit happens in _phase_advancement). Which lifecycle pattern to follow, and what 'entity_needs' concretely maps to, must be resolved as part of this ticket rather than assumed.

## Scope
- Design and implement a non-authoritative, derived, always-rebuildable entity index over 5 dimensions: role+class_id, region_id, faction, entity_needs, knowledge_domain.
- Attach the index to AuthoritativeState via object.__setattr__ following the existing world_indexes/_node_map_cache derived-cache pattern (never via StateUpdate/replace()).
- Decide and document explicitly whether the index follows WorldIndexService's lazy pull-based CacheInvalidationPolicy/DirtySet-driven lifecycle, or a new eager Persistence-phase write lifecycle -- and if eager, define which phase boundary now counts as 'Persistence' given _phase_persistence's current no-op-on-state status.
- Resolve and document the entity_needs dimension's concrete field mapping before finalizing ACs.
- Query methods return List[int]/Set[int] entity IDs only, never EntityState/component objects.

## Out of Scope
- Rewriting Kernel phase boundaries themselves -- only decide/document which lifecycle the index uses; do not restructure _phase_advancement/_phase_persistence beyond what's needed to host the index write.
- C4's scan_policy/DirtySet doc reconciliation (tracked separately, already mostly committed).
- Retrofitting any concrete call site (paid_information.py, military_conflict.py) into this index -- those are separately scoped tickets (TCK-20260822-PAID-INFO-INDEX-RETROFIT, TCK-20260822-GUARD-SCAN-INDEX-RETROFIT).
- Building an InformationNeed-style concept if entity_needs is resolved to mean BiologicalComponent fields only -- do not speculatively build unshipped structures.

## Acceptance Criteria
- [x] entity_index.by_role_class(role, class_id) returns exactly the matching entity ID set, verified against a naive linear-scan reference implementation.
- [x] All query methods return only List[int]/Set[int] entity IDs, never EntityState/component objects -- enforced by a static/type test following the pattern of tests/static/test_no_direct_dirtyset_candidate_selection.py.
- [x] After a tick where DirtySet captures a region_id/faction/role change, the index reflects the new value on next query without a full rebuild, and is bit-identical to a from-scratch rebuild.
- [x] Deleting and rebuilding the index from AuthoritativeState produces identical query results to the incrementally-maintained version, across all 5 dimensions.
- [x] The ticket documents the chosen lifecycle (lazy CacheInvalidationPolicy-driven vs. eager Persistence-phase write) and the entity_needs field mapping, with rationale, before implementation is considered complete.

## Related Tickets
- TCK-20260517-WORLD-INDEX-SERVICE
- TCK-20260517-STATIC-DIRTYSET-GUARD
- TCK-20260518-READ-MODEL-CACHE
- TCK-20260702-PLANS-IDEA-REFRESH
- TCK-20260822-PAID-INFO-INDEX-RETROFIT
- TCK-20260822-GUARD-SCAN-INDEX-RETROFIT

## Related Docs
- docs/engine/performance_contract.md
- docs/plans/idea_semantic_entity_index.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/world_index.py
- src/engine/spatial_query.py
- src/core/dirty.py
- src/core/state.py
- src/engine/kernel.py
- src/domains/information/providers.py
- src/engine/apply.py

## Assumptions / Open Questions
- Open question: lazy (WorldIndexService-style) vs. eager (Persistence-phase) lifecycle is unresolved and must be decided during planning/investigation, not assumed.
- Open question: entity_needs dimension's concrete mapping (BiologicalComponent fields vs. a broader unshipped InformationNeed concept) is unresolved.
- Assumes coordination with the doc-correction ticket (TCK-20260822-SCAN-POLICY-DOC-FIX) does not block this ticket -- that ticket is doc-only, not a structural blocker.

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260822-SEMANTIC-ENTITY-INDEX/plan.md`'s 9 steps,
with three deviations recorded in that file's "Deviations" section (also summarized here):

- **Step 1**: Added `SemanticEntityIndexes` frozen dataclass to new `src/engine/semantic_entity_index.py`,
  and `AuthoritativeState.semantic_entity_indexes: Any = field(default=None, repr=False, compare=False)`
  to `src/core/state.py` (same shape as `world_indexes`), plus carrying it through
  `to_readonly()`'s `replace(...)` call. Not added to `CanonicalStateHasher.to_canonical_data()`
  (verified excluded by omission via a dedicated test).
- **Step 2**: Added `DirtySet.identity_entities: Set[int]` and wired it through every real
  construction site: the dataclass field, `all_dirty_entities` union property, `DirtySet.from_update`,
  `DirtySet.merge`, `DirtyDependencyGraph.expand` (passthrough only, no new dependency implications),
  `pipeline.py`'s force-full-scan override block, **and** (deviation #1, see plan.md) `DirtySetBuilder`
  (`__init__`/`mark_entity`/`mark_from_update`/`build()`) plus `apply_plan.py`'s per-entity tag list —
  the latter two are the actual construction path the live `ApplyPath.apply_generation`/
  `AuthoritativeApplyPipeline.refine()` production code uses, which the plan's source citations had
  not identified as distinct from `DirtySet.from_update`.
- **Step 3**: Extended `CacheInvalidationPolicy` in `src/engine/world_index.py` additively with
  `"identity"`, `"region"` (backed by a distinctly-named `"semantic_region_index"` string, kept
  separate from the pre-existing phantom `"region_index"` per the plan), and `"needs"` domains, plus
  an always-invalidating `"knowledge"` domain (no DirtySet tag backs `information_providers`
  mutations, by design — out of scope to invent one). Existing five spatial domains untouched.
  Deviation #2: had to update one pre-existing test's exact-cardinality assertion
  (`test_region_dirty_invalidates_region_index`) since region-dirty now populates two index-domain
  strings instead of one; its behavioral assertions are unchanged.
- **Step 4**: Implemented `SemanticEntityIndexService.get_indexes()` with tick-scoped cache hit and
  per-dimension reuse-or-rebuild, mirroring `WorldIndexService.get_indexes()` exactly. Needs
  thresholds cite the Mechanics Bible verbatim (`HUNGER_NEED_THRESHOLD=95.0`,
  `SLEEP_DEBT_NEED_THRESHOLD=98.0`, `docs/mechanics/01_entity_anatomy.md:76-77`) and the existing
  `rest_pressure > 70.0` shipped precedent (`perception.py:95`, `routine.py:49`) for the field the
  Bible doesn't document.
- **Step 5**: Added `SemanticEntityQuery` with `by_role_class`/`by_region`/`by_faction`/`by_need`/
  `by_knowledge_domain`, all returning `Tuple[int, ...]` only.
- **Steps 6-8**: Determinism/bit-identity/anti-drift tests added as specified (see Test Summary).
- **Step 9**: Added a "Semantic Entity Indexes" subsection to `docs/engine/performance_contract.md`
  (§8.2), including an explicit "Known limitation" callout for deviation #3 below, and a superseded-by
  marker at the top of `docs/plans/idea_semantic_entity_index.md`.

**Deviation #3 (documented, not fixed)**: `semantic_entity_indexes` is not carried forward across
ticks in `ApplyPath.apply_generation`'s new-state construction (unlike `world_indexes`), since
`src/engine/apply.py` is an explicit Scope-Guard read-only file in the plan. Production ticks
therefore always full-rebuild on the first post-tick query rather than reusing the prior tick's
per-dimension cache; the partial-rebuild mechanism itself is implemented and fully tested at the
service level. Left as a documented known limitation for a follow-up ticket, per the plan's Scope
Guard.

## Test Summary

New tests (all passing):
- `tests/unit/domains/optimization/test_semantic_entity_index.py` — 12 tests covering AC #1-4 (naive-scan
  parity for all 5 dimensions, partial-rebuild-on-dirty behavior with rebuild-call spies, incremental-
  vs-full-rebuild bit-identity, delete-and-rebuild identity, canonical-hash exclusion, `identity_entities`
  tag population, `all_dirty_entities` union coverage, and a full `ApplyPath.apply_generation(...,
  audit_dirty_set=True)` no-leak regression).
- `tests/static/test_semantic_entity_index_returns_ids_only.py` — AC #2 runtime guard.
- `tests/static/test_semantic_entity_index_no_stateupdate_write.py` — anti-drift source-scan guard
  (no `StateUpdate`/`replace()` write path to the new field).
- `tests/unit/domains/optimization/test_dirty_dependency_graph.py` — added
  `test_dirty_dependency_identity_passes_through_without_implied_domains`.
- `tests/unit/domains/optimization/test_cache_invalidation_policy.py` — added
  `test_cache_invalidation_policy_unrelated_domains_unaffected` and extended two existing tests
  (see plan.md Deviations #2 for the one cardinality-assertion update).

Regression surface run and passing (per test_plan.md's Scoped Pytest Commands, using
`.venv/bin/python3 -m pytest`, not the ambient `python3`):
- `tests/unit/domains/optimization/` (127 passed)
- `tests/static/test_no_direct_dirtyset_candidate_selection.py`, plus the two new static files (3 passed)
- `tests/unit/perf/test_phase10_cache_invalidation.py`, `tests/unit/perf/test_phase10_dirty_work_scheduler.py`
- `tests/perf/test_dirty_set_integrity.py`, `tests/perf/test_dirty_parity.py`
- `tests/integration/optimization/` (20 passed, `-m "not slow"`)
- `tests/unit/cognition/test_information_seeking.py`, `tests/unit/quest/test_quest_generation.py` (78 passed)
- `tests/unit/engine/`, `tests/unit/core/` (394 passed, 1 skipped, `-m "not slow"`) — broad regression
  sweep since `src/core/state.py` and `src/core/dirty.py` are widely depended upon
- `tests/integration/kernel/test_checkpoint_reproducibility.py`, `tests/unit/test_dirty_refresh.py`

No `pytest tests/` full-suite run, per project testing rule.

## Files Changed

- `src/engine/semantic_entity_index.py` (new)
- `src/core/state.py`
- `src/core/dirty.py`
- `src/engine/apply_plan.py`
- `src/engine/pipeline.py`
- `src/engine/world_index.py`
- `docs/engine/performance_contract.md`
- `docs/plans/idea_semantic_entity_index.md`
- `tests/unit/domains/optimization/test_semantic_entity_index.py` (new)
- `tests/static/test_semantic_entity_index_returns_ids_only.py` (new)
- `tests/static/test_semantic_entity_index_no_stateupdate_write.py` (new)
- `tests/unit/domains/optimization/test_dirty_dependency_graph.py`
- `tests/unit/domains/optimization/test_cache_invalidation_policy.py`
- `staging_artifacts/TCK-20260822-SEMANTIC-ENTITY-INDEX/plan.md` (Deviations section added)
- `tickets/inprogress/TCK-20260822-SEMANTIC-ENTITY-INDEX.md` (this file)

## Completion Summary

Implemented `SemanticEntityIndexes`/`SemanticEntityIndexService`/`SemanticEntityQuery`
(`src/engine/semantic_entity_index.py`) as a non-authoritative, derived, always-rebuildable index
over 5 entity dimensions (role+class_id, region_id, faction, biological-threshold needs,
knowledge_domain), following `WorldIndexService`'s lazy pull-based `CacheInvalidationPolicy`-driven
lifecycle exactly (Recommendation 1), attached to `AuthoritativeState` via `object.__setattr__` and
excluded from `CanonicalStateHasher` by omission. Added a new `DirtySet.identity_entities` tag and
wired it through every real construction site in the codebase (including `DirtySetBuilder` and
`apply_plan.py`, beyond what the plan text explicitly named — see Deviations) so role/faction
changes are correctly tracked end-to-end through the live authoritative apply path. All 5 acceptance
criteria are met and verified by new tests; the one known gap (cross-tick cache carry-forward in
`apply.py`, deliberately out of scope per the plan's Scope Guard) is documented in both the ticket
and `docs/engine/performance_contract.md` for a follow-up ticket.
