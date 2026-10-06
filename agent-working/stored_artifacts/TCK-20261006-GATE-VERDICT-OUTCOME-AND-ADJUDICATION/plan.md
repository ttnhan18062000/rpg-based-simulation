---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-GATE-VERDICT-OUTCOME-AND-ADJUDICATION
artifact_type: plan
tags: [ai, agent-monitoring]
---

# Plan
1. `gate_ledger.py`: row kinds, read-time derivation, CLI, backstop adjudication.
2. `gate_verdicts.validate_record` dispatches on `row_kind`.
3. `attest_gate.py --ticket-id`, passed by `implement-ticket.js`, so a native verdict can be matched to its ticket.
4. Wire `post_native_run_check.py` to the backstop.
5. Docs: schema, delivery_process, one CLAUDE.md bullet (owner approved the literal text).

## Unresolved Questions

None.
