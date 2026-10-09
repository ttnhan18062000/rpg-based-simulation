---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261009-NATIVE-ATTESTED-COMMAND-TRANSPORT-LOSSY
artifact_type: plan
tags: [ai, agent-monitoring]
---

# Plan — TCK-20261009-NATIVE-ATTESTED-COMMAND-TRANSPORT-LOSSY

Hand-orchestrated, standard tier, lands on `agent-working-small-fixes-batch` (no push, no PR).

## Measurement (base64 chars of the command handed to the agent, as `shAttested` builds it today)

Estimated by rebuilding each site's template for 3 / 7 / 25 changed files (the real figures come from the length test below):

| site | 3 files | 7 files | 25 files |
|---|---|---|---|
| tag_check | 288 | 288 | 288 |
| plan_unresolved_questions | 456 | 456 | 456 |
| doc_staleness | 340 | 564 | 1592 |
| test_scope_coverage | 568 | 792 | 1820 |
| data_runs_cleanup | 288 | 288 | 288 |
| parity_p0_scan | 480 | 704 | 1732 |
| parity_cross_reference | 648 | 880 | 1932 |
| finalize_selfcheck | 420 | 420 | 420 |
| parity_touched_ledger | ~60 | ~60 | ~60 |

The failed run's test_scope_coverage command was ~900 chars of command (~1.2k base64) with 7 paths. Every inline
`python3 -c` site pays 250–450 chars of fixed Python before any argument; the list-carrying sites then add ~64 chars
per path.

## Changes

1. **Hash echo.** `attest_gate.attest` emits `cmd_sha` (sha256 of cmd) instead of `cmd`; the mac input becomes
   `nonce|gate|cmd_sha|exit_code|stdout_sha`. `verifyAttestation` compares `r.cmd_sha` with `sha256Hex(expectedCmd)`
   (reason `wrong command` kept for a cmd_sha mismatch). The gate_verdicts `inputs_ref.cmd_sha` already exists.
2. **Bound the payload with one short CLI.** Add `tools/gate_checks/gate_cli.py <site> --ticket-id T [--tier X]
   [--pytest-command-b64 …] FILES…` with a sub-command per inline-Python site (tag_check, plan_unresolved_questions,
   test_scope_coverage, data_runs_cleanup, parity_p0_scan, parity_cross_reference, finalize_selfcheck). Each prints the
   same marker line the script already parses, so the JS parsing code is unchanged. Fixed overhead per site drops to
   about 100–150 command chars (≈150–200 base64). The recorded **bound is 400 base64 chars for the fixed part plus 64
   per path**, enforced in a test that builds every site's command for a 10-path reference ticket and asserts
   `len(b64) <= 400 + 64 * paths`. doc_staleness already is a CLI, so it only needs to meet the bound.
3. **Retry once on transport mismatch.** In `shAttested`, reasons `no ATTEST line`, `unparseable`, `wrong gate`,
   `wrong command` re-dispatch the same site exactly once. The retry is recorded on the re-dispatched site's own `attested_command` row (`inputs_ref.attempt: 2`, `inputs_ref.retry_reason`), see Unresolved question 2. A second mismatch throws `GATE_ATTESTATION_FAILED <gate>: <reason> (after 1 retry)`. A
   verified non-zero `exit_code` returns as a real result and never retries; `bad mac` throws immediately.

## Tests (tests/tools/test_attest_gate.py plus a new tests/tools/test_gate_cli.py)

- truncated payload and truncated echo fail verification; cmd_sha round-trips between Python and the JS verifier (node).
- retry path under node with a stub `runCommand`: mismatch→match passes; mismatch→mismatch fails; non-zero exit not
  retried; bad mac not retried.
- length test: every site stays under the bound for the reference ticket.
- each `gate_cli` sub-command returns the same marker output as the inline Python it replaces (golden comparison).
- existing `test_attest_gate.py`, `test_implement_ticket_native_refusal.py` and `workflow_bash_sites.py` (0 sites) stay green.

## Unresolved questions

1. **Long file lists.** At 25 changed files even the CLI form stays ~1.7k chars, because the paths are argv. Do we
   accept that (the retry then is the defence), or should the list come from disk? Disk needs the run to write
   `files_changed.json` through another dispatch, which has the same transport risk. My recommendation: accept; make
   `gate_cli` derive the list itself with `git diff --name-only origin/main...HEAD` plus untracked, so no path travels
   through the agent. That changes what is checked (git state vs. the implementer's reported list) and needs your call.
2. **Retry record.** `implement-ticket.js` has no recorder of its own in the native runtime (everything goes through a
   dispatched command). Recording the retry means one extra dispatched `attest_gate.py --record-retry --gate-id G
   --reason R`. Acceptable, or is putting `attempt` and `retry_of` into the retry's own `attested_command` row enough?
   My recommendation: the latter (no extra dispatch).
3. **gate_ledger.** `gate_ledger outcome` rejects an `attested_command` id as unknown (`_split` excludes attested rows
   from the verdict set), so the planner's requested `outcome … stopped` for `gv-e41c39cd23e34df3` was not recordable.
   Out of scope here; say if you want it ticketed.
