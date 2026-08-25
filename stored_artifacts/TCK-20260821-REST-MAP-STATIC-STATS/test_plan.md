---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260821-REST-MAP-STATIC-STATS
artifact_type: test_plan
tags: [api-design, engine]
---

# Test Plan — TCK-20260821-REST-MAP-STATIC-STATS

## Regression Surface

Existing tests that must keep passing, grouped by category:

**Unit (`tests/unit/api/`)**
- `tests/unit/api/test_state_presenter.py` — 9 existing tests for `present_map`/`present_static`
  (added by `TCK-20260821-PRESENT-MAP-STATIC`). This ticket does not change either method's logic,
  only wraps them in routes — these must stay green unmodified. If `terrain_code_map`/`present_map`/
  `present_static` gain any new call sites (e.g. a combined stats presenter reusing
  `terrain_code_map`), re-run this file explicitly to confirm no signature drift.
- `tests/unit/api/test_economy_route.py` — the route/presenter unit-test pattern precedent this
  ticket's new tests should mirror; not modified, but its `_make_app_with_state`/`MagicMock`-manager
  helper pattern is the template for the new tests below.
- `tests/unit/api/test_engine_manager.py` — existing `V2EngineManager` liveness/health tests
  (`is_thread_alive`, `get_health_status`, real-background-thread pattern). Must stay green after
  adding `_total_spawned`/`_total_deaths` counters and the tick-loop diff — these tests exercise
  `start()`/`stop()`/`_run_loop` indirectly, so any regression in the tick loop's control flow would
  likely surface here too.
- `tests/unit/api/test_dependencies.py` — DI singleton pattern tests (added by
  `TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT`). Not touched by this ticket (no new DI singleton is
  being added — `map`/`static`/`stats` reuse the existing `get_engine_manager()`), included for
  completeness since it lives in the same directory being touched.
- `tests/unit/api/test_read_model_cache.py`, `tests/unit/api/test_read_model_service.py` — adjacent
  read-model-layer tests; not touched, included as an adjacency guard against accidental import-time
  side effects from new route/presenter modules.

**Integration / API (`tests/api/`)**
- `tests/api/test_rest_parity.py::test_api_rest_parity` — **this is the test the AC requires new
  assertions be added to** (not a new subprocess test). Must still pass its existing `/health`,
  `/api/v1/state`, `/api/v1/control/pause`, `/api/v1/control/resume` assertions unmodified, plus the
  new `/api/v1/map`, `/api/v1/static`, `/api/v1/stats` assertions appended in the same `try:` block
  against the same running server instance.
- `tests/api/test_rest_parity.py::test_api_compression` — unmodified, boots the same server binary;
  confirms the new routes don't break server startup (gzip middleware, lifespan) even though it
  doesn't directly hit the new endpoints.
- `tests/api/test_manifest_api.py` — sibling ticket's route tests (12 tests); not modified, included
  as an adjacency guard since `manifest.py`'s router registration sits immediately before where the
  new routers will be added in `server.py`.
- `tests/architecture/test_api_read_model_guard.py::test_no_api_route_directly_imports_authoritative_state`
  — **must pass with the new route file(s) in scope**. This is the primary architecture gate for this
  ticket: the new `src/api/routes/map.py`/`static.py`/`stats.py` (or combined file) must not import
  `AuthoritativeState`/`EntityState` outside `TYPE_CHECKING`.

## New Tests Required

Per acceptance criteria, one entry per required new test:

1. **`test_map_endpoint_returns_200_with_rle_shape`**
   - Category: unit (route-level, `TestClient`, mocked `V2EngineManager`)
   - Verifies: `GET /api/v1/map` returns 200 with `{width, height, grid}`, `grid` is a flat
     `List[int]`, values match a hand-constructed `AuthoritativeState.terrain` fed through the mock.
   - Location: `tests/unit/api/test_map_route.py` (new file, mirrors `test_economy_route.py`'s
     `_make_app_with_state` pattern).

