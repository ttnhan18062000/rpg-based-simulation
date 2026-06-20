---
doc_id: OBS-READ-MODEL-001
title: Read Model Service Contract
layer: observability
authority: P1
audience: agent
status: active
date: 2026-06-20
tags: [read-model, api, presenter, architecture]
---

# Read Model Service Contract

## Purpose

`ReadModelService` (`src/api/read_model_service.py`) is the unified facade for all API read paths.
No API route, WebSocket handler, or external consumer may access `AuthoritativeState` directly.
All responses must be shaped through this service or the equivalent `V2EngineManager` methods
(which delegate to `ReadModelCache → StatePresenter`).

## Contract

| Method | Returns | Cost | Backing |
|--------|---------|------|---------|
| `world_status()` | Minimal world summary | O(1) cache | `ReadModelCache.get_minimal_summary()` |
| `world_full()` | Full snapshot (all entities + regions) | O(N) | `StatePresenter.present_full()` |
| `entity_status(entity_id)` | Shaped entity DTO or `None` | O(1) cache | `ReadModelCache.get_entity_dto()` |
| `entity_timeline(entity_id)` | List of serialized timeline events or `[]` | O(k events) | `entity.timeline` via manager method |
| `entities_paged(offset, limit)` | Paged entity list with metadata | O(page) cache | `ReadModelCache.get_entities_paged()` |

## Architecture Law

- **Read-only**: `ReadModelService` never mutates `AuthoritativeState`.
- **No raw state exposure**: Returned dicts are shaped projections; internal state objects are never returned.
- **Presenter chain**: `ReadModelService → V2EngineManager → ReadModelCache → StatePresenter`

## Violation Guard

The architecture test `tests/architecture/test_api_read_model_guard.py` asserts that no file
in `src/api/routes/`, `src/api/ws/`, or `src/api/server.py` imports `AuthoritativeState`
outside a `TYPE_CHECKING` block.

## Related

- `src/api/presenters/state_presenter.py` — field-level projection logic
- `src/api/read_model_cache.py` — dirty-set-driven invalidation cache
- `src/api/engine_manager.py` — thread-safe manager; holds `_latest_state` (private)
- Parity ledger: `docs/parity_ledger/infrastructure.yaml` entry INFRA-210
