# TCK-20260428-PH9-WORLD-LIFECYCLE

## Title

World Lifecycle Dynamics (Spawning & Ecology)

## Status

DONE

## Request Summary

Implement robust world lifecycle services including regional monster spawning and resource node replenishment.

## Scope

- Create `SpawnService` for density-based monster spawning.
- Create `ResourceEcologyService` for regional node seeding.
- Extend `TransformationService` for regional recovery paths.
- Integrate services into `WorldDynamicsSystem`.
- Ensure deterministic RNG usage for all world events.

## Acceptance Criteria

- [x] Regional monster density remains stable over 1000 ticks.
- [x] Resource nodes are replenished in stable regions.
- [x] Burnt or ruined regions can recover over time.
- [x] Deterministic RNG preserves world generation across replays.

## Related Tickets

- [TCK-20260428-PH10-EXTERNAL-TRUTH](file:///home/vboxuser/Work/rpg-based-simulation/tickets/done/TCK-20260428-PH10-EXTERNAL-TRUTH.md)

## Related Docs

- [resource_v2_e3_phases.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_v2_e3_phases.md) (Phase 9)

## Related Stored Artifacts

- [staging_artifacts/TCK-20260428-PH9-WORLD-LIFECYCLE/plan.md](file:///home/vboxuser/Work/rpg-based-simulation/staging_artifacts/TCK-20260428-PH9-WORLD-LIFECYCLE/plan.md)

## Related Code Areas

- [src/world/spawn_config.py](file:///home/vboxuser/Work/rpg-based-simulation/src/world/spawn_config.py)
- [src/engine/world_dynamics.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/world_dynamics.py)
- [src/platform/rng.py](file:///home/vboxuser/Work/rpg-based-simulation/src/platform/rng.py)

## Test Summary

- `tests/engine/test_phase9_stability.py` passed (1000 tick stress test).

## Files Changed

- [src/world/spawn_config.py](file:///home/vboxuser/Work/rpg-based-simulation/src/world/spawn_config.py)
- [src/engine/world_dynamics.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/world_dynamics.py)
- [src/core/updates.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/updates.py)
- [src/engine/apply.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py)
- [src/platform/rng.py](file:///home/vboxuser/Work/rpg-based-simulation/src/platform/rng.py)
- [src/world/transformation.py](file:///home/vboxuser/Work/rpg-based-simulation/src/world/transformation.py)

## Completion Summary

Implemented regional spawning and ecology services, integrated them into the authoritative world loop, and verified long-term stability via stress testing.
