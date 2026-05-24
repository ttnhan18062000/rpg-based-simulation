# Test Plan: Guardrails and E2E Integration

## Unit Verification
We will add `tests/unit/lab_agent/test_agent_guardrails.py` targeting the following:
*   **Context budgets**: Assert that `build_generation_pack` and `build_investigation_pack` fetch limits from `context_budget` block and correctly prune/restrict files.
*   **Raw log blocking**: Assert that when `raw_logs_allowed` is False, attempts to load raw logs are completely blocked, while when True, they are permitted.
*   **Oversized experiment guardrail**: Assert that a setup exceeding profile thresholds (e.g. CI profile run_count > 20) triggers a warning or block.
*   **Storage and runtime estimation**: Verify that the calculated parameters (total ticks, entities, expected artifact size, retention costs) match our formulas.
*   **Audit logs for violations**: Assert that when a guardrail violation is encountered, a corresponding audit event is written to `LabAuditTrail`.

## Integration (E2E) Verification
We will add `tests/integration/lab_agent/test_human_gated_agentic_lab_e2e.py` covering:
*   A complete execution chain of all 7 core workflows in sequence.
*   Verifying that no workflow auto-triggers the next.
*   Checking that approval gates are strictly respected and prevent downstream steps if missing.
*   Verifying that `LabAuditTrail` records every state transition, file operation, and gate check sequentially.
