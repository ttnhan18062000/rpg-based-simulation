---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261020-INSPECT-PANEL-READS-A-STATE-SELECTED-SHAPE-THE-BACKEND-DOES-NOT-SERVE
phase: open
date: 2026-10-20
tags: []
---

# TCK-20261020-INSPECT-PANEL-READS-A-STATE-SELECTED-SHAPE-THE-BACKEND-DOES-NOT-SERVE

## Title
The frontend InspectPanel reads selected_entity from /state?selected=, a legacy V1 shape the backend no longer serves; move it to the entity detail and quest history endpoints

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
While building TCK-20261020-ENTITY-LIST-RETURNS-A-BOUNDED-SUMMARY-NOT-THE-FULL-DETAIL (branch rpg-entity-list-summary), Lane B found that `frontend/src/components/InspectPanel.tsx` (the Quests tab) reads `selected_entity` from `/state?selected=`, a legacy V1 shape the current backend does not serve. Nothing in the frontend calls `/api/v1/entities`. So the inspect panel's entity detail is probably empty or stale in the live dashboard.

## Scope
- Confirm what the panel shows today against a live server.
- Move the panel to `GET /api/v1/entities/{id}` (detail) and `GET /api/v1/entities/{id}/quests` (paged history), once that PR lands.
- Add a frontend test that pins the panel's data source.

## Out of Scope
- Backend read-model changes (the entity-list ticket).

## Acceptance Criteria
- The Inspect panel shows live entity detail and quest history from the v1 API, with a test.

## Related Tickets
- TCK-20261020-ENTITY-LIST-RETURNS-A-BOUNDED-SUMMARY-NOT-THE-FULL-DETAIL

## Related Docs
- the read_model_service_contract.md

## Related Stored Artifacts
- none

## Related Code Areas
- frontend/src/components/InspectPanel.tsx
- src/api/routes/entities.py

## Assumptions / Open Questions
- Is the panel already broken in the live dashboard, or does some other path feed it?

## Implementation Notes
After the entity-list PR merges.

## Test Summary

## Files Changed

## Completion Summary
