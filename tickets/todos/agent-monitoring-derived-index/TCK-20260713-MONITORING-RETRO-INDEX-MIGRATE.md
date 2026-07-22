---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE
phase: open
date: 2026-07-13
tags: []
---

# TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE

## Title
Migrate generate_retro.py's status/legacy-shape resolution to the SQLite index

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
The author wants generate_retro.py's hand-rolled _resolve_status(), _is_legacy_event(), and _is_gate_fail() helpers — which interpret the same legacy record shapes as the other consumers — to be replaced by querying the centralized normalization the new index's build step performs once, instead of re-deriving it per reader.

## Scope
- Remove the _resolve_status(), _is_legacy_event(), and _is_gate_fail() helpers (currently at lines 71, 82, 90) from tools/agent-monitoring/generate_retro.py
- Replace all 6 call sites inside generate() that invoke these helpers with reads against the new index's centrally-normalized status/legacy columns, migrated together (not partially) since they share one normalization source
- Add direct predicate-level tests covering the migrated status/legacy-event/gate-fail resolution paths, currently untested in isolation
- Retain a safe fallback (build-on-demand, or a clear error) in generate_retro.py if the index has not been built yet, since it must never become a hard gating dependency

## Out of Scope
- Building or modifying tools/agent-monitoring/build_index.py or its schema — that is sibling ticket TCK-20260713-MONITORING-SQLITE-INDEX's responsibility; this ticket is BLOCKED until it ships and its schema is stable
- Migrating query.py (separate ticket TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE)
- validate.py's separately-maintained, conceptually overlapping legacy-shape allowlist (separate ticket TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE)

## Acceptance Criteria
- [ ] _resolve_status(), _is_legacy_event(), and _is_gate_fail() are removed from generate_retro.py and replaced by reads against the new index's centrally-normalized status/legacy columns instead of re-deriving from raw runs.jsonl/events.jsonl per call
- [ ] generate_retro.py's report output (weekly and --all reports) is byte-identical before and after migration when run against the same fixed historical dataset, proving the new index's normalization preserves _resolve_status's documented non-normalizing behavior
- [ ] All 6 call sites inside generate() that currently invoke the three helpers are migrated together, not partially
- [ ] tests/tools/test_generate_retro.py continues to pass unmodified, plus new tests are added that directly cover the migrated status/legacy-event/gate-fail resolution paths

## Related Tickets
- TCK-20260713-MONITORING-SQLITE-INDEX (BLOCKS this ticket — build_index.py must ship first)
- TCK-20260721-MONITORING-WRITER-UNIFICATION (BLOCKS this ticket — added 2026-07-22 per Codex review of the provider-agnostic-implementation batch: this ticket's provider/execution_id-aware read migration depends on that ticket's additive writer schema fields existing first; see tickets/todos/provider-agnostic-implementation/SEQUENCE.md)
- TCK-20260607-MON-RETRO
- TCK-20260705-RETRO-METRIC-ACCURACY
- TCK-20260705-RETRO-INDEX-ALL-ROW
- TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP
- TCK-20260706-MONITORING-REASON-CODE
- TCK-20260708-RETRO-TAG-BREAKDOWN
- TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX
- TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION

## Related Docs
- docs/plans/agent_infrastructure/idea_agent_monitoring_derived_index.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/generate_retro.py
- tools/agent-monitoring/validate.py
- tools/agent-monitoring/query.py
- docs/agent-monitoring/schema.md
- tests/tools/test_generate_retro.py

## Assumptions / Open Questions
- BLOCKED until TCK-20260713-MONITORING-SQLITE-INDEX ships and its schema is stable — implementation cannot start before then
- The new index's normalization must replicate _resolve_status()'s documented non-normalizing semantics (literal status-string spellings stay distinct) or migrating is a silent behavior change potentially requiring a docs/guidelines/intentional_divergences.md entry
- No existing test isolates the 3 helpers directly today; migrating without first adding direct predicate-level tests risks an undetected regression
- Sequencing/consistency between this ticket and the validate.py migration ticket (overlapping legacy-shape allowlist) should be tracked explicitly even though out of scope here

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
