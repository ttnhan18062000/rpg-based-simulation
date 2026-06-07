# create-tickets

Parse a detailed markdown document into individual TCK-*.md ticket files, ready for `/implement-epic`.

## Usage

```
/create-tickets source=docs/plans/another_repair_phase_20_28.md
/create-tickets source=docs/plans/phase29.md structure=docs/plans/ticket_plan_structure.md
/create-tickets source=docs/plans/phase29.md output=tickets/todos/phase29-repair/
/create-tickets source=docs/plans/phase29.md epic_id=TCK-20260608-PHASE29-EPIC
```

## Input

Parse the user's input to extract:

- `source` — path to the source markdown document (required). If the user provides a bare file path with no `source=` prefix, treat it as `source`.
- `structure` — path to a ticket plan structure / template doc (optional). Used to guide task granularity and scope conventions.
- `output` — output folder override (optional). Inferred from the source document's content if omitted.
- `epic_id` — existing epic ticket ID to link the created tickets to (optional).

## Action

Invoke the Workflow tool with:
- `name: "create-tickets"`
- `args`: an object with the parsed fields above (omit any not provided)

## Pipeline

1. **Parse** — reads the source doc (and structure template if given), scans existing tickets for duplicates, extracts one task per discrete concern
2. **Write** — writes `TCK-YYYYMMDD-<SHORT-SCOPE>.md` per task into the output folder (parallel)
3. **Link** — if `epic_id` given, appends the new ticket IDs to the epic's `## Related Tickets` section

## Notes

- Output folder defaults to `tickets/todos/<inferred-name>/` — inferred from the source doc's topic
- The parse agent skips items already covered by existing tickets (reports them as skipped)
- Tasks are split aggressively — one concern per ticket, no lumping
- After creation, run `/implement-epic folder=<output_folder>` to implement the tickets
- Combine with `epic_id` to keep an epic ticket's Related Tickets section up to date automatically
