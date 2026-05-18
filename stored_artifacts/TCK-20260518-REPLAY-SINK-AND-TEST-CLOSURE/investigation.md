# Investigation Notes: Replay Sink Hardening and Test Closure

## Findings

1. **Replay Serialization (`test_replay_artifact_integrity`)**:
   - `test_replay_artifact_integrity` in `tests/cli/test_observability.py` previously failed due to JSON serialization errors on `mappingproxy` objects within entity update dictionary payloads.
   - Fixed by enhancing `_clean_for_json` in `src/engine/replay_sink.py` to deeply sanitize all `Mapping`, `Enum`, `UUID`, and `Path` objects.
   - Verification: `pytest tests/cli/test_observability.py` passed successfully (4/4 passed).

2. **Regional Conquest Debuff (`test_arena_conquest_and_debuff`)**:
   - Failed in `tests/arena/test_arena_regional_control.py` with `AssertionError: assert 12 == 80`.
   - Root Cause: In `COMBAT_ARENA_REGIONAL`, the hero starts with custom scenario combat stats (`atk=100, def_stat=20, speed=10`) but default base attributes (`strength=5`). During the 1-tick scenario run, the hero kills a goblin and gains XP.
   - When the kill reward is processed, `EvolutionSystem.evaluate` runs on the entity update and ALWAYS sets `evolution_level_set = new_level` on `IdentityUpdate` (even when `new_level == old_level`, i.e., level 5).
   - In `src/engine/apply.py`, the `stats_dirty` guard checked `update.identity.evolution_level_set is not None`. Because `EvolutionSystem` unconditionally set `evolution_level_set=5`, this check evaluated to True despite no actual level up.
   - When `stats_dirty` evaluated to True, `apply.py` called `SkillScalingService.get_effective_stats(...)` with default base stats (`base_atk=10, base_def=5, base_hp=100`). This recalculated `atk` as `10 + int(5 * 0.5) = 12`, completely overwriting the scenario's custom `atk` of 80 (after regional debuff).
   - Solution: Refactor `stats_dirty` in `src/engine/apply.py` to check `update.identity.evolution_level_set is not None and update.identity.evolution_level_set > entity.identity.evolution_level`.

3. **Release Proof Gate (`test_real_release_proof_is_valid`)**:
   - Failed due to missing `reports/release_proof/` directory.
   - Solution: Run `python scripts/generate_release_proof.py` to generate real proof artifacts.
