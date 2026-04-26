# Implementation Plan - Resource Conservation Hardening (Phase 3.1)

Hardening the Resource Conservation Law by introducing a unified `ResourceTransactionResolver` and refactoring systems to use it.

## User Review Required

> [!IMPORTANT]
> This plan introduces a new architectural layer: `ResourceTransactionResolver`. Systems (Harvest, Loot) will no longer directly propose node depletion or corpse removal. Instead, they will propose a `ResourceTransferIntent`, which the resolver will process into atomic state updates (or rejections).

## Proposed Changes

### Core Engine Refinement

#### [MODIFY] [updates.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/updates.py)
- Add `ResourceTransferIntent` dataclass.
- Add `resource_transfer: Optional[ResourceTransferIntent]` to `EntityUpdate`.

#### [MODIFY] [conservation.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/conservation.py)
- Rename/Rewrite `ResourceConservationService` to `ResourceTransactionResolver`.
- Implement `resolve(state, entity, intent)` which returns a `TransactionResult` (accepted/rejected with computed updates).
- Support source types: `NODE`, `GROUND_ITEM`, `CORPSE`.

#### [MODIFY] [interaction.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/interaction.py)
- Refactor `InteractionSystem.enforce` to call `ResourceTransactionResolver`.
- Ensure that if the transaction is rejected, the `StateUpdate` is stripped of any associated depletion/removal.

---

### Systems Refactor

#### [MODIFY] [harvest_system.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/harvest_system.py)
- Propose `ResourceTransferIntent` instead of `ResourceNodeUpdate` and `InventoryUpdate` on harvest completion.

#### [MODIFY] [loot_system.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/loot_system.py)
- Propose `ResourceTransferIntent` instead of `ground_items_remove` and `InventoryUpdate`.

---

### Verification Plan

#### Automated Tests
- [NEW] `tests/systems/test_resource_conservation_regression.py`
    - TEST: Harvest node with full inventory -> Node charges remain unchanged, no item received.
    - TEST: Loot corpse with full inventory -> Corpse remains, no items received.
    - TEST: Pickup ground item with full inventory -> Ground item remains, no item received.
- Run `pytest tests/systems/test_resource_conservation_regression.py`
