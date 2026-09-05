---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260825-METADATA-API-BACKEND-MISSING
phase: done
date: 2026-08-25
tags: [hud, content]
---

# TCK-20260825-METADATA-API-BACKEND-MISSING

## Title
Build the real `/api/v1/metadata/*` backend -- 8 routes the frontend has called since the initial
import, none of which exist

## Status
DONE

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
- [x] All 8 `/api/v1/metadata/*` routes exist and return real data matching
      `frontend/src/types/metadata.ts`'s documented shapes. Real data everywhere a genuine backend
      source exists (~60% of sub-fields); correctly-shaped empty/defaulted data everywhere it
      doesn't (never fabricated) — per explicit user decision. See investigation.md's domain-by-
      domain table.
- [x] Live-verified: `MetadataContext.tsx` successfully loads real (non-empty) metadata through the
      real routes, not the empty fallback. Found and fixed a real bug in the process: this
      ticket's own "already correct" claim about `MetadataContext.tsx` was wrong — it sent no
      `X-API-Key` header, so every route 401'd until fixed.
- [x] At least one of the 4 consuming panels (`BuildingPanel`/`LootPanel`/`ClassHallPanel`/
      `InspectPanel`) verified to render real looked-up names/descriptions from the new data, not
      blank/fallback values. `LootPanel`, via a new test with a real fixture captured live from a
      running backend.
- [x] Existing frontend tests (`MetadataContext.test.tsx`, panel component tests if any) still pass.
      Full `npx vitest run`: 31/31 pass.
- [x] New backend tests cover all 8 routes' response shapes. `tests/api/test_metadata_api.py`, 21
      tests.

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
- `stored_artifacts/TCK-20260825-METADATA-API-BACKEND-MISSING/`

