---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260607-MON-SCHEMA
artifact_type: investigation
tags: [mon, schema]
---

# Investigation — TCK-20260607-MON-SCHEMA

## Current Behavior
No agent monitoring existed. No `agent-monitoring/` directory, no tools, no docs. Workflow runs produced no machine-readable record of what agents ran, what they returned, or whether gates passed.

## Mechanics / Engine Constraints
No mechanics Bible constraints — this is tooling infrastructure only.

## Parity Ledger Overlap
No parity ledger entries affected (infrastructure/tooling, not simulation logic).

## Prior Work
None. This is the first monitoring component in the project.

## Risks and Open Questions
- JSONL format chosen over SQLite to remain append-only and git-friendly (resolved: JSONL).
- `run_id` = ticket_id for implement-ticket workflow (assumption documented in ticket).
- Empty seed files committed so git tracks the file from day 1.

## Anti-Drift Hazards
- `runs.jsonl` and `events.jsonl` must NOT be in `.gitignore`.
- `retro/` directory needs `.gitkeep` to be committed before generated reports.
- Tools must be run from the repo root (not from inside `tools/`).
