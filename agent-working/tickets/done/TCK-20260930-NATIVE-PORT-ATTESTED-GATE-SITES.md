---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-NATIVE-PORT-ATTESTED-GATE-SITES
phase: done
date: 2026-10-01
tags: [ai, agent-monitoring]
---

# TCK-20260930-NATIVE-PORT-ATTESTED-GATE-SITES

## Title
Port the 9 gate and control bash sites using the attested route

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Child of `TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT`. Depends on: TCK-20260930-NATIVE-PORT-ORCHESTRATOR-BACKSTOP, TCK-20260930-NATIVE-PORT-INPUT-SITES.

## Scope
Promote the prototype (`agent-working/stored_artifacts/TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN/prototype/`) to `tools/` with tests, inline the SHA-256 verifier in implement-ticket.js, and route the gate (7) and control (3, where a wrong answer skips required work) sites through it. State in code comments and docs that it is anti-misreport, not tamper-proof.

## Out of Scope
- Any other workflow script; sites owned by a sibling child.

## Acceptance Criteria
1. No gate-class site calls bash().
2. Checker unit tests: honest pass, honest fail, wrong command, wrong gate, tampered exit_code, wrong nonce.
3. The backstop child is landed first so enforcement does not rest on attestation.

## Related Tickets
- TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT (parent epic)
- TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN (outcome: adopt for gates only, plus backstop)

## Related Docs
- `agent-working/stored_artifacts/TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION/classification.md`
- `agent-working/stored_artifacts/TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN/design.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION/`
- `agent-working/stored_artifacts/TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN/`

## Related Code Areas
- `.claude/workflows/implement-ticket.js`

## Assumptions / Open Questions
- None beyond the parent epic's.

## Implementation Notes
Released by the owner on 2026-10-06 (batch answer "Native-port children 4-5"), without the cost measurement SEQUENCE.md had asked for; recorded in SEQUENCE.md. Plan, investigation and test plan are in `agent-working/stored_artifacts/TCK-20260930-NATIVE-PORT-ATTESTED-GATE-SITES/`. The ticket says 9 sites; the file had exactly 9 bare `bash(` calls left (7 gate and control, plus the parity touched-ledger input and one more control), all converted. A failed attestation throws (fail closed) rather than returning a blocking status.

## Test Summary
- `tests/tools/test_attest_gate.py`: 12 passed. `test_implement_ticket_native_refusal.py`, `test_implement_ticket_bash_site_classification.py`, acorn parse, helper definition order, meta conformance: pass. `pytest tests/tools -k "implement_ticket or workflow or attest or gate_check or bash_site"`: 208 passed, 1 xfailed.
- `tests/codebase` ratchet and ast-grep tests fail in this environment (ast-grep not installed); they do not touch these files.
- No native `Workflow` run yet: that is `TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN`.

## Files Changed
- `tools/gate_checks/attest_gate.py` (new)
- `.claude/workflows/implement-ticket.js`
- `tests/tools/test_attest_gate.py` (new), `test_implement_ticket_native_refusal.py`, `test_implement_ticket_bash_site_classification.py`
- `agent-working/stored_artifacts/TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION/classification.jsonl` (`ported_by` on 9 rows)
- `docs/agent-monitoring/schema.md`
- `agent-working/tickets/todos/implement-ticket-native-port/SEQUENCE.md`
- `agent-working/stored_artifacts/TCK-20260930-NATIVE-PORT-ATTESTED-GATE-SITES/`

## Completion Summary
All nine gate and control sites run through `shAttested()`; no bare `bash(` remains (AC1), checker cases covered (AC2), backstop already landed (AC3). The attestation is anti-misreport, not tamper-proof, stated in the code, the wrapper and the schema doc.
