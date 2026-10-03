---
ticket_id: TCK-20260619-P0-CODE-INTEGRITY
phase: implementation
---

# Plan: Code Integrity — Three Determinism / Isolation Bugs

## Fix 1: Sort tiebreaker in progression generator and selector

**Files:** `src/domains/progression/generator.py:94`, `src/domains/progression/selector.py:69`

**Change:** Add secondary sort key `o.kind.value` / `pair[0].kind.value` so ties in score produce the same ordering regardless of Python's list construction order.

`ConversionKind(str, Enum)` — `.value` is a string literal, always comparable.

## Fix 2: Remove upward import (core→engine) from WorldState.__post_init__

**File:** `src/core/state.py:1056-1058`

**Change:** Remove the three-line lazy import block. The `movement_cache` field already defaults to `None` (line 1008). Engine callers already guard with `getattr(state, "movement_cache", None)`. The cache is properly initialized by `kernel.py` at startup.

No behaviour change in production path; eliminates the circular dependency risk.

## Fix 3: Broken test teardown / fixture setup

**Files:** `tests/unit/core/test_registry_bridge.py:28`, `tests/unit/cognition/test_phase2_knowledge_model_service.py:27`

**Change:** Both call `seed_phase1_content(None)` which passes explicit `None` as `catalog_repo` and defaults `mode=CATALOG_WITH_COMPATIBILITY`. Since `"catalog_with_compatibility"` is in `_FORBIDDEN_FALLBACK_MODES`, this always raises `FallbackRestrictedError`.

Fix: use `seed_phase1_content(mode=RuntimeContentMode.LEGACY_FALLBACK)` — uses `_sentinel` for `catalog_repo` (auto-discovers `data/content/`), uses allowed mode.

## Test plan summary

- New `tests/unit/engine/test_sort_tiebreaker.py`: verifies stable deterministic ordering on tied scores
- Run `pytest tests/unit/cognition/` to confirm 0 errors (was 15)
- Run `pytest tests/integration/kernel/test_replay_determinism.py::test_transaction_trace_determinism`
