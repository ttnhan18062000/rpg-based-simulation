# TCK-20260607-MON-RETRO

## Title
Agent Monitoring — Implement retro report generation, validation, and query tools

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Implement `generate_retro.py` (weekly report generator), `validate.py` (integrity cross-check), `query.py` (tabular filter), full `docs/agent-monitoring/retro-guide.md`, and Makefile targets.

## Scope
- `tools/agent-monitoring/generate_retro.py` — full implementation
- `tools/agent-monitoring/validate.py` — full implementation
- `tools/agent-monitoring/query.py` — full implementation
- `docs/agent-monitoring/retro-guide.md` — full content
- `Makefile` — 3 new targets

## Out of Scope
- Docusaurus integration (TCK-MON-DASHBOARD)
- Automated scheduling

## Acceptance Criteria
- [x] `generate_retro.py --all` produces RETRO-ALL.md with 6 sections
- [x] `generate_retro.py --week 2026-W23` produces week-specific report
- [x] `generate_retro.py` updates agent-monitoring/retro/index.md
- [x] `validate.py` exits 0 on empty JSONL files
- [x] `validate.py` checks: runs with no events, incomplete runs, DONE runs with no working_log entry
- [x] `query.py` supports: --agent, --status, --phase, --run-id, --days, --summary-contains, --runs
- [x] `retro-guide.md` documents when to run, sections, validation, query, and the retrospective process
- [x] 3 Makefile targets: `agent-monitoring-retro`, `agent-monitoring-validate`, `agent-monitoring-query`

## Related Tickets
- TCK-20260607-MON-SCHEMA (dependency)
- TCK-20260607-MON-CAPTURE (dependency — populates the JSONL files)

## Related Docs
- `docs/agent-monitoring/retro-guide.md`
- `docs/agent-monitoring/schema.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260607-MON-RETRO/`

## Related Code Areas
- `tools/agent-monitoring/`
- `Makefile`

## Assumptions / Open Questions
- validate.py uses forward-direction check only (runs → working_log), not reverse, to avoid false positives from historical tickets
- ISO week format: Python %G-W%V for ISO 8601 week numbers
- Retro index at agent-monitoring/retro/index.md auto-regenerated on every run

## Implementation Notes
validate.py initially checked working_log → runs (reverse direction), which failed on all historical tickets. Fixed to forward-direction only. Also added MONITORING_START constant and TCK- prefix guard for malformed working_log rows (some rows have swapped timestamp/ticket_id columns from old format). query.py uses terminal-friendly tabular output with truncation. generate_retro.py handles --all, --days N, --week YYYY-WNN, and default (current week) modes.

## Test Summary
Smoke-tested all three tools on empty JSONL files: validate.py exits 0, query.py outputs "No matching runs.", generate_retro.py --all produces RETRO-ALL.md. Makefile targets verified (make --dry-run).

## Files Changed
- `tools/agent-monitoring/generate_retro.py` (full implementation)
- `tools/agent-monitoring/validate.py` (full implementation)
- `tools/agent-monitoring/query.py` (full implementation)
- `docs/agent-monitoring/retro-guide.md` (full content)
- `Makefile` (3 targets added)

## Completion Summary
Implemented all three processing tools and full retro documentation. validate.py, query.py, and generate_retro.py all pass smoke tests on empty data. Makefile targets wire them to `make` commands.
