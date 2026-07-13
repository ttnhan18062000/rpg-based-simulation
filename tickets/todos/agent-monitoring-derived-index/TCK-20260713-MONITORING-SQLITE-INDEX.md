---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260713-MONITORING-SQLITE-INDEX
phase: open
date: 2026-07-13
tags: []
---

# TCK-20260713-MONITORING-SQLITE-INDEX

## Title
Build derived, read-only SQLite index over agent-monitoring JSONL logs

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The author wants a new build script (tools/agent-monitoring/build_index.py) that reads runs.jsonl, events.jsonl, and tools.jsonl once, normalizes every legacy record shape in one place, and writes the result into SQLite tables (runs, events, tools) plus a normalized view (e.g. a resolved_status column). This mirrors the existing knowledge-index/knowledge.db precedent built by tools/knowledge_search.py: gitignored, derived, rebuildable, never the source of truth. The JSONL files themselves stay exactly as-is (append-only, hook-written) — this is purely a new read-path convenience layer, not a change to the write path. Full rebuild only (no incremental-build logic, since parsing ~47k lines is sub-second), exposed via one Make target (make agent-monitoring-index). Motivation: four independent consumers currently each re-implement their own interpretation/joins of the same raw data.

## Scope
- Create tools/agent-monitoring/build_index.py that reads runs.jsonl, events.jsonl, and tools.jsonl exactly once each
- Normalize every legacy record shape (5+ historical runs.jsonl schema generations per docs/agent-monitoring/schema.md) in one central place
- Write normalized data into a gitignored SQLite database with runs, events, and tools tables
- Produce a resolved_status (or equivalently-named normalized) column/value on the runs table consistent with generate_retro.py's _resolve_status() output and validate.py's LEGACY_COMPLETION_FIELDS/LEGACY_TERMINAL_STATUS_VALUES allowlists
- Add a single new Make target agent-monitoring-index (no -update variant) alongside the existing agent-monitoring-retro/validate/query/epic-staleness targets
- Add the output SQLite db path to .gitignore
- Implement full-rebuild-only logic (no incremental build)

## Out of Scope
- Migrating query.py, validate.py, or generate_retro.py to actually consume the index (tracked separately as follow-on tickets TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE, TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE, TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE)
- Any change to the JSONL write path (pre_tool_hook.py, post_tool_hook.py, record_run.py, record_events.py) — append-only write behavior must remain untouched
- Adding test coverage to query.py itself (separate migration ticket's responsibility)
- Automatic or hook-triggered index builds — this ticket delivers strictly on-demand builds only

## Acceptance Criteria
- [ ] Running `python3 tools/agent-monitoring/build_index.py` (or `make agent-monitoring-index`) reads all 3 JSONL files exactly once each, writes a gitignored SQLite file with runs/events/tools tables, and exits 0
- [ ] The build script never modifies any of the 3 source JSONL files — byte-identical before/after, verified by hash comparison in a test
- [ ] The runs table's resolved_status (or equivalently-named) column agrees with generate_retro.py's existing _resolve_status() output for every row in the current runs.jsonl
- [ ] The runs table's completeness/terminal-status classification is consistent with validate.py's LEGACY_COMPLETION_FIELDS/LEGACY_TERMINAL_STATUS_VALUES allowlists, verified on the same fixture data used by tests/tools/test_validate_agent_monitoring.py
- [ ] Re-running the build script twice in a row with unchanged JSONL inputs produces a byte-identical (or row-count-identical) SQLite output both times
- [ ] `make agent-monitoring-index` is defined as a single new Makefile target and the output db path is added to .gitignore

## Related Tickets
- TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE (sibling — depends on this ticket)
- TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE (sibling — depends on this ticket)
- TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE (sibling — depends on this ticket)
- TCK-20260607-MON-SCHEMA
- TCK-20260705-MONITORING-RUNID-JOIN
- TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT
- TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION
- TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX
- TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH
- TCK-20260612-LOCAL-CTX-HYBRID-SEARCH
- TCK-20260612-LOCAL-CTX-OPS

## Related Docs
- docs/plans/agent_infrastructure/idea_agent_monitoring_derived_index.md
- docs/agent-monitoring/schema.md
- docs/agent-monitoring/README.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/agent_infrastructure/idea_agent_monitoring_derived_index.md
- tools/agent-monitoring/query.py
- tools/agent-monitoring/generate_retro.py
- tools/agent-monitoring/validate.py
- tools/agent-monitoring/vocabulary.py
- tools/knowledge_search.py
- docs/agent-monitoring/schema.md
- docs/agent-monitoring/README.md
- Makefile
- .gitignore
- agent-monitoring/runs.jsonl
- agent-monitoring/events.jsonl
- agent-monitoring/tools.jsonl

## Assumptions / Open Questions
- Whether resolved_status should be a build-time SQL column/view vs. a Python helper is an open decision to resolve during Scope/Plan
- Whether a Make target or a tools/agent-monitoring/ CLI subcommand is the right home is an open decision (both conventions coexist in this repo); Make target is the author's stated preference
- The index should stay strictly on-demand (no hook-triggered auto-build) per the author's framing
- query.py currently has zero test coverage; this ticket does not address that gap, it is left to the query.py migration ticket
- tools.jsonl is actively growing (~49k lines); normalization logic must handle every legacy shape validate.py/generate_retro.py currently special-case

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
