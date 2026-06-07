# Investigation — TCK-20260607-MON-AGENTS

## Current Behavior
All 11 agent .md files had no `summary` field requirement in their Output sections. Schema agents (ticket-scoper, architecture-reviewer, implementer, test-scoper, done-checker) returned structured objects with no summary field. Text agents (investigator, planner, parity-updater) returned free-form text with no convention about leading with the key sentence.

## Mechanics / Engine Constraints
None — tooling only.

## Parity Ledger Overlap
None.

## Prior Work
TCK-20260607-MON-CAPTURE defined where summaries would be consumed (events[] in implement-ticket.js).

## Risks and Open Questions
- For text agents (investigator, planner, parity-updater): we can't enforce the first-sentence convention structurally — it's a prompt instruction only. Compliance tracked via `empty_summaries` metric in generate_retro.py.
- For non-implement-ticket agents (mechanics-auditor, simulation-analyst, world-debugger): they're not called by the workflow, so their summary is for human readers and future workflows.

## Anti-Drift Hazards
- If a new schema agent is added to implement-ticket.js in the future, it must add `summary` to its schema.
- Text agents must be reminded in their output section — the convention is easy to forget.
