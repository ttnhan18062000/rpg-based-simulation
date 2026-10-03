---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260607-SEMANTICS-SINGLETON
artifact_type: test_plan
tags: [semantics, singleton]
---

# Test Plan — TCK-20260607-SEMANTICS-SINGLETON

## Tests updated

- `test_relation_combat_integration.py`: added `autouse` fixture that resets the singleton cache
  after each test, preventing cross-test state leakage.

## Acceptance verified

- All existing integration tests pass with the reset fixture in place.
- `get_faction_semantics_service()` still lazy-loads from the real catalog on first call.
- `reset_faction_semantics_service()` confirmed to clear the cache (next call re-creates from ContentPathConfig).

## Run

```
pytest tests/integration/combat/test_relation_combat_integration.py -q
```
