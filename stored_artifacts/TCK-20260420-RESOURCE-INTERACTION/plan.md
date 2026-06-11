---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260420-RESOURCE-INTERACTION
artifact_type: plan
tags: [resource, interaction]
---

# Implementation Plan: Resource Interaction (Milestone 4)

## Goal
Implement deterministic resource interaction (loot/harvest channeling) and inventory pressure as the second official RPG slice in V2.

## Proposed Changes

### 1. State Expansion
- **[MODIFY] src/core/state.py**:
    - Add `InteractionComponent` {loot_progress, current_target_id}.
    - Add `InventoryComponent` {items: List[str], max_slots, max_weight}.
    - Add `ResourceNodeComponent` {harvest_ticks, items: List[str], is_available, respawn_cooldown}.

### 2. Update Protocol
- **[MODIFY] src/core/updates.py**:
    - Add `InteractionUpdate` {progress_delta, target_id_set}.
    - Add `InventoryUpdate` {add_items, remove_items}.
    - Add `NodeUpdate` {set_available, start_respawn}.

### 3. Interaction System [NEW]
- **[NEW] src/engine/interaction.py**:
    - Implements the channeling logic.
    - `process_interaction`: Logic to increment progress if target is still valid and reachable.
    - `finalize_interaction`: Logic to commit loot to inventory and deplete node.

### 4. Domain Logic Integration
- **[MODIFY] src/engine/domain_logic.py**:
    - Integrate `INTERACT` work item handler.
    - Call into `InteractionSystem`.

### 5. Apply Path
- **[MODIFY] src/engine/apply.py**:
    - Implement atomic application of inventory and interaction updates.

## Verification Plan

### Automated Tests
- **[NEW] tests/parity/interaction_oracle/**:
    - Capture script for old harvest/loot logic.
    - Parity script for V2 interaction.
- **Unit Tests**:
    - Weight/Slot limit enforcement.
    - Multi-tick progress tracking.
    - Adjacency requirements.

### Performance
- **run_benchmarks.py**: Add `HARVEST_STRESS_100` scenario.
- Measure tick-cost increase caused by interaction logic.
