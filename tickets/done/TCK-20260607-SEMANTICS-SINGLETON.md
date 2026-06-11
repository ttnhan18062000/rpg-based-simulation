---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260607-SEMANTICS-SINGLETON
phase: done
date: 2026-06-07
tags: [semantics, singleton]
---

# TCK-20260607-SEMANTICS-SINGLETON

## Title
Refactor get_faction_semantics_service singleton to support injection and reset

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
`get_faction_semantics_service()` in `faction.py` is a module-level process singleton that hardcodes the catalog path to `"data/content"` and never resets. It is called from hot paths in `legality.py` and `tactical.py`. Currently all tests use the same real catalog so there are no failures, but the singleton blocks any test that needs to exercise different catalog states (e.g. testing with a stripped-down or modified catalog for relation projection scenarios). It is also a hidden global state dependency in static methods.

## Scope

### Current problem

```python
_semantics_service_cache: Optional[FactionSemanticsService] = None

def get_faction_semantics_service() -> FactionSemanticsService:
    global _semantics_service_cache
    if _semantics_service_cache is None:
        repo = CatalogRepository("data/content")
        repo.load_all()
        _semantics_service_cache = FactionSemanticsService(repo)
    return _semantics_service_cache
```

Issues:
1. Path is hardcoded — cannot be overridden in tests.
2. Cache never resets — stale if catalog changes within a process.
3. `legality.py` and `tactical.py` call it inside static methods — no injection point.
4. Integration tests (`test_relation_combat_integration.py`) consume it directly and silently depend on real catalog files being present at test run time.

### Fix Direction

**Option A — Add a reset + override API (minimal change):**
```python
def configure_faction_semantics_service(repo: CatalogRepository) -> None:
    """Override or reset the cached service with a given repo. Intended for test setup and app boot."""
    global _semantics_service_cache
    _semantics_service_cache = FactionSemanticsService(repo)

def reset_faction_semantics_service() -> None:
    global _semantics_service_cache
    _semantics_service_cache = None
```

This allows tests to inject a configured service without changing call sites.

**Option B — Remove singleton and inject via state/context (larger refactor):**
Pass a `FactionSemanticsService` through the combat/legality context objects. This eliminates the global state entirely but requires changes in legality.py, tactical.py, and all call sites.

**Recommended approach for this ticket:** Option A. Option B is a broader architecture change that should be its own epic.

### Required additions

1. Add `configure_faction_semantics_service(repo)` and `reset_faction_semantics_service()` to `faction.py`.
2. Update integration tests to call `reset_faction_semantics_service()` in teardown (or use a pytest fixture).
3. Add a `pytest` fixture in `conftest.py` (integration level) that resets the service after each test that uses it.
4. Document the singleton contract in `faction.py` with a clear comment.

## Out of Scope
- Do not inject through legality.py/tactical.py static methods (Option B scope).
- Do not change `FactionSemanticsService` API.
- Do not remove the singleton itself — it is a valid performance optimization for the hot path.

## Acceptance Criteria
- [ ] `reset_faction_semantics_service()` clears the cache
- [ ] `configure_faction_semantics_service(repo)` installs a pre-built service
- [ ] Integration tests that call `get_faction_semantics_service()` use a fixture that resets after each test
- [ ] Tests using a custom catalog can configure the service before calling legality
- [ ] All 173 existing tests still pass
- [ ] No hardcoded path in `get_faction_semantics_service()` — use `ContentPathConfig().content_root` instead

## Related Tickets
- TCK-20260607-STRICT-MODE-PRODUCTION (same audit)

## Related Docs
- world_phase_20_28_repair.md Phase 28

## Related Code Areas
- `src/content_semantics/faction.py:15-23`
- `src/engine/legality.py:222-258`
- `src/engine/tactical.py:121-127`
- `tests/integration/combat/test_relation_combat_integration.py`

## Assumptions / Open Questions
- Should the singleton path be configurable via env var for CI? Possibly useful but out of scope here.

## Implementation Notes
Path reference in `get_faction_semantics_service()` should use `ContentPathConfig().content_root` instead of the hardcoded string `"data/content"`.

## Test Summary
Run `pytest tests/unit/content_semantics/ tests/integration/combat/ -q`.

## Files Changed
- `src/content_semantics/faction.py`
- `tests/integration/combat/test_relation_combat_integration.py`
- `tests/conftest.py` or `tests/integration/conftest.py`

## Completion Summary
Done. 169 tests pass.
