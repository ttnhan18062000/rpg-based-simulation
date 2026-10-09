---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261009-GATE-LEDGER-OUTCOME-ON-ORPHAN-ATTESTED-ROW
phase: done
date: 2026-10-09
tags: [agent-monitoring, data-quality]
---

# TCK-20261009-GATE-LEDGER-OUTCOME-ON-ORPHAN-ATTESTED-ROW

## Title
gate_ledger outcome accepts an attested row that has no verdict row, so a run that died at a gate can record "stopped"

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Native run wf_e2dc6921-bdd died at `GATE_ATTESTATION_FAILED test_scope_coverage`, before the pipeline site wrote its
static verdict row. Only the `attested_command` row `gv-e41c39cd23e34df3` (FAIL, exit 2) exists. CLAUDE.md says to
record a stop on a blocking gate with `gate_ledger.py outcome --outcome stopped`. But `gate_ledger.py outcome
--gate-verdict-id gv-e41c39cd23e34df3` returns `unknown gate_verdict_id`, because `_split` leaves every
`attested_command` row out of the verdict set. `attested_without_verdict()` already lists these orphans, but nothing
can resolve them. The stop could be recorded only in prose, in the ticket's Test Summary.

## Scope
- `gate_ledger.py outcome` accepts a `gate_verdict_id` that belongs to an attested row listed by
  `attested_without_verdict()` (an orphan), and writes the outcome row against it as usual.
- An attested row that HAS a matching verdict row still refuses, with a message naming that verdict id, so the
  native double-count fix (TCK-20261006-GATE-LEDGER-NATIVE-ATTESTED-ROWS-DOUBLE-COUNT) is not undone.
- `list --unresolved` shows an orphan with its recorded outcome as resolved.
- Tests: an orphan accepts an outcome; a paired attested row refuses and names its verdict; unresolved listing.
- After it lands, record `stopped` for `gv-e41c39cd23e34df3`, with the note "attested command corrupted in agent transport;
  see TCK-20261009-NATIVE-ATTESTED-COMMAND-TRANSPORT-LOSSY".

## Out of Scope
- Counting orphans in the verdict totals or pass rates.
- The transport fix itself.

## Acceptance Criteria
1. `outcome` on an orphan attested id succeeds and the row is written.
2. `outcome` on a paired attested id fails, naming the verdict id to use instead.
3. The orphan no longer shows as unresolved after its outcome is recorded.
4. Existing gate_ledger tests pass.

## Related Tickets
- TCK-20261006-GATE-LEDGER-NATIVE-ATTESTED-ROWS-DOUBLE-COUNT
- TCK-20261009-NATIVE-ATTESTED-COMMAND-TRANSPORT-LOSSY
- TCK-20261009-MAIN-INTEGRITY-REPORT-SILENT-TORN-RUN-EVENT-LINES (where the gap was hit)

## Related Docs
- docs/guides/delivery_process.md ("Recording what you did about a gate verdict")

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- tools/agent-monitoring/gate_ledger.py (`_split`, `attested_without_verdict`, the `outcome` command)
- tests/tools/ (gate_ledger tests)

## Assumptions / Open Questions
- `search_docs` index not built, graphify graph missing in this worktree: the duplicate scan used the ticket folders
  and grep. No open ticket covers this.

## Implementation Notes
Hand-orchestrated hotfix on `agent-working-small-fixes-batch`, with no PR of its own.

## Test Summary
tests/tools/test_gate_ledger.py: 32 passed, 3 new (an orphan accepts an outcome and then reads as resolved while staying out of the totals; a paired attested row refuses and names the verdict id; CLI exit 1 for paired, 2 for unknown). Recorded for real: `gate_ledger.py outcome --gate-verdict-id gv-e41c39cd23e34df3 --outcome stopped` succeeded and `list --unresolved` no longer shows it.

## Files Changed
- tools/agent-monitoring/gate_ledger.py
- tests/tools/test_gate_ledger.py
- docs/guides/delivery_process.md

## Completion Summary
`record_outcome` and `record_adjudication` accept an orphan attested id (`_known_verdict_ids` adds `attested_without_verdict`), refuse a paired attested id with `PairedAttestedRow` naming the verdict to use, and `list` includes orphans (`orphan_view`) so `--unresolved` shows an open one and drops it once an outcome exists. Verdict totals and pass rates still ignore orphans. The stop for `gv-e41c39cd23e34df3` is recorded.
