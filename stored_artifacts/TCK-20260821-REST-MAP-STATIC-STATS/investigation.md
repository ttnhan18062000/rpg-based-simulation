---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260821-REST-MAP-STATIC-STATS
artifact_type: investigation
tags: [api-design, engine]
---

# Investigation — TCK-20260821-REST-MAP-STATIC-STATS

## Context Scan (mandatory tools, both unavailable — documented before falling through)

- `mcp__knowledge-search__search_docs` was called first, per the Hard Rule, query `"REST route map
  static stats presenter live map reconnection"`. Result: `{"error": "index not found", "action":
  "run make knowledge-index"}` — the semantic index has not been built in this worktree.
- `graphify query "map static stats REST endpoint"` was attempted next. Result: `error: graph file
  not found: .../graphify-out/graph.json` — no graph has been built in this worktree either.
- Both confirmed unavailable exactly as the dispatch prompt stated. Fell through to the documented
  fallback: direct reads of `tickets/inprogress/TCK-20260821-REST-MAP-STATIC-STATS.md`,
  `tickets/done/TCK-20260821-PRESENT-MAP-STATIC.md`, `tickets/done/TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT.md`,
  `docs/plans/live_map_reconnection_epic.md`, and the source files below. No `docs/REGISTRY.yaml`
  exists in this worktree either (checked), so the "Finding Prior Work" fallback path (scan
  `tickets/done/` by name similarity, then `stored_artifacts/{ticket_id}/`) was used instead of the
  registry-query path.

## Current Behavior

**Route registration pattern** (`src/api/server.py::create_v2_app`, lines ~100-131): every router is
registered via `app.include_router(<module>.router, prefix="/api/v1", dependencies=[Depends(require_admission)])`
inside `create_v2_app`, in a fixed sequence (`stream`, `history`, `search`, `behavior`, `decisions`,
`scenarios`, `campaigns`, `chronicle`, `economy`, `manifest`, then `quality_routes`). A new `map`/
`static`/`stats` router (or one combined router) needs the same registration line added after
`manifest` (the most recently added one).

**`src/api/routes/economy.py` and `src/api/routes/manifest.py`** (both read in full) are this
project's two clean route-file precedents: `APIRouter(tags=[...])`, no `Depends()` injection for the
manager/catalog (direct `get_engine_manager()`/`get_catalog_repository()` calls inside the handler
body instead — `economy.py` even omits `Depends` from its handler signature entirely), `response_model=Dict[str, Any]`,
`raise HTTPException(status_code=503, ...)` when the required singleton/state is `None`, and the
route body's only job is to call a `Presenter.present_x(state)` static method and return its dict.
Neither route file imports `AuthoritativeState`/`EntityState`.

**`src/api/routes/state.py` is a 0-byte empty file** despite being listed in this ticket's own
Related Code Areas and despite the epic doc citing it as one of the files this epic's child tickets
touch. The real `/api/v1/state`, `/api/v1/control/pause`, `/api/v1/control/resume`, `/api/v1/entities`,
etc. handlers are all defined inline inside `src/api/server.py::create_v2_app` (lines 186-229), not
in a `src/api/routes/*.py` module — `routes/state.py` and `routes/control.py` and `routes/health.py`
are all empty placeholder files with no import/registration anywhere. This is a real gap in the
ticket's own Related Code Areas listing, not something to "fix": there is nothing to read there, and
the actual `/state`/`control/pause`/`control/resume` precedent lives in `server.py` itself, already
covered above.

**`StatePresenter.present_map`/`present_static`** (`src/api/presenters/state_presenter.py:157-261`,
added by `TCK-20260821-PRESENT-MAP-STATIC`, already `@staticmethod`s, already unit-tested by
`tests/unit/api/test_state_presenter.py`, already read in full):
- `present_map(state) -> {width, height, grid}` — RLE-encoded terrain. Returns `{"width": 0, "height":
  0, "grid": []}` when `state.terrain` is empty (i.e. it degrades gracefully on an empty/None-ish
  state rather than raising — no explicit `None`-state guard inside the method itself, it just
  requires `state.terrain` to be a dict, even an empty one).
- `present_static(state) -> {buildings, resource_nodes, treasure_chests, regions}` — same shape, no
  `None`-state guard either.
- Neither method mutates state (verified in ticket 1, re-confirmed by re-reading: only `state.*`
  reads).
