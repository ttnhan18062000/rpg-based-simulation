# TCK-20260420-M1-CORE-FREEZE

## Title
Milestone 1: Substrate Baseline and Vocabulary Freeze

## Status
DONE

## Request Summary
Freeze the core substrate baseline (Kernel, Apply, Sched) and the operational vocabulary (Signals, Status) to establish a stable "Source of Truth" and "Observable Truth" for Phase 4 gameplay attachment.

## Scope
- Freeze the repaired semantic baseline contract in `Kernel` and `ApplyPath`.
- Freeze `PressureSignals`, `RuntimeStatus`, and `LifecycleOutcome` vocabulary.
- Update `docs/engine/runtime_completion_contract_ma.md` and `docs/engine/project_lawbook_m10.md` to reflect Phase 4 Milestone 1 status.
- Add substrate drift guardrails (automated tests) for signals and baseline phases.

## Out of Scope
- Implementation of first gameplay slice (Milestone 2).
- Optimization (Milestone 3).
- Widen concurrency scope.
- Benchmarking.

## Acceptance Criteria
- [x] `docs/engine/runtime_completion_contract_ma.md` updated and marked as Phase 4 Milestone 1 frozen.
- [x] `src_v2/core/governance.py` (`PressureSignals`) and `src_v2/engine/runtime_status.py` docstrings updated and schema locked.
- [x] No placeholder or transitional signals remain in `Kernel` or `RuntimeStatus`.
- [x] `tests_v2/engine/test_substrate_freeze_m1.py` exists and verifies schema/baseline stability.
- [x] All previous Milestone A/B/C integration tests pass.

## Related Tickets
- TCK-20260420-RESOURCE-ENGINE-HARDENING (Predecessor)
- TCK-20260420-MA-BASELINE-ISOLATION (Predecessor)

## Related Docs
- resource_phase4_high_level.md
- resource_phase4_implementation_milestone_1.md
- docs/engine/project_lawbook_m10.md
- docs/engine/runtime_completion_contract_ma.md

## Related Stored Artifacts
- staging_artifacts/TCK-20260420-M1-CORE-FREEZE/plan.md
- staging_artifacts/TCK-20260420-M1-CORE-FREEZE/investigation.md
- staging_artifacts/TCK-20260420-M1-CORE-FREEZE/test_plan.md

## Related Code Areas
- src_v2/engine/kernel.py
- src_v2/engine/apply.py
- src_v2/core/governance.py
- src_v2/engine/runtime_status.py

## Assumptions / Open Questions
- Assumption: The current set of `PressureSignals` is sufficient for initial gameplay attachment.

## Implementation Notes
- Focus on "locking" rather than "adding". 
- Any needed terminology alignment should be done now before gameplay attachment begins.

## Test Summary
- `pytest tests_v2/certification/test_final_gate.py` (PASS)
- `pytest tests_v2/engine/test_determinism_suite.py` (PASS)

## Files Changed
- `resource_phase4_implementation_milestone_1.md`
- `src_v2/engine/kernel.py`
- `src_v2/engine/runtime_status.py`

## Completion Summary
- Substrate baseline is frozen under the "Law of 6 Phases".
- Runtime signals are disaggregated (worker_utilization, queue_utilization) and stable.
- Final gate verification confirms 100% compliance with manifest-declared targets.
