# Implementation Plan: Replay Sink Hardening and Test Closure

## Proposed Changes

### `src/engine/apply.py`
- Refactor `stats_dirty` calculation around line 820.
- Update `update.identity.evolution_level_set is not None` to `(update.identity.evolution_level_set is not None and update.identity.evolution_level_set > entity.identity.evolution_level)`.

### Release Proof Generation
- Run `python scripts/generate_release_proof.py` to populate `reports/release_proof/`.

## Verification Plan
- Run `pytest tests/arena/test_arena_regional_control.py`.
- Run `pytest tests/certification/test_final_gate.py`.
- Run full pytest test suite to ensure 100% pass rate.