- **Both methods require a real `state` argument — they will raise `AttributeError` if called with
  `state=None`** (e.g. `present_map(None)` hits `if not state.terrain` → `AttributeError: 'NoneType'
  object has no attribute 'terrain'`). This is why the AC's "503 when `manager.latest_state` is None"
  requirement must be a route-level guard *before* calling the presenter, exactly like
  `economy.py`'s `if state is None: raise HTTPException(503, ...)` pattern — not something the
  presenter methods themselves already handle.

**`V2EngineManager`** (`src/api/engine_manager.py`, read in full):
- Has **no** `_total_spawned`/`_total_deaths` counters today — confirmed by reading the whole file,
  matching the ticket's own Assumptions note. `_run_loop` (lines 273-301) calls `self._kernel.tick_once()`
  then `self._update_latest_state(self._kernel.state)` then `self._notify_listeners(...)` — this is
  the one place a `alive_before`/`alive_after` set-diff on `state.entities.keys()` can be inserted,
  matching V1's exact pattern (see below).
- `reset()` (line 268) calls `self.stop()` then `self._build()` — a new counter reset (`self._total_spawned
  = 0; self._total_deaths = 0`) belongs here, mirroring V1's `reset()` (which explicitly zeroes both
  counters — `git show 677abbfb^:src_legacy/api/engine_manager.py` lines ~221-222).
- `is_running`/`is_paused` properties (lines 308-314) already exist and are the natural source for
  the `stats` response's `running`/`paused` fields — `is_running = self._running.is_set() and not
  self._paused.is_set()`, `is_paused = self._running.is_set() and self._paused.is_set()`. Note these
  are **not** simple negations of each other (a stopped-and-not-yet-started manager is neither
  running nor paused) — matches the ticket AC's plain `running`/`paused` booleans reasonably as long
  as the implementation picks one consistent definition and doesn't invent a third state.
- `latest_state` property (line 230) is the thread-safe accessor already used by every other route
  (`economy.py`, `manifest.py`) — the new routes should use this, not `get_state()` (which returns
  the *minimal snapshot dict*, not the `AuthoritativeState` object the presenters need).

**V1 reference (`git show 677abbfb^:src_legacy/api/engine_manager.py`, confirmed by direct read)**:
counters are two plain instance ints (`self._total_spawned = 0`, `self._total_deaths = 0`),
incremented in the tick loop via:
```python
alive_before = set(self._loop.world.entities.keys())
can_continue = self._loop.tick_once()
...
alive_after = set(self._loop.world.entities.keys())
new_ids = alive_after - alive_before
dead_ids = alive_before - alive_after
self._total_spawned += len(new_ids)
self._total_deaths += len(dead_ids)
```
This is the exact pattern the ticket's Scope specifies porting. `reset()` zeroes both.

**V1 `/stats` route** (`git show 677abbfb^:src_legacy/api/routes/state.py`, lines 97-110, confirmed
by direct read — there was never a dedicated `stats.py` route file in V1 either, it lived in
`state.py` alongside `/state` and `/static`):
```python
@router.get("/stats", response_model=SimulationStats)
def get_stats(manager: EngineManager = Depends(get_engine_manager)) -> SimulationStats:
    snapshot = manager.get_snapshot()
    tick = snapshot.tick if snapshot else 0
    alive = sum(1 for e in snapshot.entities.values() if e.combat.alive) if snapshot else 0
    return SimulationStats(
        tick=tick, world_day=tick // 100, alive_count=alive,
        total_spawned=manager.total_spawned, total_deaths=manager.total_deaths,
        running=manager.running, paused=manager.paused,
    )
```
`alive_count` is `sum(1 for e in entities.values() if e.combat.alive)` — **not** `len(entities)** —
confirming `alive_count` and `entities_count`/`len(state.entities)` are meant to be different numbers
in principle (an entity could theoretically be in `state.entities` with `combat.alive=False` for one
tick before removal — see Mechanics/Engine Constraints below for whether V2 ever actually holds that
state).

**`EconomyPresenter.present_health`** (`src/api/presenters/economy.py`, spot-read) already does this
exact `if not entity.combat.alive: continue` filtering *inside a presenter*, not inside a route —
this is the established in-repo precedent for where "iterate raw entities and filter by
`combat.alive`" logic must live, directly relevant to how `/api/v1/stats`'s `alive_count` should be
computed (see Anti-Drift Hazards).

