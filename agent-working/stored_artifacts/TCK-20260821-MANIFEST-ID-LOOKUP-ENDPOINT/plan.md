---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT
artifact_type: plan
tags: [api-design, content]
---

# Implementation Plan — TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT

## Summary

Add a new `GET /api/v1/manifest` route that returns a versioned ID-to-meaning lookup table
(`terrain_types`, `entity_kinds`, `building_types`), backed by a new `CatalogRepository` singleton
loaded once at server startup and wired into `src/api/dependencies.py` following the exact
`set_x`/`get_x` pattern already used for `QualityHub`. `entity_kinds`/`building_types` are
straightforward `{catalog_id: display_name}` projections of `CatalogRepository.entity_archetypes`/
`.buildings` — confirmed clean 1:1 matches with no reconciliation issue
(investigation.md "`entity_kinds`/`building_types` — confirmed clean 1:1 catalog match").
`terrain_types` cannot be built the same way: `investigation.md`'s Risks section proves (via direct
reads of `src/worldbuilding/compiler.py:205` and `recipe.py:16`) that `present_map`'s int codes are
computed per-call over the live, per-loaded-world `state.terrain` value set — which includes
uncataloged uppercase defaults (`"PLAIN"`, `"GRASS"`) that have no `CatalogRepository.terrain` key
at all. This plan resolves that conflict by keying `terrain_types` off the **same live
`StatePresenter` terrain-code mapping `present_map` already uses** (widened from private to public,
Step 3), with catalog display names resolved case-insensitively and a `title()`-cased fallback for
any code with no catalog entry — the exact fallback precedent `present_static` already established
for building/resource-node names (`state_presenter.py:205`, `:218`). `location_types` is resolved by
explicitly dropping the field (omitted from the response, not populated as an empty placeholder),
documented in code and in `docs/engine/contracts/frontend.md`, since no `LocationDefinition`
registry exists anywhere in `src/content/schema.py` and building one is out of this ticket's scope
per its own Out of Scope section. `protocol_version` is a new fixed literal constant, independent of
`CatalogRepository._version`, to keep the manifest route's own response-contract version decoupled
from the catalog's internal versioning concept. Frontend wiring (`Manifest` type, `useSimulation.ts`
fetch) and doc/parity updates follow as later, independent steps.

## Steps

### Step 1 — Add `CatalogRepository` DI singleton to `src/api/dependencies.py`

**Files:** `src/api/dependencies.py`

**Change:** Add a fourth singleton pair, `set_catalog_repository`/`get_catalog_repository`, mirroring
the existing `set_quality_hub`/`get_quality_hub` pair exactly (`src/api/dependencies.py:22-27`, read
directly — confirmed module-level `Optional[...]` global plus a `set_x(val)`/`get_x() -> Optional[...]`
pair, no lazy-init or lock). Add `_catalog_repository: Optional["CatalogRepository"] = None` at module
scope alongside the existing three globals (`:9-11`). Import `CatalogRepository` for type purposes —
unlike `QualityHub`/`QualityPersistence` (which are guarded under `TYPE_CHECKING` at `:5-7` to avoid a
circular import with `src.simulation_quality`), `src.content.repository` does not import anything from
`src.api` (confirmed by reading `src/content/repository.py:1-24` — its only imports are `os`,
`threading`, `yaml`, `hashlib`, dataclasses/typing, `pydantic`, and `src.content.schema`/`src.content.paths`),
so a direct top-level `from src.content.repository import CatalogRepository` import is safe here and
does not need the `TYPE_CHECKING` guard used for the quality-hub pair. Unlike `get_engine_manager()`
(which raises `RuntimeError` if unset, `:17-20`) and `get_quality_hub()` (which returns `Optional[...]`
without raising, `:26-27`), model `get_catalog_repository()` on the `get_quality_hub()` style — return
`Optional[CatalogRepository]`, do not raise — because the manifest route itself decides how to
degrade (see Step 5) rather than the DI layer forcing a hard failure.

**Do NOT touch:** `_engine_manager`/`_quality_hub`/`_quality_persistence` globals or their existing
`set_x`/`get_x` functions — purely additive, no existing singleton's behavior changes.

**Verify:** `test_catalog_repository_di_wiring_loaded_once_at_startup` (new,
`tests/unit/api/test_dependencies.py`) — asserts `get_catalog_repository()` returns the same object
across two calls once `set_catalog_repository()` has been called once.

### Step 2 — Load `CatalogRepository` once at server startup in `server.py`'s `lifespan()`

**Files:** `src/api/server.py`

