---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260427-RESOURCE-CONSERVATION-HARDENING
artifact_type: investigation
tags: [resource, conservation, hardening]
---

# Investigation - Resource Conservation Law Gaps

## Current State

The V2 engine uses a "Proposal -> Refinement -> Apply" architecture.
`HarvestSystem.update()` and `LootSystem.update()` propose updates to the state.
`InteractionSystem.enforce()` refines these updates.

### Identified Bug
In `src/engine/interaction.py:L111`, when capacity check fails:
```python
refined_entity_updates[e_id] = replace(ent_upd, interaction=InteractionUpdate(reset=True))
continue
```
This resets the entity's interaction, but **does not remove** any `ResourceNodeUpdate` or `ground_items_remove` that the systems might have already proposed in the same `StateUpdate`.

### Legacy Parity
Legacy `InteractionSystem.enforce` (if it existed) likely handled this by resetting the entire `StateUpdate` or having a more atomic transaction.

## Target Architecture

`ResourceTransactionResolver` will handle the atomicity.

1. System proposes intent.
2. Resolver validates both sides (Source & Destination).
3. Resolver produces the final updates for both sides.
4. If invalid, resolver produces NO updates (or a failure update).
