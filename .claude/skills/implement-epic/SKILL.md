# implement-epic

Implement all tickets in a folder or epic sequentially using the `implement-epic` workflow.

## Usage

```
/implement-epic folder=tickets/todos/monitoring/
/implement-epic epic_id=TCK-20260607-MY-EPIC
/implement-epic request="add a caching layer to the world registry"
```

## Input

Parse the user's input (from `## Input` below) to extract one of:

- `folder` — path to a directory containing TCK-*.md tickets (e.g. `tickets/todos/monitoring/`)
- `epic_id` — an existing epic ticket ID (e.g. `TCK-20260607-MY-EPIC`)
- `request` — natural language description of a new epic (creates the epic ticket, then returns)
- `tier_override` — optional, overrides the tier for every child ticket (`hotfix`/`standard`/`epic`)

If the input is ambiguous (no `folder=`, `epic_id=`, or `request=` prefix), treat it as:
- A folder path if it looks like a path (contains `/` or starts with `tickets/`)
- A natural language request otherwise

## Action

Invoke the Workflow tool with:
- `name: "implement-epic"`
- `args`: an object with the parsed fields above (omit any that weren't provided)

## Notes

- Stops on the first gate failure and tells you which ticket blocked
- Re-running after a fix automatically skips already-done tickets
- Each child ticket writes its own monitoring records; the batch also writes one batch record
- Sequential only — not parallel (ticket dependencies make parallel unsafe by default)
