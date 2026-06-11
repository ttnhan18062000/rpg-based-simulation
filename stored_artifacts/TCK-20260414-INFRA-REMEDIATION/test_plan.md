---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260414-INFRA-REMEDIATION
artifact_type: test_plan
tags: [infra, remediation]
---

# Test Plan: Infrastructure Remediation

## 1. Brokerless Isolation (Proof)
- **Objective**: Prove that simulation tests can run without `pika` or `confluent-kafka`.
- **Method**:
    - `tests/infra/test_brokerless_isolation.py`
    - Use `unittest.mock.patch.dict("sys.modules", {"pika": None, "confluent_kafka": None})`.
    - Instantiate `WorldLoop` and run `step()`.
    - Assert no crashes occur.

## 2. Replay Assertion Repair
- **Objective**: Ensure `assert_strategic_consistency` handles the current replay schema.
- **Method**:
    - Run `tests/ai/test_cognition_integrity.py` with `HEAD` and verify it correctly detects failures (if any).
    - Update `src/testing/assertions.py` to match `ReplayRecorder.record_tick` output names.

## 3. Truth Surface Parity
- **Objective**: Ensure Replay, API, and Graph are in sync for cognitive metrics.
- **Method**:
    - `test_cognition_integrity.test_truth_surface_parity`:
        - Create a `WorldState` with one entity.
        - Run one step.
        - Record to Replay.
        - Export to Graph.
        - Map to API Presenter.
        - Compare `planning_budget`, `is_overloaded`, and `active_slice_used`.

## 4. Documentation Integrity
- **Objective**: Ensure `intel_capacity_implementation_updated.md` aligns with code.
- **Method**:
    - Add regex check in `test_cognition_integrity.py` for field presence in the markdown.