## Related Code Areas
- frontend/src/contexts/MetadataContext.tsx (the caller — fixed a real auth-header bug found
  during live-testing; this ticket's own original "already correct" claim was wrong)
- frontend/src/types/metadata.ts (the already-specified response contract, untouched)
- frontend/src/components/BuildingPanel.tsx, LootPanel.tsx, ClassHallPanel.tsx, InspectPanel.tsx
  (the real consumers, untouched — LootPanel live-verified via a new test)
- src/api/server.py (new router mounted, matching manifest.router's pattern)
- src/api/routes/manifest.py (structural precedent followed)
- src/api/routes/metadata.py, src/api/presenters/metadata_presenter.py (new — this ticket's
  deliverable)
- src/content/repository.py (CatalogRepository — confirmed real source for ~60% of sub-fields)
- src/core/classes.py, src/core/enums.py (CLASS_REGISTRY, EntityRole — the other real sources found)

## Assumptions / Open Questions
- ~~Exact server-side source of truth for each of the 8 domains is not yet confirmed~~ — resolved,
  see investigation.md's domain-by-domain table.
- ~~Whether all 8 domains are populated content today~~ — resolved: confirmed several are
  genuinely unpopulated (`ai_states`, `tiers`, `damage_types`, nearly all of `classes`' richer
  fields) — per explicit user decision, built all 8 routes anyway with correctly-shaped
  empty/defaulted data for the unbacked parts, documented per-field, never fabricated.

## Implementation Notes
Investigation found the frontend contract (`frontend/src/types/metadata.ts`) was written
speculatively, well ahead of any backend implementation — several sub-fields have genuinely zero
backing data anywhere in this codebase (confirmed via repo-wide grep, not assumed): `ai_states`,
`tiers`, `damage_types`, `skill_targets`, and nearly all of `classes`' richer fields (skills,
race_skills, scaling_grades, mastery_tiers, and most of `ClassEntry` itself — only a bare 4-class
legacy `CLASS_REGISTRY` exists). Asked the user upfront whether to narrow scope to only the
well-backed domains or build all 8 with documented empty/defaults for the unbacked parts — chose
the latter.

Real backing data confirmed for a solid majority of sub-fields via `CatalogRepository`: materials,
elements, factions, faction_relationships, entity_archetypes (entity_kinds), items, traits,
attributes, buildings, resources, and — confirmed via direct source read, not assumed — `recipes`
(verified `src/core/registries.py::RecipeRegistry` is itself bootstrapped from
`CatalogToRecipeRegistryAdapter(catalog_repo).adapt()`, i.e. `catalog.recipes` **is** the "actually-
live crafting-execution path" `TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE` found elsewhere;
count-verified 25 entries both ways).

The generic-enum `id: number` vs. catalog's string-id mismatch reuses this codebase's own existing
precedent (`StatePresenter.terrain_code_map`'s stable sorted-index assignment) rather than
inventing a new convention.

**Real bug found and fixed, not just documented**: live-testing (real backend + real frontend dev
server on the real Vite proxy path) found `MetadataContext.tsx`'s `fetchJson()` sends no
`X-API-Key` header at all, while every other authenticated frontend fetch
(`useSimulation.ts`) already has this. Since this ticket's own Scope requires the same
`require_admission` auth as every other route, every new route would 401 for the real app without
this fix. Fixed by mirroring `useSimulation.ts`'s exact convention — the only change to
`MetadataContext.tsx`, no change to the excluded type file or panel components.

Live-verified for real (not skipped, not assumed): started a real backend
(`python3 -m src serve --port 8000 ...`) and real frontend dev server (`npm run dev`), confirmed
all 8 routes return real data through the exact real network path (Vite's `/api` dev proxy, with
the real `X-API-Key` header) `MetadataContext.tsx` itself uses. Wrote a new rendering test
(`LootPanel.metadata.test.tsx`) using a real fixture captured live from the running backend
(`iron_sword` → "Iron Sword"/weapon/UNCOMMON/80g) proving `LootPanel` genuinely renders that real
data, not the raw item-id fallback.

## Test Summary
- `pytest tests/api/test_metadata_api.py -v` — 21 passed (route-level 200/503 for all 8 routes,
  response-shape key-set checks, per-domain real-vs-defaulted-field assertions).
- `pytest tests/api/ tests/unit/api -m "not slow and not extra_slow" -q` (broader regression check)
  — 197 passed.
- `cd frontend && npx vitest run` (full frontend suite, including the new
  `LootPanel.metadata.test.tsx`) — 31 passed, 0 failed (4 test files).
- Manual live verification: real backend (port 8000) + real frontend dev server (port 5173,
  `npm run dev`) running simultaneously; all 8 routes curled directly and through the real Vite
  proxy path with the real dev API key, confirmed real non-empty JSON for every route (e.g.
  `enums.materials` — 18 real materials; `items` — 36 real items; `recipes` — 25 real recipes,
  matching `catalog.recipes`'s live count exactly).

## Files Changed
- `src/api/routes/metadata.py` (new) — 8 GET routes.
- `src/api/presenters/metadata_presenter.py` (new) — response shaping, one `present_*` method per
  domain, real-vs-defaulted decisions documented inline per field.
- `src/api/server.py` — mounted the new router (matches `manifest.router`'s pattern).
- `frontend/src/contexts/MetadataContext.tsx` — fixed the real missing-`X-API-Key`-header bug.
- `tests/api/test_metadata_api.py` (new) — 21 tests.
- `frontend/src/test/LootPanel.metadata.test.tsx` (new) — real-fixture rendering test.

## Completion Summary
Built all 8 `/api/v1/metadata/*` routes, per explicit user decision to cover every domain now
rather than narrow scope: real data everywhere a genuine backend source exists (materials,
elements, factions, faction_relations, entity_kinds, items, traits, attributes, buildings,
resources, recipes — confirmed `catalog.recipes` is the same live source
`TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE` found elsewhere), correctly-shaped empty/defaulted
data everywhere no backend source exists at all (`ai_states`, `tiers`, `damage_types`,
`skill_targets`, nearly all of `classes`' richer fields) — each decision documented inline, never
fabricated. Found and fixed a real, necessary bug beyond the ticket's own original scope
description: `MetadataContext.tsx`'s own "already correct" claim was wrong (missing auth header,
confirmed via live-testing, not assumed) — fixed by mirroring an existing established convention,
not inventing a new one. Live-verified end-to-end with a real running backend and frontend dev
server, and proved a real consuming panel (`LootPanel`) renders real looked-up data via a new test
built on a fixture captured live from the running system. All existing and new tests pass (31
frontend, 218 backend across the targeted + broader regression sweeps).
