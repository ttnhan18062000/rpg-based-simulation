---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT
artifact_type: investigation
tags: [api-design, content]
---

# Investigation — TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT

## Search-Before-Grep Compliance

`mcp__knowledge-search__search_docs` (query: "manifest endpoint terrain entity building id lookup
CatalogRepository") and `graphify query "manifest endpoint catalog repository terrain entity
building"` were both called first, per CLAUDE.md's hard rule, before any grep/read. Both are
unavailable in this worktree, matching every other ticket investigated in this session:
`search_docs` → `{"error":"index not found","action":"run make knowledge-index"}`; `graphify query`
→ `error: graph file not found: .../graphify-out/graph.json` (no `graphify-out/` exists in this
worktree). Fell through to the documented fallback: `tickets/`, `docs/`, `stored_artifacts/` /
`docs/REGISTRY.yaml`, and direct source reads.

## Current Behavior

### `src/api/server.py` — no manifest route, no CatalogRepository wiring anywhere in the API layer

`create_v2_app()` registers routes two ways: `app.include_router(...)` for `src/api/routes/*.py`
modules, and direct `@app.get`/`@app.post` decorators inline in `server.py` (e.g. `/api/v1/state`,
`/api/v1/entities`, `/api/v1/control/pause`). No route named `manifest` exists anywhere (confirmed:
`grep -rn manifest src/api/` returns zero hits). `src/api/dependencies.py` holds three module-level
singletons with a `set_x`/`get_x` pair each: `_engine_manager`, `_quality_hub`,
`_quality_persistence` — the `lifespan()` context manager in `server.py` populates them at startup
(`set_engine_manager(manager)`, `set_quality_hub(...)`). **No fourth singleton for
`CatalogRepository` exists.** Confirmed via `grep -rn CatalogRepository src/api/` → zero hits inside
`src/api/` today. The ticket's own scope note ("Wire CatalogRepository into the FastAPI DI graph —
new plumbing, no existing route does this today") is accurate, not a formality.

### `src/content/repository.py` — `CatalogRepository`, no persistent server-process instance exists yet

`CatalogRepository.terrain/.entity_archetypes/.buildings` are each `Dict[str, XxxDefinition]`, keyed
by the catalog `id` field (`data/content/world/terrain.yaml`, `entities/entity_archetypes.yaml`,
`world/buildings.yaml`), each definition also carrying `display_name: Optional[str]`. `load_all()`
walks `CANONICAL_FAMILIES`, parses YAML under `data/content/`, and populates these dicts;
`_compute_fingerprint()` (called at the end of `load_all()`) SHA-256-hashes the sorted, serialized
`raw_data` into `self._fingerprint` (exposed via the `.fingerprint` property) — this is exactly the
value the ticket's AC names for `dictionary_version`. `self._version = "2.0.0"` is a fixed literal
(`.version` property) — a plausible `protocol_version` source, though it is a hardcoded string with
no independent bump mechanism today (bumping it would require a manual code edit, not an automatic
derivation the way `.fingerprint` is).

Searched every current instantiation site (`grep -rln "CatalogRepository(" src/`):
`content_semantics/faction.py`, `worldbuilding/cli.py`, `engine/behavior_consumers.py`,
`content/warmup.py`, `runtime/bootstrap.py`, `core/modes.py`, `core/registries.py`. Every one of
these either constructs a short-lived local `CatalogRepository` to feed a one-shot adapter/warmup
call, or (in `core/registries.py`'s bootstrap path) copies only `.fingerprint` out to a module-level
`catalog_fingerprint` global before the repo object itself goes out of scope. **No code path in this
codebase keeps a `CatalogRepository` instance alive and reachable for the life of the running API
server process.** `V2EngineManager` (`src/api/engine_manager.py`) has no `catalog`/`content_repo`
attribute (`grep -n "self\.\(kernel\|catalog\|content\)" src/api/engine_manager.py` → zero hits).
Building this route genuinely requires new startup-time plumbing (load once in `lifespan()`, store
via a new `set_catalog_repository`/`get_catalog_repository` pair in `dependencies.py`, mirroring the
exact existing `set_engine_manager`/`get_engine_manager` and `set_quality_hub`/`get_quality_hub`
pattern already in that file) — not a lookup of something already wired.

### `src/api/presenters/state_presenter.py` — `present_map`'s terrain codes are NOT catalog-sourced

`present_map(state)` (added by `TCK-20260821-PRESENT-MAP-STATIC`, done) RLE-encodes `state.terrain`
using `_terrain_code_map(state)`:
```python
return {t: i for i, t in enumerate(sorted(set(state.terrain.values())))}
```
This assigns int codes `0..n-1` over the alphabetically-sorted **distinct terrain-type strings
actually present in the currently-loaded `AuthoritativeState.terrain` dict** — computed fresh on
every call, entirely independent of `CatalogRepository.terrain`. This is the load-bearing fact for
this ticket's "align terrain_types id-space with present_map's encoding" AC — see **Risks and Open
Questions** below for why this makes a purely catalog-sourced `terrain_types` dict insufficient.

`present_static(state)` similarly derives `building.building_type`/`resource_node.resource_type`
directly from `BuildingState.kind`/`ResourceNodeState.kind` (raw strings), not through any catalog
lookup.

### `frontend/src/hooks/useSimulation.ts` — no manifest fetch; exact wiring point identified

`loadInitial()` (lines 86–112) is the target `useEffect`:
```ts
const [rawMap, staticData] = await Promise.all([
  fetchJSON<MapData>('/map'),
  fetchJSON<StaticData>('/static'),
]);
```
This is the one-time load, run once on mount — exactly where a third `fetchJSON<Manifest>('/manifest')`
belongs per the AC ("joined into the existing Promise.all alongside `/static`, NOT the 500ms poll
loop"). The 500ms poll loop is a separate `useEffect` (`fallbackPoll`, lines 177–256) fetching
`/stats` and `/state` — confirmed structurally distinct from `loadInitial`, so there is no risk of
conflating the two fetch sites.

**Note**: `useSimulation.ts` already calls `/map` and `/static` today (not `/manifest` — those two
routes don't exist yet either; per `SEQUENCE.md` they land in the sibling ticket
`TCK-20260821-REST-MAP-STATIC-STATS`, not this one). This is expected: per
`docs/plans/live_map_reconnection_epic.md`'s investigation, the frontend was originally built
against V1's real, working API and never updated when V2 replaced it — `useSimulation.ts` calling
routes that don't exist yet is the epic's starting condition, not something this ticket introduces
or must fix beyond its own `/manifest` addition.

### `frontend/src/types/api.ts` — no `Manifest` type exists; not listed in this ticket's Related Code Areas but will need one

Confirmed via grep: no `Manifest`/`TerrainType`/`LocationType` interface exists in `api.ts` today.
`useSimulation.ts` imports its fetch types from `@/types/api` at the top of the file
(`import type { MapData, WorldState, ... } from '@/types/api'`), matching the existing pattern for
every other fetched shape (`MapData`, `StaticData`, `SimulationStats`). A `Manifest` interface will
need to be added there for the new `fetchJSON<Manifest>('/manifest')` call to type-check. This file
is **not** in the ticket's own `## Related Code Areas` list (only `useSimulation.ts`, `colors.ts`,
`GameCanvas.tsx` are listed among frontend files, and the latter two are explicitly Out of Scope) —
flagged as a gap for the plan to account for; it is a plain type-declaration file, not a UI
component, so touching it does not cross the ticket's stated `colors.ts`/`GameCanvas.tsx` boundary.

### `frontend/src/constants/colors.ts` and `GameCanvas.tsx`'s `LOCATION_TYPE_ICONS` — confirms the drift problem, confirms scope boundary is correct

`colors.ts`'s `TILE_COLORS` is a **hardcoded 23-entry int→color map** (0=FLOOR, 1=WALL, 2=WATER, ...,
22=GRAVEYARD) — a completely different id space from both `CatalogRepository.terrain` (10 lowercase
catalog ids: `plain, forest, swamp, cave, mountain, ruin, road, snow, volcanic, river`) and the real
runtime `state.terrain` value set (see below). This confirms the epic's stated problem is real, and
confirms retiring `colors.ts` is correctly out of this ticket's scope — the mismatch is too large to
reconcile as a side effect of adding one endpoint.

`GameCanvas.tsx`'s `LOCATION_TYPE_ICONS` (line 73) is keyed by literal strings (`enemy_camp`,
`resource_grove`, `ruins`, `dungeon_entrance`, `shrine`, `boss_arena`) that match **none** of
`ResourceNodeState.kind`'s real values (`wood_node`, `herb_patch`, etc., confirmed via
`data/content/world_modules/frontier_village_core.yaml`) or `BuildingDefinition` ids
(`shop`, `town_hall`, `blacksmith`, ...). Confirms the ticket's own Assumption: **no
`LocationDefinition`/location-type registry exists anywhere in this codebase** — these are a
purely-frontend semantic layer with zero backend source, not a naming mismatch that a manifest
lookup could paper over.

