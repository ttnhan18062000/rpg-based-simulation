---
status: historical
layer: api
authority: P1
audience: agent
ticket_id: TCK-20261014-THE-LIVE-MAP-SHOWS-PLACES-AND-REGION-IDS-THROUGH-A-PRESENTER-D69
phase: done
date: 2026-10-14
tags: []
---

# TCK-20261014-THE-LIVE-MAP-SHOWS-PLACES-AND-REGION-IDS-THROUGH-A-PRESENTER-D69

## Title
The live map shows the world's places (towns, dens, named sites) and real region ids, through a presenter read-model.

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
StatePresenter.present_static returns locations: [] for every region, with region ids as None, while the spec authors places. Owner ruling D69: places appear, as a presenter read-model, never as raw domain objects.

## Scope
- A typed read-model per place: name, kind, tiles, owner and region. Region ids come through.
- The frontend draws places and labels them.
- Tests:
  - a presenter test that the read-model matches the compiled world's places for at least two worlds;
  - an API schema test;
  - no raw domain object is exposed (api read-model guard).

## Out of Scope
- The tile-colour fix, which has its own branch.
- Asset-domain scene copies.

## Acceptance Criteria
- Places and region ids reach /api/v1/static and the map.
- The api read-model guard stays kept.

## Related Tickets
TCK-20261011-LIVE-MAP-COLOURS-TERRAIN-BY-A-FIXED-CODE-TABLE-THE-API-DOES-NOT-USE.

## Related Docs
docs/audits/D28_live_map_functional_correctness.md; designer memo row 69.

## Related Stored Artifacts
None.

## Related Code Areas
src/api/presenters/state_presenter.py; src/api/routes; frontend map layer.

## Assumptions / Open Questions
Correction to the ticket text: region ids were already served (the static region key is region_id, which my first probe read as id); the empty part was locations. A place has no display name of its own yet, so the name is the place id read as words.

## Implementation Notes
src/api/schemas.py: typed PlaceReadModel and PlaceTiles. StatePresenter.present_place builds one place (owner = its own override else its region's holder; tiles = footprint or the one tile); present_static fills each region's locations from the compiled places (it was an empty list). Frontend: lib/placeMarks.ts outlines each place over its tiles and labels it on the map layer (useCanvas, from the regions' locations), Location gains owner and tiles, the locations panel gains the place types.

## Test Summary
tests/api/test_live_map_places_through_a_presenter.py (7): the read-model matches the compiled places for sandbox_world and frontier_living_world, region ids come through, plain values only (no raw domain object), owner and tiles rules, the static route serves them. frontend placeMarks.test.ts (4); full vitest 369 passed, tsc clean. tests/unit/api, tests/api and tests/architecture pass except the known pre-existing failures: test_metadata_api.py::test_resources_real_fields_from_catalog and tests/architecture/test_phase18_import_boundaries.py (starvation_record.py imports src.engine.cadence), both failing on the base.

## Files Changed
src/api/schemas.py; src/api/presenters/state_presenter.py; frontend/src/lib/placeMarks.ts; frontend/src/hooks/useCanvas.ts; frontend/src/components/GameCanvas.tsx; frontend/src/types/api.ts; tests as above.

## Completion Summary
Done: the live map shows places through a typed presenter read-model.
