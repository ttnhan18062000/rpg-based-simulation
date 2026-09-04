---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260904-AGENT-TOOL-USAGE-BASELINE
phase: open
date: 2026-09-04
tags: [governance, ai, agent-monitoring]
---

# TCK-20260904-AGENT-TOOL-USAGE-BASELINE

## Title
Per-agent tool-usage baseline audit from agent-monitoring data

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P0

## Request Summary
Mine agent-monitoring for each of the 16 agents' real historical tool-call pattern (which tools, how often, what scope) to produce one usage table — this is the evidence M3's per-agent tools: frontmatter scoping decisions will be based on, so its accuracy directly gates whether that later scoping work is safe. Pure read/aggregation against existing monitoring data, no code changes to production paths, no execution risk. Gated on nothing and can start immediately, but the concern author's own source text (referencing a tool_input field and a single agent-monitoring/tools.jsonl file) is stale and must be corrected against the real schema before implementation begins.

## Scope
- Write a read-only script that globs all agent-monitoring/data/*/tools.jsonl weekly shards (not a single retired agent-monitoring/tools.jsonl path)
- Aggregate tool-call counts per agent using the agent field, explicitly bucketing null/non-matching values as an 'unattributed' group rather than silently dropping or misassigning them
- Read tool-call detail from the real input_summary field (truncated max 120 chars), not the nonexistent tool_input field the epic doc assumes
- Produce one usage table covering all 16 currently-registered agents (from .claude/agents/*.md) plus the unattributed bucket, with at least one truthfully-labeled truncated example per tool-name entry
- Sanity-check aggregate row counts against a raw wc -l across all shards

## Out of Scope
- Any change to .claude/agents/*.md tools: frontmatter (that is a separate, dependent ticket's job, gated on this ticket's output)
- Any modification to agent-monitoring write paths, schema, or shard migration tooling
- Deriving exact Bash 'command class' beyond what input_summary's 120-char truncation actually supports

## Acceptance Criteria
- [ ] Script output contains exactly 16 agent rows (matching current .claude/agents/*.md file names) plus one explicit 'unattributed' row for null/non-matching agent values — not hardcoded or stale against the current agent roster
- [ ] Script globs all agent-monitoring/data/*/tools.jsonl shards and the sum of per-agent counts matches a wc -l sanity check across those shards
- [ ] Every tool-name entry in the output table includes at least one real representative example drawn from input_summary, explicitly labeled as truncated/summarized
- [ ] A test asserts the script is read-only against agent-monitoring/data/ (shard file bytes unchanged before vs. after running the script)

## Related Tickets
- Adjacent, different scope: TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC (done)
- Reference for correct shard structure: TCK-20260902-MONITORING-SHARD-MIGRATION
- Reference for correct write-path assumptions: TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY
- Reference for correct glob pattern: TCK-20260903-MONITORING-DATA-MIGRATION

## Related Docs
- docs/agent-monitoring/schema.md
- docs/agent-monitoring/README.md
- docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/agent-monitoring/schema.md
- docs/agent-monitoring/README.md
- agent-monitoring/data/2026-W24/tools.jsonl
- agent-monitoring/data/2026-W36/tools.jsonl
- tools/agent-monitoring/generate_retro.py
- tools/agent-monitoring/query.py
- .claude/agents/*.md
- tests/tools/test_record_events.py

## Assumptions / Open Questions
- Epic doc's assumptions of a tool_input field and a single tools.jsonl file are stale and must be corrected in this ticket's own documentation before implementation, not silently worked around
- 189,871 rows are spread across 14 shards — implementation should stream rows rather than building a large in-memory structure
- input_summary's 120-char truncation limits how precisely Bash 'command class' can be derived — this is an accepted limitation, not a gap to silently paper over
- If null-agent rows are mis-grouped instead of explicitly bucketed as unattributed, the downstream per-agent scoping ticket would be built on an incomplete picture without that gap being visible — must be avoided by design

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
