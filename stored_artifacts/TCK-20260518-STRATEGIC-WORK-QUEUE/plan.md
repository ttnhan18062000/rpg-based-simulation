# Implementation Plan: StrategicWorkQueue

## Proposed Changes

### `src/systems/strategic_systems/work_queue.py` [NEW]
- Implement `StrategicWorkQueue` class with `build(state, update, dirty, budget) -> Tuple[int, ...]`.
- Filter entities for active lifecycle, alive combat, and non-incapacitation.
- Categorize entities into 7 priority tiers.
- Deduplicate while preserving priority tier order and truncate at `budget`.

### `src/systems/strategic_systems/intelligence.py`
- In `fused_strategic_pass` and `evaluate_all_strategic_intents`, use `StrategicWorkQueue.build(state, update, update.dirty_set, budget=50)` to get candidate entities.

## Verification Plan
- Create `tests/unit/optimization/test_strategic_work_queue.py`.
- Verify all 7 priority tiers, budget enforcement, starvation prevention, and `force_full_scan`.
- Execute unit tests and full regression verification.
