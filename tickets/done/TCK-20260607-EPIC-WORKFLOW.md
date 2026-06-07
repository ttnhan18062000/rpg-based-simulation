# TCK-20260607-EPIC-WORKFLOW

## Title
Add implement-epic workflow — batch-implement all tickets in a folder or epic

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Create `.claude/workflows/implement-epic.js` that discovers all tickets in a folder or epic ticket, then calls `implement-ticket` sequentially for each, stopping on any gate failure and reporting a summary.

## Scope
- `.claude/workflows/implement-epic.js` — new workflow

## Out of Scope
- Parallel ticket implementation
- Auto-creating child tickets from description

## Acceptance Criteria
- [x] `folder` mode: discovers TCK-*.md files, skips DONE, implements rest in order
- [x] `epic_id` mode: reads Related Tickets section, skips DONE, implements rest
- [x] `request` mode: creates epic ticket, returns EPIC_CREATED with instructions
- [x] Stops on first gate failure, reports ticket_id + status + message
- [x] Remaining (not-started) tickets listed in return value so user knows what to re-run
- [x] Batch monitoring run record written to runs.jsonl
- [x] Re-running after a fix automatically skips already-done tickets

## Related Tickets
- TCK-20260607-MON-CAPTURE

## Related Docs
- `.claude/workflows/implement-ticket.js`

## Related Stored Artifacts
None.

## Related Code Areas
- `.claude/workflows/`

## Assumptions / Open Questions
- Sequential only — ticket dependencies make parallel unsafe
- `workflow('implement-ticket', ...)` call nests correctly per workflow docs
- batch run_id = `EPIC-{epic_id}` or `FOLDER-{sanitized_path}`

## Implementation Notes
Uses `workflow()` to call implement-ticket for each child — no logic duplication. Discovery agent uses bash `ls` to enumerate tickets and check done status. Loop breaks on first non-DONE result; remaining tickets reported so the user knows exactly what to re-run. Batch monitoring write is non-fatal (same pattern as implement-ticket).

## Test Summary
No automated tests — workflow script. Verified logic by reading: folder/epic_id/request modes all produce correct discovery schema; sequential loop exits on gate failure; batch monitoring record uses EPIC-/FOLDER- prefix for run_id.

## Files Changed
- `.claude/workflows/implement-epic.js` (created)

## Completion Summary
Created implement-epic.js workflow supporting three input modes (folder, epic_id, request). Calls implement-ticket sequentially via workflow(), stops on gate failure, skips already-done tickets on re-run, and writes a batch monitoring record.
