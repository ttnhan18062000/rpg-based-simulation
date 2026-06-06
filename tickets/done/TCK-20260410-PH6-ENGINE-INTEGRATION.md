# TCK-20260410-PH6-ENGINE-INTEGRATION

## Title

Engine Integration, Presentation, Replay, and Operational Observability

## Status

INPROGRESS

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Phase 6: Wire the strategic layer into the core engine surfaces—building handlers, world systems, snapshots, API/CLI presenters, replay, telemetry, and metrics. Ensure strategic behavior is visible, debuggable, and integrated with world-tier systems.

## Scope

- Standardize building handlers (Guild, Blacksmith, etc.) as strategic producers.
- Integrate strategy into the decoupled world-system layer (`StrategicWorldIntegrationSystem`).
- Extend Snapshots with strategic domain state and world registries.
- Extend API schemas and presenters for strategic inspection.
- Upgrade CLI inspector with consequence trace visualization.
- Extend Replay to capture strategic deltas (version 2.0).
- Add strategy-aware operational metrics and telemetry.

## Out of Scope

- Changes to raw physics or rendering.
- New gameplay content (items, regions) unrelated to strategy.
- Frontend UI development (only API/CLI presentation).

## Acceptance Criteria

- [x] building handlers emit typed `StrategicUpdate`s.
- [x] Strategic world pressures are managed by the world-system layer.
- [x] Immutable snapshots contain all strategic state for workers and API.
- [x] API `/inspect` endpoint exposes the full strategic domain.
- [x] Replay logs capture strategic snapshots per tick.
- [x] Prometheus metrics track project lifecycles and concern distribution.

## Test Summary

- Added `tests/integration/test_strategic_world_integration.py` covering persistence, pruning, and telemetry.
- Verified manual visualization in `EntityPresenter`.
- All tests passing.

## Files Changed

- `src/ai/states/town.py`
- `src/core/models/snapshot.py`
- `src/core/models/world_state.py`
- `src/core/models/enums.py`
- `src/core/models/strategy.py`
- `src/api/presenters/entity_presenter.py`
- `src/api/schemas.py`
- `src/utils/replay.py`
- `src/utils/metrics.py`
- `src/systems/infrastructure/telemetry_system.py`
- `src/systems/gameplay/action_system.py`
- `src/systems/world/strategy_world_integration_system.py`
- `src/core/models/world_strategy.py`

## Completion Summary

Phase 6 is complete. The strategic layer is now fully integrated into the simulation engine's core observability and operational monitoring systems. Replay version 2.0 is established, and Prometheus metrics provide real-time strategic health monitoring.

## Related Tickets

- TCK-20260410-PH5-STRATEGIC-CONSEQUENCES (Done)

## Related Docs

- thinking_implementation_phase_6.md

## Related Code Areas

- `src/ai/states/town.py`
- `src/systems/world/`
- `src/core/models/snapshot.py`
- `src/api/`
- `src/utils/replay.py`
- `src/utils/metrics.py`
- `src/ui/cli/inspector.py`

## Assumptions / Open Questions

- Replay will record strategic deltas every tick for maximum debuggability.
- Operational metrics will track all strategic transitions (Started, Completed, Abandoned).

## Implementation Notes

- Use `StrategicUpdate` for all state mutations.
- Follow existing presenter/snapshot patterns for API exposure.
- Use `SystemContext` for world-level strategic coordination.