### `entity_kinds` / `building_types` — confirmed clean 1:1 catalog match (unlike `terrain_types`)

Traced `BuildingState.kind` (`src/core/state.py:1023`) back to `kind=bld_spec.type`
(`src/worldbuilding/compiler.py:331`), and `bld_spec.type` back to real module content
(`data/content/world_modules/frontier_village_core.yaml`'s `buildings: {town_hall: 1, shop: 1, ...}`
dict keys) — these keys are exactly `BuildingDefinition.id` values from `data/content/world/buildings.yaml`
(`shop`, `town_hall`, `blacksmith`, `inn`, `watchtower`, `healer_hut`, `mine_entrance`, `shrine`,
`mage_tower`). `EntityArchetypeDefinition.id` values (`data/content/entities/entity_archetypes.yaml`:
`hungry_wolf`, `alpha_wolf`, `goblin_scout`, ...) follow the same recipe-declares-catalog-id
convention used throughout `src/worldbuilding/`. **`building_types` and `entity_kinds` can be built
as a straightforward `{id: display_name for id, definition in catalog.buildings/.entity_archetypes.items()}`
projection** — no state-dependence, no vocabulary mismatch, unlike `terrain_types` (see below).

## Mechanics / Engine Constraints

None from `docs/mechanics/` — this is a pure API-presentation-layer addition, not a simulation-law
change. One real, directly-applicable engine/architecture constraint:
**`tests/architecture/test_api_read_model_guard.py`** is an AST-based guard forbidding any file
under `src/api/routes/`, `src/api/ws/`, or `src/api/server.py` from importing `AuthoritativeState`/
`EntityState` outside a `TYPE_CHECKING` block. This directly constrains the implementation: because
`terrain_types`' correct id-space requires the live per-state terrain-code mapping (see Risks below,
not a static catalog-only projection), the manifest route **must** obtain that mapping through
`V2EngineManager`/`StatePresenter` (as every other route already does — e.g. `/api/v1/state` calls
`manager.get_state()`), never by importing `AuthoritativeState` directly into the route file.
`src/api/read_model_service.py`'s `ReadModelService` (`TCK-20260619-E-READ-MODEL`, prior work) is an
existing "unified presenter facade" built for exactly this shape of rule (`M12 Law: API presenters
MUST NOT mutate authoritative state` / all shaping happens through this layer) — worth noting it is
currently **unused in production code** (`grep -rn "ReadModelService(" src/` outside tests → zero
hits; every real route calls `manager.get_*()` directly instead). It is a viable, precedent-consistent
home for a new `content_manifest()` method, not a mandated one — the plan should treat it as an
available option, not proven current practice.

