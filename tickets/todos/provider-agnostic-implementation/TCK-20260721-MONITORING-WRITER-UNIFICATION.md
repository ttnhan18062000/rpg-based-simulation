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
Extract one shared Linux-only append-only writer (lock-file protocol, bounded retry, stale-lock recovery, malformed-line handling) that Claude and Codex both route new writes through only once stress/crash/concurrent-writer tests pass; add new fields additively while keeping every legacy record shape readable; update dashboard ingestion to group/filter by provider and execution identity while clearly labeling legacy-unknown records; writer failures stay non-blocking but observable via an out-of-band diagnostic surface. This matters because CLAUDE.md's hard rule requires every implement-ticket run to record a run+event entry with monitoring write failure never blocking the workflow, and the current writer logic is duplicated ad hoc across three call sites.

**Corrected per Codex review (2026-07-22):** this ticket's scope was narrowed to remove `query.py`/`validate.py`/`generate_retro.py` migration work, which belongs to the separate, already-scoped `tickets/todos/agent-monitoring-derived-index/` batch (see Related Tickets) — that batch now depends on this ticket landing first. This ticket also now has an explicit intra-batch dependency on `TCK-20260721-BASELINE-MONITORING-MANIFEST`.

## Scope
- **Entry criterion: consume the read-only baseline manifest produced by `TCK-20260721-BASELINE-MONITORING-MANIFEST`** before any writer change — this ticket's data-preservation claim must be checked against that manifest, not asserted from a clean-tree assumption
- Extract one shared Linux-only append-only writer module (O_CREAT|O_EXCL lock-file protocol, bounded retry, stale-lock recovery, malformed-line handling) used by post_tool_hook.py, record_run.py, and record_events.py — replacing 3 separate ad hoc implementations
- Promote tests/tools/test_monitoring_writer_lockfile_candidate.py's 3 tests to production coverage plus a concurrency+crash-recovery stress test (0 corrupted/interleaved/lost lines) and a simulated stale-lock recovery scenario
- Add new fields (execution_id, provider) additively to new records using the already-decided execution_id format (f"{provider}-{ticket_id}-{unix_ts_ms}-{secrets.token_hex(4)}"), while every legacy record shape (5+ generations) remains readable via load_jsonl
- Update src/api/agent_ops_dashboard/ingest.py to group/filter by provider and execution_id, and to visibly label legacy/unknown records rather than dropping them
- Ensure writer failures remain non-blocking to the calling workflow but become observable via an **out-of-band** diagnostic surface (e.g. structured stderr output or a local diagnostic/health file written outside the writer's own append path) — never by attempting to emit a "writer health event" through the same writer that just failed, which would either recurse or silently lose the diagnostic
- **Exit criterion: re-run the baseline manifest against the post-migration corpus and diff against the entry-criterion manifest** — the only allowed differences are explicitly identified new append records; any other change (rewrite, reorder, deletion) fails this ticket's own DoD

## Out of Scope
- Does not implement `query.py`, `validate.py`, or `generate_retro.py` migration to provider/execution_id-aware reads — that is owned by `tickets/todos/agent-monitoring-derived-index/TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE.md`, `TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE.md`, and `TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE.md`, which depend on this ticket in turn (their own `SEQUENCE.md` was updated in the same review-correction pass to record this cross-batch dependency)
- Does not modify, own, or duplicate the SQLite index schema or build process owned by `TCK-20260713-MONITORING-SQLITE-INDEX`
- Does not enable any non-Linux (Windows/macOS) writer path — Linux-only per decision, other platforms remain BLOCKED
- Does not touch or rewrite historical pre-existing JSONL records (append-only, additive-fields-on-new-records only)
- Does not begin before `TCK-20260721-BASELINE-MONITORING-MANIFEST` has landed and its manifest tooling is available to consume

## Acceptance Criteria
- [ ] This ticket's entry criterion is satisfied only once `TCK-20260721-BASELINE-MONITORING-MANIFEST`'s manifest tool exists and has been run against the pre-migration corpus to produce a baseline
- [ ] A single shared Linux-only append writer module (O_CREAT|O_EXCL lock-file, bounded retry, stale-lock recovery) is used by post_tool_hook.py AND record_run.py/record_events.py — not 3 separate ad hoc implementations (verified by code inspection/import graph)
- [ ] Concurrency+crash-recovery stress test (promoted from test_monitoring_writer_lockfile_candidate.py) shows 0 corrupted/interleaved/lost lines across concurrent writers
- [ ] A simulated stale-lock recovery scenario test passes (writer recovers from an abandoned lock file)
- [ ] New records carry additive execution_id + provider fields; every legacy record shape (all 5+ documented generations) still loads successfully via load_jsonl with zero exceptions
- [ ] dashboard ingest.py can group/filter results by provider and execution_id, visibly labeling records missing those fields as legacy/unknown rather than silently dropping or erroring on them
- [ ] Writer failures do not raise/propagate to fail the calling workflow (non-blocking), and are recorded via an out-of-band diagnostic surface (structured stderr or a separate local health file) — not by routing a "health event" back through the writer itself
- [ ] Exit criterion: re-running the baseline manifest tool against the post-migration corpus and diffing against the entry-criterion manifest shows only explicitly identified new append records — zero rewrites, reorders, or deletions of pre-existing lines
- [ ] This ticket's scope is explicitly disambiguated from TCK-20260713-MONITORING-SQLITE-INDEX and its 3 reader-migration sub-tickets: no changes are made to the SQLite index schema, its build process, or to query.py/validate.py/generate_retro.py themselves — those tickets consume this ticket's new fields, they are not implemented here

## Related Tickets
- TCK-20260721-MONITORING-WRITER-DECISION
- TCK-20260721-ORCHESTRATION-CONTRACT-ADR
- TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK
- TCK-20260719-LIVE-PHASE-AGENT-LABEL
- TCK-20260719-COST-PROXY-WRITE-PATH
- TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT
- TCK-20260607-MON-SCHEMA
- TCK-20260721-BASELINE-MONITORING-MANIFEST (hard predecessor — this ticket's entry/exit criteria consume its manifest tool)
- TCK-20260713-MONITORING-SQLITE-INDEX (dependent — its 3 sub-tickets below now depend on this ticket, not the reverse)
- tickets/todos/agent-monitoring-derived-index/TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE.md (dependent)
- tickets/todos/agent-monitoring-derived-index/TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE.md (dependent)
- tickets/todos/agent-monitoring-derived-index/TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE.md (dependent)

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
- tools/agent-monitoring/vocabulary.py
- tests/tools/test_monitoring_writer_lockfile_candidate.py
- tests/tools/test_post_tool_hook.py
- tests/tools/test_record_run.py
- tests/tools/test_record_events.py
- docs/ai/monitoring_writer_decision.md
- docs/agent-monitoring/schema.md
- docs/architecture/agent_orchestration_contract.md
- src/api/agent_ops_dashboard/ingest.py
- tickets/todos/agent-monitoring-derived-index/ (dependent batch — not modified by this ticket)

## Assumptions / Open Questions
- "Two-writer" concurrency evidence in this ticket is necessarily simulated/synthetic since no real second-provider (Codex) writer exists yet (that lands via the Codex replay/pilot tickets)
- The out-of-band writer-failure diagnostic surface (structured stderr vs. a separate local health file) is new design work for this ticket's Plan phase to choose — it must not route through the writer's own append path
- This concern is explicitly confirmed authorized to modify production writer files (post_tool_hook.py, record_run.py, record_events.py) — not containment-locked like the discovery epic. It is NOT authorized to modify query.py, validate.py, or generate_retro.py — that ownership moved to the agent-monitoring-derived-index batch's sub-tickets per Codex's 2026-07-22 review correction.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
