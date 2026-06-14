---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-CONTENT-HOTPATH-GUARD
phase: open
date: 2026-06-14
tags: [resource-safety, content, hot-path, yaml, performance, architecture]
---

# TCK-20260614-CONTENT-HOTPATH-GUARD

## Title
Add Content Hot-Path Guard — prevent YAML/content loading from inside the tick pipeline

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`WorldDynamicsSystem.resolve_dynamics()` calls `get_faction_semantics_service()` (line 65), which lazily calls `CatalogRepository.load_all()` (`src/content_semantics/faction.py:26`) if the singleton is not yet warmed. `CatalogRepository.load_all()` reads and parses YAML files from disk (`src/content/repository.py:235`). If this singleton is evicted or reset between ticks, YAML parsing occurs inside the tick hot path — a CPU and allocation spike. Add a `ContentWarmupService` that loads content at boot and freezes it, and add an architecture test that confirms no `CatalogRepository.load_all()` is reachable from `Kernel.tick_once()`.

## Scope
- Add `ContentWarmupService` in `src/content/warmup.py`:
  - `warmup() -> None` — calls `get_faction_semantics_service()` (and any other lazy content singletons) to force load before the first tick
  - `is_warm() -> bool` — checks that `_semantics_service_cache` (and peers) is not None
  - `reset() -> None` — test-only reset of all content singletons (replaces direct cache manipulation in tests)
- Call `ContentWarmupService.warmup()` in `Kernel.__init__()` after world is loaded, before first tick
- Add `_content_load_guard: bool = False` flag on `CatalogRepository` — set to True after `load_all()`. Add a `_tick_context_active: threading.local` flag; if True during `load_all()`, raise `ContentHotPathViolation`
- Add `ContentHotPathViolation(RuntimeError)` exception
- Add architecture test: call `Kernel.tick_once()` on a warm kernel with `_content_load_guard` wired; assert no `ContentHotPathViolation` is raised and no `load_all()` is triggered

## Out of Scope
- Freezing/immutability of content objects (read-only handles are future work)
- Changing content schema or YAML format
- Warming non-content singletons (only `CatalogRepository` and known content loaders in scope)

## Acceptance Criteria
- `ContentWarmupService` class exists with `warmup()`, `is_warm()`, `reset()` methods
- `Kernel.__init__()` calls `ContentWarmupService.warmup()` before first tick
- `CatalogRepository.load_all()` raises `ContentHotPathViolation` if called while tick context is active
- Architecture test `test_no_content_load_in_tick_hot_path` passes against a real (minimal) kernel run
- `ContentWarmupService.reset()` correctly clears singletons for test isolation
- Existing tests that rely on lazy loading still pass (warmup is called at kernel init, covering all normal paths)

## Related Tickets
- TCK-20260614-RESOURCE-SAFETY-EPIC (parent)
- TCK-20260607-STRICT-MODE-PRODUCTION (DONE — fixed `CatalogRepository` strict mode bug; implementer must check whether that fix affected how `load_all()` detects already-loaded state, to avoid double-load after warmup)

## Related Docs
- `docs/content/pipeline_contract.md` — PRIMARY AUTHORITY: compliance IDs WORLD-CAT-004 ("Content must be loaded before any simulation tick begins") and WORLD-CAT-005 ("Content is read-only after initial load") provide explicit contract backing for this ticket; reference these in implementation notes and tests
- `docs/engine/kernel.md` — 6-phase tick pipeline (Init phase is where warmup belongs)
- `memory_features.md` (Feature 9)

## Related Code Areas
- `src/content_semantics/faction.py:21` — `get_faction_semantics_service()` singleton factory
- `src/content_semantics/faction.py:26` — `repo.load_all()` lazy call
- `src/content/repository.py:134` — `CatalogRepository` class
- `src/content/repository.py:198` — `load_all()` method
- `src/content/repository.py:235` — `yaml.safe_load(f)` disk read
- `src/engine/world_dynamics.py:65` — `get_faction_semantics_service()` call in resolve_dynamics
- `src/engine/kernel.py:34` — `Kernel.__init__()` (add warmup call here)

## Assumptions / Open Questions
- Are there other content singletons besides `_semantics_service_cache` in `faction.py` that need warming? grep for other `_*_cache = None` patterns in `src/content_semantics/` before implementing.
- Tick context detection: inject via `threading.local` in `Kernel.tick_once()` — set before entering tick, clear after. `CatalogRepository.load_all()` checks this thread-local. This is the minimal approach without requiring DI refactor.
- WORLD-CAT-004/WORLD-CAT-005 compliance: these IDs exist in `docs/content/pipeline_contract.md` — read the exact wording before implementing to confirm the contract covers singleton warm-up, not just batch load sequencing.

## Implementation Notes
- `_tick_context_active` must be `threading.local` to be thread-safe (each worker thread has its own value)
- `ContentWarmupService.reset()` is test-only — add an assertion `assert "pytest" in sys.modules` to prevent accidental use in production

## Test Summary
- `tests/unit/engine/test_content_hotpath_guard.py` (new):
  - `test_warmup_service_loads_content_before_first_tick`
  - `test_catalog_repository_raises_on_tick_context_load`
  - `test_no_content_load_in_tick_hot_path` (architecture test — runs a minimal kernel tick)
  - `test_reset_clears_singletons_for_test_isolation`
- Run: `pytest tests/unit/engine/ tests/unit/content/ -v`

## Files Changed
_(filled after implementation)_

## Completion Summary
_(filled after implementation)_