## Docs Requiring Update

- `docs/engine/contracts/frontend.md`: §2A ("Initial Load") documents `useSimulation.ts`'s exact two
  fetch calls in `loadInitial()` (`/api/v1/map`, `/api/v1/static`) as an enumerated list. Once this
  ticket adds a third fetch (`/api/v1/manifest`) to that same `Promise.all`, this enumerated list
  becomes stale/incomplete unless updated to include it.

The `docs/plans/live_map_reconnection_epic.md` roadmap doc (path:
`docs/plans/live_map_reconnection_epic.md`, under `docs/`) is not required to change for this
ticket: per the precedent set by the already-done sibling ticket
`TCK-20260821-PRESENT-MAP-STATIC` (its own investigation.md reached the same conclusion for its
own, closer-to-the-design-doc scope), it is a roadmap/scope-planning artifact, not a living API
reference that gets updated per landed child ticket — its own "Acceptance Signal for This Epic"
section states explicitly that no implementation happens on the epic doc itself.

The `docs/mechanics/content_usage_matrix.md` doc (path: `docs/mechanics/content_usage_matrix.md`,
under `docs/`) is not required to change: its `world/terrain` row documents the
`TerrainDefinition` → `RegionResolver` → `RegionRegistry`/`WorldCompiler` **content-resolution**
pipeline (how terrain content feeds world compilation), which this ticket does not touch or
reinterpret — this ticket only adds a new read-only API projection of already-loaded catalog data,
downstream of that pipeline, not a change to it.

