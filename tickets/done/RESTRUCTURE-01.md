# Ticket RESTRUCTURE-01: Component-Based Codebase Restructure

## Summary
Refactor the monolithic simulation codebase into a modular, feature-based "Aspect-Oriented" architecture. This involves decomposing God Objects (WorldLoop, AI States), implementing an Aspect Framework for Entities, and reorganizing files into domain-specific feature folders.

## Motivation
- **God Objects**: `WorldLoop.py` (96KB) and `states.py` (70KB) are too large to maintain and violate SRP.
- **Tangled Logic**: Logic is grouped by technical layer rather than simulation feature, leading to fragmentation and complexity.
- **Extension Difficulty**: Adding new features requires modifying core model classes and large AI state files.
- **Maintainability**: Smaller, focused modules are easier to test, understand, and enhance safely.

## Features

### F1: Modular Entity Framework (Aspects)
- Refactor `Entity` class from `src/core/models.py` into a lightweight container.
- Implement base `Aspect` class and registry mechanism.
- Split monolithic entity properties into `CombatAspect`, `InventoryAspect`, `StatsAspect`, etc.

### F2: Feature Folder Reorganization
- Group related logic into domain folders: `src/features/combat/`, `src/features/economy/`, `src/features/world/`.
- Co-locate Models, Actions, and AI States for each domain.

### F3: AI State Decomposition
- Split the 70KB `src/ai/states.py` into individual state modules within feature folders.
- Adopt a State Strategy pattern to reduce deep inheritance complexity.

### F4: Engine God Object Split
- Decompose `src/engine/world_loop.py` into `SimulationTickRegistry`, `SnapshotManager`, and `EntityProcessor`.
- Move phase-specific logic (e.g., move resolution) into respective feature modules.

### F6: Test Suite Restructuring
- Reorganize `tests/` into `unit/`, `integration/`, `component/`, and `e2e/`.
- Ensure `unit/` tests reflect the `src/` directory structure for discoverability.

## Implementation Status
- [x] Phase 1: Foundation (Core/Platform layers)
- [x] Phase 2: Entity & Aspect Framework
- [/] Phase 3: Combat Feature Migration (Stabilization & E2E Verification Complete)
- [ ] Phase 4: Economy & World Migration
- [ ] Phase 5: Engine Loop Decomposition
- [ ] Phase 6: Final Cleanup & Dependency Resolution
- [ ] Phase 7: Test Suite Restructuring

## Historical Context & Progress
- **2026-03-20**: Completed combat system stabilization. Resolved issues with AoE targeting, AI skill selection logic, and threat table unification. All 35 E2E tests in `tests/e2e/test_combat_arena_e2e.py` are now PASSING.

## Labels
`refactor`, `architecture`, `clean-code`, `epic`, `inprogress`