**Change:** In `create_v2_app()`'s `lifespan()` (`src/api/server.py:33-73`, read directly), add
catalog construction and `load_all()` immediately after `manager.start()` (`:37`) and before the
quality-hub wiring block (`:39-43`), and in all cases *before* `yield` (`:53`) so the singleton is
populated before any request can reach a route. `manager.start()` spawns the kernel's tick loop on a
separate background thread (`src/api/engine_manager.py:236-245`: `self._thread =
threading.Thread(target=self._run_loop, ...); self._thread.start()`), and confirmed `start()` itself
does not construct or load any `CatalogRepository` — the kernel's own internal catalog loading (via
`ContentWarmupService`, referenced in investigation.md) happens inside that background thread's own
init path, entirely independent of this new lifespan-level instance. `CatalogRepository.load_all()`'s
`WORLD-CAT-004` hot-path guard (`_tick_context_active`, `src/content/repository.py:21-23`) is a
`threading.local()`, so it only detects a reentrant call on the **same** thread already inside a tick
— it cannot fire from a cross-thread race with the kernel's background tick thread. This means placing
`load_all()` before or after `manager.start()` carries no hot-path-violation risk either way; placing
it after (as below) is purely for grouping with the other post-`start()` wiring already in this
function (quality hub), not because of any ordering requirement:
```python
from src.content.repository import CatalogRepository
from src.api.dependencies import set_catalog_repository
catalog = CatalogRepository()
catalog.load_all()
set_catalog_repository(catalog)
```
Add `set_catalog_repository` to the existing `from src.api.dependencies import (...)` block at
`server.py:18-21` (currently imports `set_engine_manager, get_engine_manager, set_quality_hub,
set_quality_persistence` — add `set_catalog_repository` to this tuple). This is the only lifespan
change — do not add a corresponding shutdown/reset call, since no other singleton in `lifespan()`
(`_engine_manager`, `_quality_hub`, `_quality_persistence`) is explicitly cleared at shutdown either
(confirmed: `:55-73`'s shutdown block only calls `publisher.unregister`, `LiveAnomalyCounter.reset_instance()`,
writes the quality report, and `manager.stop()` — none of the three existing dependency-module globals
are reset to `None`), so adding a reset for the new fourth singleton would be inconsistent with the
existing pattern, not a fix.

**Other writers to `lifespan()`:** `lifespan()` is a single function with no concurrent writers within
one process (FastAPI calls it once per app instance at startup/shutdown) — the only "other writers" to
this shared function body are prior tickets that already added code to it (quality-hub wiring,
`LiveAnomalyCounter` registration, quality-report-at-shutdown). This step must insert without
reordering or removing any of that existing code — confirmed reading the full function body above,
insertion point is a pure addition between two existing statements, not a restructuring.

**Do NOT touch:** The quality-hub wiring block (`:39-43`), the anomaly-counter subscriber registration
(`:45-50`), or the shutdown block (`:55-73`) — no logic in any of these changes.

**Verify:** `tests/api/test_rest_parity.py::test_api_rest_parity` (existing, run unmodified) — this
subprocess-server-based test's server-starts-successfully assertion is the cheapest real regression
check that the new `lifespan()` catalog-load step doesn't break server boot (per test_plan.md's
Integration/REST parity section).

### Step 3 — Widen `StatePresenter._terrain_code_map` to a public method, reused by the manifest presenter

**Files:** `src/api/presenters/state_presenter.py`

**Change:** Rename `_terrain_code_map` (`state_presenter.py:144-154`, read directly — confirmed
`@staticmethod def _terrain_code_map(state) -> Dict[str, int]: return {t: i for i, t in
enumerate(sorted(set(state.terrain.values())))}`) to a public `terrain_code_map` (drop the leading
underscore). Update its two existing internal call sites in the same file — `present_map`
(`:169`, `code_map = StatePresenter._terrain_code_map(state)`) and `present_static` (`:200`, same
call) — to call `StatePresenter.terrain_code_map(state)`. This is a pure rename with no logic change:
the method body, its per-call computation, its alphabetical-sort determinism, and its return type are
all untouched — test_plan.md explicitly frames this as "a widening of its visibility, not a behavior
change" (test_plan.md, New Tests section, item 3's Location note), which this rename satisfies exactly.
No existing test references the old private name directly — confirmed by grepping
`tests/unit/api/test_state_presenter.py` for `_terrain_code_map`: zero hits; all 9 existing tests call
only the public `present_map`/`present_static` entry points, so none of their assertions are affected
by the rename.

