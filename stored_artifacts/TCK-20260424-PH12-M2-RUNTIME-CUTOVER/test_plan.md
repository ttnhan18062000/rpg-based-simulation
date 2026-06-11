---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260424-PH12-M2-RUNTIME-CUTOVER
artifact_type: test_plan
tags: [ph12, m2, runtime, cutover]
---

# Phase 12 M2 Test Plan: Runtime Cutover Validation

## 1. Unit Tests
- `tests/engine/test_manager_dispatch.py`: Verify V2EngineManager intercepts calls correctly.
- `tests/api/test_presenter_parity.py`: Verify V2 presenters match legacy schema.

## 2. Integration Tests
- `python -m src cli --ticks 10 --seed 42`: Verify V2-driven CLI run completes without error.
- `python -m src serve`: Verify REST/WebSocket endpoints respond with V2 state.

## 3. Parity Verification
- Compare `replay.json` from a legacy run vs a V2 run under identical seeds (Bit-identical where supported).
