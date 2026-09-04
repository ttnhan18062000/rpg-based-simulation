---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260904-OWNERSHIP-LIFECYCLE-DOC
phase: open
date: 2026-09-04
tags: [ai, documentation, governance]
---

# TCK-20260904-OWNERSHIP-LIFECYCLE-DOC

## Title
Canonical ownership and lifecycle doc for new subsystems

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
For every remaining subsystem this epic and its Horizon-0/1 siblings touch, the plan calls for recording an accountable role (not a person), update trigger, staleness signal, and removal condition, in one canonical doc referenced from every sibling epic doc rather than duplicated — the draft already has 2 rows (capability-envelope baseline, ticket-claim detection log). Investigation found the epic doc's own citation of "the roadmap's shared role vocabulary" is dangling: roadmap.md contains no such section, and the two roles used were invented ad hoc in the epic doc itself. This ticket must both build the canonical table and fix that dangling citation, plus make an explicit inclusion/exclusion call for the 5+ other new subsystems this batch created that the draft table doesn't yet cover.

## Scope
- Create a single canonical doc with columns Subsystem | Accountable role | Update trigger | Staleness signal | Removal condition
- Include the 2 already-drafted rows (capability-envelope baseline -> Agent Configuration Maintainer; ticket-claim detection log -> Workflow Runtime Maintainer)
- Add an explicit row-or-justified-exclusion decision for each other new/changed subsystem in this batch (bash secret-scan hook, tools frontmatter rollout, AST import-boundary enforcement, doc-coverage reverse-check, test-scoper hang guard), the same way the weekly-shard layout got an explicit exclusion note
- Resolve the dangling "roadmap's shared role vocabulary" citation — either add a real role-vocabulary section (in roadmap.md or a more suitable doc) and reference it correctly, or correct the citation to point at wherever roles are actually defined
- Update the sibling epic docs to link to the canonical doc rather than restating rows
- Give the new doc valid frontmatter (registry-backed layer + tags per CLAUDE.md Ticket Format), confirm it passes tools/validate_frontmatter.py, and confirm it appears in docs/REGISTRY.yaml after regeneration

## Out of Scope
- Reassigning ownership of the agent-monitoring/data/ weekly-shard layout — explicitly excluded in the source epic doc
- Merging or rewriting the 3 existing differently-shaped ownership docs (docs/testing/content_migration_test_ownership.md, docs/simulation/domains/domain_ownership_map.md, docs/architecture/cognition_domain_ownership.md) — cross-link to them for disambiguation only, they serve code/domain ownership, a different purpose than this governance/lifecycle table
- Building or populating M2's artifact-retention classification table content — tracked as a separate ticket

## Acceptance Criteria
- [ ] Single committed doc with columns Subsystem | Accountable role | Update trigger | Staleness signal | Removal condition, covering at minimum the 2 drafted rows plus an explicit row-or-justified-exclusion decision for each other new/changed subsystem in this batch
- [ ] Sibling epic docs link to the canonical table doc rather than restating rows
- [ ] The dangling "roadmap's shared role vocabulary" citation is resolved — either a real section is added and referenced correctly, or the citation is corrected to point at wherever roles are actually defined
- [ ] New doc passes tools/validate_frontmatter.py and appears in docs/REGISTRY.yaml after regeneration

## Related Tickets
- TCK-20260609-TEST-OWNERSHIP-MAP
- TCK-20260612-DOMAINS-ARCH-MAP
- TCK-20260613-DOC-DOMAIN-CONTRACTS

## Related Docs
- docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md
- docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md
- docs/testing/content_migration_test_ownership.md
- docs/simulation/domains/domain_ownership_map.md
- docs/architecture/cognition_domain_ownership.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md
- docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md
- docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md
- docs/plans/agent_infrastructure/ai_first_hardening_epics/workflow_reliability_epic.md
- docs/plans/agent_infrastructure/ai_first_hardening_epics/guardrail_enforcement_epic.md
- docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md
- docs/testing/content_migration_test_ownership.md
- docs/simulation/domains/domain_ownership_map.md
- docs/architecture/cognition_domain_ownership.md
- registries/tag_registry.jsonl

## Assumptions / Open Questions
- Scope of "remaining subsystems" beyond the 2 drafted rows is ambiguous in the source doc — this ticket must make and justify the inclusion/exclusion call explicitly, not leave it implicit
- The dangling role-vocabulary citation is a genuine gap, not a formatting nit, and must be fixed rather than left as-is
- The new doc's file placement (docs/plans/... is planning-stage/not-yet-ticketed; repo convention for permanent governance docs favors docs/ai/ or docs/guidelines/) needs an explicit decision during Plan
- Whether M2's own artifact-retention-classification output should get a row in this table is unaddressed in the source doc and should be decided during Plan
- `layer: observability` was chosen because this doc governs cross-subsystem staleness/removal signals (an observability concern) rather than any single subsystem; no more specific registered layer fit better — flagged here per CLAUDE.md's Ticket Format guidance

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
