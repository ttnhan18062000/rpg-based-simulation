---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260822-SEMANTIC-ENTITY-INDEX
phase: open
date: 2026-08-22
tags: [engine, performance, determinism]
---

# TCK-20260822-SEMANTIC-ENTITY-INDEX

## Title
Build maintained semantic entity index for role/class/region/faction/needs lookups

## Status
OPEN

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
- [ ] entity_index.by_role_class(role, class_id) returns exactly the matching entity ID set, verified against a naive linear-scan reference implementation.
- [ ] All query methods return only List[int]/Set[int] entity IDs, never EntityState/component objects -- enforced by a static/type test following the pattern of tests/static/test_no_direct_dirtyset_candidate_selection.py.
- [ ] After a tick where DirtySet captures a region_id/faction/role change, the index reflects the new value on next query without a full rebuild, and is bit-identical to a from-scratch rebuild.
- [ ] Deleting and rebuilding the index from AuthoritativeState produces identical query results to the incrementally-maintained version, across all 5 dimensions.
- [ ] The ticket documents the chosen lifecycle (lazy CacheInvalidationPolicy-driven vs. eager Persistence-phase write) and the entity_needs field mapping, with rationale, before implementation is considered complete.

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

## Test Summary

## Files Changed

## Completion Summary
