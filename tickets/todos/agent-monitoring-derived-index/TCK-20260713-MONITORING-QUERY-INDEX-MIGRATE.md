---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE
phase: open
date: 2026-07-13
tags: []
---

# TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE

## Title
Migrate query.py to the SQLite index and add its first test suite

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
The author wants tools/agent-monitoring/query.py — currently a 120-line full in-memory linear scan with zero test coverage — to become the first consumer migrated onto the new SQLite index, since it's the lowest-risk target, and to gain net-new tests as part of that migration (with an open question on whether tests should land before or in the same diff as the migration).

## Scope
- Migrate tools/agent-monitoring/query.py's read path from an in-memory linear scan over runs.jsonl/events.jsonl to querying the SQLite index built by build_index.py
- Add tests/tools/test_query.py exercising query.py's CLI argument-parsing/filtering logic for --agent, --status, --phase, --run-id, --days, --summary-contains, and --runs, individually and combined
- Add a regression parity test comparing pre-migration in-memory-scan output vs post-migration index-backed output field-for-field on fixed fixtures
- Add a clear, actionable error path when the index is missing or stale (e.g. "run `make agent-monitoring-index` first") instead of a raw exception or silent empty result

## Out of Scope
- Building or modifying tools/agent-monitoring/build_index.py or its schema — that is sibling ticket TCK-20260713-MONITORING-SQLITE-INDEX's responsibility; this ticket is BLOCKED until it ships and its schema is stable
- Migrating validate.py's drift-report logic (separate ticket TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE)
- Migrating generate_retro.py's legacy-shape helpers (separate ticket TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE)
- Any change to the JSONL write path

## Acceptance Criteria
- [ ] tests/tools/test_query.py exists and exercises query.py's CLI argument-parsing/filtering logic directly for --agent, --status, --phase, --run-id, --days, --summary-contains, and --runs filters, individually and combined
- [ ] After migration, query.py's output for a fixed set of runs/events fixtures is field-for-field identical between the pre-migration in-memory-scan path and the post-migration SQLite-index-backed path
- [ ] query.py's migrated read path queries only the derived SQLite index and performs zero direct reads of agent-monitoring/runs.jsonl or events.jsonl once migrated
- [ ] If the index is missing or stale, query.py fails with a clear, actionable error (e.g. "run `make agent-monitoring-index` first") rather than a raw exception or silent empty-result output

## Related Tickets
- TCK-20260713-MONITORING-SQLITE-INDEX (BLOCKS this ticket — build_index.py must ship first)
- TCK-20260607-MON-RETRO
- TCK-20260705-MONITORING-RUNID-JOIN
- TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT
- TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION

## Related Docs
- docs/plans/agent_infrastructure/idea_agent_monitoring_derived_index.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/query.py
- tools/agent-monitoring/validate.py
- tools/agent-monitoring/generate_retro.py
- tools/knowledge_search.py
- docs/agent-monitoring/schema.md
- tests/tools/test_validate_agent_monitoring.py

## Assumptions / Open Questions
- BLOCKED until TCK-20260713-MONITORING-SQLITE-INDEX ships and its schema is stable — implementation cannot start before then
- Whether tests land before the migration (two sequenced diffs) or in the same diff is an open sequencing question to resolve during Scope/Plan; the idea doc leans toward sequencing as lower-risk
- The index's normalization must cover all 5+ historical runs.jsonl schema generations documented in docs/agent-monitoring/schema.md, or query.py's --status filter may silently diverge from the legacy in-memory scan's behavior on old records

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
