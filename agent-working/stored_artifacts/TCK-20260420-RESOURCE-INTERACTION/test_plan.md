---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260420-RESOURCE-INTERACTION
artifact_type: test_plan
tags: [resource, interaction]
---

# Test Plan: Resource Interaction (Milestone 4)

## Parity Verification
- **Target**: Ensure V2 interaction logic matches old engine behavior.
- **Scenarios**:
    - Full Harvest: 5 ticks of progress -> Item gained.
    - Interrupted Harvest: Move away during tick 3 -> Progress reset.
    - Full Inventory: Try to loot -> Fails at first tick.
    - Weight Limit: Try to loot heavy item -> Fails.
    - Depletion: Harvest node twice -> Second attempt fails (available=False).

## Contract Laws
- **Law: Weight Enforcement**: If entity total weight + new item weight > max_weight, update MUST NOT append item.
- **Law: Slot Enforcement**: If len(items) >= max_slots, update MUST NOT append item.
- **Law: Adjacency Requirement**: Interaction only allowed if dist(Actor, Node) <= 1.

## Performance Verification
- **Baseline Scenario**: 100 entities harvesting 100 nodes.
- **Metric**: Compare TPS against Baseline IDLE and MOVEMENT.
- **Goal**: < 5% overhead compared to MOVEMENT stress.
