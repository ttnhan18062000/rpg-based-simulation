# Implementation Plan: TCK-20260408-PHASE3-ROUTINE

## 1. Data Layer
- Update `data/items.json`:
    - `wild_berries`: add `"hunger_reduction": 0.3`
    - `herb`: add `"hunger_reduction": 0.1`

## 2. Action Layer
- Create `src/actions/eat.py`:
    - `validate()`: Actor must be alive and have food item (or be in a food-source area).
    - `apply()`: Find food item in inventory. If found, emit `RoutineUpdate(hunger_delta=-item.hunger_reduction)` and `ProgressionUpdate(inventory_remove=[item_id])`.
- Update `src/actions/rest.py`:
    - If `AIState` is `SLEEPING`, emit `RoutineUpdate(is_sleeping=True)`.

## 3. System Layer
- Update `src/systems/gameplay/action_system.py`:
    - Refine `_apply_biological_decay`.
    - Ensure forced sleep (passing out) at `sleep_debt >= 1.0` emits a notification/event.
    - Handle `RoutineUpdate` in `_apply_updates`.

## 4. AI Layer
- Update `src/ai/goals/scorers.py`:
    - Refactor `SleepScorer` and `EatScorer` to use `RoutineService`.
- Update `src/ai/states/routine.py`:
    - `EatingHandler`: Add logic to select a food item from inventory to "use".

## 5. API Layer
- Update `src/api/presenters/entity_presenter.py`:
    - Ensure `to_full_schema` correctly populates `RoutineStateSchema`.

## 6. Verification
- Run unit tests for `RoutineService`.
- Create integration test for full biological loop.
