---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260420-RESOURCE-INTERACTION
artifact_type: investigation
tags: [resource, interaction]
---

# Investigation: Resource Interaction Slice (Milestone 4)

## Core Mechanics from Old src
Based on research in src/core/aspects/interaction.py and src/ai/states/interaction.py:

### 1. Interaction Progress (Channeling)
- Actors have a `loot_progress` state.
- Interaction takes N ticks ( `config.loot_duration` or `res.harvest_ticks`).
- If the actor stays on tile and interacts, progress increments.
- If progress reaches duration, the actual "LOOT" or "HARVEST" action is resolved.

### 2. Inventory Pressure
- Inventory has `max_slots` and `max_weight`.
- `is_effectively_full` triggers when at 90% weight or full slots.
- Adding an item requires:
    - Slot availability.
    - Weight availability (sum of weights of items in bag).
    - Weights are retrieved from `ITEM_REGISTRY`.

### 3. Resource Nodes
- Resource nodes have an `is_available` state.
- After being harvested, they enter a "looted" state and potentially respawn after a cooldown.

## V2 Migration Design
We will not port the full ITEM_REGISTRY yet (too complex for Gate 2).
Instead, we will use a **Property-Based Item System**:
- Item ID is a string.
- Entity State (Authoritative) stores the list of item IDs.
- Metadata (Non-authoritative) defines weight/description for comparison.

### Interaction Workflow in V2:
1. **Work Packet**: Scheduler emits `INTERACT` work item with a target entity ID (neighbor).
2. **Worker Resolution**:
    - If actor is adjacent to target.
    - Interaction system increments progress.
3. **Completion Update**:
    - If progress >= duration.
    - Update includes `inventory_add` for actor and `deplete` for target node.

### Challenges:
- **Concurrency**: If two players harvest the same node simultaneously.
    - Resolution Law: Only one entity can "finish" a harvest on a specific node per tick if the node is non-infinite.
    - V1 of this slice will follow a FIRST-FINISH-WINS or DETERMINISTIC-ID-WINS model.
