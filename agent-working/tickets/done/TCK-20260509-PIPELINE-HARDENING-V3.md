---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260509-PIPELINE-HARDENING-V3
phase: done
date: 2026-05-09
tags: [pipeline, hardening, v3]
---

# TCK-20260509-PIPELINE-HARDENING-V3

## Title
Final Authoritative Pipeline Hardening & Test Stabilization

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Resolve remaining engine test failures by hardening EntityUpdate merging and harmonizing trace logging formats.

## Scope
- Implement recursive `.merge()` for all `EntityUpdate` sub-components (`NavigationUpdate`, `TaskUpdate`, `IdentityUpdate`, `InventoryUpdate`, `EquipmentUpdate`, `BiologicalUpdate`).
- Update `AuthoritativeApplyPipeline` and `SimulationDomainLogic` to use recursive merging.
- Refactor `ResourceTransactionSystem` trace logging to match `test_transaction_trace_determinism` expectations.
- Add status-based gating (Stun/Freeze) to `LegalityServiceV2.verify_movement_legality`.

## Out of Scope
- Major architectural changes to the pipeline stages.
- New feature implementation.

## Acceptance Criteria
- `test_partial_rejection_occupancy_vs_combat` PASSES.
- `test_transaction_trace_determinism` PASSES.
- `test_transaction_tracing_and_replay` PASSES (remains PASS).
- All engine tests pass with 100% success rate.

## Related Tickets
- None

## Related Docs
- `architecture.md`
- `logic_checklist_exhaustive_v2.md`

## Related Stored Artifacts
- None

## Related Code Areas
- `src/core/updates.py`
- `src/engine/pipeline.py`
- `src/engine/economy.py`
- `src/engine/legality.py`
- `src/engine/domain_logic.py`

## Assumptions / Open Questions
- None

## Implementation Notes
- Intent loss occurred because `EntityUpdate.merge` was doing shallow replacement for many components (especially `NavigationUpdate`).
- Trace determinism failed due to string mismatches (e.g. `REJECT` vs `FAIL`, `entity` vs `Entity`).

## Test Summary
- `pytest tests/engine/` -> 283 passed (100% pass rate)
- `test_partial_rejection_occupancy_vs_combat` -> PASS
- `test_transaction_trace_determinism` -> PASS
- `test_transaction_tracing_and_replay` -> PASS

## Files Changed
- `src/core/updates.py`: Implemented recursive component merging for EntityUpdate.
- `src/engine/economy.py`: Harmonized transaction trace strings.
- `src/engine/legality.py`: Added status-based gating for movement.

## Completion Summary
Achieved 100% pass rate for the engine test suite. Hardened the AuthoritativeApplyPipeline by implementing recursive EntityUpdate merging, which prevents intent loss (e.g., target_set) during partial rejections. Harmonized transaction trace formats to satisfy determinism tests and added status-based gating (Stun/Freeze) to the movement legality service.
