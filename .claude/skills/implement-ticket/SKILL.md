# implement-ticket

Run the full ticket implementation pipeline for a single ticket.

## Usage

```
/implement-ticket ticket_id=TCK-20260607-MY-TICKET
/implement-ticket request="add pagination to the world listing endpoint"
/implement-ticket ticket_id=TCK-20260607-MY-TICKET tier=hotfix
```

## Input

Parse the user's input (from `## Input` below) to extract:

- `ticket_id` — existing ticket ID to resume (e.g. `TCK-20260607-MY-TICKET`); looks for it in `tickets/inprogress/` or `tickets/done/`
- `request` — natural language description of a new ticket to create and implement
- `tier` — optional override: `hotfix` (skip Investigate/Plan/Review), `standard` (full pipeline), `epic` (scope only)

If the input is a bare TCK-... ID, treat it as `ticket_id`.
If the input is a natural language sentence, treat it as `request`.

## Action

Invoke the Workflow tool with:
- `name: "implement-ticket"`
- `args`: an object with the parsed fields above (omit any that weren't provided)

## Pipeline (standard tier)

1. **Scope** — create or load ticket
2. **Investigate** — produce investigation.md and test_plan.md
3. **Plan** — produce plan.md
4. **Review** — architecture review (gate)
5. **Implement** — write code
6. **Test** — run scoped pytest
7. **Parity** — update parity ledger
8. **Verify** — Definition-of-Done checklist
9. **Finalize** — move ticket, append working_log, migrate artifacts

Hotfix tier skips steps 2–4.

## Notes

- Pass `ticket_id` to resume from an existing in-progress ticket
- Gate failures return early with the blocking status and a re-run instruction
- Agent monitoring records are written at every exit point
