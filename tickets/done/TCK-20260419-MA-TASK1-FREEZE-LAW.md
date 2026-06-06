# TCK-20260419-MA-TASK1-FREEZE-LAW

## Title
Freeze exact Milestone A runtime law set

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Write the finished law set for the deterministic single-process baseline so implementation, tests, and later milestones all target one exact contract.

## Scope
- [x] Create `docs/engine/runtime_completion_contract_ma.md`
- [x] Create `docs/engine/ma_test_matrix.md`
- [x] Add code-facing law comments to `src/engine/kernel.py`, `apply.py`, `checkpoint.py`, `scheduler.py`

## Out of Scope
- Replay hardening (beyond isolation)
- Worker deepening
- Certification broadening
- RPG attachment

## Acceptance Criteria
- [x] One exact runtime-completion contract document.
- [x] One exact test matrix document.
- [x] Law comments in core engine files.
- [x] Document defines: phases, ownership, mutation boundaries, work-order rules, checkpoint rules, out-of-scope list, prohibit placeholders.

## Related Tickets
- None

## Related Docs
- `resource_high_level_v3.md`
- `resource_implementation_v3_milestone_a.md`
- `resource_handbook.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260419-MA-TASK1-FREEZE-LAW/investigation.md`
- `stored_artifacts/TCK-20260419-MA-TASK1-FREEZE-LAW/plan.md`
- `stored_artifacts/TCK-20260419-MA-TASK1-FREEZE-LAW/test_plan.md`

## Related Code Areas
- `src/engine/kernel.py`
- `src/engine/apply.py`
- `src/engine/checkpoint.py`
- `src/engine/scheduler.py`

## Assumptions / Open Questions
- Assumption: The existing 6-phase sequence is the correct baseline to freeze. (Confirmed in code).

## Implementation Notes
- Comprehensive expansion of the contract document to meet all Milestone A "Done" gates.
- Added explicit tie-break rules for the scheduler.
- Pinned authoritative field boundaries for hashing.

## Test Summary
- Manual consistency check passed.
- All existing engine tests (`tests/engine`) passed.

## Files Changed
- `docs/engine/runtime_completion_contract_ma.md`
- `docs/engine/ma_test_matrix.md`
- `src/engine/kernel.py`
- `src/engine/apply.py`
- `src/engine/checkpoint.py`
- `src/engine/scheduler.py`

## Completion Summary
- Finalized the Milestone A runtime contract and test matrix. This establishes the "Law" for the deterministic single-process baseline, which is the foundation for all subsequent work in Milestone A.
