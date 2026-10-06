---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-NATIVE-PORT-ATTESTED-GATE-SITES
artifact_type: plan
tags: [ai, agent-monitoring]
---

# plan

Written during the work, kept short. Dispatched by agent-working-design on 2026-10-06 after the owner released items 4-5 of the native-port sequence without waiting for the cheap children's cost.

1. Promote the prototype `attest_gate.py` to `tools/gate_checks/attest_gate.py`. Change from the prototype: the command arrives base64-encoded (`--cmd-b64`) and runs under `bash -c`, because the nine gate commands are multi-line shell strings with nested quotes that an agent would otherwise re-quote; stdout is printed in full, not truncated.
2. Inline the verifier in `implement-ticket.js` between `ATTEST-VERIFIER-BEGIN/END` markers: SHA-256, a UTF-8 encoder (the prototype used `unescape`, which the native runtime's probed globals do not list) and base64 (no `btoa`/`Buffer` natively), plus `verifyAttestation`.
3. Add `shAttested(cmd, gate, label)`. Legacy runtime: the runtime's own `bash()`, unchanged. Native: dispatch the wrapper, verify, return stdout without the `ATTEST:` line. Fail closed by throwing `GATE_ATTESTATION_FAILED <gate>: <reason>` on a missing, malformed, wrong-gate, wrong-command, bad-mac or non-zero result; the file's own catch records `WORKFLOW_ERROR` and rethrows. Chosen over returning a new blocking status per site because several sites treat a missing marker as "no problem", and one throw covers all nine.
4. Convert the nine sites (gate ids: tag_check, plan_unresolved_questions, doc_staleness, test_scope_coverage, data_runs_cleanup, parity_p0_scan, parity_touched_ledger, parity_cross_reference, finalize_selfcheck); empty `NATIVE_UNPORTED_GATE_SITES`; stamp the nine classification rows `ported_by`.
5. Tests: wrapper, verifier verdicts under node (honest pass, honest fail, wrong command, wrong gate, tampered exit_code, wrong nonce, plus no line, unparseable), SHA-256/base64 parity with Python, `shAttested` end to end, the stated forgery limit; keep the refusal mechanism tested by re-populating the list.
6. State "anti-misreport, not tamper-proof" in the code comment, the wrapper docstring and `docs/agent-monitoring/schema.md`.
