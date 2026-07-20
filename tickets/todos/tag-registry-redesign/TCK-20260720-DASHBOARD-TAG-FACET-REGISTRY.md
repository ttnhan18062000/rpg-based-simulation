---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260720-DASHBOARD-TAG-FACET-REGISTRY
phase: open
date: 2026-07-20
tags: [dashboard, observability, api-design]
---

# TCK-20260720-DASHBOARD-TAG-FACET-REGISTRY

## Title
Make the Agent Ops Dashboard tags facet registry-derived instead of corpus-derived

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
src/api/agent_ops_dashboard/ingest.py currently derives its tags filter facet only from tags actually present on tickets in the filtered corpus, unlike tier/layer/status/priority, which already became fully canonical fixed lists sourced from their registries in TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL. Change the tags facet to read registries/tag_registry.jsonl directly so every registered tag is a selectable filter option regardless of whether any ticket currently uses it.

## Scope
- Change ingest.py's tags facet to read registries/tag_registry.jsonl via tag_registry.load_registry(), mirroring the existing layer_registry.load_registry() pattern already used for get_glossary()
- Rewrite ingest.py's stale comment rationale (around lines 598-604) describing tags as open-vocabulary/corpus-derived to reflect the new registry-backed model
- Update docs/parity_ledger/infrastructure.yaml's INFRA-275 entry in the same session
- Update docs/guides/agent_ops_dashboard.md and docs/observability/agent_ops_dashboard_contract.md's descriptions of the Tickets view's tags filter to describe the registry-derived (not corpus-derived) behavior

## Out of Scope
- TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX (separate, already-filed hotfix — not duplicated or absorbed by this batch)
- Frontend changes to TicketsView.tsx — MAX_VISIBLE_TAGS(40)/search-narrowing already exists and is tested against larger synthetic counts; verify live rather than assume, but no change is expected

## Acceptance Criteria
- [ ] get_tickets()'s facets['tags'] equals sorted(tag_registry.load_registry(repo_root).keys()) regardless of which tags appear in the filtered/paginated corpus — a registered tag with zero current tickets still appears
- [ ] facets['tags'] is unaffected by active tier/layer/status/priority/tags query filters (mirrors the existing canonical-facet test pattern)
- [ ] ingest.py imports tag_registry via the same module-level cross-package pattern already used for layer_registry (confirmed at line 51's get_glossary() call) — not a new bespoke import mechanism
- [ ] docs/parity_ledger/infrastructure.yaml's INFRA-275 entry (which currently documents facets['tags'] as "the one facet that remains corpus-derived") is updated in the same session
- [ ] The semantic behavior change — legacy/pre-taxonomy free-text tags present on tickets but absent from tag_registry.jsonl will disappear from the filter facet, and open-ended phase-N tags won't appear in a pure registry-keys facet — is stated as a deliberate, explicitly recorded decision in this ticket, not a silent regression
- [ ] docs/guides/agent_ops_dashboard.md and docs/observability/agent_ops_dashboard_contract.md describe the tags filter as registry-derived, matching how those docs already describe tier/layer/status/priority since TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL

## Related Tickets
- TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL
- TCK-20260718-STATUS-FACET-CANONICAL
- TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM
- TCK-20260706-TAG-REGISTRY-DATA
- TCK-20260719-TAG-COLLISION-DEDUP
- TCK-20260720-TAG-REGISTRY-RELOCATE

## Related Docs
- docs/parity_ledger/infrastructure.yaml
- docs/guidelines/tag_registry.jsonl
- docs/guides/agent_ops_dashboard.md
- docs/observability/agent_ops_dashboard_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/api/agent_ops_dashboard/ingest.py
- tools/ticket_field_values.py
- tools/tag_registry.py
- tools/layer_registry.py
- dashboard-frontend/src/views/TicketsView.tsx
- dashboard-frontend/src/test/TicketsView.test.tsx
- tests/tools/test_agent_ops_dashboard_ingest.py

## Assumptions / Open Questions
- tag_registry.load_registry() raises ValueError on a duplicate JSONL line — the existing get_glossary() layer_registry call has no try/except for this, so this mirrors existing precedent, but get_tickets() is a hotter path and this should be confirmed acceptable
- Facet option count grows from corpus-subset to the full ~52 registered tags — TicketsView.tsx's existing tests already tolerate larger synthetic counts, but this should be verified live rather than assumed
- Phase-N tags won't appear in a pure registry-keys facet — likely fine since they're not typically filter-browsed, but this should be an explicit scope note

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
