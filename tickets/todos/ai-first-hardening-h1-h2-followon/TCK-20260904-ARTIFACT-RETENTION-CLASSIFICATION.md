---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION
phase: open
date: 2026-09-04
tags: [ai, agent-monitoring, data-quality, documentation]
---

# TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION

## Title
Classify retention treatment for repo artifact classes outside monitoring shards

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
The already-shipped TCK-20260902/903-MONITORING-* epics cover only runs/events/tools.jsonl, leaving stored_artifacts/, tickets/done/, working_log.csv, graphify-out/, and knowledge-index/ unclassified for retention. This ticket classifies every artifact class using the 4-category taxonomy (Ephemeral/Run-scoped/Ticket-scoped/Long-lived-Institutional) in a committed doc. The source concern posed graphify-out/ and knowledge-index/ as 2 open questions to resolve with evidence or explicitly defer — investigation found both are in fact resolvable now with concrete evidence already on hand (gitignore lines, zero CI references, zero tracked files, existing documentation and rebuild automation for each), so this ticket resolves them directly rather than leaving them open.

## Scope
- Create a new committed doc with a retention-classification table covering all 8 artifact classes: agent-monitoring/data/, stored_artifacts/, tickets/done/, retro/RETRO-*.md, working_log.csv, graphify-out/, knowledge-index/, .claude/current_run — each row assigned a category from the 4-way taxonomy plus a recommended treatment
- Resolve the graphify-out/ question with cited evidence (.gitignore lines 260-261, zero .github/workflows/*.yml references, zero git-tracked files, tests/tools/test_code_health_impact.py's documentation, prior TCK-20260818-HOTFIX-GRAPHIFY-CLI-TEST-MISSING-INDEX-SKIP finding) and a resolved recommendation
- Resolve the knowledge-index/ question with cited evidence (.gitignore line 264, Makefile:331's 'developer env only — not CI' comment, docs/guidelines/agent_working_environment.md's existing table, tools/hooks/post-commit-reindex.sh) and a resolved recommendation
- Decide the new doc's location/filename during Plan (e.g. docs/observability/ or docs/guidelines/) — not specified in the source material
- Reference this batch's TCK-20260904-WORKING-LOG-CSV-PARSER by ID for working_log.csv's row rather than duplicating or blocking on it

## Out of Scope
- Actually implementing the working_log.csv parser/cleanup fix — tracked separately
- M3's ownership/lifecycle documentation deliverable — separate milestone with its own ticket, do not conflate despite sharing a References/Out-of-Scope boundary in the source epic doc
- Rewriting docs/guidelines/agent_working_environment.md's existing table to add a missing graphify-out/ row unless the implementer chooses to do so in this ticket; if deferred, must be flagged explicitly as a named follow-up rather than silently left

## Acceptance Criteria
- [ ] New committed doc contains a retention-classification table covering all 8 artifact classes (agent-monitoring/data/, stored_artifacts/, tickets/done/, retro/RETRO-*.md, working_log.csv, graphify-out/, knowledge-index/, .claude/current_run), each with a category from the 4-way taxonomy and a recommended treatment
- [ ] graphify-out/ row cites concrete evidence (gitignore line, zero CI references, zero tracked files) and a resolved recommendation
- [ ] knowledge-index/ row cites concrete evidence (gitignore line, Makefile comment, existing rebuild automation) and a resolved recommendation
- [ ] If either question is left unresolved instead of resolved, the doc names a specific follow-up owner/role and trigger

## Related Tickets
- TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC
- TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC
- TCK-20260818-HOTFIX-GRAPHIFY-CLI-TEST-MISSING-INDEX-SKIP
- TCK-20260816-HOTFIX-KGMCP-LOCAL-DATA-BOOTSTRAP-DOCS

## Related Docs
- docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md
- docs/guidelines/agent_working_environment.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md
- docs/guidelines/agent_working_environment.md
- .gitignore
- Makefile
- tools/hooks/post-commit-reindex.sh
- tests/tools/test_code_health_impact.py
- tickets/done/agent-monitoring-weekly-sharding/TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC.md
- tickets/done/agent-monitoring-unified-weekly-data/TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC.md
- tickets/done/TCK-20260818-HOTFIX-GRAPHIFY-CLI-TEST-MISSING-INDEX-SKIP.md

## Assumptions / Open Questions
- The new doc's exact location/filename is undecided and must be chosen during Plan
- working_log.csv's row should reference TCK-20260904-WORKING-LOG-CSV-PARSER by ID rather than duplicate or gate on it, since this ticket is itself gated on nothing
- M3 (ownership/lifecycle doc) is a separate milestone that shares a References/Out-of-Scope boundary with this ticket in the source epic doc — must not be conflated

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
