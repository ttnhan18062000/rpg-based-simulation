---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE
phase: open
date: 2026-07-13
tags: []
---

# TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE

## Title
Migrate validate.py's drift-report logic to the SQLite index

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
The author wants validate.py's compute_drift_report() and compute_tool_count_drift_report() functions — which currently hand-roll their own LEGACY_COMPLETION_FIELDS/LEGACY_TERMINAL_STATUS_VALUES allowlists and re-derive groupings by hand — to be migrated to query the shared normalized index instead, consolidating logic that is currently duplicated separately from generate_retro.py's equivalent handling.

## Scope
- Migrate compute_drift_report() and compute_tool_count_drift_report() in tools/agent-monitoring/validate.py to query the shared normalized index (built by build_index.py) instead of hand-rolling LEGACY_COMPLETION_FIELDS/LEGACY_TERMINAL_STATUS_VALUES groupings from raw runs/events lists
- Remove or reduce the LEGACY_COMPLETION_FIELDS and LEGACY_TERMINAL_STATUS_VALUES allowlists in validate.py to a single reference to the index's shared normalization, eliminating duplication with generate_retro.py's equivalent helpers
- Preserve validate.py's read-only, non-gating exit-code contract through the migration

## Out of Scope
- Building or modifying tools/agent-monitoring/build_index.py or its schema — that is sibling ticket TCK-20260713-MONITORING-SQLITE-INDEX's responsibility; this ticket is BLOCKED until it ships and its schema is stable
- Migrating query.py (separate ticket TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE)
- Migrating generate_retro.py's own independent legacy-shape handling (separate ticket TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE)

## Acceptance Criteria
- [ ] compute_drift_report() and compute_tool_count_drift_report() query the shared normalized index instead of directly re-deriving LEGACY_COMPLETION_FIELDS/LEGACY_TERMINAL_STATUS_VALUES groupings from raw runs/events lists
- [ ] All 13 existing tests in tests/tools/test_validate_agent_monitoring.py continue to pass unmodified in behavior (same report string output for the same fixture input), proving the migration is output-preserving
- [ ] The LEGACY_COMPLETION_FIELDS and LEGACY_TERMINAL_STATUS_VALUES allowlists in validate.py are either removed entirely or reduced to a single reference to the index's shared normalization
- [ ] validate.py's exit-code contract is unchanged: compute_drift_report/compute_tool_count_drift_report remain purely additive/read-only, and read-only-style assertions still hold when reading from the index

## Related Tickets
- TCK-20260713-MONITORING-SQLITE-INDEX (BLOCKS this ticket — build_index.py must ship first)
- TCK-20260705-MONITORING-RUNID-JOIN
- TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT
- TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION
- TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP

## Related Docs
- docs/plans/agent_infrastructure/idea_agent_monitoring_derived_index.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/validate.py
- tools/agent-monitoring/generate_retro.py
- tools/agent-monitoring/vocabulary.py
- tests/tools/test_validate_agent_monitoring.py
- docs/agent-monitoring/schema.md

## Assumptions / Open Questions
- BLOCKED until TCK-20260713-MONITORING-SQLITE-INDEX ships and its schema is stable — implementation cannot start before then
- The exact index schema/API is undecided per the idea doc's Open Questions; this ticket may need to confirm the sibling ticket's index shape before implementation
- The index's normalization must reproduce validate.py's exact legacy-shape handling or risk silently regressing already-fixed false positives from prior hardening tickets

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
