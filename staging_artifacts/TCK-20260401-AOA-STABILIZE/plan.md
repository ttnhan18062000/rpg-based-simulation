# AOA Runtime & Test Suite Stabilization Plan

Resolving the remaining 29 failures in the 748-test suite to achieve 100% pass rate and enforce AOA integrity.

## Proposed Changes

### Core & Systems
- **[MODIFY] src/engine/phases/resolution.py**: Update `hero_lifecycle.tick` to `on_tick(system_ctx, tick)`.
- **[MODIFY] src/ai/goals/base.py**: Harden `manhattan` and `evaluate` to handle serialized positions in snapshots.

### Test Suite (AOA Compliance)
- **[MODIFY] tests/component/engine/test_subsystem_ticks.py**: Update `mind.ai_state` to `mind.decision.ai_state`.
- **[MODIFY] tests/helpers/combat_arena.py**: Update helper for aspect-based access.
- **[MODIFY] tests/e2e/test_combat_arena_e2e.py**: Purge legacy shims.

## Verification Plan
- Run `tests/component/engine/test_subsystem_ticks.py`
- Run `tests/e2e/test_combat_arena_e2e.py`
- Run full 748-test suite.
