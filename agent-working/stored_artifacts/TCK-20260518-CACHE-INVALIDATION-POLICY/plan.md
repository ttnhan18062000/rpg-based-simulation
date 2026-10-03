---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260518-CACHE-INVALIDATION-POLICY
artifact_type: plan
tags: [cache, invalidation, policy]
---

# Implementation Plan: CacheInvalidationPolicy

## Proposed Changes

### `src/engine/world_index.py`
- Add `invalidated_indexes(dirty: DirtySet) -> set[str]` to `CacheInvalidationPolicy`.
- Check all dirty set fields and aggregate the set of invalidated index names.

## Verification Plan
- Create `tests/unit/optimization/test_cache_invalidation_policy.py`.
- Verify individual dirty triggers and empty dirty sets.
- Execute unit tests and full regression verification.
