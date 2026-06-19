---
ticket_id: TCK-20260619-P0-CODE-INTEGRITY
phase: test_plan
---

# Test Plan

## New tests — `tests/unit/engine/test_sort_tiebreaker.py`

### test_generator_sort_is_stable_on_tied_scores
Build multiple `ConversionOption` instances all with the same `score`. Assert the returned tuple from `ConversionOptionGenerator._sort_options()` (or by calling `generate()` with a stubbed state) is identical across multiple calls. Expect the secondary key (`kind.value`) to break ties deterministically.

### test_selector_sort_is_stable_on_tied_scores
Build `(ConversionOption, float)` pairs with identical floats. Call the sort lambda twice and assert results are identical.

### test_different_scores_still_rank_correctly
Confirm that a high-scoring option still wins over a low-scoring option regardless of `.kind.value` ordering.

## Regression tests

### `pytest tests/unit/cognition/` — must show 0 errors
Previously: 15 ERRORs from `FallbackRestrictedError` in module-scoped fixture. After fix: fixture succeeds and all cognition tests run normally.

### `pytest tests/unit/core/test_registry_bridge.py` — must show 0 errors in teardown
Previously: teardown raised per test. After fix: teardown succeeds; registries reset cleanly.

### `pytest tests/integration/kernel/test_replay_determinism.py::test_transaction_trace_determinism`
Must pass — verifies the end-to-end trace is bit-identical across two independent runs.

## Out of scope
- Exhaustive progression pipeline tests — those live in `tests/unit/progression/`
- Full cognition suite coverage — only isolation/teardown regression is verified here