**`tests/api/test_rest_parity.py`** (read in full): `test_api_rest_parity` boots the real server as a
subprocess (`python3 -m src serve --port 8002 ...`), then does plain `requests.get`/`requests.post`
calls against `/health`, `/api/v1/state`, `/api/v1/control/pause`, `/api/v1/control/resume`. This is
the exact function the ticket's AC says to extend with new `/api/v1/map`, `/api/v1/static`,
`/api/v1/stats` assertions (adding `requests.get` calls + shape assertions inside the same `try:`
block, same running server instance) — not a new subprocess-spinning test.

**`tests/unit/api/test_economy_route.py`** (read in full) is the established pattern for
route/presenter-level tests that do **not** spin a subprocess: build a bare `FastAPI()` app,
`app.include_router(router, prefix="/api/v1")`, `deps.set_engine_manager(MagicMock(latest_state=state))`,
drive it with `fastapi.testclient.TestClient`. This is the right pattern for the new `map`/`static`/
`stats` route unit tests (200/503 shape checks), separate from the required `test_rest_parity.py`
extension (which is an end-to-end smoke check, not exhaustive shape coverage).

**`tests/unit/api/test_engine_manager.py`** (read in full) is the established pattern for testing
`V2EngineManager` behavior against a **real background thread** (`manager.start()`, poll
`manager._tick_times`, `manager.stop()` in a `finally`), not a mocked kernel. Relevant because a
naive "assert counters increase after spawns/deaths" test cannot rely on the real `RaidService`
spawn cadence (see Risks below) — it will need either a shorter, deterministic path to a spawn/death
event, or to test the diff-and-increment logic more directly (e.g. by driving two consecutive
`_update_latest_state`-equivalent ticks with controlled `state.entities` dicts) rather than waiting
out real raid/combat cadence in real time.

## Mechanics / Engine Constraints

- **`docs/mechanics/05_world_evolution.md` §1 "The Passage of Time"** (Certified Level 1,
  `authority: P0`): `1 Tick = 1`, `1 Hour = 100 ticks`, **`1 Day = 2400 ticks`**. This is the
  authoritative, canonical tick-to-day law. `world_day` for the new `/api/v1/stats` response should
  therefore be derived as `state.tick // 2400` to stay consistent with this law — **not** `tick //
  100` (V1's literal value, see Risks below) and **not** `RaidService.TICKS_PER_DAY = 100` (a
  same-named-but-different, module-local constant scoped only to raid cadence, see below).
- **`src/engine/apply.py:226-232`** confirms the authoritative apply path removes dead entities from
  `state.entities` via `update.entities_remove` / `new_entities.pop(e_id, None)` — i.e. a dead entity
  does **not** linger in `state.entities` with `combat.alive=False` across a tick boundary in the
  normal case; it is removed the same tick it dies (converted to a `CorpseState` elsewhere in the
  apply pipeline, out of scope for this ticket). This means `alive_before - alive_after` (dead_ids)
  and `len(state.entities)` both correctly reflect death, and V1's `alive_count = sum(1 for e in
  entities if e.combat.alive)` (rather than plain `len(entities)`) is likely defensive/legacy caution
  rather than something V2 actually needs distinctly — but since the ticket AC doesn't specify which
  to use and V1's own route used the `combat.alive`-filtered form, the safer choice is to port that
  form exactly (matches the "byte-for-byte port and adapt" epic framing) rather than substitute
  `len(state.entities)`.
- **`src/world/raid.py:19-20`**: `RaidService.RAID_INTERVAL_DAYS = 5`, `TICKS_PER_DAY = 100` — this
  is a **separate, real inconsistency already present in the live V2 codebase**, not introduced by
  this ticket: `RaidService`'s internal "1 day = 100 ticks" does not match Mechanics Bible §1's "1
  day = 2400 ticks" (which governs the actual day/night biological cycle,
  `src/systems/strategic_systems/intelligence.py:541`: `state.tick % 2400`). `RaidService.TICKS_PER_DAY`
  is a private class constant used only for raid-cadence math, not a general-purpose day/tick
  conversion helper — it happens to numerically match V1's `world_day = tick // 100` because V1's
  route literally used the same (V1-era, un-updated-to-2400) 100-tick day length. This ticket should
  **not** attempt to fix `RaidService`'s constant (out of scope — a pre-existing divergence, not
  something this REST-route ticket introduced or was asked to touch) but **should** use the
  Mechanics-Bible-correct `tick // 2400` for the new `/api/v1/stats.world_day` field rather than
  copying V1's `tick // 100` verbatim, since the Mechanics Bible takes precedence over legacy
  behavior per this project's Authoritative Mechanics Rule. Flagged as an open decision for the
  planner/implementer, not resolved unilaterally here (see Risks).
