---
status: done
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260618-AUDIT-D16-DX
phase: open
date: 2026-06-18
tags: [audit, dx, scenario-authoring, content-authoring, developer-experience]
---

# TCK-20260618-AUDIT-D16-DX

## Title
D16 — Scenario & Content Authoring DX Audit

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Assess the developer experience for adding new simulation scenarios and world modules.
How many files must change? How discoverable is the process? How quickly do errors surface?

## Scope
- Survey the authoring surface for world modules, world compositions, simulation scenarios
- Identify documentation gaps for content authors
- Assess validation tooling (make targets, Pydantic schema, ContentUsageMatrix)
- Score authoring tasks by DX gap

## Out of Scope
- Implementation changes
- Runtime content loading performance

## Acceptance Criteria
- `docs/audits/D16_scenario_authoring_dx.md` written with scoring rubric
- `audit_dimensions.md` D16 row updated to `done`
- Working log and monitoring entries written

## Related Tickets
- TCK-20260618-AUDIT-EPIC (parent)
- TCK-20260618-AUDIT-D10-TESTS (content registry drift finding F6 is related)

## Related Docs
- `docs/world/modules_contract.md`
- `src/scenarios/schema.py`
- `src/scenarios/templates.py`
- `data/content/world_modules/*.yaml`
- `data/content/world_compositions/*.yaml`
- `data/content/simulation_scenarios/*.yaml`

## Related Stored Artifacts
- `staging_artifacts/TCK-20260618-AUDIT-D16/`

## Assumptions / Open Questions
None.

## Implementation Notes
Key findings:
- `make world-validate WORLD=<id>` and `make world-template` exist — good baseline
- No content author guide
- ContentUsageMatrix drift is the highest-friction authoring trap (only caught in CI)
- 8 allowed initial_condition categories only documented in schema.py, not in a guide
- Module schema has sharp edges (observability_tags, no provided_features)

## Test Summary
N/A

## Files Changed
- docs/audits/D16_scenario_authoring_dx.md (create)
- docs/audits/audit_dimensions.md (update)
- tickets/working_log.csv (append)
- agent-monitoring/runs.jsonl + events.jsonl (append)

## Completion Summary
D16 audit complete. 4 authoring tasks scored with 3×5 DX Gap rubric. Highest gap: adding a new content pack (12/15 — ContentUsageMatrix drift, no authoring-time warning). Lowest gap: scaffold via `make world-template` (4/15). Key structural gap: no content author guide. 5 follow-up tickets recommended (2 P1, 3 P2).