**Other writers to `state_presenter.py`:** No other in-flight ticket touches this file per this
session's investigation (Prior Work section names `TCK-20260821-PRESENT-MAP-STATIC` as the ticket that
added `present_map`/`present_static`/`_terrain_code_map`, already done/closed — no concurrent writer).

**Do NOT touch:** `present_map`'s or `present_static`'s own logic beyond the one-line call-site rename
in each — the RLE walk, the width/height derivation, and the building/resource-node/chest/region
projection logic in `present_static` must stay byte-for-byte identical (test_plan.md's Regression
Surface: "must stay byte-for-byte unchanged").

**Verify:** All 9 existing tests in `tests/unit/api/test_state_presenter.py`, run unmodified — must
stay green, proving the rename didn't alter `present_map`/`present_static`'s behavior.

### Step 4 — Add `ManifestPresenter` with the terrain reconciliation logic (the central design decision)

**Files:** `src/api/presenters/manifest_presenter.py` (new file)

**Change:** Create a new presenter file matching the existing flat-file-under-`src/api/presenters/`
convention (`src/api/presenters/economy.py` is the direct precedent — a single `EconomyPresenter`
class with static methods, imported by its route as `from src.api.presenters.economy import
EconomyPresenter`). Add:

```python
from __future__ import annotations
from typing import Any, Dict, Optional
from src.core.state import AuthoritativeState
from src.content.repository import CatalogRepository
from src.api.presenters.state_presenter import StatePresenter

# Fixed independently of CatalogRepository._version (src/content/repository.py:226, :632-634) —
# that field versions the catalog's own internal schema/loader contract, a different concept from
# this route's response-shape contract. Bump this manually only when the manifest response's own
# field set/shape changes; dictionary_version (catalog.fingerprint) already carries content-only
# changes, per AC #3.
MANIFEST_PROTOCOL_VERSION = "1.0.0"

class ManifestPresenter:
    @staticmethod
    def present_manifest(state: Optional[AuthoritativeState], catalog: CatalogRepository) -> Dict[str, Any]:
        entity_kinds = {
            def_id: (d.display_name or d.id) for def_id, d in catalog.entity_archetypes.items()
        }
        building_types = {
            def_id: (d.display_name or d.id) for def_id, d in catalog.buildings.items()
        }

        terrain_types: Dict[str, str] = {}
        if state is not None:
            code_map = StatePresenter.terrain_code_map(state)  # {raw_terrain_str: int_code}
            for raw_terrain, code in code_map.items():
                terrain_types[str(code)] = ManifestPresenter._terrain_display_name(raw_terrain, catalog)

        return {
            "protocol_version": MANIFEST_PROTOCOL_VERSION,
            "dictionary_version": catalog.fingerprint,
            "terrain_types": terrain_types,
            "entity_kinds": entity_kinds,
            "building_types": building_types,
            # location_types intentionally omitted — see docs/engine/contracts/frontend.md §2A and
            # investigation.md's Risks section: no LocationDefinition/CatalogRepository.locations
            # registry exists anywhere in src/content/schema.py; building one is out of this
            # ticket's scope (Out of Scope: "Building any new location-type registry beyond the
            # minimal decision documented above, if dropping the field is chosen instead").
        }

    @staticmethod
    def _terrain_display_name(raw_terrain: str, catalog: CatalogRepository) -> str:
        definition = catalog.terrain.get(raw_terrain.lower())
        if definition is not None:
            return definition.display_name or definition.id
        # Uncataloged default (e.g. "PLAIN"/"GRASS" from src/worldbuilding/compiler.py:205 and
        # recipe.py:16) — same fallback precedent as present_static's b.kind.title() /
        # n.kind.title() (state_presenter.py:205, :218).
        return raw_terrain.title()
```

`CatalogBaseDefinition.id`/`.display_name` fields (used above for both entity_kinds/building_types
and the terrain fallback) are confirmed to exist on every relevant schema class: `id: str` and
`display_name: Optional[str]` are declared on `CatalogBaseDefinition` itself
(`src/content/schema.py:12-13`), and `TerrainDefinition`, `BuildingDefinition`,
`EntityArchetypeDefinition` all subclass it (`src/content/schema.py:267`, `:248`, `:206` respectively)
without overriding either field — confirmed by reading each class body directly. `CatalogRepository.terrain`/
`.buildings`/`.entity_archetypes` are `Dict[str, TerrainDefinition/BuildingDefinition/EntityArchetypeDefinition]`
keyed by catalog id (`src/content/repository.py:196, 205-206`). `catalog.fingerprint` is a read-only
property returning `self._fingerprint`, set by `_compute_fingerprint()` at the end of every
`load_all()` call (`src/content/repository.py:628-630`, `:402-411`, `:367`) — confirmed this is the
exact field the ticket's AC names for `dictionary_version`.

