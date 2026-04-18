# TCK-20260418-RESOURCE-KERNEL-M1

## Title
Milestone 1: Simulation Kernel Contract and Resource-Envelope Rulebook

## Status
DONE

## Request Summary
Establish the foundational laws, contracts, and skeletal engine structure for the fresh resource-safe simulation project (`src_v2`).

## Scope
- Define simulation kernel contract (docs & types).
- Define runtime-profile and resource-envelope contract (docs & types).
- Implement authoritative state classification.
- Create skeletal kernel phase orchestration.
- Implement deterministic contract tests.
- Ensure 100% isolation from legacy `src/` and `tests/`.

## Out of Scope
- Scheduler optimization.
- Replay implementation.
- Concurrency model.
- Resource governor implementation.
- AI logic or rich entity behavior.

## Acceptance Criteria
- [x] Contract documents (`simulation_kernel_contract_m1.md`, `runtime_profiles_m1.md`, `m1_test_matrix.md`) exist and are approved.
- [x] Code-facing contract types (`Pydantic` and `Dataclasses`) exist in `src_v2/`.
- [x] Skeletal kernel shell (`src_v2/engine/kernel.py`) orchestrates frozen phase order.
- [x] Deterministic enforcement tests (`tests_v2/`) pass 100%.
- [x] Zero legacy imports in `src_v2/` or `tests_v2/`.

## Related Tickets
- None

## Related Docs
- `resource_high_level.md`
- `resource_implementation_milestone_1.md`
- `docs/superpowers/specs/2026-04-18-resource-safe-engine-milestone-1.md`

## Related Stored Artifacts
- None

## Related Code Areas
- `src_v2/` (New)
- `tests_v2/` (New)
- `docs/engine/` (New)

## Assumptions / Open Questions
- **Assumption**: We use Pydantic for configuration and lean dataclasses for authoritative state.
- **Assumption**: "Authoritative state" is defined strictly as state required for future simulation outcomes.

## Implementation Notes
- Follow the four-step sequence: Docs -> Types -> Tests -> Shell.
- Strict isolation from legacy dependencies.

## Test Summary
- 12 contract tests passed in `tests_v2/`.
- Verifed zero legacy imports from `src/`.

## Files Changed
- `src_v2/` (all files)
- `tests_v2/` (all files)
- `docs/engine/` (all files)

## Completion Summary
Milestone 1 finalized. All laws frozen in docs and pinned in code/tests. Structural isolation achieved.
