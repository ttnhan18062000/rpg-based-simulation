---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260510-CORE-IMPORT-STABILIZATION
phase: done
date: 2026-05-10
tags: [core, import, stabilization]
---

# TCK-20260510-CORE-IMPORT-STABILIZATION

## Title
Stabilizing Engine Import Paths & Social Domain Unification

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Resolve import resolution failures introduced during modularization and consolidate social domain logic (Contracts, Memory, Appraisal) into a hardened, authoritative structure while maintaining backward compatibility.

## Scope
- [x] Fix re-exports in `src/systems/belief.py`.
- [x] Fix re-exports and missing imports in `src/systems/genetics.py`.
- [x] Fix re-exports in `src/systems/narrative.py`.
- [x] Fix re-exports in `src/systems/social_memory.py`.
- [x] Merge `ContractService` and `SocialContractSystem` into `src/systems/social_systems/contracts.py`.
- [x] Update `transition_contract` return signature for pipeline compatibility.
- [x] Implement betrayal and social update consequences in contract resolution.

## Out of Scope
- Major architectural changes to other subsystems.
- Modifying legacy tests in `tests_legacy/`.

## Acceptance Criteria
- [x] All import errors in `src/` and `tests/` resolved.
- [x] `SocialContractSystem` unified and hardened.
- [x] Backward compatibility maintained via wrappers in `src/systems/social_contract.py` and `src/social/contracts.py`.
- [x] 413 tests passing across Cognition, Progression, Social, Strategic, Combat, and Core domains.

## Related Tickets
- [TCK-20260510-PIPELINE-DECOMPOSITION](file:///home/vboxuser/Work/rpg-based-simulation/tickets/done/TCK-20260510-PIPELINE-DECOMPOSITION.md)

## Related Docs
- [walkthrough.md](file:///home/vboxuser/Work/rpg-based-simulation/walkthrough.md)

## Related Stored Artifacts
- [stored_artifacts/TCK-20260510-CORE-IMPORT-STABILIZATION/](file:///home/vboxuser/Work/rpg-based-simulation/stored_artifacts/TCK-20260510-CORE-IMPORT-STABILIZATION/)

## Related Code Areas
- `src/systems/`
- `src/social/`
- `src/systems/social_systems/`

## Implementation Notes
- Used façades to bridge the gap between modularized logic and legacy import paths.
- Enforced strict state transitions in contracts while allowing shortcuts for recruitment flows.

## Test Summary
- `pytest tests/cognition tests/progression tests/unit/social tests/unit/strategic tests/unit/combat tests/unit/core -q`
- 413 passed, 1 warning in 11.07s

## Files Changed
- `src/systems/belief.py`
- `src/systems/genetics.py`
- `src/systems/narrative.py`
- `src/systems/social_memory.py`
- `src/systems/social_contract.py`
- `src/social/contracts.py`
- `src/systems/social_systems/contracts.py`

## Completion Summary
Resolved the instability caused by the recent modularization effort. The engine now correctly resolves all imports while benefiting from a more cohesive social domain implementation. The 413 passing tests confirm that no regressions were introduced during the stabilization process.
