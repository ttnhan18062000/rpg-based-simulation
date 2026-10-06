---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-NATIVE-PORT-ATTESTED-GATE-SITES
artifact_type: test_plan
tags: [ai, agent-monitoring]
---

# test_plan

| AC | Test | Result |
|---|---|---|
| 1. No gate-class site calls `bash()` | `test_implement_ticket_bash_site_classification.py::test_ported_rows_route_through_sh_helpers_and_legacy_bash_is_kept` (0 call sites, 0 unported rows); `workflow_bash_sites.py` reports 0 | pass |
| 2. Checker unit tests: honest pass, honest fail, wrong command, wrong gate, tampered exit_code, wrong nonce | `test_attest_gate.py::test_checker_verdicts_for_honest_pass_honest_fail_and_each_tamper` (runs the real inline block under node, lines from the real wrapper) | pass |
| 3. Backstop landed first | `TCK-20260930-NATIVE-PORT-ORCHESTRATOR-BACKSTOP` is in `agent-working/tickets/done/`; SEQUENCE.md records the release | pass |

Also: wrapper exit-code and multi-line-command cases; node SHA-256/base64 parity with Python including multibyte text; `shAttested` native returns stdout minus the `ATTEST:` line, fails closed on a skipped, wrong-command or non-zero result and on an unsafe nonce, and leaves the legacy path unchanged; the refusal mechanism stays covered by re-populating the empty list.
Not tested: a real native `Workflow` run.
