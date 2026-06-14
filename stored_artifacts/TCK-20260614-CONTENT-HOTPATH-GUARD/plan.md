---
ticket_id: TCK-20260614-CONTENT-HOTPATH-GUARD
date: 2026-06-14
---

# Implementation Plan: TCK-20260614-CONTENT-HOTPATH-GUARD

## Step 1 — Add guard types to `src/content/repository.py`
- Add `import threading`
- Add `ContentHotPathViolation(RuntimeError)` with docstring citing WORLD-CAT-004
- Add module-level `_tick_context_active: threading.local = threading.local()`
- At top of `load_all()`: check `getattr(_tick_context_active, "active", False)` and raise

## Step 2 — Create `src/content/warmup.py`
- `ContentWarmupService.warmup(repo=None)`: if repo provided, call `configure_faction_semantics_service(repo)`; else call `get_faction_semantics_service()` to trigger lazy load
- `ContentWarmupService.is_warm()`: check `_semantics_service_cache is not None`
- `ContentWarmupService.reset()`: guard `assert "pytest" in sys.modules`, then call `reset_faction_semantics_service()`

## Step 3 — Wire into `Kernel`
- `__init__`: after `self.validate(flags)`, add try/except warmup call (non-fatal)
- `tick_once()`: set `_tick_context_active.active = True`, delegate to `_tick_once_inner()`, clear in finally
- `_tick_once_inner()`: original tick body (phases + perf timing)

## Step 4 — Tests (`tests/unit/engine/test_content_hotpath_guard.py`)
10 tests covering warmup lifecycle, guard enforcement, thread safety, exception safety, and architecture assertion.

## Files Changed
- `src/content/repository.py`
- `src/content/warmup.py` (new)
- `src/engine/kernel.py`
- `tests/unit/engine/test_content_hotpath_guard.py` (new)