**`terrain_types`' int-code keys are JSON object keys, so they serialize as strings** (e.g. `"0"`,
`"1"`, not `0`, `1`) — Python dicts with int keys are still valid, but FastAPI's JSON encoder renders
all object keys as strings regardless. This is stated explicitly in Anti-Drift Notes below since it's
an interop detail the frontend step (Step 8) must account for.

**Other writers to `state_presenter.py`'s public surface used here:** `StatePresenter.terrain_code_map`
(Step 3) is called read-only from this new file — no write, no mutation of `state`. `present_map`
(the only other caller of `terrain_code_map`, via `present_static` too) is unaffected since this step
only adds a third call site, doesn't change the method.

**Do NOT touch:** `src/api/presenters/economy.py` or `src/api/presenters/state_presenter.py`'s public
`present_map`/`present_static`/`present_entity`/`present_region`/`present_minimal`/`present_full`
methods — this step only adds a new file and reuses `terrain_code_map` read-only.

**Verify:** `test_manifest_terrain_types_live_from_catalog_repository`,
`test_manifest_terrain_types_id_space_matches_present_map_grid` (the single most important new test
per test_plan.md — must include a `"PLAIN"`/`"GRASS"` fixture exercising the fallback path),
`test_manifest_entity_kinds_and_building_types_from_catalog`,
`test_manifest_dictionary_version_changes_with_catalog_fingerprint`,
`test_manifest_returns_separate_protocol_and_dictionary_version`,
`test_manifest_location_types_decision_documented_behavior` (asserts the `location_types` key is
absent from the response) — all in `tests/api/test_manifest_api.py` per test_plan.md.

### Step 5 — Add `GET /api/v1/manifest` route

**Files:** `src/api/routes/manifest.py` (new file)

**Change:** Follow `src/api/routes/economy.py`'s exact pattern (read directly, `economy.py:1-34`) —
a bare `APIRouter`, calling `get_engine_manager()`/new `get_catalog_repository()` directly inside the
handler (not via FastAPI `Depends`), and never importing `AuthoritativeState`/`EntityState` at all
(economy.py doesn't import it either — it accesses `manager.latest_state` untyped and passes it
straight to its presenter, which is the pattern this route replicates):
```python
from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from src.api.dependencies import get_engine_manager, get_catalog_repository
from src.api.presenters.manifest_presenter import ManifestPresenter

router = APIRouter(tags=["Manifest"])

@router.get("/manifest", response_model=Dict[str, Any], summary="ID-to-meaning content dictionary")
async def get_manifest() -> Dict[str, Any]:
    catalog = get_catalog_repository()
    if catalog is None:
        raise HTTPException(status_code=503, detail="Catalog not ready — no content loaded")
    manager = get_engine_manager()
    state = manager.latest_state  # Optional[AuthoritativeState] — untyped here, matches economy.py
    return ManifestPresenter.present_manifest(state, catalog)
```
`manager.latest_state` is a documented public property returning `Optional[AuthoritativeState]`
(`src/api/engine_manager.py:231-234`, read directly) — same property `economy.py:30` already reads.
Unlike the catalog (hard 503 if unset — this should never happen once Step 2 lands, since it's
populated before `yield`), a missing/not-yet-ready `state` is **not** treated as an error here: per
Step 4's design, `ManifestPresenter.present_manifest` already degrades gracefully (`terrain_types={}`
when `state is None`) since `entity_kinds`/`building_types`/`protocol_version`/`dictionary_version`
are all still valid without live state — no reason to fail the whole endpoint for a state-dependent
subset of one field. `APIRouter(tags=["Manifest"])` has no `prefix` (unlike `economy.py`'s
`prefix="/economy"`) because the route path itself is the bare `/manifest` segment, matching the
ticket's literal `GET /api/v1/manifest` (the `/api/v1` prefix is added by `include_router()` in
Step 6, same as every other router).

