---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260721-MONITORING-WRITER-UNIFICATION
phase: open
date: 2026-07-21
tags: []
---

# TCK-20260721-MONITORING-WRITER-UNIFICATION

## Title
Linux common monitoring writer plus additive reader/query/dashboard support

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Extract one shared Linux-only append-only writer (lock-file protocol, bounded retry, stale-lock recovery, malformed-line handling) that Claude and Codex both route new writes through only once stress/crash/concurrent-writer tests pass; add new fields additively while keeping every legacy record shape readable; update validation, query, retro generation, the monitoring index, and dashboard ingestion to group/filter by provider and execution identity while clearly labeling legacy-unknown records; writer failures stay non-blocking but observable. This matters because CLAUDE.md's hard rule requires every implement-ticket run to record a run+event entry with monitoring write failure never blocking the workflow, and the current writer logic is duplicated ad hoc across three call sites.

## Scope
- Extract one shared Linux-only append-only writer module (O_CREAT|O_EXCL lock-file protocol, bounded retry, stale-lock recovery, malformed-line handling) used by post_tool_hook.py, record_run.py, and record_events.py — replacing 3 separate ad hoc implementations
- Promote tests/tools/test_monitoring_writer_lockfile_candidate.py's 3 tests to production coverage plus a concurrency+crash-recovery stress test (0 corrupted/interleaved/lost lines) and a simulated stale-lock recovery scenario
- Add new fields (execution_id, provider) additively to new records using the already-decided execution_id format (f"{provider}-{ticket_id}-{unix_ts_ms}-{secrets.token_hex(4)}"), while every legacy record shape (5+ generations) remains readable via load_jsonl
- Update validate.py, query.py, generate_retro.py, and src/api/agent_ops_dashboard/ingest.py to group/filter by provider and execution_id, and to visibly label legacy/unknown records rather than dropping them
- Add test coverage for query.py (currently zero coverage)
- Ensure writer failures remain non-blocking to the calling workflow but become observable (e.g. a writer health/error event or log surface)

## Out of Scope
- Does not modify, own, or duplicate work belonging to the still-open TCK-20260713-MONITORING-SQLITE-INDEX ticket batch (the derived SQLite monitoring index) — "the monitoring index" in this ticket's scope refers only to updates needed for provider/execution_id-aware querying of the existing JSONL files, not the SQLite index itself
- Does not enable any non-Linux (Windows/macOS) writer path — Linux-only per decision, other platforms remain BLOCKED
- Does not touch or rewrite historical pre-existing JSONL records (append-only, additive-fields-on-new-records only)

## Acceptance Criteria
- [ ] A single shared Linux-only append writer module (O_CREAT|O_EXCL lock-file, bounded retry, stale-lock recovery) is used by post_tool_hook.py AND record_run.py/record_events.py — not 3 separate ad hoc implementations (verified by code inspection/import graph)
- [ ] Concurrency+crash-recovery stress test (promoted from test_monitoring_writer_lockfile_candidate.py) shows 0 corrupted/interleaved/lost lines across concurrent writers
- [ ] A simulated stale-lock recovery scenario test passes (writer recovers from an abandoned lock file)
- [ ] New records carry additive execution_id + provider fields; every legacy record shape (all 5+ documented generations) still loads successfully via load_jsonl with zero exceptions
- [ ] query.py, validate.py, generate_retro.py, and dashboard ingest.py can each group/filter results by provider and execution_id
- [ ] Records missing provider/execution_id fields are visibly labeled as legacy/unknown in query/validate/retro/dashboard output rather than being silently dropped or erroring
- [ ] Writer failures do not raise/propagate to fail the calling workflow (non-blocking), and are recorded as an observable event/log entry
- [ ] This ticket's scope is explicitly disambiguated from TCK-20260713-MONITORING-SQLITE-INDEX: no changes are made to the SQLite index schema or its derived-index build process

## Related Tickets
- TCK-20260721-MONITORING-WRITER-DECISION
- TCK-20260721-ORCHESTRATION-CONTRACT-ADR
- TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK
- TCK-20260719-LIVE-PHASE-AGENT-LABEL
- TCK-20260719-COST-PROXY-WRITE-PATH
- TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT
- TCK-20260607-MON-SCHEMA
- TCK-20260713-MONITORING-SQLITE-INDEX

## Related Docs
- docs/ai/monitoring_writer_decision.md
- docs/agent-monitoring/schema.md
- docs/architecture/agent_orchestration_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/post_tool_hook.py
- tools/agent-monitoring/record_run.py
- tools/agent-monitoring/record_events.py
- tools/agent-monitoring/validate.py
- tools/agent-monitoring/query.py
- tools/agent-monitoring/generate_retro.py
- tools/agent-monitoring/vocabulary.py
- tests/tools/test_monitoring_writer_lockfile_candidate.py
- tests/tools/test_post_tool_hook.py
- tests/tools/test_record_run.py
- tests/tools/test_record_events.py
- tests/tools/test_validate_agent_monitoring.py
- tests/tools/test_generate_retro.py
- docs/ai/monitoring_writer_decision.md
- docs/agent-monitoring/schema.md
- docs/architecture/agent_orchestration_contract.md
- src/api/agent_ops_dashboard/ingest.py
- tickets/todos/agent-monitoring-derived-index/TCK-20260713-MONITORING-SQLITE-INDEX.md

## Assumptions / Open Questions
- "Two-writer" concurrency evidence in this ticket is necessarily simulated/synthetic since no real second-provider (Codex) writer exists yet (that lands via the Codex replay/pilot tickets)
- No "writer health/error event" concept exists anywhere today — its schema/shape is new design work for this ticket's Plan phase
- This concern is explicitly confirmed authorized to modify production writer/reader files (post_tool_hook.py, record_run.py, record_events.py, validate.py, query.py, generate_retro.py) — not containment-locked like the discovery epic

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
