---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260822-SCAN-POLICY-DOC-FIX
phase: open
date: 2026-08-22
tags: [documentation]
---

# TCK-20260822-SCAN-POLICY-DOC-FIX

## Title
Correct two stale performance claims in the semantic-index reconciliation doc

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Preserves the original intent that performance_contract.md §7's scan_policy+DirtySet mitigation must be reconciled with any semantic-index proposal rather than treating the index as the only mitigation in play. Corrected by investigation: that reconciliation is already committed in docs/plans/idea_semantic_entity_index.md (same-session commit 4fc13ac4, the staleness-fix pass). The real remaining scope is two narrower factual corrections still needed in that doc: (1) scan_policy/DirtySet do not actually gate paid_information.py's live hotspot -- that call site ignores both mechanisms entirely; and (2) MOVEMENT_STRESS_100_ACTORS is cited as a benchmark-scale scenario but has zero hits in src/perf/scenarios.py or tests/ -- it is not a real wired scenario.

## Scope
- Correct docs/plans/idea_semantic_entity_index.md to state explicitly that scan_policy/DirtySet do not currently gate paid_information.py's hotspot.
- Correct or remove the MOVEMENT_STRESS_100_ACTORS reference in that doc, since it is not a wired scenario anywhere in src/perf/scenarios.py or tests/.
- Note (documentation-only) the unrelated pre-existing bug found during investigation: CacheInvalidationPolicy.invalidated_indexes() references 'region_index' with a passing test, but WorldIndexes has no region_index field/method -- flag as a known follow-up, do not fix it here.

## Out of Scope
- Building the index itself (TCK-20260822-SEMANTIC-ENTITY-INDEX) or retrofitting any call site (TCK-20260822-PAID-INFO-INDEX-RETROFIT, TCK-20260822-GUARD-SCAN-INDEX-RETROFIT).
- Fixing the CacheInvalidationPolicy 'region_index' dead-code/phantom-field bug -- flagged for awareness only, tracked as a separate future concern, not fixed in this ticket.
- Any code changes -- this ticket is doc-only.

## Acceptance Criteria
- [ ] docs/plans/idea_semantic_entity_index.md's Status review note is verified accurate: 0 repo-wide hits for ProviderLocator/TerritorialObserver, and WorldIndexes has no role/faction/region dimension, confirming scan_policy/DirtySet reduce but don't eliminate the semantic-index gap.
- [ ] Doc explicitly states scan_policy/DirtySet do NOT currently gate paid_information.py's hotspot -- today's mitigation is engine-wide precedent, not an applied fix at that call site.
- [ ] MOVEMENT_STRESS_100_ACTORS benchmark-scale claim is corrected in the doc to note it is not a real wired scenario (zero hits in src/perf/scenarios.py or tests/).
- [ ] The region_index CacheInvalidationPolicy/WorldIndexes mismatch is recorded as a known follow-up note (doc or ticket), not silently dropped and not fixed in this pass.

## Related Tickets
- TCK-20260517-WORLD-INDEX-SERVICE
- TCK-20260518-CACHE-INVALIDATION-POLICY
- TCK-20260517-STATIC-DIRTYSET-GUARD
- TCK-20260702-PLANS-IDEA-REFRESH

## Related Docs
- docs/plans/idea_semantic_entity_index.md
- docs/engine/performance_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/idea_semantic_entity_index.md
- docs/engine/performance_contract.md
- src/core/dirty.py
- src/engine/phase_governor.py
- src/engine/policy.py
- src/engine/candidate_selector.py
- src/engine/world_index.py
- src/engine/spatial_query.py
- src/engine/pipeline_phases/paid_information.py
- src/perf/scenarios.py

## Assumptions / Open Questions
- Assumes the doc-level reconciliation committed in 4fc13ac4 remains the current state at implementation time (not re-reverted by concurrent work).
- The region_index dead-code bug is explicitly deferred, not silently dropped -- should be captured as a follow-up note per investigation's risk flag.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
