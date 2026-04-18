# Design Spec: Core Rulebook Hardening (Milestone 1)

**Date**: 2026-04-18
**Topic**: Rulebook Hardening and Quiet-Tick Integrity
**Status**: DRAFT

## 1. Goal
Harden the `LegalityService` as the authoritative source of truth for all spatial and combat legality rules, and ensure that passive progression systems (biological decay, lifecycle, group bonding) are protected against tick-drift.

## 2. Architecture Changes

### 2.1 LegalityService Expansion
The `LegalityService` will be expanded to include:
- `get_occupant_id(pos, world) -> int | None`: Returns the ID of the living entity at the given position. Encapsulates spatial querying for the "rulebook".
- `check_targeting_legality(origin, target, range, world, requires_los=True) -> bool`: Encapsulates both Manhattan distance check and Line-of-Sight (LOS) check. This moves the grid-level LOS responsibility into the rulebook.
- `get_distance(a, b) -> int`: Authoritative Manhattan distance retrieval.

### 2.2 Movement Model Integration
Refactor `src/core/logic/movement_model.py`:
- Replace `_get_blocker` with `LegalityService.get_occupant_id`.
- Replace `cand.manhattan(target_pos)` with `LegalityService.get_distance`.
- Ensure all movement proposals are routed through high-level `LegalityService` checks.

### 2.3 Combat Action Integration
Refactor `src/actions/combat.py`:
- Use `LegalityService.check_targeting_legality` inside `validate()`.
- Remove raw `world.grid.has_line_of_sight` calls.

## 3. Quiet-Tick Drift Guards
We will implement regression tests that verify the "Passive Progression Set".

### 3.1 Passive Progression Set
The following systems are guaranteed to advance every tick:
- `ActionSystem._apply_biological_decay` (Hunger, Sleep)
- `HeroLifecycleSystem.on_tick` (Bonding, aging)
- Registered `Subsystems` in `SystemManager` (Combat, Progression, Quest, etc.)

### 3.2 Integrity Tests
New tests in `tests/engine/test_quiet_tick_integrity.py`:
- `test_total_quiet_tick`: 0 entities ready, ensure tick increments and decay happens.
- `test_no_proposal_quiet_tick`: Entities ready but choose to REST, ensure passive systems still tick.
- `test_system_manager_advancement`: Verify registered subsystems receive the tick signal.

## 4. Design for Isolation
`LegalityService` remains a stateless static service, maintaining its ease of testing and isolation. By consolidating LOS and Occupancy, we reduce the "surface area" of raw grid/spatial math that can drift between implementation layers.

## 5. Error Handling
- `get_occupant_id` will return `None` if no living entity is found.
- `check_targeting_legality` will return `False` if range or LOS (if required) fails.