2. **`test_map_endpoint_returns_503_when_state_none`**
   - Category: unit
   - Verifies: `GET /api/v1/map` returns 503 when `manager.latest_state is None` (AC explicit
     requirement — `present_map(None)` would otherwise raise `AttributeError` uncaught, per the
     investigation's finding that the presenter methods have no internal `None` guard).
   - Location: `tests/unit/api/test_map_route.py`.

3. **`test_static_endpoint_returns_200_with_static_data_shape`**
   - Category: unit
   - Verifies: `GET /api/v1/static` returns 200 with `buildings`/`resource_nodes`/`treasure_chests`/
     `regions` keys, each a list, sourced only via `StatePresenter.present_static` (assert response
     body matches `StatePresenter.present_static(state)` called directly on the same fixture state —
     the "never raw AuthoritativeState fields" AC is verified by shape equality against the known
     presenter contract, same technique `test_economy_route.py::test_economy_presenter_shapes_correctly`
     uses: assert no field has `model_dump`/raw-object leakage).
   - Location: `tests/unit/api/test_static_route.py` (new file).

4. **`test_static_endpoint_returns_503_when_state_none`**
   - Category: unit
   - Verifies: same 503-on-`None`-state requirement as `/map`.
   - Location: `tests/unit/api/test_static_route.py`.

5. **`test_stats_endpoint_returns_200_with_expected_fields`**
   - Category: unit
   - Verifies: `GET /api/v1/stats` returns 200 with exactly `{tick, world_day, alive_count,
     total_spawned, total_deaths, running, paused}` (AC's literal field list — assert both presence
     and no extra/missing keys), correct types (`int`/`int`/`int`/`int`/`int`/`bool`/`bool`).
   - Location: `tests/unit/api/test_stats_route.py` (new file).

6. **`test_stats_alive_count_excludes_dead_entities`**
   - Category: unit
   - Verifies: `alive_count` reflects `combat.alive`-filtered entities, not `len(state.entities)` —
     construct a mock/fixture state with one alive + one `combat.alive=False` entity (mirrors
     `test_economy_route.py::test_presenter_excludes_dead_entities`'s technique) and assert
     `alive_count == 1`, matching the ported V1 semantics documented in investigation.md.
   - Location: `tests/unit/api/test_stats_route.py`.

7. **`test_stats_world_day_derivation`**
   - Category: unit
   - Verifies: `world_day` is computed consistently with whatever divisor the implementation settles
     on for the investigation's flagged open question (`tick // 2400` recommended, per Mechanics
     Bible §1 "1 Day = 2400 ticks" — `docs/mechanics/05_world_evolution.md`). This test should assert
     the *documented* value directly (e.g. `state.tick = 4800` → `world_day == 2` if `2400` is chosen)
     so a silent later change to the divisor is caught as a real regression, not silently passed by a
     looser assertion.
   - Location: `tests/unit/api/test_stats_route.py`.

8. **`test_engine_manager_total_spawned_incremented_on_new_entity`**
   - Category: unit (architecture/behavior guard on `V2EngineManager`, not a route test)
   - Verifies: after a tick in which `state.entities` gains an id not present the prior tick,
     `manager._total_spawned` increases by exactly the count of new ids. Given the investigation's
     finding that `RaidService`'s real spawn cadence (every 500 ticks) is too slow for a fast unit
     test, this test should drive the diff-and-increment code path directly rather than running the
     real background loop to a real raid tick — e.g. by calling the extracted diff/increment method
     (or by monkeypatching `self._kernel.tick_once`/`self._kernel.state` between two manual
     `_run_loop`-equivalent steps) with a controlled before/after `state.entities` key set. The exact
     mechanism depends on how the implementer structures the diff (see plan.md), but the test must
     exercise the real counter-increment code path, not reimplement the diff logic independently in
     the test itself (which would test the test, not the implementation).
   - Location: `tests/unit/api/test_engine_manager.py` (existing file — add alongside the existing
     liveness/health tests).

9. **`test_engine_manager_total_deaths_incremented_on_removed_entity`**
   - Category: unit
   - Verifies: same as above, for `_total_deaths`, driven by an id present before and absent after.
   - Location: `tests/unit/api/test_engine_manager.py`.

10. **`test_engine_manager_reset_zeroes_spawn_death_counters`**
    - Category: unit
    - Verifies: after incrementing both counters (via the same direct-drive technique as tests 8/9),
      calling `manager.reset()` returns both to `0`. This is the AC's explicit "reset to 0 after
      `V2EngineManager.reset()`" requirement, and directly guards against the investigation's flagged
      hazard (`_build()` alone does not re-zero arbitrary instance attributes — `reset()` must
      explicitly zero them).
    - Location: `tests/unit/api/test_engine_manager.py`.

11. **`test_stats_counters_non_decreasing_across_ticks`**
    - Category: unit
    - Verifies: the AC's "counters non-decreasing across ticks" property — run two or three
      controlled diff-drive steps (same technique as tests 8/9) and assert
      `total_spawned`/`total_deaths` never decrease between reads, only increase or stay flat.
    - Location: `tests/unit/api/test_engine_manager.py`.

12. **New `/api/v1/map`, `/api/v1/static`, `/api/v1/stats` assertions in `test_api_rest_parity`**
    - Category: integration (end-to-end, real subprocess server)
    - Verifies: each of the three new routes responds 200 with the top-level expected keys present
      (`width`/`height`/`grid` for map; `buildings`/`resource_nodes`/`treasure_chests`/`regions` for
      static; `tick`/`world_day`/`alive_count`/`total_spawned`/`total_deaths`/`running`/`paused` for
      stats) against the real running server — a smoke-level end-to-end check that the routes are
      actually registered and wired, not exhaustive shape validation (that's tests 1-7 above).
    - Location: `tests/api/test_rest_parity.py::test_api_rest_parity` (append to existing function
      body, per the AC's explicit instruction — do not create a new subprocess-spinning test).

13. **`test_no_api_route_directly_imports_authoritative_state` — architecture guard, unmodified but
    must be re-run**
    - Category: architecture guard
    - Verifies: the new route file(s) (`src/api/routes/map.py`, `static.py`, `stats.py` or combined)
      import neither `AuthoritativeState` nor `EntityState` outside `TYPE_CHECKING`. No new test code
      needed — this existing test (`tests/architecture/test_api_read_model_guard.py`) automatically
      covers any new file under `src/api/routes/`.

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/unit/api/ tests/architecture/test_api_read_model_guard.py -v
.venv/bin/python3 -m pytest tests/api/test_rest_parity.py -v
.venv/bin/python3 -m pytest tests/api/test_manifest_api.py -v
```

The first command covers all new unit-level presenter/route/engine-manager tests plus the
architecture guard, fast and hermetic (no subprocess). The second command runs the extended
`test_rest_parity.py` — note it boots a real server subprocess via `python3 -m src serve` and has a
known, pre-existing, environment-only failure mode when invoked with a bare `python3` lacking
`pydantic` on `PATH` (documented in `tickets/done/TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT.md`'s Test
Summary) — run with `PATH=.venv/bin:$PATH` prefixed, or invoke via `.venv/bin/python3 -m pytest`
directly, to avoid a false failure unrelated to this ticket's changes. The third command is an
adjacency regression check on the immediately-preceding sibling route.

Never: `pytest tests/` (full suite) — all commands above are scoped to the API domain this ticket
touches, per the Testing Rule.

## Anti-Drift Test Guards

- **`tests/unit/api/test_state_presenter.py` staying green unmodified** is itself an anti-drift guard:
  it proves this ticket did not alter `present_map`/`present_static`'s logic, only added routes that
  call them — any diff to that test file signals scope creep back into ticket 1's already-closed
  territory.
- **Test 2/4 (503-on-`None`-state for `/map`/`/static`)** guards against the easy mistake of calling
  `StatePresenter.present_map(manager.latest_state)` without a `None` check first — since the
  presenter methods themselves have no internal guard (confirmed in investigation.md), skipping the
  route-level check would surface as an unhandled 500 in production instead of a clean 503, and this
  test would catch that regression immediately.
- **Test 6 (`alive_count` excludes dead entities)** guards against a silent simplification to
  `len(state.entities)` that would happen to pass today (per the apply-path removing dead entities the
  same tick) but would diverge from the documented, ported V1 semantics the moment that apply-path
  behavior ever changes (e.g. if a future ticket introduces a "dying" grace-tick state that keeps a
  dead entity in `state.entities` for one more tick before removal).
- **Test 7 (`world_day` derivation)** guards against silently defaulting to V1's `tick // 100` (or
  `RaidService.TICKS_PER_DAY`'s coincidentally-matching `100`) instead of the Mechanics-Bible-correct
  `tick // 2400` — since both produce plausible-looking small integers for small tick counts, only an
  explicit, documented-divisor assertion at a tick count that clearly distinguishes them (e.g.
  `tick=4800` gives `world_day=48` under `//100` vs. `world_day=2` under `//2400`) will catch a wrong
  choice.
- **Test 10 (`reset()` zeroes counters)** guards against exactly the failure mode investigation.md
  flags: adding the counters in `__init__` but forgetting the explicit re-zero in `reset()`, which
  `_build()` alone does not provide (confirmed `_build()` never touches `_errors_total` either — the
  same latent gap already exists for that counter, so this is a demonstrated real failure shape in
  this class, not a hypothetical).
- **The `test_api_rest_parity` extension (test 12) staying inside the existing `try:`/`finally` block
  of one running server instance** guards against the ticket accidentally introducing a second,
  redundant subprocess-boot test — the AC is explicit that this is disallowed, and a reviewer/gate
  should treat a new subprocess-spinning test file as a direct AC violation, not just a style
  nitpick.
- **`/api/v1/speed` and `/api/v1/clear_events` must not appear in any new test** — their absence from
  every new test listed above is itself the scope-creep guard; a new test asserting either route's
  existence or 200/404 status would signal the ticket drifted into explicitly Out-of-Scope territory.
