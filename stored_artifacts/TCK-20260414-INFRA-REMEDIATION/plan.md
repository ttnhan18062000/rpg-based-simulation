# Infrastructure Isolation & Replay-Assertion Repair

This plan addresses the remediation track for the Strategic Cognition pipeline, ensuring that the system is structurally sound, decoupled from external message brokers, and verifiable through deterministic replay assertions.

## Proposed Changes

### Infrastructure

#### [MODIFY] [rabbitmq_client.py](file:///home/vboxuser/Work/rpg-based-simulation/src/api/rabbitmq_client.py)
- Ensure heartbeat and timeout parameters are robust for isolated local runs. (Done in previous tick, but will verify).

#### [NEW] [test_brokerless_isolation.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/infra/test_brokerless_isolation.py)
- A dedicated test that mocks `ImportError` for `pika` and `confluent-kafka`.
- Verifies that `WorldLoop.step()` and `AIBrain.decide()` function normally without brokers.

### Testing & Assertions

#### [MODIFY] [assertions.py](file:///home/vboxuser/Work/rpg-based-simulation/src/testing/assertions.py)
- Audit and repair `assert_strategic_consistency` and `assert_cognition_consistency`.
- Ensure they read from the correct `ticks[-1]["entities"]` structure.
- Add assertions for `primary_overload_source` and `last_overload_tick` parity between Replay and Cognition Graph.

#### [MODIFY] [test_cognition_integrity.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/ai/test_cognition_integrity.py)
- Expand documentation-integrity tests to verify `intel_capacity_implementation_updated.md`.
- Add a "Truth Surface Parity" check that ensures the same entity state serializes consistently across Replay, API Schema, and Exporter.

### Replay Utility

#### [MODIFY] [replay.py](file:///home/vboxuser/Work/rpg-based-simulation/src/utils/replay.py)
- Ensure `ReplayRecorder` captures enough detail to satisfy the new consistency assertions without bloating the file.

## Verification Plan

### Automated Tests
- `PYTHONPATH=. pytest tests/infra/test_brokerless_isolation.py`
- `PYTHONPATH=. pytest tests/ai/test_cognition_integrity.py`
- `PYTHONPATH=. pytest tests/integration/strategy/test_strategic_explainability.py` (Regression check)

### Manual Verification
- Run a short simulation with `DISABLE_RABBITMQ=1` and verify the replay file is generated correctly.
