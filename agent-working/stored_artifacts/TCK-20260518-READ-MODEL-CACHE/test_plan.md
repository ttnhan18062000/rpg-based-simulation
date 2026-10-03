---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260518-READ-MODEL-CACHE
artifact_type: test_plan
tags: [read, model, cache]
---

# Test Plan: Read Model and API Projection Optimization

## Verification Goals
Verify that `ReadModelCache` correctly caches and serves API DTOs with 100% semantic parity while significantly reducing CPU overhead during paged and entity lookups.

## Planned Automated Tests

### 1. Unit Tests: `tests/unit/api/test_read_model_cache.py`
- **`test_cache_minimal_summary`**: Verify `update(state)` stores and serves correct minimal summary matching `StatePresenter.present_minimal`.
- **`test_cache_hit_and_miss_counting`**: Accessing entity DTO twice without invalidation records 1 miss and 1 hit.
- **`test_selective_invalidation_by_dirtyset`**: Marking Entity A dirty in `movement_entities` invalidates Entity A's DTO while leaving Entity B's cached DTO perfectly intact.
- **`test_full_invalidation_on_empty_or_forced_scan`**: Passing `dirty_set = None` or `force_full_scan = True` invalidates the entire entity cache.
- **`test_paged_retrieval_caching`**: Paged retrieval reuses cached DTOs for clean entities.

### 2. Performance Tests: `tests/perf/test_api_projection_perf.py`
- **`test_api_projection_performance_gain`**: Create an engine manager with 500 entities. Perform 50 repeated `get_entities_paged` calls across multiple ticks with minimal dirty sets. Assert that total execution time with `ReadModelCache` is at least 3x faster than uncached `StatePresenter` generation.

## Existing Regression Tests
Run existing API and engine tests to ensure 0 regressions:
- `pytest tests/api/test_paged_logic.py`
- `pytest tests/api/test_rest_parity.py`
- `pytest tests/api/test_ws_protocol.py`
