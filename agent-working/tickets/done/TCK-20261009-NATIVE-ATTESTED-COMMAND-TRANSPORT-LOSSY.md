---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261009-NATIVE-ATTESTED-COMMAND-TRANSPORT-LOSSY
phase: done
date: 2026-10-09
tags: [ai, agent-monitoring]
---

# TCK-20261009-NATIVE-ATTESTED-COMMAND-TRANSPORT-LOSSY

## Title
Attested gate commands survive the agent transport: hash the echo, bound the payload, retry a transport mismatch once

## Status
DONE

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
- agent-working/stored_artifacts/TCK-20261009-NATIVE-ATTESTED-COMMAND-TRANSPORT-LOSSY/ (investigation.md, plan.md, test_plan.md)

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
Hand-orchestrated (no Workflow run), on `agent-working-small-fixes-batch`, no push, no PR. plan.md carries the planner's two decisions: the changed-file list is derived from git against the run's start commit (not `origin/main...HEAD`), and the retry is recorded on the re-dispatched site's own row. `parity_touched_ledger` is no longer a separate site: `gate_cli parity_xref` reads `git status --porcelain -- docs/parity_ledger/` itself.

## Test Summary
- New: tests/tools/test_gate_cli.py (11: bound for 8 sites, derivation and exclusions, sub-command output), 6 new tests in tests/tools/test_attest_gate.py (retry once with `--attempt 2 --retry-reason`, no retry on a verified non-zero exit or a bad mac, cmd_sha round-trip, truncated payload, short ATTEST line), 1 in tests/tools/test_gate_ledger.py (a retry is one verdict, not two). Updated the doc-staleness and document-update wiring tests.
- Measured command size (base64 chars, reference ticket): 120-316 per site for any number of changed files; before: 288-1932, growing with file count. Bound recorded and enforced: 400.
- `tools/workflow_bash_sites.py`: 0 sites. Related subset (workflow, attest, native, gate, docs, registry ...): 1056 passed.
- Full `tests/tools/`: 4707 passed, 1 failed, 1 error. The failure is `test_entity_lifecycle_score::TestRealIntegration::...800t_end_to_end` (harness TimeoutError at machine load ~10, also failed before this change) and the error is the thread-leak check that follows it in `test_write_path_guard`; neither touches a changed file.
- Not exercised: a real native Workflow run (needs the owner's opt-in); TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN stays BLOCKED until a rerun with a new vehicle.

## Files Changed
- .claude/workflows/implement-ticket.js
- tools/gate_checks/attest_gate.py
- tools/gate_checks/gate_cli.py (new)
- tools/agent-monitoring/gate_ledger.py
- tests/tools/test_attest_gate.py, tests/tools/test_gate_cli.py (new), tests/tools/test_gate_ledger.py, tests/tools/test_doc_staleness_gate_wiring.py, tests/tools/test_document_update_phase_wiring.py
- docs/agent-monitoring/schema.md

## Completion Summary
The ATTEST line now carries `cmd_sha`; the verifier compares it and the mac covers it. Every attested gate site is one short `gate_cli.py` call (120-316 base64 chars, bound 400, enforced by test); the changed files are derived from git against the run's start commit, with an advisory when the derived list differs from the implementer's report. A transport mismatch re-dispatches the site once, recorded as `attempt: 2` on the retry's row; a verified non-zero exit and a bad mac never retry; a second mismatch fails closed. The gate ledger treats a superseded first attempt as one verdict, not an orphan. Follow-ups not done here: the Scope-ordering cost observation (tag check after the scoper) and TCK-20261009-GATE-LEDGER-OUTCOME-ON-ORPHAN-ATTESTED-ROW.
