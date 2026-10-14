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

## Decisions (planner, 2026-10-09)

- **Q1, file lists: derive from git, with the run's start commit as the base.** Not `origin/main...HEAD`: at Test time the
  implementation is uncommitted, and on a batch branch that base pulls in earlier tickets' files. At Scope an attested
  `git rev-parse HEAD` captures `startSha` (its stdout hash must match the sha handed back). `gate_cli` derives
  `git diff --name-only <startSha>` (working tree against that commit) plus `git ls-files --others --exclude-standard`,
  minus the run's own bookkeeping. **Exclusions** (`gate_cli.EXCLUDED_PREFIXES`/`EXCLUDED_FRAGMENTS`):
  `agent-working/agent-monitoring/`, `data/runs/`, `reports/release_proof/`, `graphify-out/`, `.claude/current_run*`,
  `/__pycache__/`, `/.pytest_cache/`. Staging artifacts and the ticket file are NOT excluded (they were in the
  implementer's reports before). Advisory only: `test_scope` prints `DERIVED_FILES_JSON:` and the script logs and
  records a non-blocking `Test:files_changed_vs_git` row when the derived list and the implementer's `files_changed` differ.
  All four list-carrying sites (doc_staleness, test_scope_coverage, parity_p0_scan, parity_cross_reference) use the same
  derivation; the bound is therefore a fixed per-site number: **400 base64 chars**, measured 120-316.
- **Q2, retry record: on the re-dispatched site's own `attested_command` row** (`inputs_ref.attempt: 2`, `retry_reason`),
  no extra dispatch. Attempt 1's row stays; `gate_ledger.attested_without_verdict` treats it as superseded, with a test.

## Changes (as built)

1. `attest_gate.py`: ATTEST line carries `cmd_sha`; mac over `nonce|gate|cmd_sha|exit_code|stdout_sha`; `--attempt`/`--retry-reason`.
2. `implement-ticket.js`: verifier compares `cmd_sha`; `attestWithRetry` re-dispatches once on `no ATTEST line`, `unparseable`,
   `wrong gate`, `wrong command` (inside the node-tested ATTEST-VERIFIER block); `gateCmd` builders (GATE-CMD block) replace every
   inline `python3 -c` attested site; `parity_touched_ledger` folded into `gate_cli parity_xref`; `start_sha` captured at Scope.
3. `tools/gate_checks/gate_cli.py`: sub-commands tag_check, plan_unresolved, doc_staleness, test_scope, data_runs_cleanup,
   p0_scan, parity_xref, finalize_selfcheck.
4. `gate_ledger.attested_without_verdict`: a first attempt superseded by a retry row is not an orphan.
5. Docs: `docs/agent-monitoring/schema.md`.

## Tests

tests/tools/test_attest_gate.py (cmd_sha, retry once, no retry on non-zero exit or bad mac, truncated payload),
tests/tools/test_gate_cli.py (length bound for every site, git derivation and exclusions, sub-command output),
tests/tools/test_gate_ledger.py (retry is one verdict), updated wiring tests (doc staleness, document-update).
