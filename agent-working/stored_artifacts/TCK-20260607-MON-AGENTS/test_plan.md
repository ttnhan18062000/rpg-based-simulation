---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260607-MON-AGENTS
artifact_type: test_plan
tags: [mon, agents]
---

# Test Plan — TCK-20260607-MON-AGENTS

## Regression Surface
- All 11 .claude/agents/*.md files (prompt changes, not behavior changes)
- .claude/workflows/implement-ticket.js (schema changes only)

## New Tests Required
None — prompt changes are verified by running the workflow and checking events.jsonl.

## Scoped Pytest Commands
```
# No automated tests for agent prompt changes.
# Verify summary quality via retro:
python3 tools/agent-monitoring/generate_retro.py --all
# Check "Summary Quality" section in generated report for empty_summaries count.
```

## Anti-Drift Test Guards
- generate_retro.py tracks empty_summaries per week — rising count signals agent prompt drift.
