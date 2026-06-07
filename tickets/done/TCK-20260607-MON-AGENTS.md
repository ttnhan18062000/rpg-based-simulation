# TCK-20260607-MON-AGENTS

## Title
Agent Monitoring — Add summary field to all agent output specifications

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Add `summary` field (one sentence ≤200 chars) to the output specification of all 11 agent .md files and to all 5 schema agents' JSON schemas in implement-ticket.js.

## Scope
- All 11 `.claude/agents/*.md` files: Output section updated with summary expectation
- `.claude/workflows/implement-ticket.js`: summary added to TICKET_SCHEMA, REVIEW_SCHEMA, IMPL_SCHEMA, TEST_SCHEMA, DONE_SCHEMA

## Out of Scope
- Agent logic or behavior changes (prompt changes only)
- Adding automated tests for prompt compliance

## Acceptance Criteria
- [x] ticket-scoper.md: summary field in Output (returned in schema)
- [x] investigator.md: Output leads with one sentence ≤200 chars
- [x] planner.md: Output leads with one sentence ≤200 chars
- [x] architecture-reviewer.md: summary field in Output (returned in schema)
- [x] implementer.md: summary field in Output (returned in schema alongside implementation_summary)
- [x] test-scoper.md: summary field in Output (returned in schema)
- [x] parity-updater.md: Output leads with one sentence ≤200 chars
- [x] done-checker.md: summary field in Output + condition 12 added to checklist
- [x] mechanics-auditor.md: one-sentence summary as Output item 0
- [x] simulation-analyst.md: one-sentence summary as Output item 0
- [x] world-debugger.md: one-sentence summary as Output item 0
- [x] implement-ticket.js: all 5 schema agents have summary in required[] and properties

## Related Tickets
- TCK-20260607-MON-CAPTURE (consumer)

## Related Docs
- `docs/agent-monitoring/schema.md` (summary field documented)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260607-MON-AGENTS/`

## Related Code Areas
- `.claude/agents/` (all 11 files)
- `.claude/workflows/implement-ticket.js`

## Assumptions / Open Questions
- Text agent summary compliance is enforced by prompt instruction only (not structurally verifiable)
- Summary quality is tracked by generate_retro.py empty_summaries metric

## Implementation Notes
For schema agents: added `summary: { type: 'string', description: '...' }` to required[] and properties. For text agents: added "Begin your response with one sentence (≤200 chars) summarizing the key finding" to the Output section. For standalone agents (mechanics-auditor, simulation-analyst, world-debugger): added "one-sentence summary" as item 0 of the Output list. done-checker gets condition 12 (agent monitoring, pre-marked PASS by workflow).

## Test Summary
No automated tests — prompt changes only. Quality tracked via generate_retro.py empty_summaries metric after first workflow runs.

## Files Changed
- `.claude/agents/ticket-scoper.md`
- `.claude/agents/investigator.md`
- `.claude/agents/planner.md`
- `.claude/agents/architecture-reviewer.md`
- `.claude/agents/implementer.md`
- `.claude/agents/test-scoper.md`
- `.claude/agents/parity-updater.md`
- `.claude/agents/done-checker.md`
- `.claude/agents/mechanics-auditor.md`
- `.claude/agents/simulation-analyst.md`
- `.claude/agents/world-debugger.md`
- `.claude/workflows/implement-ticket.js` (schema changes only)

## Completion Summary
Added summary field expectation to all 11 agent prompts and to all 5 schema agents' JSON schemas. Schema agents return summary as a required field; text agents are instructed to lead with the key sentence. Compliance tracked via the retro empty_summaries metric.