**Architecture guard compliance:** `tests/architecture/test_api_read_model_guard.py` scans every file
under `src/api/routes/` for direct `AuthoritativeState`/`EntityState` imports outside
`TYPE_CHECKING` (investigation.md's Mechanics/Engine Constraints section). This route file imports
neither — `state` flows through untyped, exactly as `economy.py` already does — so it is compliant
by construction, not by suppression.

**Do NOT touch:** Any existing file under `src/api/routes/` — this is a new file only.

**Verify:** `test_manifest_route_does_not_import_authoritative_state` — covered by the existing
`tests/architecture/test_api_read_model_guard.py` running unmodified against the new file (test_plan.md
New Test #8 — confirm during implementation the new route lands under `src/api/routes/`, which it
does, so it's automatically in the guard's `_API_ROOTS` scan).

### Step 6 — Register the manifest router in `create_v2_app()`

**Files:** `src/api/server.py`

**Change:** Add, alongside the other `include_router` calls (`server.py:94-122`, read directly — each
follows the pattern `from src.api.routes import X` then `app.include_router(X.router, prefix="/api/v1",
dependencies=[Depends(require_admission)])`):
```python
from src.api.routes import manifest
app.include_router(manifest.router, prefix="/api/v1", dependencies=[Depends(require_admission)])
```
Insert this near the other `src.api.routes` registrations (e.g. immediately after the `economy`
registration at `:118-119`) — ordering among routers has no functional effect (FastAPI dispatches by
path, not registration order, and no two routers share a path prefix), so this is a pure addition, not
a reordering. Use the same `dependencies=[Depends(require_admission)]` every sibling router already
uses — no new auth mechanism, matching the existing admission-control pattern uniformly applied to
every `/api/v1/*` router-based route.

**Other writers to `create_v2_app()`'s router-registration block:** Every ticket that has ever added a
router (`history`, `search`, `behavior`, `decisions`, `scenarios`, `campaigns`, `chronicle`,
`economy`, `quality_routes`) wrote one `from ... import X` + one `app.include_router(...)` pair each,
all independent of each other — this step follows the identical shape, so it cannot collide with any
of them.

**Do NOT touch:** Any existing `include_router` call, the inline `@app.get`/`@app.post` routes
(`:127-283`), or the CORS/GZip middleware setup (`:85-92`).

**Verify:** `test_manifest_returns_separate_protocol_and_dictionary_version` (confirms the route is
reachable and returns 200 with the right top-level shape) plus
`tests/api/test_rest_parity.py::test_api_rest_parity` (confirms server still boots and existing routes
are unaffected).

### Step 7 — Add `Manifest` type to `frontend/src/types/api.ts`

**Files:** `frontend/src/types/api.ts`

**Change:** Add a new exported interface following the exact shape/placement convention of
`StaticData`/`MapData` (`api.ts:332-352`, read directly):
```ts
export interface Manifest {
  protocol_version: string;
  dictionary_version: string;
  terrain_types: Record<string, string>;  // keyed by present_map's int codes, stringified
  entity_kinds: Record<string, string>;
  building_types: Record<string, string>;
}
```
`location_types` is intentionally absent from this interface, matching the backend's decision (Step 4)
to omit the field entirely rather than send an empty placeholder. `terrain_types`/`entity_kinds`/
`building_types` are typed `Record<string, string>` (not `Record<number, string>`) because JSON object
keys are always strings — this mirrors the note in Step 4 about `terrain_types`' int codes serializing
as string keys; frontend code reading `terrain_types` by a `present_map` grid int value must do
`manifest.terrain_types[String(code)]`, not `manifest.terrain_types[code]`.

**Not in the ticket's own `## Related Code Areas` list** (only `useSimulation.ts`, `colors.ts`,
`GameCanvas.tsx` are listed among frontend files) — investigation.md flags this explicitly as a gap
the plan must account for: it is a plain type-declaration file, not a UI component, so touching it
does not cross the ticket's `colors.ts`/`GameCanvas.tsx` Out of Scope boundary.

**Do NOT touch:** `StaticData`, `MapData`, `SimulationStats`, `SimulationConfig`, or any other
existing interface in this file — purely additive.

**Verify:** TypeScript compiles cleanly (`Manifest` type-checks against the new
`fetchJSON<Manifest>('/manifest')` call added in Step 8) — no dedicated unit test exists for a type
declaration file; correctness here is enforced structurally by Step 8's usage compiling.

### Step 8 — Fetch `/manifest` once in `useSimulation.ts`'s `loadInitial()`

**Files:** `frontend/src/hooks/useSimulation.ts`

