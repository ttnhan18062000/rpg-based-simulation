# Plan: Backend Restructure (TCK-20260328)

## Phase 1: Fix Regression Blockers [COMPLETED 🟢]
- [x] Fix NameError in CombatArena.
- [x] Fix AI transition error in WanderHandler.
- [x] Resolve maze navigation distraction in integration tests.
- [x] Verify full 628-test pass.

## Phase 2: Subsystem Extraction [COMPLETED 🟢]
- [x] Create `src/systems/telemetry_system.py` and move `_update_detailed_metrics` there.
- [x] Create `src/systems/world_evolution_system.py` and move `_update_world_evolution` there.
- [x] Integrate `CombatTrackingSystem` into `src/systems/combat_system.py`.
- [x] Extract death logic into `src/systems/lifecycle_system.py` or similar.
- [x] Update `WorldLoop` to delegate to these systems via `SystemManager`.

## Phase 3: Finalize StatsProxy Cleanup [COMPLETED 🟢]
- [x] Search for all remaining `effective_` method usages.
- [x] Remove `effective_` shims from `Entity`.
- [x] Ensure all combat and progression logic uses the new aspect-oriented `StatsProxy`.

## Verification Plan
- [x] 100% pytest pass.
- [x] Manually verify Kafka/Redis persistence.
- [x] Verify metrics exposure in Prometheus.