- **`M12 Law`** (`StatePresenter`'s own docstring, `src/api/presenters/state_presenter.py:9`): "API
  presenters MUST NOT mutate authoritative state." Any new stats-computation logic added to
  `StatePresenter` (or a new presenter) must stay read-only, consistent with `present_map`/
  `present_static`.
- **Architecture Rule / API boundary** (`CLAUDE.md`): "API/routes present shaped read models through
  presenters/schemas, not raw domain objects" and "Decision logic reads state. It does not
  authoritatively mutate durable state." The `_total_spawned`/`_total_deaths` counters are
  **non-authoritative manager-level telemetry** (same category as `V2EngineManager._tick_times`,
  `_errors_total`), computed *outside* the authoritative apply/kernel pipeline in `_run_loop` — this
  is architecturally sound (matches V1, matches the existing `_errors_total` pattern) and does not
  touch durable simulation state.
- **`tests/architecture/test_api_read_model_guard.py`**: AST-scans `src/api/routes/`, `src/api/ws/`,
  and `src/api/server.py` for any non-`TYPE_CHECKING` import of `AuthoritativeState`/`EntityState`.
  The new route file(s) must not import either name at module scope. Since `/api/v1/stats`'s
  `alive_count` needs to iterate `state.entities.values()` and read `.combat.alive`, that iteration
  must live in a presenter (or `V2EngineManager` method) that the route calls, not inline in the
  route body — even though the guard is AST-only and would not literally catch inline field access
  without an import, doing it inline in the route would violate the broader "routes present shaped
  read models through presenters" architecture rule the guard test exists to encode. See Anti-Drift
  Hazards.

## Docs Requiring Update

- `docs/engine/contracts/frontend.md`: its "Known gap (2026-07-16)" callout at the top of the file
  currently states `/map`, `/static`, `/stats`, `/speed`, `/clear_events` "none of which exist as
  routes." After this ticket, three of the five (`/map`, `/static`, `/stats`) will exist — the
  callout is now factually wrong for those three and must be narrowed to only the two still-missing
  routes (`/speed`, `/clear_events`, both explicitly Out of Scope for this ticket per its own Scope
  section). §2A ("Initial Load (Full State)") currently lists only two `Promise.all` fetch calls
  (`/api/v1/map`, `/api/v1/static` per the manifest ticket's prior edit, actually three counting
  `/manifest`) — this ticket does not touch `useSimulation.ts`'s fetch wiring itself (frontend rewire
  is epic item 4, a separate, not-yet-created child ticket per `docs/plans/live_map_reconnection_epic.md`),
  so §2A's fetch-call list does not need a new entry for `/stats` (stats is fetched by the *secondary
  slow-poll*, §2C, not `loadInitial()`'s `Promise.all` — confirmed by reading
  `frontend/src/hooks/useSimulation.ts` lines 179-193 directly, `fetchJSON<SimulationStats>('/stats')`
  lives inside the 500ms inspection-poll `useEffect`, separate from `loadInitial()`). Only the "Known
  gap" callout needs editing for this ticket's scope.
- `docs/parity_ledger/infrastructure.yaml`: a new entry is required. `INFRA-210` (added by ticket 1,
  text ends "...StatePresenter's present_map/present_static (TCK-20260821-PRESENT-MAP-STATIC,
  2026-08-24) follow the same shape...") documents the *presenter* half of this work but not the
  *route* half — no existing entry documents `/api/v1/map`, `/api/v1/static`, `/api/v1/stats` as real
  registered routes, nor the new `_total_spawned`/`_total_deaths` counters. The next available ID
  (highest existing is `INFRA-383`, added by ticket 2 for `/api/v1/manifest`) is `INFRA-384`. This
  should follow the exact shape of `INFRA-383` (`test_path: tests/api/test_rest_parity.py` plus the
  new unit test file(s), `status: verified`, priority left to the parity-updater phase to set
  consistently with `INFRA-210`/`INFRA-383` — both are `P1`, and this is the same subsystem, so `P1`
  is the natural default rather than `P2`).