**Change:** In `loadInitial()` (`useSimulation.ts:84-112`, read directly), add a third
`fetchJSON<Manifest>('/manifest')` call into the existing `Promise.all` alongside `/map` and
`/static` (`:88-91`):
```ts
const [rawMap, staticData, manifest] = await Promise.all([
  fetchJSON<MapData>('/map'),
  fetchJSON<StaticData>('/static'),
  fetchJSON<Manifest>('/manifest'),
]);
```
Add `Manifest` to the existing `import type { MapData, WorldState, ... } from '@/types/api'` block at
the top of the file (exact import list not re-derived here — append `Manifest` to whatever the current
list is). This ticket does not specify what React state the fetched `manifest` value is stored into —
consuming it to retire `colors.ts`'s hardcoded maps is the explicit fast-follow (ticket's Request
Summary: "Retiring the frontend's hardcoded color maps to actually consume it is explicitly left for a
fast-follow, not this item"). To satisfy the AC ("fetches `/manifest` exactly once... joined into
`loadInitial()`'s existing `Promise.all`") without overreaching into the fast-follow's scope, store the
fetched value via a new `useState<Manifest | null>(null)` (mirroring how `mapData`/other `loadInitial`
results are already stored as state in this hook) but do not wire it into any rendering/color logic —
that wiring is the fast-follow ticket's job, not this one.

**Other writers to `loadInitial()`'s `useEffect`:** none — this is the one-time-on-mount effect,
structurally distinct from the separate `fallbackPoll` `useEffect` (`:177-256`) that fetches `/stats`
and `/state` on a 500ms interval (investigation.md confirmed these are two separate `useEffect` blocks
with no shared code path). This step must not touch `fallbackPoll` — the AC is explicit that the
manifest fetch is "NOT the 500ms poll loop."

**Do NOT touch:** `fallbackPoll`'s `useEffect` (`:177-256`), the EventSource/SSE delta-sync effect
(mentioned in `docs/engine/contracts/frontend.md` §2B), or any rendering/canvas code — this step is
confined to `loadInitial()`.

**Verify:** No existing frontend test harness covers `loadInitial()`'s current `/map`/`/static`
fetches (investigation.md confirmed this gap) — test_plan.md flags this as a gap to surface at Test
phase rather than a concrete test this plan can cite. Manual/structural verification: `loadInitial()`
still resolves all three fetches via one `Promise.all` (not three sequential awaits, not moved into
`fallbackPoll`).

### Step 9 — Update `docs/engine/contracts/frontend.md` §2A

**Files:** `docs/engine/contracts/frontend.md`

**Change:** §2A ("Initial Load (Full State)", `frontend.md:30-33`, read directly) currently documents
exactly two fetch calls (`/api/v1/map`, `/api/v1/static`) as an enumerated list. Add a third item:
```
3.  **`/api/v1/manifest`**: Fetches the versioned ID-to-meaning lookup table (`terrain_types`,
    `entity_kinds`, `building_types`; `location_types` intentionally omitted — no backend registry
    exists for it, see investigation.md/plan.md for TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT).
```
This is the doc-update investigation.md flagged as required (Docs Requiring Update section) — the
enumerated list becomes stale/incomplete once a third fetch joins the same `Promise.all` (Step 8)
unless updated here.

**Do NOT touch:** §2B (Delta Sync/SSE) or §2C (Inspection Polling) — neither describes behavior this
ticket changes. Do not touch `docs/plans/live_map_reconnection_epic.md` or
`docs/mechanics/content_usage_matrix.md` — investigation.md confirmed both are out of scope for this
ticket (roadmap doc not updated per landed child ticket; content-resolution pipeline doc unaffected by
a read-only API projection).

**Verify:** No automated test covers doc prose; verified by review that §2A's enumerated list now
lists all three `loadInitial()` fetch calls, matching Step 8's actual code.

