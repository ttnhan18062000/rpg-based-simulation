---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260418-RESOURCE-KERNEL-M1
phase: done
date: 2026-04-18
tags: [resource, kernel, m1]
---

# TCK-20260418-RESOURCE-KERNEL-M1

## Title
Milestone 1: Simulation Kernel Contract and Resource-Envelope Rulebook

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Establish the foundational laws, contracts, and skeletal engine structure for the fresh resource-safe simulation project (`src`).

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
- [x] Code-facing contract types (`Pydantic` and `Dataclasses`) exist in `src/`.
- [x] Skeletal kernel shell (`src/engine/kernel.py`) orchestrates frozen phase order.
- [x] Deterministic enforcement tests (`tests/`) pass 100%.
- [x] Zero legacy imports in `src/` or `tests/`.

## Related Tickets
- None

## Related Docs
- `resource_high_level.md`
- `resource_implementation_milestone_1.md`
- `docs/superpowers/specs/2026-04-18-resource-safe-engine-milestone-1.md`

## Related Stored Artifacts
- None

## Related Code Areas
- `src/` (New)
- `tests/` (New)
- `docs/engine/` (New)

## Assumptions / Open Questions
- **Assumption**: We use Pydantic for configuration and lean dataclasses for authoritative state.
- **Assumption**: "Authoritative state" is defined strictly as state required for future simulation outcomes.

## Implementation Notes
- Follow the four-step sequence: Docs -> Types -> Tests -> Shell.
- Strict isolation from legacy dependencies.

## Test Summary
- 12 contract tests passed in `tests/`.
- Verifed zero legacy imports from `src/`.

## Files Changed
- `src/` (all files)
- `tests/` (all files)
- `docs/engine/` (all files)

## Completion Summary
Milestone 1 finalized. All laws frozen in docs and pinned in code/tests. Structural isolation achieved.
