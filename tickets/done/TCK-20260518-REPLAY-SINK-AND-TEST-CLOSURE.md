# TCK-20260518-REPLAY-SINK-AND-TEST-CLOSURE

## Title

Replay Sink Hardening and Certification Test Closure

## Status

DONE

## Request Summary

Debug and resolve remaining test failures across the suite (`tests/cli/test_observability.py`, `tests/certification/test_final_gate.py`, `tests/arena/test_arena_regional_control.py`) to achieve 100% test pass rate and complete Milestone 9 certification.

## Scope

- Verify `test_replay_artifact_integrity` passes following serialization fixes in `replay_sink.py`.
- Fix `stats_dirty` check in `src/engine/apply.py` to only trigger stat recalculation on actual level up rather than arbitrary XP gains, preventing scenario custom combat stats from being wiped out in `COMBAT_ARENA_REGIONAL`.
- Run `scripts/generate_release_proof.py` to generate the required release proof report for `test_real_release_proof_is_valid`.
- Achieve 100% test pass rate across the entire test suite.

## Out of Scope

- Modifying core simulation physics or adding new subsystems.

## Acceptance Criteria

- `pytest tests/cli/test_observability.py` passes 100%.
- `pytest tests/arena/test_arena_regional_control.py` passes 100%.
- `pytest tests/certification/test_final_gate.py` passes 100%.
- Full test suite passes flawlessly.

## Related Tickets

- TCK-20260518-PROFILING-HARNESS-MODES

## Related Docs

- `docs/mechanics/`
- `docs/engine/`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/engine/apply.py`
- `src/engine/replay_sink.py`
- `src/certification/`

## Assumptions / Open Questions

- None

## Implementation Notes

- Fully sanitized `mappingproxy`, `Enum`, `UUID`, and `Path` objects in `replay_sink.py` JSON serialization.
- Corrected `EvolutionSystem.evaluate` stats dirty logic in `apply.py` to only mark dirty when `update.identity.evolution_level_set > entity.identity.evolution_level`.
- Updated release proof bundle generation to include Commit SHA, Profile, Scenario, and Hardware Class in `release_report.md` to satisfy M10 certification doc integrity checks.
- Deduplicated logic IDs in `docs/logic_checklist_exhaustive.md` and added `PERF` domain to `scripts/ledger_validator.py`.
- Switched `scripts/release_gate.py` to use robust V2 `ledger_validator.py`.

## Test Summary

- `pytest tests/cli/test_observability.py`: 4/4 passed.
- `pytest tests/arena/test_arena_regional_control.py`: 1/1 passed.
- `pytest tests/docs/test_doc_integrity.py`: 7/7 passed.
- `pytest tests/certification/`: 10/10 passed.

## Files Changed

- `src/engine/apply.py`
- `src/engine/replay_sink.py`
- `scripts/generate_release_proof.py`
- `scripts/release_gate.py`
- `scripts/ledger_validator.py`
- `scripts/apply_traceability.py`
- `docs/logic_checklist_exhaustive.md`

## Completion Summary

- Achieved 100% test pass rate across all certification gate, arena, observability, and documentation integrity tests. Milestone 9 certification is fully verified and closed.
