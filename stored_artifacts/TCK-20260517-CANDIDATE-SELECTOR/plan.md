# Implementation Plan: CandidateSelector & ScanPolicy

## Objectives
Implement the centralized `CandidateSelector` in `src/core/dirty.py` and its comprehensive unit test suite in `tests/unit/optimization/test_candidate_selector.py`.

## Proposed Changes

### `src/core/dirty.py`
Add `CandidateSelector` class with `@staticmethod def entities(...)`.
Map standard pipeline domains:
- `movement`: `dirty_set.movement_entities`
- `combat`: `dirty_set.combat_entities`
- `inventory`: `dirty_set.inventory_entities`
- `strategic`: `dirty_set.strategic_entities`
- `social`: `dirty_set.social_entities`
- `lifecycle`: `dirty_set.lifecycle_entities`
- `biological`: `dirty_set.biological_entities`
- `attributes`: `dirty_set.attribute_entities`
- `town`: `dirty_set.town_entities`
- `interactions`: `movement_entities | strategic_entities`
- `groups`: `movement_entities | combat_entities | social_entities`
- `shop`: `movement_entities | inventory_entities`
- `capacity`: `strategic_entities`
- `redirection`: `strategic_entities`
- `all`: `all_dirty_entities`

### `tests/unit/optimization/test_candidate_selector.py`
Create the unit test file covering the 7 required test cases:
1. `force_full_scan = True` returns all entities regardless of `dirty_set`
2. `dirty_set = None` returns all entities
3. Single domain (`{"movement"}`) returns exact subset
4. Multiple domains (`{"movement", "strategic"}`) returns exact union
5. `include_inactive = False` excludes inactive entities during full scan and dirty scan
6. `include_inactive = True` includes inactive entities during full scan
7. Result order is deterministic (sorted integer tuple)

## Verification
Run `pytest tests/unit/optimization/test_candidate_selector.py`. Ensure 100% pass rate.
