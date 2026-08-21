---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT
phase: open
date: 2026-08-21
tags: [api-design, content]
---

# TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT

## Title
Add GET /api/v1/manifest endpoint for ID-to-meaning lookups

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The frontend currently hardcodes its own independent copy of what terrain/entity/building/location IDs mean (colors.ts), which is architecturally backwards for a project that otherwise treats registries as the source of truth. The author wants a small GET /api/v1/manifest endpoint (backend + useSimulation.ts only) returning a versioned ID-to-meaning lookup table, fetched once alongside the static call. Retiring the frontend's hardcoded color maps to actually consume it is explicitly left for a fast-follow, not this item.

## Scope
- Add GET /api/v1/manifest backend route returning terrain_types/entity_kinds/building_types populated live from CatalogRepository.terrain/.entity_archetypes/.buildings (id->display_name), shaped as plain dicts, never raw catalog objects
- Wire CatalogRepository into the FastAPI DI graph (new plumbing -- no existing route does this today)
- Return separate protocol_version and dictionary_version fields (dictionary_version derived from CatalogRepository._compute_fingerprint(), protocol_version stays fixed across dictionary-only changes)
- Fetch /manifest exactly once in useSimulation.ts's loadInitial(), joined into the existing Promise.all alongside /static -- not the 500ms fallback poll loop
- Resolve where location_types meaning comes from, given no LocationDefinition/CatalogRepository.locations registry exists today (its only current source is GameCanvas.tsx's LOCATION_TYPE_ICONS, out of this ticket's file boundary) -- decide new minimal registry entry vs. explicitly dropping the field, document the decision
- Align terrain_types id-space with whatever the present_map RLE encoding settles on (int ordinal vs string)

## Out of Scope
- frontend/src/constants/colors.ts -- not modified (retiring the hardcoded color maps to consume the manifest is an explicit fast-follow, not this ticket)
- frontend/src/components/GameCanvas.tsx -- not modified
- Building any new location-type registry beyond the minimal decision documented above, if dropping the field is chosen instead

## Acceptance Criteria
- [ ] GET /api/v1/manifest returns 200 with SEPARATE protocol_version and dictionary_version fields (not one combined schema_version)
- [ ] terrain_types/entity_kinds/building_types populated LIVE from CatalogRepository.terrain/.entity_archetypes/.buildings (id->display_name or id), not hardcoded literals duplicating colors.ts
- [ ] dictionary_version changes when catalog content changes (derived from CatalogRepository._compute_fingerprint()) while protocol_version stays fixed across a dictionary-only change
- [ ] useSimulation.ts fetches /manifest exactly once, joined into loadInitial()'s existing Promise.all alongside /static, NOT the 500ms poll loop
- [ ] terrain_types id-space matches whatever id scheme present_map's grid encoding uses
- [ ] location_types' data source (new minimal registry vs. explicit field drop) is documented as an explicit decision, not left implicit

## Related Tickets
- TCK-20260821-PRESENT-MAP-STATIC
- TCK-20260821-EPIC-LIVE-MAP-RECONNECTION

## Related Docs
- docs/plans/live_map_reconnection_epic.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/api/server.py
- src/content/repository.py
- src/content/schema.py
- frontend/src/hooks/useSimulation.ts
- frontend/src/constants/colors.ts
- frontend/src/components/GameCanvas.tsx
- tests/api/test_rest_parity.py
- src/api/presenters/state_presenter.py

## Assumptions / Open Questions
- location_types has no backend registry today at all; resolution approach (new registry vs drop) is left to implementation-time decision within the documented options
- terrain id-space alignment depends on which choice the present_map ticket actually makes for its grid encoding, not fully known until that ticket lands
- No "api" layer is registered in registries/layer_registry.jsonl; assigned layer `world` since this endpoint's content (terrain/entity/building type dictionaries) is sourced from CatalogRepository's world-content registries, closest existing match to an API-surface-over-content-registries ticket

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
