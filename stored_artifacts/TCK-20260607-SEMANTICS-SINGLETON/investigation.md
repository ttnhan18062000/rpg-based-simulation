---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260607-SEMANTICS-SINGLETON
artifact_type: investigation
tags: [semantics, singleton]
---

# Investigation — TCK-20260607-SEMANTICS-SINGLETON

## Finding

`get_faction_semantics_service()` in `faction.py` has two issues:

1. **Hardcoded path**: `CatalogRepository("data/content")` — cannot be overridden in tests
   without patching the module. Should use `ContentPathConfig().content_root`.

2. **No reset API**: the cache is never cleared. Tests that need to exercise different
   catalog states (or that want test isolation) have no way to reset it.
   `test_relation_combat_integration.py` calls `get_faction_semantics_service()` in every
   test function — if the first call loads a catalog and the singleton persists, subsequent
   tests that try to install a custom catalog cannot do so.

## Decision

**Option A (chosen)**: Add `configure_faction_semantics_service(repo)` and
`reset_faction_semantics_service()` to `faction.py`. Add autouse fixture to the integration
test. No changes to call sites in `legality.py` / `tactical.py`.

**Option B (deferred)**: Full injection via combat context objects — larger scope, separate epic.
