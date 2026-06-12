# create-tickets

Parse a natural-language proposal document into investigation-backed TCK-*.md ticket files, ready for `/implement-epic`.

The proposal can be written by anyone — developer, BA, tester — in any natural markdown format. The workflow does the investigation work so the author doesn't have to.

## Usage

```
/create-tickets source=docs/plans/proposal.md
/create-tickets source=docs/plans/proposal.md structure=docs/plans/ticket_plan_structure.md
/create-tickets source=docs/plans/proposal.md output=tickets/todos/phase29-repair/
/create-tickets source=docs/plans/proposal.md epic_id=TCK-20260608-PHASE29-EPIC
```

## Input

Parse the user's input to extract:

- `source` — path to the source markdown document (required). If the user provides a bare file path with no `source=` prefix, treat it as `source`.
- `structure` — path to a ticket plan structure / template doc (optional). Guides concern granularity and scope conventions.
- `output` — output folder override (optional). Inferred from the proposal content if omitted.
- `epic_id` — existing epic ticket ID to link the created tickets to (optional).

## Action

Invoke the Workflow tool with:
- `name: "create-tickets"`
- `args`: an object with the parsed fields above (omit any not provided)

## Pipeline

1. **Comprehend** — reads the proposal as natural language, extracts discrete concerns without enforcing ticket schema. Preserves the author's intent and framing.
2. **Investigate** — per concern (parallel): greps the actual codebase, checks the Mechanics Bible and Engine contracts, scans existing tickets, finds real file paths and derives testable AC signals from code behavior.
3. **Structure** — one synthesis agent takes all investigation results and produces properly-formed ticket fields: real file paths from grep, concrete ACs from code evidence, correct tier from scope, author's intent preserved in request_summary.
4. **Write** — creates `TCK-YYYYMMDD-<SHORT-SCOPE>.md` per task into the output folder (parallel).
5. **Link** — if `epic_id` given, appends the new ticket IDs to the epic's `## Related Tickets` section.

## Notes

- The proposal author does NOT need to provide file paths or acceptance criteria — the Investigate phase derives them from the codebase
- Output folder defaults to `tickets/todos/<inferred-name>/` — inferred from the proposal topic
- Concerns already fully covered by existing tickets are detected in Investigate and skipped (reported as duplicates)
- Concerns are split or merged based on what investigation reveals about the actual code structure
- If intra-batch ticket dependencies are detected, a `SEQUENCE.md` is written to enforce implementation order
- After creation, run `/implement-epic folder=<output_folder>` to implement the tickets
