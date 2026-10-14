---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261009-NATIVE-ATTESTED-COMMAND-TRANSPORT-LOSSY
artifact_type: test_plan
tags: [ai, agent-monitoring]
---

# Test Plan — TCK-20261009-NATIVE-ATTESTED-COMMAND-TRANSPORT-LOSSY

## Proof Plan

| AC | Proof | Where |
|---|---|---|
| 1 No ATTEST line carries the command; verifier checks `cmd_sha` and the mac covers it | wrapper output has no `cmd` key; node verifier rejects a truncated command | test_attest_gate.py |
| 2 Every site's base64 command under the bound | length test over the GATE-CMD block, 8 sites | test_gate_cli.py |
| 3 One retry on transport mismatch, recorded, second mismatch fails closed | node e2e with `truncates_once`, `wrong_cmd`, `skips` agents; `--attempt 2 --retry-reason` on the retry | test_attest_gate.py |
| 4 Non-zero exit and bad mac never retry | node e2e call counts | test_attest_gate.py |
| 5 Existing attestation and refusal tests pass, 0 bash sites | native_refusal tests, `workflow_bash_sites.py` | tests/tools |

Also: the retry is one verdict, not two (test_gate_ledger.py); the git-derived list and its exclusions (test_gate_cli.py).
