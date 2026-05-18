# TCK-20260421-V2-TEST-HARDENING

## Title
V2 Test Suite Hardening & Phase 4 Alignment

## Status
DONE

## Request Summary
Verify all `tests` and ensure they pass after the engine reconstruction.

## Scope
- Fix regressions in substrate freeze tests due to Phase Law updates.
- Resolve async races in Replay Manager tests.
- Repair link integrity in documentation tests.
- Hardened Final Gate certification test against stale/missing proof bundles.

## Acceptance Criteria
- 100% pass rate for `tests` (168 tests).
- Robust handling of async persistence in tests.
- Alignment of doc links with real file structure.

## Related Tickets
- TCK-20260420-PHASE-LAW
- TCK-20260420-REPLAY-RACE

## Implementation Notes
- Updated `TickPhase` enum checks in tests to reflect 7-phase reality.
- Introduced `wait_for_file` patterns in replay tests.
- Added `ensure_passing_bundle` fixture to `test_final_gate.py` for runtime stability.

## Test Summary
- `pytest tests`: 168 passed.

## Files Changed
- `tests/engine/test_substrate_freeze_m1.py`
- `tests/engine/test_milestone_b_closure.py`
- `tests/engine/test_replay_contract.py`
- `tests/engine/test_replay_chunk_rotation.py`
- `tests/engine/test_replay_pressure.py`
- `tests/certification/test_final_gate.py`
- `tests/docs/test_doc_integrity.py`
- `docs/engine/project_lawbook_m10.md`
- `docs/engine/manifest.json`

## Completion Summary
Verified and hardened the entire V2 test suite. The engine is now certified passing across all 168 canonical engine tests.