## Parity Ledger Overlap

Grepped all of `docs/parity_ledger/` for `manifest`, `CatalogRepository`, `dictionary_version`,
`protocol_version` — the only `manifest` hits are unrelated file families (replay-run manifests,
certification-harness manifests, agent-monitoring-tooling manifests, `RunManifest.world_id`) with no
overlap to a game-content ID-lookup manifest. **No existing parity ledger entry governs this
endpoint.** No P0 entry is implicated, so this ticket does not need a passing `test_path` to satisfy
an existing entry — but per the Authoritative Mechanics Rule, a new entry should still be added at
Parity phase once implemented (likely `docs/parity_ledger/infrastructure.yaml`, matching where other
API/read-model-shape entries like `TCK-20260619-E-READ-MODEL`'s live), documenting the new
`/api/v1/manifest` contract and its `protocol_version`/`dictionary_version` split.

## Prior Work

- **`TCK-20260821-PRESENT-MAP-STATIC`** (done, this batch, ticket 1 of 8): added
  `StatePresenter.present_map`/`present_static`/`_terrain_code_map` — the exact terrain-code
  mechanism this ticket's `terrain_types` must align with. See its
  `stored_artifacts/TCK-20260821-PRESENT-MAP-STATIC/investigation.md` for the full terrain-code
  design rationale (no fixed terrain enum exists in this codebase; codes are a deterministic,
  per-call, alphabetically-sorted mapping over whatever terrain strings are actually present).
- **`TCK-20260619-E-READ-MODEL`** (`docs/REGISTRY.yaml`-matched via `related_code_areas` overlap on
  `state_presenter.py`/`read_model_cache.py`): introduced `ReadModelService` as the unified
  presenter facade and `tests/architecture/test_api_read_model_guard.py` as its enforcement guard —
  both directly relevant to where this ticket's manifest-building logic should live (see Mechanics /
  Engine Constraints above).
- **`TCK-20260630-SIMQ-WIRE-SERVER`** / **`TCK-20260701-SIMQ-KERNEL-WIRE`** (registry-matched via
  `server.py`/`dependencies.py` overlap): both wired a new singleton (`QualityHub`) into the exact
  `set_x`/`get_x` `dependencies.py` pattern this ticket needs to replicate for `CatalogRepository` —
  direct, reusable precedent for the new DI plumbing.
- No prior ticket in the registry or `tickets/done/` addresses an ID-to-meaning manifest endpoint,
  `dictionary_version`/`protocol_version` versioning, or a `location_types` registry — this is
  genuinely new ground within the codebase's existing patterns, not a duplicate of past work.

## Risks and Open Questions

