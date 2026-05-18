# Plan - TCK-20260420-CORE-MOVEMENT-SLICE

## Goal
Implement deterministic grid-based movement resolve logic in V2 engine substrate with bit-identical parity to the original `src` engine.

## Scope
- Port `LegalityService` essentials (occupancy, terrain).
- Implement `MovementSystem` for cardinal step resolution.
- Integrate into `LocalSequentialExecutor` and `SimulationDomainLogic`.

## Proposed Changes
1. Update `AuthoritativeState` with spatial truth.
2. Implement `LegalityServiceV2` and `MovementSystem`.
3. Update `WorkerPacket` for context-aware validation.
4. Verify results against captured oracle.