Nothing else requires updating. `docs/mechanics/05_world_evolution.md` (path:
`docs/mechanics/05_world_evolution.md`, under `docs/mechanics/`) is not required to change for this
ticket: its §1 tick-to-day law is being *read* and applied (`tick // 2400`), not changed — this
ticket derives a value consistent with the existing law, it does not alter the law itself. The
`src/world/raid.py`/`TICKS_PER_DAY=100` divergence noted above (path: `src/world/raid.py`) is a
pre-existing, separate issue this ticket did not introduce and is not in this ticket's Scope to fix
or document in `docs/guidelines/intentional_divergences.md` — flagging it in Risks below for
awareness only, not proposing a doc change here.

## Parity Ledger Overlap

- `INFRA-210` (`status: verified`, `priority: P1`) — documents `present_map`/`present_static`
  themselves (the presenter layer this ticket wraps). Not modified by this ticket, but directly
  relevant context: this ticket's new routes are the "wiring" half of what `INFRA-210`'s text already
  calls out as already-compliant with the read-model-only architecture.
- `INFRA-383` (`status: verified`, `priority: P2`, `test_path: tests/api/test_manifest_api.py`) —
  documents `/api/v1/manifest`, the immediately-preceding sibling route this ticket's routes should
  match in registration pattern. Not modified by this ticket.
- No P0 entries in `infrastructure.yaml` overlap this ticket's scope (confirmed by the greps above —
  no existing entry's `text` mentions `/api/v1/map`, `/api/v1/static`, `/api/v1/stats`, or
  `total_spawned`/`total_deaths`).
- A new entry (`INFRA-384`, see Docs Requiring Update) is required once implementation lands.

## Prior Work

- `stored_artifacts/TCK-20260821-PRESENT-MAP-STATIC/` (investigation.md, plan.md, test_plan.md) —
  direct hard dependency, already DONE. Its investigation.md has the full field-level drop-vs-derive
  decision record for `present_static`'s output shape (building name/owner, resource-node
  name/terrain, chest guard/tier/looted, region terrain/difficulty/locations) — this ticket does not
  need to re-derive any of that, it only wraps the already-finished presenter methods.
- `stored_artifacts/TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT/` (investigation.md, plan.md,
  test_plan.md) — the immediately-preceding sibling ticket, establishing the exact route-registration
  pattern (`src/api/routes/manifest.py`, `app.include_router(..., prefix="/api/v1",
  dependencies=[Depends(require_admission)])` in `server.py`) this ticket should replicate for
  `map`/`static`/`stats`.
- `docs/plans/live_map_reconnection_epic.md` — the epic plan; item 3 in its "Scope for the eventual
  `create-tickets` pass" section is this exact ticket, already tracing `total_spawned`/`total_deaths`
  to V1's proven pattern.
- V1 reference implementation, recoverable via `git show 677abbfb^:<path>` — `src_legacy/api/routes/state.py`
  (the real `/stats` handler, and confirmation that `/static` also lived in this same file, not a
  dedicated `static.py`), `src_legacy/api/routes/map.py` (the real `/map` RLE handler, already ported
  by ticket 1 into the presenter), `src_legacy/api/engine_manager.py` (the counter pattern), and
  `src_legacy/api/schemas.py` (`SimulationStats` Pydantic model, confirming the exact 7-field shape
  the ticket's AC already states).

## Risks and Open Questions

- **`world_day` divisor is not specified by the ticket's AC and has three plausible-but-different
  candidate values found in this investigation**: V1's literal `tick // 100`, `RaidService
  .TICKS_PER_DAY = 100` (numerically the same as V1 but a different, raid-scoped constant), and the
  Mechanics Bible's canonical `tick // 2400` (§1, the actual day/night cycle divisor used elsewhere in
  V2). This investigation recommends `tick // 2400` per the Authoritative Mechanics Rule (Mechanics
  Bible takes precedence over legacy behavior in case of ambiguity), but this is a real open decision
  the planner should make explicitly (and record), not silently default to copying V1's number without
  noting the divergence. **Flagged as blocking a clean AC read** — the AC's `world_day` field name
  alone does not disambiguate.