**The central open question — `terrain_types`' id-space cannot be a plain, static, catalog-sourced
dict without breaking the AC that it must "match present_map's grid encoding."** Traced concretely,
not assumed:

- `CatalogRepository.terrain` keys are the catalog's own lowercase ids: `plain, forest, swamp, cave,
  mountain, ruin, road, snow, volcanic, river` (from `data/content/world/terrain.yaml`).
- Real world-module content (`grep -rhn "terrain:" data/content/world_modules/*.yaml`) declares
  terrain as lowercase strings drawn from that same set (`"plain"`, `"forest"`, `"swamp"`, `"cave"`,
  `"mountain"`, `"ruin"`, `"road"`, `"river"` — confirmed across all `world_modules/*.yaml` files
  that declare an explicit `terrain:` field) — these do line up with the catalog.
- **But** `src/worldbuilding/recipe.py:16`'s `RegionRecipeSpec.terrain` field defaults to `"GRASS"`
  (uppercase) when a region doesn't declare one explicitly, and `src/worldbuilding/compiler.py:205`
  pre-fills the **entire** world grid with `"PLAIN"` (uppercase) before any region painting happens
  — confirmed via direct read of `compiler.py:200-234`. **Neither `"GRASS"` nor `"PLAIN"` exists as a
  `CatalogRepository.terrain` key** (the catalog only has lowercase `"plain"`, no `"grass"` entry at
  all). Confirmed via `tests/unit/api/test_state_presenter.py`'s own test fixtures, which use exactly
  `"PLAIN"`/`"GRASS"` as terrain values — these are not edge-case inputs, they are the actual
  real-world default/background terrain values, likely covering the majority of tiles in any
  compiled world (every tile outside an explicitly-painted region, plus every region that doesn't
  declare its own `terrain:`).
- Confirmed no runtime mutation of `state.terrain` after world-compile time (`grep -rn
  "\.terrain\[" src/` outside `compiler.py` → zero hits) — so the value set is stable for the life
  of one loaded world, but that stable value set is **world-content-dependent, not catalog-content-
  dependent**, and includes values (`"PLAIN"`, `"GRASS"`) that have no catalog counterpart at all.

**Consequence**: `present_map`'s int codes are assigned over `sorted(set(state.terrain.values()))` —
a per-loaded-world, non-catalog value space that includes uncataloged uppercase defaults. A
`terrain_types` dict built as `{catalog_id: display_name for catalog_id, definition in
catalog.terrain.items()}` (the literal reading of AC #2, "populated LIVE from
`CatalogRepository.terrain`") would (a) use the wrong key space entirely — string catalog ids, not
`present_map`'s int codes — failing AC #5 ("terrain_types id-space matches... present_map's grid
encoding"), and (b) even if re-keyed by int code via `StatePresenter._terrain_code_map`, would have
no display-name source for `"PLAIN"`/`"GRASS"` codes, since neither exists in the catalog at all.
**This is a real, unresolved design decision the plan must make explicitly, not a wiring detail**:
whichever of the two approaches below is chosen, it needs a documented fallback for
catalog-lookup-miss terrain strings (e.g. title-casing the raw string, matching the exact precedent
`present_static` already set for building/resource-node `name` derivation: `b.kind.title()`).
Two concrete options, not mutually exclusive with each other in principle:
1. Key `terrain_types` by the same int codes `present_map` emits (requires calling
   `StatePresenter._terrain_code_map(state)` against live state at request time, not a pure
   catalog-only projection — this is why the manifest route needs access to `V2EngineManager`, not
   just `CatalogRepository`, for at least this one field), with `display_name` resolved via a
   case-insensitive catalog lookup that falls back to `title()`-casing the raw string on a miss.
2. Key `terrain_types` by the raw terrain string itself (not an int), sidestepping the int-alignment
   AC's literal wording but requiring the frontend to key its terrain lookup by string instead of by
   `present_map`'s int grid value — which would defeat the purpose of `present_map` using compact
   int codes in the first place, so this reads as the weaker option.

This is exactly the ambiguity the ticket's own "Assumptions / Open Questions" section flagged as
unresolved until `PRESENT-MAP-STATIC` landed ("terrain id-space alignment depends on which choice
the present_map ticket actually makes... not fully known until that ticket lands") — it has now
landed, and the answer this investigation surfaces is that the two ACs (LIVE-from-catalog,
matches-present_map's-encoding) are **not simultaneously satisfiable by a purely-static,
catalog-only `terrain_types` dict** — the plan must pick and document one of the two approaches
above (or an equivalent) rather than treating this as settled.

**Secondary, lower-stakes open question**: since `terrain_types`' effective content (per option 1
above) depends on which world/state is currently loaded, not on `CatalogRepository`'s own content,
`dictionary_version` (derived purely from `CatalogRepository._compute_fingerprint()`, per the AC)
would **not** change if a different world with a different terrain-value distribution were loaded,
even though the manifest's actual `terrain_types` payload would differ. This is a real version-
coherency edge case worth the plan documenting as an accepted limitation (matching this project's
existing pattern of disclosed, honest limitations over invented completeness — e.g.
`docs/parity_ledger/infrastructure.yaml`'s own disclosed-limitation entries) rather than silently
leaving unstated.

**`location_types` decision is genuinely open, not pre-decided**: confirmed no
`LocationDefinition`/location registry exists anywhere in `src/content/schema.py` or
`src/content/repository.py` (only `RuntimeRegionDefinition` exists under "World", a different
concept — danger/travel-cost metadata per region, not a POI/location type registry).
`GameCanvas.tsx`'s `LOCATION_TYPE_ICONS` is the only place this vocabulary exists at all, and it is
explicitly out of this ticket's file boundary. The ticket's own Scope already frames this correctly
as "decide new minimal registry entry vs. explicitly dropping the field, document the decision" —
this investigation found no new information that resolves it either way; it remains an
implementation-time judgment call for the plan to make and document (not to defer further).

## Anti-Drift Hazards

- **Do not silently expand this ticket into fixing the `"PLAIN"`/`"GRASS"` uncataloged-default
  problem in `compiler.py`/`recipe.py`.** That is a real, adjacent gap (found above) but changing
  `RegionRecipeSpec`'s default terrain value or `compiler.py`'s fill logic is a durable-state/
  world-compile change, well outside this ticket's stated Scope (API-only) and outside
  `TCK-20260821-PRESENT-MAP-STATIC`'s already-closed scope too. The manifest's job is to represent
  reality (including the uncataloged defaults via a documented fallback), not to fix reality.
- **Do not build `terrain_types` as a naive static `CatalogRepository.terrain` passthrough** — see
  Risks above; this would silently produce a manifest whose keys don't correspond to any value
  `present_map`'s grid ever emits, defeating the endpoint's stated purpose (AC #5 would be violated
  even though AC #2's literal wording would appear satisfied).
- **Do not touch `frontend/src/constants/colors.ts` or `frontend/src/components/GameCanvas.tsx`** —
  both explicitly Out of Scope; retiring the hardcoded color maps is a stated fast-follow.
- **Do not build a `location_types` registry beyond the minimal decision the ticket scopes** — the
  Out of Scope section is explicit that anything beyond the documented drop-vs-minimal-registry
  decision is out of bounds for this ticket.
- **Do not skip adding a `Manifest` type to `frontend/src/types/api.ts`** just because that file
  isn't named in `## Related Code Areas` — it is a necessary, in-boundary addition (plain type
  declarations, not a UI component) for `useSimulation.ts`'s new fetch call to type-check against
  the project's existing pattern (every other fetched shape has a corresponding `api.ts` interface).
- **Do not instantiate a fresh `CatalogRepository` and call `load_all()` per-request** inside the new
  route handler — this re-reads and re-parses every YAML file under `data/content/` on every single
  `/api/v1/manifest` call. Load once at server startup (in `lifespan()`, alongside
  `set_engine_manager(manager)`) and store it via the new DI singleton, matching every existing
  precedent in `dependencies.py`.
