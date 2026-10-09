---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261009-HAND-CLOSURE-TEMPLATED-EVENTS-GUARD
phase: open
date: 2026-10-09
tags: [agent-monitoring, data-quality]
---

# TCK-20261009-HAND-CLOSURE-TEMPLATED-EVENTS-GUARD

## Title
record_hand_orchestrated_closure refuses events copied from another ticket and a Parity "ok" with no ledger change

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
PR #457 (rpg-batch-d36-d32) hand-closed 6 tickets with one events payload reused for all of them. All six got the
same six summaries ("pinned 5x3 report" even on a crash fix), and Parity was `ok` for 4 tickets that changed no
`docs/parity_ledger/` file. Main records that phase as `skipped`/`condition_false`. The record was found only by a
human review. `record_hand_orchestrated_closure.py` already refuses a duplicate working_log row. The owner asked
(2026-10-09) for the tool to catch this class too, so that no domain repeats it.

## Scope
Two checks in `tools/agent-monitoring/record_hand_orchestrated_closure.py`, run before anything is written. Each one
fails with `ERROR:`, a non-zero exit and a message saying how to fix the events, the same way the duplicate-row
refusal does:
1. **Parity claimed without a ledger change.** A Parity event with status `ok` while the ticket changed no
   `docs/parity_ledger/` file is refused. "Changed" uses
   `mechanism_registry_changed_code_check.get_changed_files_for_ticket` (the ticket's own commits plus the working
   tree). The message says to use `"status":"skipped","skip_reason":"condition_false"`, or to commit the ledger change
   first.
2. **Events copied from another ticket.** The new events are refused when, phase for phase, all of their non-empty
   summaries equal the summaries of an already-recorded run for a different ticket in the same per-batch shard
   (`<week>/<branch>.events.jsonl`). The message names that ticket.
- An explicit override flag, `--allow-shared-summaries`, for the rare honest case. It records `summaries_shared: true`
  on the run row, so the override stays visible.
- Update the closure-recorder line in `docs/guides/delivery_process.md`, or wherever the tool's usage is documented,
  with the two refusals.
- Tests: Parity ok without a ledger change refuses; Parity ok with a ledger change passes; Parity skipped passes;
  a second ticket with identical summaries refuses and names the first; partly different summaries pass; the override
  passes and marks the row.

## Out of Scope
- Rewriting existing shards on main or on PR #457 (the rpg side is regenerating #457's events shard itself).
- Timestamps: `--start-ts` and `--end-ts` already exist. Back-recorded closures with start == end stay allowed.
- Checking whether summaries are true. Only the two mechanical signals above are checked.

## Acceptance Criteria
1. The PR #457 payload, replayed for a second ticket in the same shard, is refused and names the first ticket.
2. Parity `ok` for a ticket with no `docs/parity_ledger/` change is refused with the skipped/condition_false hint.
3. Honest inputs pass unchanged. The override records `summaries_shared: true`.
4. Existing closure-recorder tests pass, and the duplicate-row refusal is unchanged.

## Related Tickets
- TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE (the duplicate-row refusal precedent)
- TCK-20261009-PR-RENDER-RAW-PROBE-OUTPUT-ADVISORY (the probe half of the same PR #457 review)

## Related Docs
- docs/guides/delivery_process.md
- CLAUDE.md's closure-recorder bullet is the owner's; propose any wording change there, don't edit it.

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- tools/agent-monitoring/record_hand_orchestrated_closure.py
- tools/mechanism_registry/mechanism_registry_changed_code_check.py (`get_changed_files_for_ticket`, reused)
- tests/tools/ (closure-recorder tests)

## Assumptions / Open Questions
- A non-zero refusal does not break "monitoring write failure must never fail the workflow". It is input validation
  before any write, the same as the existing duplicate-row refusal, and the fix is to correct the events and rerun.
- `search_docs` index not built, graphify graph missing in this worktree: the duplicate scan used the ticket folders
  and grep. No open ticket covers this.

## Implementation Notes
Hand-orchestrated hotfix on `agent-working-small-fixes-batch`, in the same batch PR (owner, 2026-10-09). When it lands,
agent-working-planner tells rpg-planner (and the other planners) that the recorder now refuses both patterns.

## Test Summary
## Files Changed
## Completion Summary
