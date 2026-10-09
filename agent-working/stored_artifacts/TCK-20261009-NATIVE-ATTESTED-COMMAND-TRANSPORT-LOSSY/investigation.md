---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261009-NATIVE-ATTESTED-COMMAND-TRANSPORT-LOSSY
artifact_type: investigation
tags: [ai, agent-monitoring]
---

# Investigation — TCK-20261009-NATIVE-ATTESTED-COMMAND-TRANSPORT-LOSSY

- Evidence: run `wf_e2dc6921-bdd` journal. The `test_scope_coverage` ATTEST line echoed a `cmd` missing its closing quote and
  `exit_code: 2`, `stdout_sha` of empty output: the shell received a truncated command. `shAttested` hands the agent
  `--cmd-b64 <base64>` and the wrapper echoed the full command back, so two lossy copies of one long string.
- Site sizes (base64 chars, before): 288-1932 for 3-25 changed files; after the change 120-316 and independent of file count.
- Code read: `.claude/workflows/implement-ticket.js` (`verifyAttestation`, `shAttested`, 9 attested sites),
  `tools/gate_checks/attest_gate.py`, `tools/agent-monitoring/gate_ledger.py` (`_split`, `attested_without_verdict`,
  `derive_outcomes`), `tools/gate_checks/doc_staleness_check.py` CLI, tests/tools/test_attest_gate.py.
- Finding kept out of scope: `gate_ledger outcome` rejects an attested row id (planner ticketed it separately).
