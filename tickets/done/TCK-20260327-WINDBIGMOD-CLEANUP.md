# TCK-20260327-WINDBIGMOD-CLEANUP: Architectual Stat Logic Refactor (BigMod)

## Goal
Remove all backward compatibility shims and legacy `effective_*()` methods from the `Entity` model, replacing them with a clean, properties-driven `StatsProxy` pattern. This simplifies the core model and aligns the simulation with strict Clean Code principles.

## User Review Required
> [!IMPORTANT]
> This is a **breaking change** that affects nearly every system in the project (Combat, AI, Movement, Systems, and all unit tests).

## Scope
- `src/core/stats_proxy.py`: Full redesign.
- `src/core/models.py`: Remove legacy `__init__` logic and `effective_*` methods.
- Everywhere: Replace `effective_atk()` etc. with `stats.atk`.
- Tests: Synchronize the entire suite.

## Acceptance Criteria
- [x] `StatsProxy` has no `__getattr__` or `__setattr__`.
- [x] `Entity` class has no methods starting with `effective_`.
- [x] Full `pytest` execution passes with 100% success.
- [x] `EntitySchema` remains valid for the frontend.

## Related Tickets
- `TCK-20260327-WINDBIGMOD` (Implementation)

## Status
DONE
