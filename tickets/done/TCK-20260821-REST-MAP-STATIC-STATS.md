---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260821-REST-MAP-STATIC-STATS
phase: done
date: 2026-08-21
tags: [api-design, engine]
---

# TCK-20260821-REST-MAP-STATIC-STATS

## Title
Add /api/v1/map, /api/v1/static, /api/v1/stats REST routes

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Five REST routes the frontend calls do not exist on the real backend at all: /api/v1/map, /api/v1/static, /api/v1/stats, /api/v1/speed, /api/v1/clear_events. The author wants the map/static/stats routes built (wrapping the new presenter methods), including adding total_spawned/total_deaths counters to V2EngineManager, which V1 had but V2 genuinely lacks today.

## Scope
- Add GET /api/v1/map wrapping StatePresenter.present_map
- Add GET /api/v1/static wrapping StatePresenter.present_static
- Add GET /api/v1/stats returning {tick,world_day,alive_count,total_spawned,total_deaths,running,paused}
- Add _total_spawned/_total_deaths counters to V2EngineManager, incremented once per tick via new_ids/dead_ids set-diff (comparing state.entities.keys() before/after kernel.tick_once()), following V1's alive_before/alive_after pattern
- Reset counters to 0 on V2EngineManager.reset()
- Follow existing router pattern (APIRouter+Depends+get_engine_manager, response_model, 503 when not ready) from src/api/routes/economy.py

