# Phase 9 Plan: World Lifecycle Dynamics

## Goal
Implement regional monster spawning and resource replenishment to ensure long-term simulation health.

## Approach
1. Create `SpawnService` to manage regional entity density.
2. Create `ResourceEcologyService` to seed and replenish resource nodes.
3. Integrate into `WorldDynamicsSystem` with deterministic RNG.

## Verification
1000-tick stress test checking density and resource counts.
