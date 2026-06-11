---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260425-PH6-M2-LOOT
artifact_type: plan
tags: [ph6, m2, loot]
---

# PH6 M2: Channeled Loot and Corpse Recovery

Implement deterministic channeled looting and ground item management.

## Proposed Changes

### [Core State] [MODIFY] [state.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py)
- Add `GroundItemState`: `id: int`, `item_id: str`, `quantity: int`, `position: tuple[float, float]`.
- Add `CorpseState`: `id: int`, `position: tuple[float, float]`, `items: List[ItemStack]`, `decay_tick: int`.
- Update `AuthoritativeState` to include `ground_items: Dict[int, GroundItemState]` and `corpses: Dict[int, CorpseState]`.

### [State Updates] [MODIFY] [updates.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/updates.py)
- Update `StateUpdate` to include:
  - `ground_items_add_or_update: List[GroundItemState]`
  - `ground_items_remove: List[int]`
  - `corpses_add_or_update: List[CorpseState]`
  - `corpses_remove: List[int]`

### [Loot Action] [NEW] [loot.py](file:///home/vboxuser/Work/rpg-based-simulation/src/actions/loot.py)
- Implement `LootAction.start(entity, target_id, target_kind)`:
  - Validates proximity (< 1.5 tiles).
  - Sets `InteractionComponent(target_id=target_id, progress=0, required_ticks=10)`.

### [Loot System] [NEW] [loot_system.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/loot_system.py)
- Implement `LootSystem.update(state)`:
  - Identifies entities with looting progress.
  - On progress == required_ticks:
    - Finds target (ground item or corpse).
    - Emits `InventoryUpdate` (add items).
    - Emits `StateUpdate` (remove target).
    - Emits `InteractionUpdate` (reset progress).

### [Apply Path] [MODIFY] [apply.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py)
- Implement `AuthoritativeState` updates for `ground_items` and `corpses`.

## Verification Plan

### Automated Tests
- `tests/inventory/test_loot_channeling.py`:
  - Verify looting takes 10 ticks.
  - Verify item transfer from ground to inventory.
  - Verify ground item removal upon completion.
  - Verify looting is interrupted if entity moves.

### Manual Verification
- Visual audit of state advancement logs to ensure no duplication during the handoff.
