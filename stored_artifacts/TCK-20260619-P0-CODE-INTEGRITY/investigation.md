---
ticket_id: TCK-20260619-P0-CODE-INTEGRITY
phase: investigation
---

# Investigation: Code Integrity Findings

## Bug 1 — Non-deterministic sort in ConversionOptionGenerator and PersonalityAwareSelector

### Location
- `src/domains/progression/generator.py:94`
- `src/domains/progression/selector.py:69`

### Root cause
`sorted(options, key=lambda o: o.score, reverse=True)` — single float key. When two options share the same score, Python's Timsort preserves insertion order, which depends on how `options` was constructed (dict iteration order, list append sequence). This is implementation-dependent and not guaranteed stable across Python versions or runs with different entity counts.

### Evidence
`ConversionKind(str, Enum)` values: `STORE_ITEM`, `CRAFT_ITEM`, `SAVE_FOR_LATER`, `SELL_ITEM`, etc. String comparison is total and deterministic. Adding `.kind.value` as secondary key produces a canonical ordering.

---

## Bug 2 — Upward import: `src/core/state.py` imports from `src/engine/`

### Location
`src/core/state.py:1056-1058`

### Root cause
```python
if getattr(self, "movement_cache", None) is None:
    from src.engine.movement_cache import MovementPlanCache
    object.__setattr__(self, "movement_cache", MovementPlanCache())
```
`core` is the lowest layer. `engine` depends on `core`. Importing engine from core creates an upward reference that violates the layering invariant and can cause circular import failures in test isolation contexts.

### Why it is safe to remove
1. `movement_cache: Any = field(default=None, repr=False, compare=False)` already at line 1008 — field defaults to `None`.
2. All engine-side consumers of `movement_cache` already guard: `if getattr(state, "movement_cache", None) is not None`.
3. `kernel.py` initializes the cache at startup before the first tick; `__post_init__` eager-init is redundant.

---

## Bug 3 — `seed_phase1_content(None)` raises FallbackRestrictedError

### Location
- `tests/unit/core/test_registry_bridge.py:28` (teardown fixture)
- `tests/unit/cognition/test_phase2_knowledge_model_service.py:27` (module-scoped setup fixture)

### Root cause
`seed_phase1_content` signature:
```python
def seed_phase1_content(
    catalog_repo: Optional[Any] = _sentinel,
    required: bool = False,
    mode: RuntimeContentMode = RuntimeContentMode.CATALOG_WITH_COMPATIBILITY,
) -> Optional[AdapterProjectionResult]:
```
Passing `None` explicitly sets `catalog_repo=None` (not `_sentinel`). The code then hits the `else` branch and checks:
```python
if mode.value in _FORBIDDEN_FALLBACK_MODES:  # "catalog_with_compatibility" IS forbidden
    raise FallbackRestrictedError(mode)
```
So `seed_phase1_content(None)` always raises regardless of test order.

### Effect
- `test_registry_bridge.py`: teardown raises for every test → pytest reports each as an error; global registry state from the test is not reset
- `test_phase2_knowledge_model_service.py`: module-scoped `seed_registries` fixture raises → all 15 tests in the module are marked ERROR

### Fix
Replace `seed_phase1_content(None)` with `seed_phase1_content(mode=RuntimeContentMode.LEGACY_FALLBACK)`.
- `catalog_repo` uses `_sentinel` default → auto-discovers `data/content/` if present
- `LEGACY_FALLBACK` is NOT in `_FORBIDDEN_FALLBACK_MODES` → no exception