- **The `_total_spawned`/`_total_deaths` counters cannot be trivially tested against a real running
  engine within a fast unit test**: `RaidService` (the only currently-wired source of mid-tick entity
  spawns) fires once every `500` ticks (`RAID_INTERVAL_DAYS(5) * TICKS_PER_DAY(100)`), and deaths
  require actual combat resolution to occur, both too slow/nondeterministic for a fast test running
  the manager's real background thread at its default tick rate. The test_plan below recommends
  testing the diff-and-increment logic directly (constructing two `AuthoritativeState`s with a
  controlled `entities` key-set difference and driving the counter-update code path directly) rather
  than waiting out real spawn/death cadence — this is a real implementation-time decision (whether the
  diff logic is extracted into a small testable helper, or tested by monkeypatching
  `self._kernel.tick_once`/`self._kernel.state` between two `_run_loop` iterations), not something
  this investigation prescribes exactly.
- **`src/api/routes/state.py`/`control.py`/`health.py` being empty stub files** (not created or
  modified by this ticket) is worth flagging in case a future maintainer assumes those files hold live
  route logic — they don't; the real handlers are inline in `server.py`. Out of scope to fix here
  (not part of this ticket's Scope), but noted so the implementer doesn't mistakenly try to "move"
  existing `/state` logic into `routes/state.py` as an unscoped drive-by change.
- **Whether `map`/`static`/`stats` should be three separate route files or one combined file** is not
  specified by the ticket. `economy.py` and `manifest.py` are both single-concern, single-file
  precedents; V1 put `/map` in its own file but `/static` and `/stats` together in `state.py`. Given
  this project's one-router-per-concern pattern (`economy.py`, `manifest.py`, `campaigns.py`, etc.,
  all single-purpose), three separate small files (`src/api/routes/map.py`, `static.py`, `stats.py`)
  most closely matches the established convention and is the recommended approach, but this is a
  planner-level naming decision, not dictated by the ticket text.

## Anti-Drift Hazards

- **Do not implement `/api/v1/stats`'s `alive_count` by iterating `manager.latest_state.entities
  .values()` and reading `.combat.alive` directly inside the route function.** This would still pass
  the AST-only `test_api_read_model_guard.py` check (it scans imports, not attribute access) but
  violates the project's actual architecture rule ("routes present shaped read models through
  presenters/schemas, not raw domain objects") and the established in-repo pattern
  (`EconomyPresenter.present_health` does exactly this filtering *inside a presenter*, never inside
  `economy.py`'s route body). Add the `alive_count` computation to `StatePresenter` (a new method, or
  folded into a combined stats presentation) or to `V2EngineManager` itself, not inline in the route.
- **Do not silently swap V1's `alive_count = sum(1 for e in entities if e.combat.alive)` for
  `len(state.entities)`** without an explicit note — they are very likely equal in V2 given the
  apply-path always removes dead entities the same tick (see Mechanics/Engine Constraints above), but
  since the ticket's own AC just says `alive_count` without defining it, and V1's own route
  deliberately filtered rather than using `len()`, porting the filtered form is the safer,
  lower-drift choice consistent with the "port-and-adapt from a proven reference" epic framing.
- **Do not touch `/api/v1/speed` or `/api/v1/clear_events`** — explicitly Out of Scope on this ticket
  even though both were found in the same original grep that found `/map`/`/static`/`/stats` missing.
  Do not add a generic control dispatcher either (epic item 4, separate ticket, not this one).
- **Do not modify `useSimulation.ts` or any other frontend file** — this ticket's Related Code Areas
  and Scope are backend-only (`src/api/*`); the frontend already calls `/map`, `/static`, `/stats` in
  their expected shapes (confirmed by reading `useSimulation.ts` directly), so no frontend change is
  needed or in scope to make this ticket's routes actually consumed.
- **Do not fix `RaidService.TICKS_PER_DAY`'s divergence from the Mechanics Bible's 2400-tick day** as
  a drive-by — it's a real, separate, pre-existing issue (see Risks), out of this ticket's Scope, and
  fixing it would touch calamity/raid-cadence balance, a different subsystem than this ticket's REST
  wiring.
- **`V2EngineManager.reset()` must zero both new counters** — the AC explicitly requires this
  (mirroring V1). Since `reset()` calls `self._build()` (which reconstructs `self._kernel` and
  `self._latest_state` from scratch), it would be easy to add the counters as instance attributes in
  `__init__` only and forget the explicit re-zero in `reset()` — `_build()` alone does not reset
  arbitrary instance attributes not touched inside it (confirmed by reading `_build()` in full: it
  never resets `_errors_total` either, which is arguably a pre-existing minor gap in the same vein,
  out of scope to fix here, but a useful signal that "reset forgets to zero a counter" is a real,
  already-observed failure mode in this exact class).
