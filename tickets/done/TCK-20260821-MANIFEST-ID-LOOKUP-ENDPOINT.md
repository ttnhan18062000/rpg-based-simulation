---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT
phase: done
date: 2026-08-21
tags: [api-design, content]
---

# TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT

## Title
Add GET /api/v1/manifest endpoint for ID-to-meaning lookups

## Status
DONE

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
- [x] GET /api/v1/manifest returns 200 with SEPARATE protocol_version and dictionary_version fields (not one combined schema_version)
- [x] terrain_types/entity_kinds/building_types populated LIVE from CatalogRepository.terrain/.entity_archetypes/.buildings (id->display_name or id), not hardcoded literals duplicating colors.ts
- [x] dictionary_version changes when catalog content changes (derived from CatalogRepository._compute_fingerprint()) while protocol_version stays fixed across a dictionary-only change
- [x] useSimulation.ts fetches /manifest exactly once, joined into loadInitial()'s existing Promise.all alongside /static, NOT the 500ms poll loop
- [x] terrain_types id-space matches whatever id scheme present_map's grid encoding uses
- [x] location_types' data source (new minimal registry vs. explicit field drop) is documented as an explicit decision, not left implicit

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

Implemented all 10 plan.md steps in order, verified sound (no deviations from architecture):

1. **`src/api/dependencies.py`** — added `_catalog_repository: Optional[CatalogRepository]` module
   global plus `set_catalog_repository`/`get_catalog_repository`, mirroring `set_quality_hub`/
   `get_quality_hub` exactly (`Optional[...]` return, no raise). `CatalogRepository` is imported
   directly at module scope (not `TYPE_CHECKING`-guarded) since `src/content/repository.py` has no
   import back into `src/api`.
2. **`src/api/server.py`'s `lifespan()`** — after `manager.start()`, construct a `CatalogRepository()`,
   call `.load_all()`, and `set_catalog_repository(catalog)`, before the quality-hub wiring block and
   before `yield`. No shutdown/reset added (matches the existing pattern: none of the other 3
   singletons are reset at shutdown either).
3. **`src/api/presenters/state_presenter.py`** — renamed `_terrain_code_map` to public
   `terrain_code_map` (pure rename); updated its two internal call sites in `present_map` and
   `present_static`. No behavior change — verified by running the file's existing 9 tests unmodified
   (all green).
4. **`src/api/presenters/manifest_presenter.py`** (new) — `ManifestPresenter.present_manifest(state,
   catalog)`. `entity_kinds`/`building_types` are `{id: display_name or id}` projections of
   `catalog.entity_archetypes`/`.buildings`. `terrain_types` is keyed by `StatePresenter
   .terrain_code_map(state)`'s int codes (matching `present_map`'s id-space exactly), with display
   names resolved via `catalog.terrain.get(raw.lower())`, falling back to `raw.title()` for
   uncataloged values. `terrain_types = {}` when `state is None`. `location_types` is omitted from
   the response entirely (not an empty placeholder), documented in-code. `MANIFEST_PROTOCOL_VERSION
   = "1.0.0"` is a fixed literal independent of `catalog.fingerprint`/`catalog.version`.
5. **`src/api/routes/manifest.py`** (new) — `GET /manifest`, following `economy.py`'s exact pattern:
   no `Depends`, direct `get_engine_manager()`/`get_catalog_repository()` calls, 503 only when the
   catalog singleton itself is unset (state-is-None degrades gracefully per Step 4, not a 503). No
   `AuthoritativeState`/`EntityState` import anywhere in the file — verified compliant against
   `tests/architecture/test_api_read_model_guard.py`'s AST scan.
6. **`src/api/server.py`'s `create_v2_app()`** — registered `manifest.router` with
   `prefix="/api/v1"`, `dependencies=[Depends(require_admission)]`, alongside the other
   `src.api.routes` registrations (immediately after `economy`).
7. **`frontend/src/types/api.ts`** — added `Manifest` interface (`protocol_version`,
   `dictionary_version`, `terrain_types`/`entity_kinds`/`building_types` all `Record<string, string>`
   — JSON object keys are always strings, so `terrain_types`' int codes serialize as `"0"`, `"1"`,
   etc.). `location_types` intentionally absent.
