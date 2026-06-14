---
status: done
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-CONTENT-HOTPATH-GUARD
phase: done
date: 2026-06-14
tags: [resource-safety, content, hot-path, yaml, performance, architecture]
---

# TCK-20260614-CONTENT-HOTPATH-GUARD

## Title
Add Content Hot-Path Guard — prevent YAML/content loading from inside the tick pipeline

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`WorldDynamicsSystem.resolve_dynamics()` calls `get_faction_semantics_service()`, which lazily calls `CatalogRepository.load_all()` if the singleton is not yet warmed. Add a `ContentWarmupService` that loads content at boot and a `ContentHotPathViolation` guard that raises if `load_all()` is called during a kernel tick.

## Scope
- Added `ContentHotPathViolation(RuntimeError)` and `_tick_context_active: threading.local` to `src/content/repository.py`
- `CatalogRepository.load_all()` raises `ContentHotPathViolation` if `_tick_context_active.active` is True
- Created `src/content/warmup.py` with `ContentWarmupService.warmup()`, `is_warm()`, `reset()` 
- `Kernel.__init__()` calls `ContentWarmupService.warmup()` (non-fatal — logs warning on failure)
- `Kernel.tick_once()` sets `_tick_context_active.active = True` before delegating to `_tick_once_inner()`, clears in finally
- `_tick_once_inner()` contains original tick body (refactored from `tick_once()`)

## Out of Scope
- Freezing/immutability of content objects
- Warming non-content singletons
- Changing content schema or YAML format

## Acceptance Criteria
- [x] `ContentWarmupService` class exists with `warmup()`, `is_warm()`, `reset()` methods
- [x] `Kernel.__init__()` calls `ContentWarmupService.warmup()` before first tick
- [x] `CatalogRepository.load_all()` raises `ContentHotPathViolation` if called while tick context is active
- [x] Architecture test `test_load_all_not_called_during_warm_kernel_tick` passes
- [x] `ContentWarmupService.reset()` clears singletons (guarded by `assert "pytest" in sys.modules`)
- [x] 10 tests pass

## Related Tickets
- TCK-20260614-RESOURCE-SAFETY-EPIC (parent)
- TCK-20260607-STRICT-MODE-PRODUCTION (DONE — confirmed no interaction; load_all guard check happens before duplicate-spec check)

## Related Docs
- `docs/content/pipeline_contract.md` — WORLD-CAT-004, WORLD-CAT-005

## Related Code Areas
- `src/content_semantics/faction.py` — `get_faction_semantics_service()` singleton factory
- `src/content/repository.py` — `CatalogRepository`, `load_all()`, guard added here
- `src/content/warmup.py` — new: `ContentWarmupService`
- `src/engine/kernel.py` — warmup call in `__init__`, tick context in `tick_once()`

## Assumptions / Open Questions
- Only one content singleton found (`_semantics_service_cache` in faction.py) — confirmed by grep
- Tick context is `threading.local` for thread safety per ticket requirements
- warmup call in Kernel is non-fatal (wrapped in try/except) — content dir may be unavailable in test contexts

## Implementation Notes
- `tick_once()` refactored into `tick_once()` (context setter/clearer) + `_tick_once_inner()` (all phases). No logic moved, just wrapped.
- `ContentWarmupService.warmup(repo=...)` accepts an optional pre-loaded repo to skip disk I/O in tests.
- `reset()` is guarded by `assert "pytest" in sys.modules` to prevent production use.
- Two pre-existing content test failures exist on main (packs/swamp_border_pack, compatibility/migration_map not in matrix) — not introduced by this ticket.

## Test Summary
- `tests/unit/engine/test_content_hotpath_guard.py` — 10 tests:
  - `test_warmup_populates_faction_singleton`
  - `test_is_warm_false_before_warmup`
  - `test_is_warm_true_after_warmup`
  - `test_reset_clears_singletons`
  - `test_reset_blocked_outside_pytest`
  - `test_load_all_raises_inside_tick_context`
  - `test_load_all_ok_outside_tick_context`
  - `test_tick_context_flag_is_thread_local`
  - `test_tick_context_cleared_on_exception`
  - `test_load_all_not_called_during_warm_kernel_tick` (architecture test)

## Files Changed
- `src/content/repository.py` — Added `threading` import, `ContentHotPathViolation`, `_tick_context_active`, guard check in `load_all()`
- `src/content/warmup.py` — New file: `ContentWarmupService`
- `src/engine/kernel.py` — Added warmup call in `__init__`; refactored `tick_once()` into `tick_once()` + `_tick_once_inner()` with context flag
- `tests/unit/engine/test_content_hotpath_guard.py` — New file: 10 tests

## Completion Summary
`ContentWarmupService` created with warmup/is_warm/reset. `CatalogRepository.load_all()` now raises `ContentHotPathViolation` if called during a kernel tick. `Kernel.__init__()` warms all content singletons. `tick_once()` sets/clears the thread-local tick context flag via a try/finally. 10 tests pass, no regressions.
