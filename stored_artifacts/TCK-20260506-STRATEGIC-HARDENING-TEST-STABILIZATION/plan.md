---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260506-STRATEGIC-HARDENING-TEST-STABILIZATION
artifact_type: plan
tags: [strategic, hardening, test, stabilization]
---

# Implementation Plan - Strategic Hardening Test Stabilization

Migrate `tests/strategic/` to `V2EntityBuilder` to resolve `TypeError` regressions.

## Proposed Changes

### Tests Migration

#### [MODIFY] [test_biological_needs.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/strategic/test_biological_needs.py)
#### [MODIFY] [test_detour_suggestion.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/strategic/test_detour_suggestion.py)
#### [MODIFY] [test_event_interpretation.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/strategic/test_event_interpretation.py)
#### [MODIFY] [test_interruption_resistance.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/strategic/test_interruption_resistance.py)
#### [MODIFY] [test_role_biasing.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/strategic/test_role_biasing.py)

## Verification Plan

### Automated Tests
- `pytest tests/strategic -vv --tb=short`
