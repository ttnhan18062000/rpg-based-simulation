---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260509-STRAT-BLOCKER-RESOLUTION
artifact_type: plan
tags: [strat, blocker, resolution]
---

# Plan - Implement Access and Inventory Blocker Resolution

Implement missing resolution logic in `StrategicIntelligenceSystem.resolve_blockers` to ensure 'access' and 'inventory' blockers are correctly resolved.

## Proposed Changes

### Strategic Subsystem

#### [MODIFY] [strategic.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/strategic.py)
- Update `resolve_blockers` to handle `kind == "access"` by checking distance to the target position.
- Update `resolve_blockers` to handle `kind == "inventory"` by checking if inventory has free space.

## Verification Plan

### Automated Tests
- `pytest tests/engine/test_phase6_strategic_cognition.py -v`
- `pytest tests/integrity/test_logic_guards.py -v`

### Manual Verification
- None required.
