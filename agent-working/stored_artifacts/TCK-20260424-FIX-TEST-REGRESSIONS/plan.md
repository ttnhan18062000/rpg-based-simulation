---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260424-FIX-TEST-REGRESSIONS
artifact_type: plan
tags: [fix, test, regressions]
---

# Plan: Fix Test Regressions

Fix 4 failed test cases in `tests/` to restore 100% test stability.

## Proposed Changes

### [Tactical]

#### [MODIFY] [tactical.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/tactical.py)
- Verify if `evaluate` was renamed to `decide` or integrated into `StrategicIntelligenceSystem`.

#### [MODIFY] [test_tactical_parity.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/parity/test_tactical_parity.py)
- Align test with current `TacticalDecisionSystem` API.

### [Opportunity Attack]

#### [MODIFY] [test_oa_parity.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/parity/test_oa_parity.py)
- Investigate why OA is failing on disengagement. Likely a threshold or legality check mismatch.

### [Movement Parity]

#### [MODIFY] [test_movement_parity.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/parity/test_movement_parity.py)
- Fix `blocked_terrain` parity mismatch.

## Verification Plan

### Automated Tests
- `pytest tests/parity/test_tactical_parity.py`
- `pytest tests/parity/test_oa_parity.py`
- `pytest tests/parity/test_movement_parity.py`
- `pytest tests/` (Full suite)