8. **`frontend/src/hooks/useSimulation.ts`** — added `fetchJSON<Manifest>('/manifest')` as a third
   entry in `loadInitial()`'s existing `Promise.all` (alongside `/map`, `/static`), stored via a new
   `useState<Manifest | null>(null)`. **Deviation from plan.md's literal wording**: the plan said to
   store the value in state "but do not wire it into any rendering/color logic" — I additionally
   added `manifest` to the `SimulationState` interface and the hook's return object (matching every
   other `loadInitial()`-fetched value, all of which are returned this way). This was necessary, not
   optional: `frontend/tsconfig.app.json` sets `noUnusedLocals: true`, so a `useState` value that is
   never read anywhere would fail `tsc` compilation (`TS6133`). Returning it from the hook is
   exposing/storing state, not rendering/color-logic wiring — the fast-follow ticket still owns
   actually consuming `manifest.terrain_types`/`entity_kinds`/`building_types` in `colors.ts`/
   `GameCanvas.tsx`, which this ticket does not touch. Recorded in
   `staging_artifacts/TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT/plan.md`'s new Deviations section.
9. **`docs/engine/contracts/frontend.md` §2A** — added `/api/v1/manifest` as a third enumerated
   `loadInitial()` fetch call, noting it's joined into the same `Promise.all`, its `terrain_types` id
   space matches `/api/v1/map`'s, `location_types` is omitted, and the fetched value isn't yet
   consumed by rendering (fast-follow).
