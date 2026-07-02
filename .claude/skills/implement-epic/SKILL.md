# implement-epic

Implement all tickets in a folder or epic sequentially.

## Usage

```
/implement-epic folder=tickets/todos/monitoring/
/implement-epic epic_id=TCK-20260607-MY-EPIC
/implement-epic request="add a caching layer to the world registry"
```

## Input

Parse the user's input to extract one of:

- `folder` — path to a directory containing TCK-*.md tickets (e.g. `tickets/todos/monitoring/`)
- `epic_id` — an existing epic ticket ID (e.g. `TCK-20260607-MY-EPIC`)
- `request` — natural language description of a new epic (creates the epic ticket, then returns)
- `tier_override` — optional, overrides the tier for every child ticket (`hotfix`/`standard`)

If the input is ambiguous (no prefix), treat as a folder path if it contains `/` or starts with `tickets/`, otherwise as a natural language request.

## Action

**Do not call the Workflow tool — it is not available.** Execute the workflow directly:

1. Read `.claude/workflows/implement-epic.js` in full before doing anything else.
2. Execute each phase using the same JS → tool translation as `implement-ticket` (see that skill's translation table).
3. For the `await workflow('implement-ticket', args)` call inside the ticket loop:
   - Do not call a Workflow tool.
   - Instead, read `.claude/workflows/implement-ticket.js` and execute the full implement-ticket pipeline for that `ticket_id`, following the same translation rules.
   - Carry the result back into the epic loop as the JS specifies.
4. Execute child tickets **sequentially** — complete one fully before starting the next. Stop on the first non-DONE result.

## Phases

| Phase | What happens |
|---|---|
| **Discover** | List tickets in folder or read epic's Related Tickets; check `tickets/done/` to skip already-done ones; capture start timestamp (`ts` field, required) |
| **Implement** | Run implement-ticket pipeline for each pending ticket in order; stop on first gate failure |
| **Report** | Summarise: DONE count, gate failures, remaining tickets |

After the Implement phase, write the batch monitoring record (the block at the bottom of the Implement phase in the JS). Then, if `batchStatus === 'DONE'` and mode is `folder`, move the entire `tickets/todos/{folder}/` to `tickets/done/{folder}/` — this preserves SEQUENCE.md and any folder-level metadata. Then move to Report.

## Notes

- Stops on the first gate failure and tells the user which ticket blocked and why
- Re-running after a fix automatically skips already-done tickets — Discover re-checks `tickets/done/` each time
- Each child ticket writes its own `implement-ticket` monitoring records; the epic also writes one batch record (`EPIC-{id}` or `FOLDER-{path}`)
- Sequential only — not parallel
- For `request` mode: creates the epic ticket and returns `EPIC_CREATED`; no implementation happens until re-run with `epic_id`
