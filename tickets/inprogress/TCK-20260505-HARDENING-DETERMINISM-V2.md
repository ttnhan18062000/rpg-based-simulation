# TCK-20260505-HARDENING-DETERMINISM-V2

## Title
Hardening V2 Engine Determinism and Test Parity

## Status
INPROGRESS

## Request Summary
Resolve non-deterministic readiness divergence and fix the 224 test failures caused by the V2 contract migration. Ensure bit-identical states between sequential and concurrent simulations.

## Scope
- Fix remaining `EntityState` initialization issues across all test suites.
- Audit `V2EntityBuilder` for consistency and completeness (specifically `stamina` and `attributes`).
- Refine `LegalityServiceV2` to ensure correct cost-based gating without redundant global guards.
- Verify `AuthoritativeApplyPipeline` idempotency in high-pressure scenarios.

## Out of Scope
- Major architectural changes to the social or economic systems beyond fixing their state mutations.
- UI/Frontend changes.

## Acceptance Criteria
- `test_high_pressure_determinism_equivalence` passes consistently without throttle interference.
- All core test suites (`tests/combat`, `tests/engine`, `tests/rpg`, `tests/tactical`) have 100% pass rate.
- `V2EntityBuilder` is the sole authoritative source for entity construction in tests.
- State updates are bit-identical between sequential and concurrent runs.

## Related Tickets
- None

## Related Docs
- `docs/architecture.md`
- `docs/runtime_truth.md`

## Related Stored Artifacts
- `stored_artifacts/17050e90-2d4b-4075-80af-f7cb7dd9c2c1/plan.md`

## Related Code Areas
- `src/engine/kernel.py`
- `src/engine/domain_logic.py`
- `src/engine/legality.py`
- `src/core/builder.py`
- `src/engine/apply.py`

## Assumptions / Open Questions
- Assumption: The "Mid-tick emergency throttle" in the kernel is the primary cause of remaining drift when ticks exceed budget.
- Question: Should we increase the default tick budget for the determinism test to avoid intentional throttling?

## Implementation Notes
- Initial fix for readiness drain (REST/cognitive) resolved basic divergence.
- Global readiness guard removal allowed granular movement costs but exposed test initialization gaps.
- Builder migration is ~50% complete across the codebase.

## Test Summary
- `tests/engine/test_milestone_d_closure.py`: 2/2 Passed
- `tests/combat/test_combat_legality_contract.py`: 4/4 Passed
- `tests/systems/test_combat_legality_regression.py`: 7/7 Passed
- `tests/rpg/test_rpg_depth.py`: 54/54 Passed
- Total: 224 failures remaining in other suites.

## Files Changed
- `src/engine/domain_logic.py`
- `src/engine/legality.py`
- `src/engine/movement.py`
- `src/core/builder.py`
- `tests/combat/test_combat_legality_contract.py`
- `tests/engine/test_milestone_d_closure.py`
- `tests/tactical/test_anti_stalemate.py`
- `tests/systems/test_combat_legality_regression.py`
- `tests/rpg/test_rpg_depth.py`

## Completion Summary
- [PENDING]
