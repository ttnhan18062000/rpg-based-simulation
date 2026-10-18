---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261018-RETRO-GATE-FAILURES-ROW-CITES-LEDGER
phase: open
date: 2026-10-18
tags: [ai, agent-monitoring, data-quality]
---

# TCK-20261018-RETRO-GATE-FAILURES-ROW-CITES-LEDGER

## Title
The retro Run Summary's "Gate failures" row cites the gate ledger's blocking count instead of a misleading 0

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Owner decision 2026-10-18 (via lead-planner), from the RETRO-2026-W42 final note (81 runs).
- The Run Summary row `| Gate failures | 0 |` counts only runs whose `final_status` is a gate failure.
- Hand closures fix and rerun, or override, so runs almost never end that way. Meanwhile the gate ledger recorded 27 blocking Finalize verdicts out of 108 that week (6 overridden, 1 unresolved).
- TCK-20261015-CLOSURE-RECORDER-PHASE-EVIDENCE-AND-PARITY-SKIP-REASON added a second row ("Blocking gate verdicts (ledger)"), but the first row still reads "0" at a glance.
- The same run-based count feeds the "Gate failures" column of `retro/index.md`.

## Scope
- `tools/agent-monitoring/generate_retro.py`, Run Summary: when the ledger figures exist (`ledger_blocks is not None`), the **"Gate failures" row shows the ledger's blocking count**. Shape:
  `| Gate failures | 27 blocking verdicts of 114 (ledger: 6 overridden, 1 without an outcome); 0 runs ended in a gate failure |`
  - The outcome breakdown comes from fields `_ledger_blocks` already has, or adds cheaply.
  - The separate "Blocking gate verdicts (ledger)" row is folded into it, so there's no duplicate number.
  - With no ledger for the window (`--all`, `--days`, or weeks before the ledger existed), keep the run-based count, labelled `| Gate failures (runs; no gate ledger for this window) | N |`.
- `retro/index.md` "Gate failures" column: use the same rule per report. The ledger blocking count applies where the report's week has ledger data, otherwise the run count with a `r` suffix or a footnote. Pick the least noisy option and state it in the index header note.
- Tests in `tests/tools/test_generate_retro.py`, using fixture ledgers with blocking verdicts and 0 gate-failed runs:
  - the row shows the ledger count;
  - with no ledger, the labelled run fallback appears;
  - the index column follows the same rule;
  - regenerating keeps `## Notes`, which is the existing behaviour.

## Out of Scope
- The per-tag "Gate failures" column (run-based, with a different meaning). Leave it unchanged, and add a header note only if it's a one-liner.
- Any change to the ledger itself.

## Acceptance Criteria
- Regenerating RETRO-2026-W42 locally shows a "Gate failures" row with the ledger's blocking count, not 0. Don't commit the regenerated real report unless asked; the next retro does that.
- Tests are green.

## Related Tickets
- TCK-20261015-CLOSURE-RECORDER-PHASE-EVIDENCE-AND-PARITY-SKIP-REASON
- TCK-20261006-GATE-PRECISION-REPORT-AND-RETRO

## Related Docs
- docs/guides/agent_monitoring.md (Report Sections table)

## Related Stored Artifacts
- none

## Related Code Areas
- tools/agent-monitoring/generate_retro.py (`_ledger_blocks`, Run Summary, `update_index`)

## Assumptions / Open Questions
- none

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
