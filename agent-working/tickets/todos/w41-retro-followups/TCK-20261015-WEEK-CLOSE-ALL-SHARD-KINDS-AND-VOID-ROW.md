---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261015-WEEK-CLOSE-ALL-SHARD-KINDS-AND-VOID-ROW
phase: open
date: 2026-10-15
tags: [agent-monitoring, data-quality]
---

# TCK-20261015-WEEK-CLOSE-ALL-SHARD-KINDS-AND-VOID-ROW

## Title
Week close folds gate_verdicts, manual_actions and role_boundary shards too, and a dropped ticket can void its pending working_log row

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Source: RETRO-2026-W41 final note (PR #605), W41/W42 deep investigation 2026-10-15, finding 6, and PR #603's known gap. `week_close.py` folds only `JSONL_KINDS = ("runs","events","tools")`
(`monitoring_consolidation.py` around L61) plus working_log. So W41's 96 `*.gate_verdicts.jsonl` shards,
`manual_actions.jsonl` and `role_boundary.jsonl` stay in place after the close. Separately,
`TCK-20261014-DEPENDABOT-IGNORE-MAJOR-BUMPS` was dropped (deleted in 0582ec8db) but is recorded DONE in
`2026-W42/platform-implementer-step1-closure.runs.jsonl` and has a pending row in
`2026-W42/platform-implementer-step1-closure.working_log.jsonl`. Closing W42 would write a working_log.csv row for a ticket
that never shipped. There is no row kind for "this pending row is void".

## Scope
1. Week close folds gate_verdicts shards into a canonical weekly `gate_verdicts.jsonl` (and the bare manual_actions /
   role_boundary files, if they are per-batch anywhere). Keep the conservation check (lines in = lines out).
2. Every gate_ledger reader keeps working on the folded file (gate_ledger.py list/report, retro Gates section).
3. A void mechanism for a pending working_log row of a dropped ticket: a typed void row or a supported removal command,
   whichever fits the existing design. It is recorded, never a silent delete. Apply it to the DEPENDABOT row before W42 closes.
4. Run it on W41 after #603 merges (fold the remaining W41 gate_verdicts shards).

## Out of Scope
- Changing shard keying (seat/idle/sync branches writing tools-only shards: note it as an idea, no change).
- Closing W42 itself (only after 2026-10-18).

## Acceptance Criteria
- Tests: a fixture week with gate_verdicts shards closes to one canonical file with equal line counts, and
  `gate_ledger.py list --unresolved` gives the same ids before and after.
- The DEPENDABOT pending row is voided by the new mechanism, and a W42 close dry run writes no working_log.csv row for it.
- W41's gate_verdicts shards are folded on main.

## Related Tickets
- TCK-20261001-MONITORING-WEEK-CLOSE-COMMAND
- TCK-20261006-EPIC-GATE-OVERRIDE-LEDGER
- PR #603 (W41 close)

## Related Docs
- docs/agent-monitoring/README.md (Closing a finished week)

## Related Stored Artifacts
- agent-working/agent-monitoring/retro/RETRO-2026-W41.md (final note, runs=281)

## Related Code Areas
- tools/agent-monitoring/week_close.py, tools/agent-monitoring/monitoring_consolidation.py, tools/agent-monitoring/gate_ledger.py

## Assumptions / Open Questions
- Depends on #603 merging first (W41 canonical files).

## Implementation Notes
(filled during work)

## Test Summary
(filled during work)

## Files Changed
(filled during work)

## Completion Summary
(filled at close)
