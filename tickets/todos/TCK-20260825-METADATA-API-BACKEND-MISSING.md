---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260825-METADATA-API-BACKEND-MISSING
phase: open
date: 2026-08-25
tags: [hud, content]
---

# TCK-20260825-METADATA-API-BACKEND-MISSING

## Title
Build the real `/api/v1/metadata/*` backend -- 8 routes the frontend has called since the initial
import, none of which exist

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`frontend/src/contexts/MetadataContext.tsx` (present since the repo's initial import, predating the
ticket-based workflow) calls 8 endpoints under `/api/v1/metadata/`: `/enums`, `/items`, `/classes`,
`/traits`, `/attributes`, `/buildings`, `/resources`, `/recipes`. None of them exist anywhere in
`src/api/` -- confirmed live (`curl` against a real running backend returns 404 for all 8, not an
auth issue) and confirmed by exhaustive grep across `src/api/routes/` and `src/api/server.py` while
auditing the live-map-reconnection and world-rendering-core epics
(`TCK-20260825-LIVE-MAP-DEV-AUTH-AND-WS-PROXY-FIX`). This data feeds HUD detail panels
(`BuildingPanel.tsx`, `LootPanel.tsx`, `ClassHallPanel.tsx`, `InspectPanel.tsx`) -- item names,
class/skill definitions, trait descriptions, building-type labels, etc. -- shown when a player
inspects an entity, building, or loot item.

**Not part of either the live-map-reconnection or world-rendering-core epics** -- this data belongs
to the HUD subsystem (`hud-core-panel-wiring`, `hud-contextual-panel-wiring`,
`hud-design-system-foundation`, all still `tickets/todos/`, not yet built). Filed as its own ticket
rather than folded into either epic's own follow-up work, so it lands with the epic that actually
consumes it.

`MetadataContext.tsx`'s `MetadataProvider` used to hard-block the entire app (a full-screen "Failed
to load game metadata" error, `<App/>` never rendered) on any of these 8 fetches failing --
`TCK-20260825-LIVE-MAP-DEV-AUTH-AND-WS-PROXY-FIX` made that non-blocking (falls back to an
all-empty `GameMetadata` object instead), so the live map and other app surfaces now render
regardless of this gap. This ticket is the real, substantive fix: build the 8 backend routes for
real, so the HUD detail panels this data actually feeds have real content to show instead of silent
empty lookups.

## Scope
- Investigate the real server-side content-catalog data model (likely `src/core/registries.py`
  and/or `data/content/`-loaded catalogs -- not yet confirmed, this ticket's own Investigate phase's
  job) for each of the 8 domains: enums (materials/ai_states/tiers/rarities/item_types/damage_types/
  elements/entity_roles/factions/faction_relations/entity_kinds), items, classes (classes/skills/
  race_skills/scaling_grades/mastery_tiers/skill_targets), traits, attributes, buildings, resources,
  recipes.
- Build a new `src/api/routes/metadata.py` router (or split further if the catalog data model makes
  one file unwieldy) with 8 GET routes matching `frontend/src/types/metadata.ts`'s already-defined
  response shapes exactly (`EnumsData`, `ItemsData`, `ClassesData`, `TraitsData`, `AttributesData`,
  `BuildingsData`, `ResourcesData`, `RecipesData`) -- the frontend contract is already fully
  specified and should not need to change.
- Mount the router the same way `map`/`static`/`stats` are mounted (`prefix="/api/v1"`,
  `dependencies=[Depends(require_admission)]`) -- same auth posture as the other read-only content
  routes, no special-casing.
- Once real routes exist, reconsider (in this ticket, not a separate one) whether
  `MetadataContext.tsx`'s non-blocking-fallback behavior should also surface a visible-but-non-blocking
  warning banner when it silently degrades, now that a real failure would indicate an actual bug
  rather than "not built yet."

## Out of Scope
- Any change to `frontend/src/types/metadata.ts` or the 4 consuming panel components
  (`BuildingPanel.tsx`, `LootPanel.tsx`, `ClassHallPanel.tsx`, `InspectPanel.tsx`) -- their contract
  and rendering logic are already correct against the documented shapes; this ticket only needs to
  make the backend satisfy that contract.
- `MetadataContext.tsx`'s non-blocking-fallback mechanism itself -- already shipped by
  `TCK-20260825-LIVE-MAP-DEV-AUTH-AND-WS-PROXY-FIX`; this ticket's own last Scope bullet only
  revisits whether a warning banner is now warranted, not the fallback's existence.
- Any of the HUD epics' own remaining scope (panel layout, design-system tokens, wiring) -- this
  ticket is purely the backend data source those epics' panels already assume exists.

## Acceptance Criteria
- [ ] All 8 `/api/v1/metadata/*` routes exist and return real data matching
      `frontend/src/types/metadata.ts`'s documented shapes
- [ ] Live-verified: `MetadataContext.tsx` successfully loads real (non-empty) metadata through the
      real routes, not the empty fallback
- [ ] At least one of the 4 consuming panels (`BuildingPanel`/`LootPanel`/`ClassHallPanel`/
      `InspectPanel`) verified to render real looked-up names/descriptions from the new data, not
      blank/fallback values
- [ ] Existing frontend tests (`MetadataContext.test.tsx`, panel component tests if any) still pass
- [ ] New backend tests cover all 8 routes' response shapes

## Related Tickets
- TCK-20260825-LIVE-MAP-DEV-AUTH-AND-WS-PROXY-FIX (discovered this gap; shipped the non-blocking
  fallback that keeps the rest of the app usable in the meantime)
- TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT (closest real precedent: a similar single-content-lookup
  read-only REST endpoint, `/api/v1/manifest`, though narrower in scope -- terrain/entity/building
  ID-to-meaning only, not the full RPG-mechanics catalog this ticket needs)
- hud-core-panel-wiring, hud-contextual-panel-wiring, hud-design-system-foundation (all
  `tickets/todos/`, not yet built -- the real consumers of this data; this ticket is a prerequisite
  for their panels to show real content, but is filed independently since it is pure backend work)

## Related Docs
None yet -- no existing doc describes a metadata/content-catalog REST surface.

## Related Stored Artifacts
None yet (standard tier -- will need `investigation.md`/`plan.md`/`test_plan.md` once picked up).

## Related Code Areas
- frontend/src/contexts/MetadataContext.tsx (the caller, already correct)
- frontend/src/types/metadata.ts (the already-specified response contract)
- frontend/src/components/BuildingPanel.tsx, LootPanel.tsx, ClassHallPanel.tsx, InspectPanel.tsx
  (the real consumers)
- src/api/server.py (router mounting pattern to follow)
- src/api/routes/manifest.py (closest structural precedent)
- src/core/registries.py / data/content/ (likely real data source -- not yet confirmed)

## Assumptions / Open Questions
- Exact server-side source of truth for each of the 8 domains is not yet confirmed -- this ticket's
  own Investigate phase must trace where item/class/trait/attribute/building/resource/recipe
  definitions actually live server-side before designing the routes' implementation.
- Whether all 8 domains are populated content today, or whether some (e.g. `recipes`,
  `mastery_tiers`) are still design-only/unpopulated in the current content catalog -- if so, this
  ticket may need to report a partial result (routes exist, return correctly-shaped but empty data
  for domains with no real content yet) rather than a full one.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