## Out of Scope
- /api/v1/speed and /api/v1/clear_events routes -- explicitly deferred to HUD-tied scope, must not be added even though found in the same grep
- present_map/present_static implementation itself (that's a hard dependency on TCK-20260821-PRESENT-MAP-STATIC)

## Acceptance Criteria
- [x] GET /api/v1/map returns 200 {width,height,grid} RLE-encoded, 503 when manager.latest_state is None
- [x] GET /api/v1/static returns 200 StaticData-shaped payload sourced only via StatePresenter.present_static, never raw AuthoritativeState fields
- [x] GET /api/v1/stats returns 200 {tick,world_day,alive_count,total_spawned,total_deaths,running,paused}, counters non-decreasing across ticks, reset to 0 after V2EngineManager.reset()
- [x] V2EngineManager gains _total_spawned/_total_deaths incremented once per tick by len(new_ids)/len(dead_ids) (same alive_before/alive_after set-diff pattern as V1), verified by a test asserting counters increase after spawns/deaths and zero on reset()
- [x] new assertions added to the existing tests/api/test_rest_parity.py::test_api_rest_parity rather than a new subprocess-spinning test

## Related Tickets
- TCK-20260821-PRESENT-MAP-STATIC
- TCK-20260821-EPIC-LIVE-MAP-RECONNECTION

## Related Docs
- docs/engine/contracts/frontend.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/api/server.py
- src/api/engine_manager.py
- src/api/presenters/state_presenter.py
- src/api/routes/economy.py
- src/api/routes/state.py
- tests/api/test_rest_parity.py

## Assumptions / Open Questions
- V2's tick loop currently has no new_ids/dead_ids diffing at all -- this is a real addition to the hot tick path, not incidental wiring

## Implementation Notes

Implemented exactly per staging_artifacts/TCK-20260821-REST-MAP-STATIC-STATS/plan.md's 8 steps, no
deviations from the plan's design decisions:

1. **`StatePresenter.present_stats`** added to `src/api/presenters/state_presenter.py` after
   `present_static`. `world_day = state.tick // 2400` (Mechanics Bible §1, per Design Decision 1),
   `alive_count = sum(1 for e in state.entities.values() if e.combat.alive)` (Design Decision 2,
   matching `EconomyPresenter.present_health`'s precedent). `total_spawned`/`total_deaths`/`running`/
   `paused` passed through unchanged — pure function of its arguments, no mutation.
2. **`V2EngineManager`** (`src/api/engine_manager.py`): added `self._total_spawned = 0` /
   `self._total_deaths = 0` to `__init__`; inserted the `alive_before`/`alive_after` set-diff on
   `state.entities.keys()` around `self._kernel.tick_once()` inside `_run_loop`, folding the two new
   increments into the existing `with self._state_lock:` block (no new lock acquisition); added the
   explicit zero of both counters to `reset()` after `self.stop()`; added `total_spawned`/
   `total_deaths` read-only properties mirroring `errors_total`.
3. Added three new route files (`src/api/routes/map.py`, `static.py`, `stats.py`), each shaped
   exactly like `economy.py`/`manifest.py`: `APIRouter(tags=[...])`, no `Depends()` in the handler
   signature, direct `get_engine_manager()` call, 503 guard on `state is None` before calling the
   presenter. None import `AuthoritativeState`/`EntityState`.
4. Registered all three routers in `src/api/server.py`'s `create_v2_app`, immediately after the
   `manifest` registration and before `quality_routes`, using the same
   `app.include_router(..., prefix="/api/v1", dependencies=[Depends(require_admission)])` pattern.
   `map` aliased to `map_routes` on import (Python builtin shadowing); `static`/`stats` aliased the
   same way for consistency.
5. Added unit tests per test_plan.md tests 1-11: `tests/unit/api/test_map_route.py` (2 tests),
   `tests/unit/api/test_static_route.py` (2 tests), `tests/unit/api/test_stats_route.py` (4 tests),
   and 4 new tests appended to the existing `tests/unit/api/test_engine_manager.py` (spawn increment,
   death increment, reset-zeroes, non-decreasing-across-ticks). The counter tests drive the real
   `_run_loop` diff-and-increment code path directly by class-level-patching `Kernel.tick_once`
   (`unittest.mock.patch.object(Kernel, "tick_once", side_effect=...)`, matching this file's existing
   pattern for patching a `__slots__` class) to swap `manager._kernel._state` between controlled
   before/after `entities` dicts via `dataclasses.replace`, rather than waiting on the real
   `RaidService` spawn cadence (500 ticks) or real combat deaths — per investigation.md's flagged
   testability risk.
6. Extended `tests/api/test_rest_parity.py::test_api_rest_parity` with three new `requests.get` blocks
   (map/static/stats) inside the existing `try:` block, asserting 200 + top-level key presence. No new
   subprocess-spinning test was created.
7. Narrowed `docs/engine/contracts/frontend.md`'s Known-gap callout (line 12) to state that `/map`,
   `/static`, `/stats` now exist as real routes, with `/speed`/`/clear_events` still missing
   (out of scope).
8. Appended `INFRA-384` to `docs/parity_ledger/infrastructure.yaml` (re-verified immediately before
   writing it that `INFRA-383` was still the highest existing ID — confirmed via
   `grep -o 'INFRA-[0-9]*' ... | sort -t- -k2 -n | uniq | tail -5`, no concurrent claim).

**One fix beyond the plan's literal text, within Step 5's scope**: while running the new
`test_engine_manager_reset_zeroes_spawn_death_counters` test in isolation, discovered it leaked 2
`QueueDrainWorker` threads past the session-scoped leak sentinel (`tests/conftest.py::
_observability_worker_thread_sentinel`). Root cause: `manager.reset()` internally calls `self._build()`,
which constructs a brand-new `Kernel` (and its own `QueueDrainWorker` threads) — the test called
`manager.stop()` once (for the original kernel, inside the `with patch.object(...)` block) but never
called `manager.stop()` again after `reset()` to tear down the *new* kernel `reset()` had just built.
Fixed by moving the `manager.stop()` teardown into the test's `finally:` block so it runs once more,
after `reset()`. This is a test-hygiene fix within the same test this step was already writing, not a
change to `V2EngineManager.reset()` itself (which is correct as specified in the plan — `reset()`
zeroing the counters was never the bug; the test's own cleanup was incomplete).

**INFRA-384's `test_path`**: set to `tests/api/test_rest_parity.py::test_api_rest_parity` (the
end-to-end smoke test), matching `INFRA-383`'s convention of pointing to the integration test rather
than enumerating every unit test file.

## Test Summary

```
.venv/bin/python3 -m pytest tests/unit/api/ tests/architecture/test_api_read_model_guard.py -v
45 passed in 4.55s

PATH=.venv/bin:$PATH .venv/bin/python3 -m pytest tests/api/test_rest_parity.py -v
2 passed in 6.87s

PATH=.venv/bin:$PATH .venv/bin/python3 -m pytest tests/api/test_manifest_api.py -v
11 passed in 2.79s
```

`tests/api/test_rest_parity.py` and `test_manifest_api.py` boot a real server subprocess via a bare
`python3 -m src serve` command; when the scoped pytest command itself is invoked with a bare `python3`
lacking `pydantic` on `PATH`, that subprocess fails with `ModuleNotFoundError: No module named
'pydantic'` even though the pytest process itself runs fine under `.venv/bin/python3`. This is the
same pre-existing, environment-only gap already documented in
`tickets/done/TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT.md`'s Test Summary — confirmed, not
re-investigated, and resolved the same way (prefixing `PATH=.venv/bin:$PATH`) rather than treated as a
new regression. All tests pass cleanly once the venv's `python3` is first on `PATH`.

Architecture-Verify additionally ran a wider transitive-dependent scope covering `src/api/engine_manager.py`
(a shared module several other test files import directly): `tests/api/test_paged_logic.py`,
`tests/observability/test_metrics_export.py`, `tests/perf/test_api_projection_perf.py` — all pass.
Combined total across every file this ticket's changes could plausibly affect: **65 passed, 0 failed**.

No regressions: `tests/unit/api/test_state_presenter.py`'s 9 pre-existing tests, `test_economy_route.py`'s
6 tests, and `test_engine_manager.py`'s 6 pre-existing liveness/health tests all stayed green
unmodified (only new tests were appended to `test_engine_manager.py`).

## Files Changed

- `src/api/presenters/state_presenter.py` — added `present_stats` static method.
- `src/api/engine_manager.py` — added `_total_spawned`/`_total_deaths` counters (`__init__`, `_run_loop`
  set-diff, `reset()` explicit zero, `total_spawned`/`total_deaths` properties).
- `src/api/routes/map.py` — new route file, `GET /map`.
- `src/api/routes/static.py` — new route file, `GET /static`.
- `src/api/routes/stats.py` — new route file, `GET /stats`.
- `src/api/server.py` — registered the three new routers after `manifest`, before `quality_routes`.
- `tests/unit/api/test_map_route.py` — new file, 2 tests.
- `tests/unit/api/test_static_route.py` — new file, 2 tests.
- `tests/unit/api/test_stats_route.py` — new file, 4 tests.
- `tests/unit/api/test_engine_manager.py` — appended 4 new tests + a `_make_entity` helper.
- `tests/api/test_rest_parity.py` — extended `test_api_rest_parity` with map/static/stats assertions.
- `docs/engine/contracts/frontend.md` — narrowed the Known-gap callout (line 12) to reflect that
  `/map`, `/static`, `/stats` now exist.
- `docs/parity_ledger/infrastructure.yaml` — appended `INFRA-384`.
- `staging_artifacts/TCK-20260821-REST-MAP-STATIC-STATS/investigation.md`,
  `staging_artifacts/TCK-20260821-REST-MAP-STATIC-STATS/plan.md`,
  `staging_artifacts/TCK-20260821-REST-MAP-STATIC-STATS/test_plan.md` — pre-existing this run's own
  Investigate/Plan phases (untracked in git prior to this Implement pass); no content changes made to
  them by the Implement step itself (plan followed with zero deviations, so plan.md's Deviations
  section was left as "None" rather than fabricating one — see that file).
- `tickets/inprogress/TCK-20260821-REST-MAP-STATIC-STATS.md` — this ticket file itself (Status,
  Acceptance Criteria checkboxes, Implementation Notes, Test Summary, Files Changed, Completion
  Summary).

## Completion Summary

Added three new GET REST routes — `/api/v1/map`, `/api/v1/static`, `/api/v1/stats` — as three
single-concern route files under `src/api/routes/`, matching the `economy.py`/`manifest.py`
precedent exactly (503 guard before presenter call, no raw domain model imports). `/map` and
`/static` thinly wrap the already-implemented `StatePresenter.present_map`/`present_static`; `/stats`
required a new `StatePresenter.present_stats` method plus new `_total_spawned`/`_total_deaths`
counters on `V2EngineManager`, incremented once per tick via a `new_ids`/`dead_ids` set-diff on
`state.entities.keys()` inside the existing tick-loop lock and explicitly zeroed in `reset()`.
`world_day` is derived as `tick // 2400` per the Mechanics Bible's canonical day length (a documented,
deliberate divergence from V1's legacy `tick // 100`), and `alive_count` filters by `combat.alive`
matching the `EconomyPresenter.present_health` precedent. All three routers are registered in
`server.py`, 12 new unit tests were added (all passing, no regressions), `test_api_rest_parity` was
extended with the three new endpoint assertions (no new subprocess test), and both
`docs/engine/contracts/frontend.md` and `docs/parity_ledger/infrastructure.yaml` (new `INFRA-384`
entry) were updated in the same pass.
