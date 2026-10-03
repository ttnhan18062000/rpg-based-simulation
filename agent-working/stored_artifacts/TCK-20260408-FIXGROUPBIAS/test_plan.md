---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260408-FIXGROUPBIAS
artifact_type: test_plan
tags: [fixgroupbias]
---

# Test Plan: TCK-20260408-FIXGROUPBIAS

## Existing Tests
- `pytest tests/integration/social/test_group_coordination.py::test_brain_group_behavior_bias` (Priority: High)
- `pytest tests/integration/social/test_group_coordination.py` (Priority: Medium)

## New Scenarios
- N/A - Existing test already covers the core coordination logic.

## Core Scenarios
- **Shared Goal Bias**: Raider2 (member) near leader (R1) should have `motive_utility_biases[COMBAT] > 1.2` when group shared goal is `COMBAT`.
- **Proximity Bias**: Raider2 far from leader (> 5 tiles) should have `motive_utility_biases[SOCIAL] > 1.2`.

## Edge Cases
- **Isolated member**: If dist > 15, cohesion should be 0.0 and `COMBAT` bias should be 1.0 (no bonus).
- **Lonely member**: Groups with 1 member should dissolve.

## Regression Surface
- `AIBrain` decision throughput (ensure no new bottlenecks from group lookups).
- `GroupSystem` maintenance overhead.
