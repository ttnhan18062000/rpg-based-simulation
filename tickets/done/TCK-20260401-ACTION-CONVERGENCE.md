# TCK-20260401-ACTION-CONVERGENCE: Unify Action Application Pipeline

## Description
This ticket addresses the second priority of the `final_implementation_plan.md`. It aims to unify the authoritative application pipeline between live ticks and the replay/recovery path. It also involves replacing loose dict-based `intent_metadata` with explicit, typed update models.

## Scope
- **Pipeline Unification**: Ensure all `ActionProposal` objects go through a single `validate` -> `apply` pathway.
- **Replay Consistency**: Align the `ConflictResolver` and action routing between live simulation and replay recovery.
- **Typed Updates**: Refactor `intent_metadata` to use structured, typed models for deferred AI-generated updates (e.g., shop purchases, crafting results).
- **Building Sabotage**: Refactor building attack targeting to use a proper typed model instead of string-keyed hacks.

## Acceptance Criteria
- [x] Refactor `ConflictResolver` to share logic with the authoritative application loop.
- [x] No unbounded dicts used for AI deferred updates.
- [x] Replay recovery produces bit-identical matching world state to the original live tick.
- [x] Building attack logic uses a typed `BuildingTarget` model.

## Related Tickets
- [TCK-20260331-RUNTIME-INTEGRITY](file:///home/vboxuser/Work/rpg-based-simulation/tickets/inprogress/TCK-20260331-RUNTIME-INTEGRITY.md)

## Status
DONE

## Final Status
**DONE**: Unified resolver/action system/replay via authoritative update-driven pipeline. Verified replay consistency and implemented typed update models for AI-generated intents and building sabotage targeting.
