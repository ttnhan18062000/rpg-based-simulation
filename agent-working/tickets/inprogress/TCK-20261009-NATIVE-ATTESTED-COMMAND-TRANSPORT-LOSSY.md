---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261009-NATIVE-ATTESTED-COMMAND-TRANSPORT-LOSSY
phase: open
date: 2026-10-09
tags: [ai, agent-monitoring]
---

# TCK-20261009-NATIVE-ATTESTED-COMMAND-TRANSPORT-LOSSY

## Title
Attested gate commands survive the agent transport: hash the echo, bound the payload, retry a transport mismatch once

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
The first full native implement-ticket run (wf_e2dc6921-bdd, 2026-10-09; vehicle
TCK-20261009-MAIN-INTEGRITY-REPORT-SILENT-TORN-RUN-EVENT-LINES) died at the Test phase with
`GATE_ATTESTATION_FAILED test_scope_coverage: wrong command`. It had reached Implement, the doc and architecture phases
and the Test agent (tests/tools/ 4691 passed). It cost 20 agents, 925,732 tokens and 27.8 min. No result of the
command itself was wrong: `shAttested` hands an agent
`attest_gate.py ... --cmd-b64 <base64>` to run verbatim (`runCommand`, implement-ticket.js line 53). The agent dropped
the tail of the base64 payload, so the command was missing its closing quote and the shell exited 2. The verifier
failed closed, as designed. The real fault is the channel: every attested gate copies a long string through an LLM
twice, once as the base64 input and once as `cmd` inside the echoed `ATTEST:` JSON. `test_scope_coverage` is the
worst case (inline Python plus 7 quoted paths plus the pytest command). Until this is fixed, a native standard run
cannot finish reliably, so TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN is blocked on this ticket.

## Scope
1. **Echo a hash, not the command.** `attest_gate.py` puts `cmd_sha = sha256(cmd)` in the ATTEST line instead of the
   full `cmd`. The mac covers `cmd_sha`. `verifyAttestation` compares it with `sha256Hex(expectedCmd)` (which the
   script already has). This removes the second copy of the payload.
2. **Bound the input payload.** Measure the base64 length of all 9 attested sites as built for a realistic ticket. Each
   site above a stated bound (set the bound from the measurement and record it in plan.md) becomes a short committed
   CLI under `tools/gate_checks/`. It takes its long inputs from files already on disk (for example the staging
   artifacts, or a JSON input file that the run writes and attests by its sha) instead of inline Python plus argv.
   `test_scope_coverage`, `p0_scan` and the parity cross-ref site are the expected candidates; confirm by measuring.
3. **Retry a transport mismatch once.** The reasons `no ATTEST line`, `unparseable`, `wrong gate` and the new
   `wrong command` (cmd_sha mismatch) mean the command did not run as the script built it, so no gate verdict exists
   yet. Re-dispatch that site exactly once, write a gate-ledger or monitoring row that names the retry and its reason,
   and fail closed if the retry also mismatches. A verified non-zero `exit_code` is a real gate result: it NEVER
   retries. Neither does `bad mac`, which signals tampering, not transport.
4. Tests: the verifier on a truncated payload, the retry path (mismatch then match; mismatch twice; a real non-zero
   exit never retried; bad mac never retried), the cmd_sha mac round-trip between `attest_gate.py` and the JS
   verifier, and a length test that holds every attested site under the bound.

## Out of Scope
- Making the attestation tamper-proof. It stays anti-misreport; the orchestrator backstop and CI remain the
  unforgeable checks (TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN).
- Re-ordering Scope so the tag check runs before the scoper (a cost observation from the fail run, tracked separately
  if it is ticketed at all).
- Rerunning the native run itself: that is TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN, after this lands, with
  the owner's Workflow opt-in.

## Acceptance Criteria
1. No attested ATTEST line carries the full command; the verifier checks `cmd_sha` and the mac covers it.
2. Every attested site's base64 command is under the recorded bound, enforced by a test.
3. A transport mismatch retries exactly once, the retry is recorded, and a second mismatch fails closed.
4. A verified non-zero exit and a bad mac never retry.
5. Existing attestation and native-refusal tests still pass, and `tools/workflow_bash_sites.py` still reports 0 sites.

## Related Tickets
- TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT (parent epic, stays OPEN)
- TCK-20260930-NATIVE-PORT-ATTESTED-GATE-SITES (introduced shAttested)
- TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN
- TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN (blocked on this ticket)

## Related Docs
- agent-working/stored_artifacts/TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN/design.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN/

## Related Code Areas
- .claude/workflows/implement-ticket.js (`runCommand`, `verifyAttestation`, `shAttested`, the 9 call sites)
- tools/gate_checks/attest_gate.py
- tools/gate_checks/ (new short gate CLIs)
- tests/tools/ (attestation tests)

## Assumptions / Open Questions
- Assumed from the implementer's report: the input payload was corrupted, since the shell itself saw the unterminated
  quote. The echo path is still fixed (scope item 1) because it is the same failure surface.
- `search_docs` index not built, graphify graph missing in this worktree: the duplicate scan used the ticket folders
  and grep. No open ticket covers this.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
