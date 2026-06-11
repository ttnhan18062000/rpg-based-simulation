---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260607-MON-RETRO
artifact_type: plan
tags: [mon, retro]
---

# Implementation Plan — TCK-20260607-MON-RETRO

## Summary
Implement generate_retro.py (weekly report), validate.py (integrity check), query.py (tabular filter), retro-guide.md (doc), and Makefile targets.

## Steps

### Step 1 — Implement validate.py
Cross-check runs.jsonl vs events.jsonl vs working_log.csv. Exit 0/1. Three checks: incomplete runs, runs with no events, done tickets with no run record.

### Step 2 — Implement query.py
Tabular query with filters: --agent, --status, --phase, --run-id, --days, --summary-contains, --runs.

### Step 3 — Implement generate_retro.py
6 report sections: Run Summary, Gate Failure Breakdown, Tier Distribution, Agent Status Distribution, Summary Quality, Slow Runs. Auto-update index.md.

### Step 4 — Write retro-guide.md
Full content: when to run, how to generate, report sections, validation, query usage, retrospective process, Makefile targets.

### Step 5 — Add Makefile targets
agent-monitoring-retro, agent-monitoring-validate, agent-monitoring-query (with ARGS passthrough).

## Scope Guards
Do not touch: implement-ticket.js, CLAUDE.md, agent .md files. Makefile targets only for agent-monitoring.

## Acceptance Criteria Map
| AC | Steps |
|---|---|
| validate.py exits 0 on empty files | 1 |
| query.py produces tabular output | 2 |
| generate_retro.py --all writes RETRO-ALL.md | 3 |
| retro-guide.md documents the full process | 4 |
| 3 Makefile targets exist | 5 |