### Step 10 — Add a parity ledger entry for the new manifest contract

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Per the Authoritative Mechanics Rule, add one new entry documenting the
`/api/v1/manifest` contract, its `protocol_version`/`dictionary_version` split, and the
`terrain_types` reconciliation decision from Step 4. Follow the existing entry shape in this file
(`infrastructure.yaml:1-10`, read directly — fields: `id`, `text`, `status`, `priority`,
`legacy_evidence`, `v2_evidence`, `proof_type`, `test_path`, `divergence_note`, `support_boundary`).
Investigation.md confirmed no existing entry in any `docs/parity_ledger/*.yaml` file covers this
endpoint (grepped for `manifest`, `CatalogRepository`, `dictionary_version`, `protocol_version` — only
unrelated file-manifest families matched), and no P0 entry is implicated, so this is a net-new,
non-P0 addition, not an update to an existing entry. Use the repo's next-ID/existing-entry lookup
tooling (referenced in recent commit history, e.g. `a9c0d753`/related tooling for
`docs/parity_ledger/`) to allocate the next `INFRA-` id rather than hand-picking a number. Set
`status: verified`, `priority: P2` (matching the ticket's own `## Priority`), `test_path` pointing at
`tests/api/test_manifest_api.py`, and `divergence_note` summarizing the terrain-reconciliation
decision (live per-state code mapping, not a static catalog passthrough) so a future reader of the
ledger doesn't have to re-derive it from this plan.

**Other writers to `docs/parity_ledger/infrastructure.yaml`:** This is an append-only YAML list shared
across every ticket that has ever added an `INFRA-*` entry — this step must append one new list entry
at the end (or wherever the repo's tooling places it) without editing or reordering any existing
entry. No other ticket is concurrently touching this specific file per this session's scope.

**Do NOT touch:** Any existing entry's `status`/`v2_evidence`/`test_path` in this file — this is a
pure addition.

**Verify:** No pytest test exercises the parity ledger directly for this ticket (no P0 entry
implicated); verified by review that the new entry's `id` doesn't collide with an existing one and its
`test_path` points at a real, passing test file.

## Scope Guards

- Do not modify `frontend/src/constants/colors.ts` or `frontend/src/components/GameCanvas.tsx` —
  explicitly Out of Scope; retiring the hardcoded color maps is a stated fast-follow.
- Do not fix the `"PLAIN"`/`"GRASS"` uncataloged-default problem in `src/worldbuilding/compiler.py`
  or `recipe.py` — that is a real, adjacent gap this investigation surfaced, but changing either file
  is a durable-state/world-compile change, well outside this ticket's API-only scope.
- Do not build a new `location_types` registry (new schema class, `CANONICAL_FAMILIES` entry, YAML
  content file) — the ticket's Out of Scope section explicitly forbids this beyond the documented
  drop-vs-minimal-registry decision, and this plan documents the "drop" branch of that decision.
- Do not change `CatalogRepository`, its `load_all()`/`_compute_fingerprint()`/`.fingerprint`/
  `.version` contracts, or any of its existing instantiation sites (`content_semantics/faction.py`,
  `worldbuilding/cli.py`, `engine/behavior_consumers.py`, `content/warmup.py`, `runtime/bootstrap.py`,
  `core/modes.py`, `core/registries.py`) — this ticket only reads `CatalogRepository` via a new,
  separate, server-process-lifetime instance; it never touches those short-lived local instances.
- Do not instantiate a fresh `CatalogRepository` and call `load_all()` per-request inside the route
  handler — load once at startup (Step 2) and reuse via the DI singleton (Step 1).
- Do not alter `_terrain_code_map`'s/`terrain_code_map`'s return values, `present_map`'s RLE encoding,
  or `present_static`'s existing field derivations — Step 3 is a pure rename, nothing else in
  `state_presenter.py` changes behaviorally.
- Do not wire the fetched `Manifest` value into any rendering, color, or canvas logic in
  `useSimulation.ts` beyond storing it in state — consuming it is the fast-follow ticket's job.

## Dependency Map

- Step 1 (DI singleton) must land before Step 2 (lifespan wiring calls `set_catalog_repository`) and
  before Step 5 (route calls `get_catalog_repository`).
- Step 3 (rename `_terrain_code_map` → `terrain_code_map`) must land before Step 4 (`ManifestPresenter`
  calls the renamed public method).
- Step 4 (`ManifestPresenter`) must land before Step 5 (route imports and calls it).
- Step 5 (route file) must land before Step 6 (registers that route's router).
- Step 7 (`Manifest` type) must land before Step 8 (`useSimulation.ts` uses `fetchJSON<Manifest>`).
- Steps 9 and 10 (docs, parity ledger) depend on Steps 1–8 being functionally complete (they document
  the landed behavior) but do not block each other or any other step.
- Steps 1–2 (backend DI/lifespan) and Steps 3–4 (presenter logic) are independent of each other and
  could be implemented in either order or in parallel; both must complete before Step 5.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| GET /api/v1/manifest returns 200 with SEPARATE protocol_version and dictionary_version fields | Steps 1, 2, 4, 5, 6 | `test_manifest_returns_separate_protocol_and_dictionary_version` |
| terrain_types/entity_kinds/building_types populated LIVE from CatalogRepository, not hardcoded literals | Steps 1, 2, 4 | `test_manifest_terrain_types_live_from_catalog_repository`, `test_manifest_entity_kinds_and_building_types_from_catalog` |
| dictionary_version changes with catalog fingerprint; protocol_version stays fixed | Step 4 | `test_manifest_dictionary_version_changes_with_catalog_fingerprint` |
| useSimulation.ts fetches /manifest exactly once, joined into loadInitial()'s Promise.all, NOT the poll loop | Step 8 | Manual/structural verification (no existing frontend test harness — flagged gap) |
| terrain_types id-space matches present_map's grid encoding | Steps 3, 4 | `test_manifest_terrain_types_id_space_matches_present_map_grid` |
| location_types data source documented as an explicit decision | Step 4 (drop, with code comment), Step 9 (doc update) | `test_manifest_location_types_decision_documented_behavior` |

## Anti-Drift Notes

- **The central risk this ticket surfaced**: a `terrain_types` dict built as a naive
  `{catalog_id: display_name for catalog_id, definition in catalog.terrain.items()}` passthrough would
  satisfy AC #2's literal wording while silently violating AC #5 (id-space must match `present_map`'s
  grid) — this plan's Step 4 avoids that by deriving `terrain_types` from the same
  `StatePresenter.terrain_code_map(state)` call `present_map` itself uses, not from
  `CatalogRepository.terrain` directly.
- **`terrain_types`' JSON keys are stringified ints** (`"0"`, `"1"`, ...), not native ints — a
  frontend consumer must index by `String(code)`, not `code`, when looking up a `present_map` grid
  value's meaning. Documented in Steps 4 and 7.
- **`dictionary_version` is a known, accepted limitation, not a bug**: because it's derived purely
  from `CatalogRepository._compute_fingerprint()` (catalog-content-only), it will *not* change if a
  different world with a different terrain-value distribution is loaded, even though `terrain_types`'
  actual payload would differ for that world. This matches investigation.md's Secondary Open Question
  and this project's existing pattern of disclosed, honest limitations — it must be called out in the
  parity ledger entry (Step 10), not silently left unstated.
- **`location_types` is dropped, not deferred silently**: the field is omitted from the JSON response
  entirely (no empty-dict placeholder), with the rationale in a code comment
  (`manifest_presenter.py`) and in `docs/engine/contracts/frontend.md` §2A (Step 9). If a future
  ticket adds a real `LocationDefinition` registry, this decision should be revisited then — not
  worked around by adding an empty registry in this ticket.
- **`CatalogRepository` has no other live-process writer to race with**: every existing instantiation
  site (`content_semantics/faction.py`, `worldbuilding/cli.py`, `engine/behavior_consumers.py`,
  `content/warmup.py`, `runtime/bootstrap.py`, `core/modes.py`, `core/registries.py`) constructs its
  own short-lived local instance and never touches the new `dependencies.py` singleton — there is no
  double-load or concurrent-mutation risk introduced by Step 2's startup load.
- **`WORLD-CAT-004` hot-path law**: `CatalogRepository.load_all()` raises `ContentHotPathViolation` if
  called while a kernel tick is active on the *same thread* (`src/content/repository.py:21-23`'s
  `_tick_context_active` is a `threading.local()`, and `:229-237`'s check reads it). Step 2's
  `load_all()` call runs on the `lifespan()`/event-loop thread, while the kernel's own tick loop runs
  on the separate background thread `manager.start()` spawns (`engine_manager.py:236-245`) — so this
  guard cannot fire for Step 2's call regardless of ordering relative to `manager.start()`. Do not,
  however, add any future call to `catalog.load_all()` from inside a route handler or any code that
  could run on the kernel's own tick thread — that is the actual scenario this law guards against.

## Deviations

All 10 steps landed as planned, with one deviation in Step 8, discovered only during
implementation (not knowable from a plan-time read):

- **Step 8 (`useSimulation.ts`)**: the plan's literal wording said to store the fetched `Manifest`
  value via `useState` "but do not wire it into any rendering/color logic." Implementation
  additionally added `manifest` to the `SimulationState` interface and to the hook's returned object
  — the same treatment every other `loadInitial()`-fetched value (`mapData`, `buildings`,
  `resourceNodes`, `treasureChests`, `regions`, ...) already receives. This was not optional:
  `frontend/tsconfig.app.json` sets `noUnusedLocals: true`, and a `useState` value whose getter is
  never read anywhere in the file fails `tsc` compilation with `TS6133` ("declared but its value is
  never read"). Returning a value from the hook is exposing/storing state — consistent with the
  plan's own "mirroring how `mapData`/other `loadInitial` results are already stored as state in this
  hook" instruction — not the rendering/color-logic wiring the plan's scope guard forbids. The scope
  guard's actual target (not consuming `manifest.terrain_types`/`entity_kinds`/`building_types` in
  `colors.ts` or `GameCanvas.tsx` to replace their hardcoded maps) is fully respected: neither file
  was touched, and no component reads `manifest` off the hook's return value yet.
