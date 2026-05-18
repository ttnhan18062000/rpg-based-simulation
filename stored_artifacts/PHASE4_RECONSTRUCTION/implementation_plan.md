# Phase 4 — Controlled RPG-Core Attachment and Resource Loop Recovery

This plan implements the updated Phase 4 requirements, transitioning from pure infrastructure hardening into a disciplined gameplay attachment phase while resolving lingering substrate defects.

## User Review Required

> [!IMPORTANT]
> **Replay Manifest Truth**: The current `ReplayManager` has a race condition in chunk persistence. I will move to a "Snapshot-and-Submit" model where metadata is captured before the background thread starts.
> 
> **Town Resource Resolution**: I propose implementing a "Town Interaction Service" that triggers when an entity is on a Town tile during the ADVANCEMENT phase, converting harvested materials into gold/secondary resources based on the original `src` pricing.

## Proposed Changes

### [Component] Substrate Truth Closure

Narrow focus on resolving artifacts that make Milestone 1 "dishonest."

#### [MODIFY] [replay_manager.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/replay_manager.py)
- Refactor `_rotate_chunk` to capture `current_chunk_id` and `chunk_start_tick` in a local DTO before executor submission.
- Centralize manifest updates to the main thread or use a thread-safe queue for metrics.

#### [MODIFY] [kernel.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/kernel.py)
- Move `ProfileValidator` calls into a separate `validate()` method or a pre-flight check to allow for smoother patch/hot-reload boundaries.

---

### [Component] Deterministic Resource Interaction Core

Narrow focus on recovering original parity for interaction laws.

#### [MODIFY] [interaction.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/interaction.py)
- **Weight Pressure**: Update `Pressure Law` to check `current_weight <= max_weight`.
- **Looting**: Expand `InteractionSystem.enforce` to handle items on the ground (Looting Law).
- **Interruption**: Strictly enforce that any `moved_this_tick` or `target_change` resets progress to 0 (Channeling Law).

#### [NEW] [town_resolution.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/town_resolution.py)
- Implement authoritative "sell-on-entry" logic for the town loop.
- Provides the "Material/Gold/Capability Resolution" mentioned in Phase Task 5.

---

### [Component] Performance & Measurement

#### [MODIFY] [governor.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/governor.py)
- Implement "End-to-End CPU Contract" by having the `Governor` reduce `active_worker_count` or shed `DEFERRABLE` work if `worker_utilization` exceeds thresholds.

## Open Questions

1. **Town Interaction**: Should the "sell" logic be automatic (on town tile entry) or require a deliberate `InteractionIntent` at a specific building ID? The original `src` uses specific shop buildings.
2. **CPU Shedding**: Is proactive worker reduction (reducing concurrency) the preferred shedding mechanism, or should we drop work items entirely?

## Verification Plan

### Automated Tests
- `pytest tests/engine/test_replay_truth.py`: New test for race conditions in rotation.
- `pytest tests/engine/test_interaction_parity.py`: Verifies weight pressure and looting interruptions.
- `python3 scripts/refresh_proofs.py`: Verifies that integrated scenarios still produce deterministic outcomes.

### Manual Verification
- Review generated `manifest.json` under high pressure to ensure NO chunk IDs are skipped or duplicated.
- Verify `InventoryUpdate` in traces reflects weight-based rejections.
