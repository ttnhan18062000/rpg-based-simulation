---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260618-AUDIT-D07-CONTENT
phase: done
date: 2026-06-18
tags: [audit, content-depth, variety, quests, factions, modules, archetypes]
---

# TCK-20260618-AUDIT-D07-CONTENT

## Title
D07 — Content Depth & Variety Audit

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Count and assess authored content across all catalog categories. Identify which content
types are sufficiently populated, which are thin, and which represent critical gaps for
producing interesting simulation runs.

## Scope
- Count all catalog entries by category
- Assess world modules, entity archetypes, quests, factions, scenarios, recipes
- Score each gap by RPG simulation impact

## Out of Scope
- Content quality / narrative coherence (requires run-sim)
- Procedurally generated content

## Acceptance Criteria
- `docs/audits/D07_content_depth.md` written with scoring rubric
- `audit_dimensions.md` D07 row updated to `done`
- Working log and monitoring entries written

## Related Tickets
- TCK-20260618-AUDIT-EPIC (parent)
- TCK-20260618-AUDIT-D01-RPG-IMPACT (quests noted as missing Tier-1 system)

## Related Stored Artifacts
- `staging_artifacts/TCK-20260618-AUDIT-D07/`

## Assumptions / Open Questions
- Count excludes procedurally generated content (data/content/world_compositions/generated/)

## Implementation Notes
Key counts from scan:
- 430 total catalog entries (35 files)
- 14 world modules (6 conflict, 3 ecology, 2 danger_zone, 2 settlement, 1 economy; 0 terrain, 0 population type)
- 4 quest definitions (only 3 of 14 modules have quests)
- 21 entity archetypes (4 scouts, 2 raiders, 2 leaders — rest unique)
- 16 factions, 14 faction relationships
- 8 crafting recipes
- 8 simulation scenarios (1 file)
- 5 world compositions

## Test Summary
N/A

## Files Changed
- docs/audits/D07_content_depth.md (create)
- docs/audits/audit_dimensions.md (update)
- tickets/working_log.csv (append)
- agent-monitoring/runs.jsonl + events.jsonl (append)

## Completion Summary
D07 audit complete. 430 catalog entries counted across 35 files. Critical gap: 4 quest definitions (15/15, P0) — only 3 of 14 modules have quests. Secondary gaps: 0 terrain/population module types (10/15), 8 crafting recipes for 34 items (10/15), 3 of 5 world compositions have zero scenarios. Foundation layer (traits, themes, profiles) is mature. 7 follow-up tickets recommended (1 P0, 3 P1, 3 P2).
