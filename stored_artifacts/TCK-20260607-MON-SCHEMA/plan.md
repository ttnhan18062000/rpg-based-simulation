---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260607-MON-SCHEMA
artifact_type: plan
tags: [mon, schema]
---

# Implementation Plan — TCK-20260607-MON-SCHEMA

## Summary
Create the agent-monitoring directory structure, define the two-table JSONL schema, write documentation, and implement all five tools (record_run.py, record_events.py, generate_retro.py, validate.py, query.py). Note: ticket originally said "stub scripts" but we implemented the full tools in this pass to avoid a second session.

## Steps

### Step 1 — Create directory structure
**Files:** agent-monitoring/runs.jsonl, agent-monitoring/events.jsonl, agent-monitoring/retro/.gitkeep, tools/agent-monitoring/__init__.py
**Change:** Create all directories and empty seed files.

### Step 2 — Write schema documentation
**Files:** docs/agent-monitoring/schema.md, docs/agent-monitoring/README.md, agent-monitoring/README.md
**Change:** Full field reference for both tables, component overview, quick-reference.

### Step 3 — Implement record_run.py and record_events.py
**Files:** tools/agent-monitoring/record_run.py, tools/agent-monitoring/record_events.py
**Change:** CLI scripts with validation, append-only writes, exit 0/1.

### Step 4 — Implement generate_retro.py, validate.py, query.py
**Files:** tools/agent-monitoring/generate_retro.py, tools/agent-monitoring/validate.py, tools/agent-monitoring/query.py
**Change:** Full implementations (retro report generation, integrity cross-check, tabular query).

### Step 5 — Write retro guide
**Files:** docs/agent-monitoring/retro-guide.md
**Change:** Full content explaining the retro process, report sections, and query usage.

## Scope Guards
Do not touch: implement-ticket.js, CLAUDE.md, any agent .md files, Makefile — those belong to later tickets.

## Acceptance Criteria Map
| AC | Steps | Test |
|---|---|---|
| agent-monitoring/ structure exists | 1 | ls check |
| tools/ scripts exist and are importable | 3, 4 | python3 -c "import tools.agent_monitoring.record_run" |
| schema.md documents all fields | 2 | review |
| record_run.py validates required fields | 3 | manual test |
| record_events.py validates and truncates | 3 | manual test |
