# Investigation: Phase 3 Routine and Biological Needs

## Codebase Findings
- `RoutineState` is already defined in `MindAspect` with `sleep_debt`, `hunger_level`, `is_sleeping`, and `active_start_hour`/`active_end_hour`.
- `ActionSystem` has a stub `_apply_biological_decay` that increments needs per tick.
- `AIBrain` already calls `RoutineService.calculate_routine_biases` to adjust goal utilities.
- `SleepScorer` and `EatScorer` exist in `scorers.py` but are basic.
- `SleepingHandler` and `EatingHandler` are in `routine.py` but `EatingHandler` needs logic to actually use food items.

## Duplication/Conflict Scan
- No existing `RoutineSystem` was found; the logic is currently inside `ActionSystem`. This is AOA-compliant as `ActionSystem` already handles authoritative updates, but I will consolidate it for clarity.
- `RestAction` exists but needs to be updated to handle `RoutineUpdate`.
- `data/items.json` contains `warm_berries` with `heal_amount` but no `hunger_reduction`.

## Reused Patterns
- `IntentUpdate` (specifically `RoutineUpdate`) will be used for all biological state changes.
- `RoutineService` will be the central stateless calculator for biological biases, following the `SocialAppraisalService` pattern.

## Assumptions
- 1 hour = 10 ticks.
- Simulation runs at approximately 1-2 ticks per second, meaning a "day" is 240 ticks (~4 minutes in real time).

## Risks
- Biological decay might be too fast/slow. I will expose decay rates to `SimulationConfig`.
- Entities might get "stuck" in a sleep loop if recovery is too slow.