10. **`docs/parity_ledger/infrastructure.yaml`** — added `INFRA-386` (next ID allocated via
    `tools/gate_checks/parity_updater_static.py`'s `next_available_id()`, confirmed no existing entry
    overlaps via `search_existing_entries()`), `status: verified`, `priority: P2`,
    `test_path: tests/api/test_manifest_api.py`, `divergence_note` documenting the
    `dictionary_version` known-limitation (catalog-content-only, does not reflect a different loaded
    world's terrain-value distribution). Written via `tools/parity_ledger_writer.py`'s
    `write_entry()`, which validated the entry and rebuilt the derived SQLite parity index
    in-process.

Per architecture-review's refinement, `test_manifest_terrain_types_id_space_matches_present_map_grid`
asserts the PLAIN and GRASS cases as two separate assertions: PLAIN resolves via the real catalog
lookup (`catalog.terrain["plain"]` exists, `display_name: "Plain"`), while GRASS has no catalog entry
at all and hits the `title()` fallback (`"Grass"`) — confirmed by reading
`data/content/world/terrain.yaml` directly (10 lowercase ids, no `"grass"`).

## Test Summary

New tests, all passing:
- `tests/api/test_manifest_api.py` (12 tests) — route-level (200 with separate versions, 503 when
  catalog unset, graceful degradation when state is None) and presenter-level (entity_kinds/
  building_types catalog projection, dictionary_version/protocol_version split, location_types
  dropped, terrain_types live-from-catalog, terrain_types id-space matches present_map's grid with
  PLAIN/GRASS asserted as two separate cases per architecture-review's refinement, plain-dict
  shape verification).
- `tests/unit/api/test_dependencies.py` (2 tests, new file — none existed before) — DI singleton
  wiring (`get_catalog_repository()` returns the same object across calls; returns `None` when
  unset).
- Existing `tests/unit/api/test_state_presenter.py` (9 tests) — run unmodified, all green, proving
  the `_terrain_code_map` → `terrain_code_map` rename is a pure rename with no behavior change.
- Existing `tests/architecture/test_api_read_model_guard.py` — run unmodified, passes with the new
  `src/api/routes/manifest.py` in scope (it imports neither `AuthoritativeState` nor `EntityState`).
- `tests/api/test_rest_parity.py` (2 tests) — server-boot regression check. **Note**: this test
  hardcodes a bare `python3` subprocess call and fails in this sandbox with
  `ModuleNotFoundError: No module named 'pydantic'` regardless of my changes (confirmed pre-existing
  by running the same test against `git stash` of this ticket's diff — identical failure). Re-ran
  with the venv prepended to `PATH` (`PATH=.venv/bin:$PATH`) and both tests pass, confirming the
  server boots successfully with the new `lifespan()` catalog-load step and the new router
  registered, with no regression to existing routes.
- Full sweep: `tests/unit/api/`, `tests/api/`, `tests/architecture/test_api_read_model_guard.py` — 142
  passed, 6 failed (all 6 are the same bare-`python3`-lacking-pydantic subprocess-server tests;
  confirmed passing when re-run with the venv on `PATH`), 2 deselected (the rest-parity tests, run
  separately above).

**Known, disclosed gap (not a blocker)**: AC "useSimulation.ts fetches /manifest exactly once, joined
into loadInitial()'s existing Promise.all" has no automated test. `loadInitial()` has zero existing
test coverage anywhere in this codebase (confirmed by investigation.md and by grep — no test file
under `frontend/` exercises this hook's fetch effects at all), so this is a structural gap in the
project's frontend test harness, not something this ticket introduces or should paper over with a
fabricated test. Verified structurally instead: `loadInitial()` still resolves all three fetches via
one `Promise.all` (not sequential awaits, not moved into the separate `fallbackPoll` 500ms-poll
`useEffect`), matching this project's existing disclosed-limitation pattern (e.g.
`docs/parity_ledger/infrastructure.yaml`'s own disclosed-limitation entries).

## Files Changed

- `src/api/dependencies.py` — new `CatalogRepository` DI singleton pair
- `src/api/server.py` — lifespan catalog load + `set_catalog_repository`; router registration
- `src/api/presenters/state_presenter.py` — `_terrain_code_map` → `terrain_code_map` rename
- `src/api/presenters/manifest_presenter.py` (new) — `ManifestPresenter`
- `src/api/routes/manifest.py` (new) — `GET /api/v1/manifest` route
- `frontend/src/types/api.ts` — new `Manifest` interface
- `frontend/src/hooks/useSimulation.ts` — `/manifest` fetch in `loadInitial()`'s `Promise.all`;
  `manifest` state added to `SimulationState` and the hook's return object (see Deviation above)
- `docs/engine/contracts/frontend.md` — §2A updated to list the third `loadInitial()` fetch call
- `docs/parity_ledger/infrastructure.yaml` — new `INFRA-386` entry
- `tests/api/test_manifest_api.py` (new)
- `tests/unit/api/test_dependencies.py` (new)
- `staging_artifacts/TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT/plan.md` — added Deviations section
- `tickets/inprogress/TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT.md` — this file

## Completion Summary

Added `GET /api/v1/manifest`, a versioned ID-to-meaning content dictionary
(`terrain_types`/`entity_kinds`/`building_types`, separate `protocol_version`/`dictionary_version`
fields), backed by a new `CatalogRepository` DI singleton loaded once at server startup. The central
design decision — `terrain_types` must be keyed by the same live, per-state int codes
`StatePresenter.present_map`'s RLE grid uses (not a static catalog passthrough), since real compiled
worlds contain uncataloged uppercase terrain defaults (`"PLAIN"`, `"GRASS"`) with no
`CatalogRepository.terrain` key — was resolved by widening `StatePresenter._terrain_code_map` to
public `terrain_code_map` and reusing it in the new `ManifestPresenter`, with a case-insensitive
catalog lookup falling back to `title()`-casing for uncataloged values. `location_types` is dropped
from the response entirely (documented decision, no registry exists to source it from). Frontend
wiring (`Manifest` type, `useSimulation.ts` fetch joined into `loadInitial()`'s `Promise.all`) and
doc/parity updates landed as later steps; consuming the manifest to retire `colors.ts`'s hardcoded
maps remains an explicit fast-follow, per the ticket's own scope. One disclosed, non-blocking test
gap: `loadInitial()`'s fetch wiring has no automated frontend test, since no test harness covers that
hook's effects anywhere in this codebase today.
