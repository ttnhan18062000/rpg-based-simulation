---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-GATE-VERDICT-OUTCOME-AND-ADJUDICATION
artifact_type: test_plan
tags: [ai, agent-monitoring]
---

# Test plan
Fixtures only, in tmp_path: derivation cases, explicit-over-derived, append-only supersede, unknown id and bad values refused, CLI exit codes, backstop idempotence and scoping (mode, ticket), env guard, and the `post_native_run_check` call per failed check. Node harness check that the wrapper call carries `--ticket-id`.

## Proof Plan
- level: unit
- proof kind: pytest
- oracle source: rows written to a scratch data root, read back through `resolved_view`
- expected effect: derived and explicit outcomes and adjudications resolve as specified
- selected commands: `pytest tests/tools/test_gate_ledger.py tests/tools/test_attest_gate.py`
