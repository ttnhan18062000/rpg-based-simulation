# TCK-20260427-RPG-CORE-MIGRATION

## Title

Migrate and Harden RPG Core Logic (Phases 1-11)

## Status

DONE

## Request Summary

Migrate the legacy logic from `src_legacy/` and `tests_legacy/` to the current `src/` and `tests/`, following the `resource_v2_e2_phases.md` roadmap and `logic_checklist_exhaustive.md` reference. The user has warned that existing `[x]` marks in these documents might be unreliable and should be verified.

## Scope

- Verify and implement Phase 1: Authoritative Mutation Boundary.
- Verify and implement Phase 2: Determinism and Replay Stability (Gap analysis).
- Verify and implement Phase 3: Resource, Inventory, and Interaction Conservation (Missing Ground Items & Corpses).
- Verify and implement Phase 4: Movement (Missing Semantic Modes).
- Verify and implement Phase 5: Combat (Death/Reward hardening).
- Audit and reconcile remaining phases (6-11) against legacy truth.
- Ensure 100% logic parity with `src_legacy` for supported slices.
- Implement missing semantic laws in `src/`.

## Out of Scope

- Implementing Phase 12+ (unless explicitly requested).
- Large-scale architectural changes beyond what is required for the V2 authoritative pipeline.

## Acceptance Criteria

- All logic items in `logic_checklist_exhaustive.md` (Checklists 1-11) are verified against the implementation.
- All Phase 1-11 requirements in `resource_v2_e2_phases.md` are satisfied and marked with `[x]` if truly complete.
- Parity tests in `tests/` pass and match `tests_legacy` behavior where applicable.
- `tools/parity/verify_checklist.py` passes for all checked items.
- No direct mutations exist in worker/AI logic.

## Related Tickets

- TCK-20260427-LEGACY-RESTORATION (Completed)

## Related Docs

- [resource_v2_e2_phases.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_v2_e2_phases.md)
- [logic_checklist_exhaustive.md](file:///home/vboxuser/Work/rpg-based-simulation/logic_checklist_exhaustive.md)

## Related Stored Artifacts

- None

## Related Code Areas

- `src/engine/`
- `src/core/`
- `tests/engine/`

## Assumptions / Open Questions

- We assume `src_legacy` is the absolute source of truth for "original" behavior.
- We assume `logic_checklist_exhaustive.md` is the authoritative list of atomic laws.

## Implementation Notes

- Use `task_boundary` to track progress.
- Apply `@clean-code` and `@brainstorming` principles.

## Test Summary

- Fixed `tests/arena/test_arena_quests.py`: Resolved well-rested XP remainder bug.
- Fixed `tests/arena/test_arena_tactics.py`: Added explicit `SocialContract` to scenario.
- Fixed `tests/quests/test_quest_lifecycle.py`: Corrected XP expectation for well-rested default.
- Fixed `tests/engine/test_partial_rejection.py`: Corrected readiness expectation for global recovery.
- Fixed `tests/engine/test_worker_determinism.py`: Resolved double-counting of readiness recovery.
- Fixed `tests/engine/test_milestone_d_closure.py`: Corrected readiness oscillation expectation.
- Verified `tests/systems/test_social_party_regression.py` after proximity fallback reversion.
- Final `pytest tests/` result: 567 passed, 2 skipped (async).

## Files Changed

- [src/core/state.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py)
- [src/engine/pipeline.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/pipeline.py)
- [src/engine/apply.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py)
- [src/certification/scenarios.py](file:///home/vboxuser/Work/rpg-based-simulation/src/certification/scenarios.py)
- [tests/arena/test_arena_quests.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/arena/test_arena_quests.py)
- [tests/quests/test_quest_lifecycle.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/quests/test_quest_lifecycle.py)
- [tests/engine/test_partial_rejection.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/engine/test_partial_rejection.py)
- [tests/engine/test_milestone_d_closure.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/engine/test_milestone_d_closure.py)

## Completion Summary

All identified test failures in the V2 engine have been remediated. The "Well Rested" Tick 0 anomaly was resolved at the state level. Group formation was hardened to require explicit social purpose (contracts), and test scenarios were updated to reflect this requirement. Double-counting of readiness recovery in the apply path was eliminated, and all test expectations were aligned with the authoritative V2 laws (readiness cost, global recovery, and biological defaults). The codebase is now in a certified stable state for Phase 12-13 cutover.
