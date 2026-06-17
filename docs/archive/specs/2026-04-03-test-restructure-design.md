---
status: archive
authority: P2
audience: historical
layer: testing
original_date: 2026-04-03
---

# Test Suite Restructure and AOA Alignment Design Spec

**Date**: 2026-04-03
**Topic**: Restructuring `tests/` for Domain-First AOA Validation

## Status
**Status**: DRAFT (Awaiting Spec Review)
**Reference**: `final_implementation_plan_3.md`

---

## 1. Goal
Restructure the `tests/` directory to eliminate redundancy, align with the Aspect-Oriented Architecture (AOA), and enforce functional domain ownership. This will resolve the "split-brain" state of the test suite and ensure 100% pass rate for the combat and AI refinement modules.

## 2. Architecture: The Domain-First Test Pyramid

The test suite will be organized into four primary layers, with logic-heavy layers subdivided by functional domain.

### 2.1 Unit Layer (`tests/unit/`)
Tests pure logic and individual components in isolation.
- **core/**: Generic AOA structures, base models, serialization, and recursive freeze logic.
- **combat/**: `CombatAspect` and specialized combat services.
- **mind/**: `MindAspect` sub-models and `AIBrain` phase logic.
- **spatial/**: Position, grid, and navigation logic.
- **identity/**: Faction and tier logic.
- **progression/**: Leveling and skill mastery logic.
- **inventory/**: Item and equipment logic.
- **interaction/**: Object and building interaction logic.

### 2.2 Integration Layer (`tests/integration/`)
Tests the interaction between multiple domains or systems.
- **gameplay/**: Multi-domain flows (e.g., combat → xp gain → level up).
- **world/**: Regional events, terrain effects, and world generation.
- **infrastructure/**: Parallel workers, messaging (Kafka/RabbitMQ), and engine recovery.

### 2.3 E2E Layer (`tests/e2e/`)
Full pipeline validation using deterministic fixtures.
- **test_combat_arena_e2e.py**: Merged canonical version of the combat arena suite.
- **test_deterministic_replay.py**: Fingerprint-based simulation parity validation.

### 2.4 API Layer (`tests/api/`)
Validates presentation and transport.
- **presenters/**: `WorldPresenter` and introspection query logic.
- **transport/**: REST, SSE, and WebSocket stability.

---

## 3. Data Flow and Validation Patterns

### 3.1 The AOA Observation Pattern
Tests must observe the simulation cycle without direct side-effects:
1. **Setup**: Initialize `WorldState` with entities using refined aspect paths.
2. **Action**: Invoke a logic phase (e.g., `AIBrain.decide` or `ConflictResolver.resolve`).
3. **Capture**: Collect returned `ActionProposal` and `IntentUpdate` objects.
4. **Assert**:
   - Verify update values in the proposal (e.g., `damage`, `xp_delta`).
   - Verify state change in the world *after* application (e.g., `entity.combat.hp`).

### 3.2 Immutability Validation
Snapshots used in `DecisionPhase` must be verified for deep immutability:
- Use `pytest.raises(RuntimeError)` to ensure frozen models cannot be mutated by AI handlers.

---

## 4. Components and Implementation Rules

### 4.1 Consolidating Combat Arena E2E
- The version in `tests/e2e/` is the canonical destination.
- **Mandatory Migrations**:
  - `mob.combat_target_id` → `mob.combat.combat_target_id`.
  - `CombatTraceUpdate` must wrap details in a `CombatTraceRecord` object.
  - Failures in `TestThreatSystemE2E` and `TestAIRefinementE2E` must be resolved by fixing the data structure mismatch in `src/actions/combat.py`.

### 4.2 AOA Integrity Sentinel
Create `tests/unit/core/test_aoa_boundary_integrity.py`:
- Uses `inspect` or `sys.modules` to look for legacy imports.
- Ensures `Entity` model does not contain `.stats` or flat `mind` proxies.

---

## 5. Migration Strategy

1. **Phase 1: Subdirectory Creation**: Scaffold all new domain folders.
2. **Phase 2: E2E Consolidation**: Merge the split-brain `test_combat_arena_e2e.py` and fix combat update bugs.
3. **Phase 3: Mass Move**: Relocate 30+ root files to their new domains.
4. **Phase 4: Import Correction**: Batch update imports in all moved files.
5. **Phase 5: Final Purge**: Delete root duplicates and legacy `test_epic_*.py` scaffolds.

## 6. Success Criteria
- [ ] No test files remain in the root of `tests/` except `conftest.py`.
- [ ] `pytest tests/e2e/test_combat_arena_e2e.py` returns 41/41 PASSED.
- [ ] Entire suite collects and executes with no structural regressions.
- [ ] All entity attribute access follows `entity.<aspect>.<field>` pattern.
