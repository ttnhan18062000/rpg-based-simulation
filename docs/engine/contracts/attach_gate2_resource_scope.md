---
status: historical
layer: engine
authority: P2
audience: developer
---

# Attach Gate 2: Resource Interaction Support Boundary (Milestone 1)

## Supported Behavior
- **Harvesting**: Multi-tick work towards node depletion.
- **Looting**: Picking up items from the ground.
- **Authoritative Law Enforcement**:
  - **Inventory Capacity**: Reset interaction if slots are full.
  - **Weight Pressure**: Reset interaction if weight limit exceeded.
  - **Proximity Gate**: Reset interaction if actor moves or targets another node.
  - **Node Availability**: Reset interaction if node is depleted or on cooldown.
- **Node Mutation**:
  - Decrement charges on successful harvest.
  - Set cooldown when charges hit zero.

## Explicitly Excluded
- **Complex Looting**: Looting from corpses (handled in Milestone 4).
- **Node Respawn Logic**: The *logic* of when a node respawns is an economy concern; this gate only covers the *finalization* of the interaction.
- **Multi-Actor Contention**: Concurrent harvesting of the same node is excluded for this gate (processed sequentially).
- **Tool Requirements**: Specialized tool checks are excluded for Gate 2.

## Support Boundary
- Resource Interaction is officially supported for **all Hero entities** in the standard simulation loop.
- Supported in both **Local** and **Concurrent** execution modes.

## Proof Path
- **Parity Proof**: `tests/parity/test_resource_interaction_parity.py`
  - Enforces bit-identical behavior against original `src` for harvesting progress and interruption scenarios.
- **Contract Proof**: `tests/contract/test_resource_contract.py`
  - Enforces authoritative state boundaries and V2-specific resource laws (weight, capacity).
