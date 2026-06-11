---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260607-MON-AGENTS
artifact_type: plan
tags: [mon, agents]
---

# Implementation Plan — TCK-20260607-MON-AGENTS

## Summary
Add summary field to all 11 agent prompts and to all 5 schema agents' JSON schemas in implement-ticket.js.

## Steps

### Step 1 — Schema agents: add summary to JSON schemas in implement-ticket.js
TICKET_SCHEMA, REVIEW_SCHEMA, IMPL_SCHEMA, TEST_SCHEMA, DONE_SCHEMA. Add to required[] and properties.

### Step 2 — Schema agents: update Output sections in agent .md files
ticket-scoper.md, architecture-reviewer.md, implementer.md, test-scoper.md, done-checker.md.

### Step 3 — Text agents: update Output sections to lead with key sentence
investigator.md, planner.md, parity-updater.md.

### Step 4 — Standalone agents: add one-sentence summary to Output
mechanics-auditor.md, simulation-analyst.md, world-debugger.md.

## Scope Guards
Do not change agent logic, only Output/return specifications. Do not change tool schemas in any file other than implement-ticket.js.

## Acceptance Criteria Map
| AC | Steps |
|---|---|
| All 5 schema agents have summary in schema | 1 |
| All 11 agent .md files document summary expectation | 2, 3, 4 |
