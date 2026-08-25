---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260821-REST-MAP-STATIC-STATS
artifact_type: plan
tags: [api-design, engine]
---

# Implementation Plan — TCK-20260821-REST-MAP-STATIC-STATS

## Summary

Add three GET routes (`/api/v1/map`, `/api/v1/static`, `/api/v1/stats`) as three small single-concern
route files under `src/api/routes/`, following the `economy.py`/`manifest.py` precedent exactly
(`APIRouter(tags=[...])`, direct `get_engine_manager()` call, `503` guard on `state is None`,
registered in `src/api/server.py` after `manifest`). `/map` and `/static` are thin wraps of the
already-implemented, already-tested `StatePresenter.present_map`/`present_static`
(`src/api/presenters/state_presenter.py:157-261`). `/stats` requires a new `StatePresenter.present_stats`
method (state-derived `tick`/`world_day`/`alive_count`, manager-supplied `total_spawned`/`total_deaths`/
`running`/`paused` passed through) plus two new counters on `V2EngineManager`
(`src/api/engine_manager.py`), incremented once per tick via a `new_ids`/`dead_ids` set-diff on
`state.entities.keys()` (V1's exact ported pattern) and explicitly zeroed in `reset()`. Two design
decisions flagged as open by investigation.md are resolved explicitly below (`world_day` divisor,
`alive_count` filter semantics) rather than left ambiguous. Docs (`docs/engine/contracts/frontend.md`'s
Known-gap callout, a new `INFRA-387` parity ledger entry) are updated in the same pass per the
project's Parity Rule.

## Design Decisions (resolving investigation.md's flagged open questions)

### Decision 1 — `world_day` divisor: `tick // 2400`

investigation.md flags three candidate divisors: V1's literal `tick // 100`, `RaidService
.TICKS_PER_DAY = 100` (`src/world/raid.py:20`, a private raid-cadence-only constant), and the
Mechanics Bible's canonical day length. Read directly: `docs/mechanics/05_world_evolution.md:15-22`
("1. The Passage of Time" table) states `1 Tick = 1`, `1 Hour = 100`, **`1 Day = 2400`**, Certified
Level 1 (`authority: P0` per that doc's own frontmatter). This is independently corroborated by live
usage elsewhere in V2: `src/systems/strategic_systems/intelligence.py:541` computes the day/night
cycle as `state.tick % 2400`, not `% 100`.

Per this project's Authoritative Mechanics Rule ("the Mechanics Bible takes precedence" in case of
ambiguity), **`world_day` = `state.tick // 2400`**. This is a deliberate divergence from V1's literal
`tick // 100` value — not a bug, a resolved design decision. `RaidService.TICKS_PER_DAY = 100`
(`src/world/raid.py:20`) is **not** touched or used as a source for this computation; it is a
separate, pre-existing, out-of-scope divergence from the Mechanics Bible scoped only to raid cadence
math, not a general tick-to-day helper.

### Decision 2 — `alive_count`: `combat.alive`-filtered, not `len(state.entities)`

V1's route (`git show 677abbfb^:src_legacy/api/routes/state.py:97-110`, per investigation.md) computes
`alive = sum(1 for e in snapshot.entities.values() if e.combat.alive)`, not `len(entities)`. Reading
`src/engine/apply.py:226-232` confirms V2's authoritative apply path removes dead entities from
`state.entities` the same tick they die, so today `len(state.entities)` and the `combat.alive`-filtered
count are very likely numerically equivalent. The ticket's own AC does not specify which form to use.
Decision: **port V1's filtered form exactly** (`sum(1 for e in state.entities.values() if e.combat.alive)`),
matching this project's established in-repo precedent for this exact filtering pattern —
`src/api/presenters/economy.py:27-29`'s `EconomyPresenter.present_health`:
```python
for entity in state.entities.values():
    if not entity.combat.alive:
        continue
```
Rationale (documented here per investigation.md's instruction, not left implicit): this is the safer,
lower-drift choice consistent with "port-and-adapt from a proven reference," and it costs nothing
today since the two forms are equivalent under current apply-path behavior. **This assumption should
be revisited if a future change ever introduces an entity that persists in `state.entities` with
`combat.alive=False` for more than the tick it died in** (e.g. a "dying" grace-tick state) — at that
point the two forms would diverge and the filtered form remains correct while `len()` would not.

### Decision 3 — three separate route files, not one combined file

`economy.py`, `manifest.py`, `campaigns.py`, etc. are this project's established one-router-per-concern
convention (confirmed by reading `economy.py` and `manifest.py` in full). V1 mixed `/static` and
`/stats` into one `state.py` file, but that is legacy shape, not a V2 convention to port. Decision:
`src/api/routes/map.py`, `src/api/routes/static.py`, `src/api/routes/stats.py` — three small files,
each with its own `APIRouter(tags=[...])`, matching `manifest.py`'s flat style (no extra sub-prefix
beyond the app-level `/api/v1`).

## Steps

### Step 1 — Add `StatePresenter.present_stats`

**Files:** `src/api/presenters/state_presenter.py`

**Change:** Add a new `@staticmethod present_stats` after `present_static` (currently ends at
`src/api/presenters/state_presenter.py:261`). Signature and body:

```python
@staticmethod
def present_stats(
    state: AuthoritativeState,
    total_spawned: int,
    total_deaths: int,
    running: bool,
    paused: bool,
) -> Dict[str, Any]:
    """Live simulation counters: {tick, world_day, alive_count, total_spawned, total_deaths, running, paused}.

    world_day = tick // 2400 per docs/mechanics/05_world_evolution.md:15-22 ("1 Day = 2400 ticks",
    Certified Level 1) -- NOT V1's legacy tick // 100, NOT src/world/raid.py's unrelated
    RaidService.TICKS_PER_DAY=100 (see plan.md Design Decisions).
    alive_count filters state.entities by combat.alive, ported from V1's exact semantics and
    matching the in-repo precedent at src/api/presenters/economy.py:27-29 (EconomyPresenter
    .present_health's `if not entity.combat.alive: continue` filter) -- not len(state.entities)
    (see plan.md Design Decisions for the revisit condition).
    total_spawned/total_deaths/running/paused are V2EngineManager-level telemetry, passed through
    unchanged -- this keeps the method a pure function of its arguments, consistent with the M12
    Law docstring at the top of this file (line 9): "API presenters MUST NOT mutate authoritative
    state."
    """
    alive_count = sum(1 for e in state.entities.values() if e.combat.alive)
    return {
        "tick": state.tick,
        "world_day": state.tick // 2400,
        "alive_count": alive_count,
        "total_spawned": total_spawned,
        "total_deaths": total_deaths,
        "running": running,
        "paused": paused,
    }
```

No changes to `present_map`/`present_static` (lines 157-261) or `terrain_code_map` (lines 144-154) —
this step only adds a new method.

**Do NOT touch:** `present_map`, `present_static`, `terrain_code_map`, `present_minimal`,
`present_full`, `present_entity`, `present_region` — all pre-existing and out of this ticket's scope.

**Verify:** New tests 5, 6, 7 from test_plan.md (`tests/unit/api/test_stats_route.py`, not yet
created — see Step 5).

### Step 2 — Add `_total_spawned`/`_total_deaths` counters to `V2EngineManager`

**Files:** `src/api/engine_manager.py`

**Change:** Four sub-edits, all in this one file (confirmed by reading the whole file):

1. **`__init__`** (currently sets `self._errors_total = 0` at line 55): add
   `self._total_spawned = 0` and `self._total_deaths = 0` alongside it.

2. **`_run_loop`** (lines 273-301): insert the V1-ported `alive_before`/`alive_after` set-diff
   around the existing `self._kernel.tick_once()` call (line 286), and fold the two new increments
   into the **existing** `with self._state_lock:` block that already wraps `self._tick_times.append(...)`
   (lines 287-288) — do not add a second, separate lock acquisition:
   ```python
   try:
       alive_before = set(self._kernel.state.entities.keys())
       self._kernel.tick_once()
       alive_after = set(self._kernel.state.entities.keys())
       new_ids = alive_after - alive_before
       dead_ids = alive_before - alive_after
       with self._state_lock:
           self._tick_times.append(time.time())
           self._total_spawned += len(new_ids)
           self._total_deaths += len(dead_ids)
       self._update_latest_state(self._kernel.state)
       self._notify_listeners(self._latest_snapshot)
   except Exception as e:
       ...  # unchanged
   ```
   This matches V1's exact pattern (`git show 677abbfb^:src_legacy/api/engine_manager.py`, cited in
   investigation.md lines 92-105) and is architecturally sound per CLAUDE.md's Durable State Rule:
   these are non-authoritative manager-level telemetry (same category as the pre-existing
   `_tick_times`/`_errors_total`), computed outside the authoritative apply/kernel pipeline, not
   durable simulation state.

3. **`reset()`** (lines 268-271): add the explicit zero **after** `self.stop()` returns:
   ```python
   def reset(self):
       self.stop()
       self._build()
       with self._state_lock:
           self._total_spawned = 0
           self._total_deaths = 0
       logger.info("V2EngineManager reset.")
   ```

4. **New properties**, mirroring the existing `errors_total` property (lines 332-334, unlocked read
   — same convention, not a new pattern):
   ```python
   @property
   def total_spawned(self) -> int:
       return self._total_spawned

   @property
   def total_deaths(self) -> int:
       return self._total_deaths
   ```

**Every other writer to `_total_spawned`/`_total_deaths` (both are brand-new attributes — confirmed
by reading the whole file, matching investigation.md line 74-75's finding that no counters exist
today):** there are none besides the three sub-edits above (`__init__` initializes, `_run_loop`
increments, `reset()` zeroes) — no other method in this class touches them. Concurrency: `_run_loop`
runs on the dedicated `v2-engine-loop` daemon thread (started at line 243); `reset()` may be called
from a different thread (e.g. a FastAPI route handler). `reset()`'s `self.stop()` (line 269) joins
that thread with a 5-second timeout (`self._thread.join(timeout=5.0)`, line 252) **before** `reset()`
proceeds to zero the counters, so under normal operation the tick thread has already exited before
the zero happens — no race. If `join(timeout=5.0)` times out (thread still alive), a subsequent tick
could theoretically increment between the zero and `_build()`'s kernel replacement — this is a
pre-existing, unaddressed risk already shared by every other piece of manager state `reset()` touches
(e.g. `_kernel` itself being swapped without first confirming the old thread fully stopped), not
something newly introduced or newly solved by this ticket.

**Do NOT touch:** `_errors_total`'s own reset gap (confirmed also un-zeroed by `reset()`/`_build()`,
same latent class of bug) — out of scope, not part of this ticket's AC, do not fix as a drive-by.
`RaidService.TICKS_PER_DAY` (`src/world/raid.py:20`) — do not touch.

**Verify:** New tests 8, 9, 10, 11 from test_plan.md (`tests/unit/api/test_engine_manager.py`,
existing file — add alongside).

### Step 3 — Add three route files with 503 guards

**Files:** `src/api/routes/map.py` (new), `src/api/routes/static.py` (new), `src/api/routes/stats.py`
(new)

**Change:** Each file follows `src/api/routes/economy.py:1-33`'s exact shape (`APIRouter(tags=[...])`,
no `Depends()` in the handler signature, direct `get_engine_manager()` call, `if state is None: raise
HTTPException(status_code=503, ...)` guard **before** calling the presenter — required because
`present_map`/`present_static` have no internal `None`-state guard themselves and would raise
`AttributeError` on `state=None`, confirmed in investigation.md lines 66-71 by direct trace of
`present_map`'s `if not state.terrain` line, which requires `state` to already be a real object).

`src/api/routes/map.py`:
```python
from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from src.api.dependencies import get_engine_manager
from src.api.presenters.state_presenter import StatePresenter

router = APIRouter(tags=["Map"])

@router.get(
    "/map",
    response_model=Dict[str, Any],
    summary="RLE-encoded terrain grid",
    description="Returns {width, height, grid} -- RLE-encoded terrain. Read-only -- no state mutation.",
)
async def get_map() -> Dict[str, Any]:
    manager = get_engine_manager()
    state = manager.latest_state
    if state is None:
        raise HTTPException(status_code=503, detail="Engine not ready — no state available")
    return StatePresenter.present_map(state)
```

`src/api/routes/static.py`: identical shape, `router = APIRouter(tags=["Static"])`,
`@router.get("/static", ...)`, calls `StatePresenter.present_static(state)`.

`src/api/routes/stats.py`: identical shape, `router = APIRouter(tags=["Stats"])`,
`@router.get("/stats", ...)`, calls:
```python
return StatePresenter.present_stats(
    state,
    total_spawned=manager.total_spawned,
    total_deaths=manager.total_deaths,
    running=manager.is_running,
    paused=manager.is_paused,
)
```
`manager.is_running`/`manager.is_paused` are pre-existing properties (`src/api/engine_manager.py:308-314`)
— confirmed not simple negations of each other (a stopped-and-not-yet-started manager is neither), and
this is the natural, already-established source for the AC's plain `running`/`paused` booleans (per
investigation.md lines 82-87).

None of the three files import `AuthoritativeState`/`EntityState` at module scope — matches
`economy.py`/`manifest.py`, required by `tests/architecture/test_api_read_model_guard.py`.

**Do NOT touch:** `src/api/routes/state.py`, `src/api/routes/control.py`, `src/api/routes/health.py` —
all three are pre-existing 0-byte stub files. Investigation confirms (lines 45-53) the real
`/api/v1/state`, `/api/v1/control/pause`, `/api/v1/control/resume` handlers live inline in
`src/api/server.py` (lines 186-229), not in these stub files. **Do not relocate that inline logic into
these stubs as unscoped drive-by work** — it is a real, separate, pre-existing gap noted for future
maintainers, not something this ticket touches. Do not add `/api/v1/speed` or `/api/v1/clear_events` —
explicitly Out of Scope on the ticket.

**Verify:** New tests 1-7 from test_plan.md (`tests/unit/api/test_map_route.py`,
`test_static_route.py`, `test_stats_route.py`), plus the existing (unmodified but must-stay-green)
`tests/architecture/test_api_read_model_guard.py::test_no_api_route_directly_imports_authoritative_state`.

### Step 4 — Register the three routers in `server.py`

**Files:** `src/api/server.py`

**Change:** Add three registration blocks immediately after the existing `manifest` registration
(`src/api/server.py:127-128`) and before `quality_routes` (line 130), following the exact same
`app.include_router(<module>.router, prefix="/api/v1", dependencies=[Depends(require_admission)])`
pattern every other router in this function uses (lines 100-131, `stream` through `quality_routes`):

```python
from src.api.routes import map as map_routes
app.include_router(map_routes.router, prefix="/api/v1", dependencies=[Depends(require_admission)])

from src.api.routes import static as static_routes
app.include_router(static_routes.router, prefix="/api/v1", dependencies=[Depends(require_admission)])

from src.api.routes import stats as stats_routes
app.include_router(stats_routes.router, prefix="/api/v1", dependencies=[Depends(require_admission)])
```
Alias `map` to `map_routes` on import — `map` is a Python builtin, and importing an unaliased `map`
name into `server.py`'s module namespace would shadow it there. `static`/`stats` are not builtins, but
aliased the same way for naming consistency across the three new imports.

**Every other writer to this registration list:** `server.py`'s `create_v2_app` router-registration
block (lines 100-131) is a single ordered sequence edited by whichever ticket adds a new route file —
the immediately-preceding edit was `TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT`'s addition of the
`manifest` block (lines 127-128). No other in-flight ticket is known (per investigation.md's Prior
Work section) to be concurrently editing this same block; append after `manifest`, before
`quality_routes`, per the established chronological-append convention.

**Do NOT touch:** the `stream`/`history`/`search`/`behavior`/`decisions`/`scenarios`/`campaigns`/
`chronicle`/`economy`/`manifest`/`quality_routes` registration lines (lines 100-131) — only add, do
not reorder or edit existing entries. Do not touch the inline `/api/v1/state`,
`/api/v1/control/pause`, `/api/v1/control/resume`, `/api/v1/entities*` handlers (lines 186-229+) —
unrelated to this ticket's scope.

**Verify:** Test 12 from test_plan.md (extended `tests/api/test_rest_parity.py::test_api_rest_parity`,
Step 6) — this is what proves the routes are actually registered and reachable end-to-end, not just
unit-testable in isolation.

### Step 5 — Add new unit tests

**Files:** `tests/unit/api/test_map_route.py` (new), `tests/unit/api/test_static_route.py` (new),
`tests/unit/api/test_stats_route.py` (new), `tests/unit/api/test_engine_manager.py` (existing, append)

**Change:** Implement test_plan.md's tests 1-11 exactly as specified there:
- `test_map_route.py`: tests 1 (200 + RLE shape), 2 (503 on `None` state).
- `test_static_route.py`: tests 3 (200 + StaticData shape sourced only via `present_static`), 4 (503).
- `test_stats_route.py`: tests 5 (200 + exact 7-key shape/types), 6 (`alive_count` excludes dead
  entities — construct one alive + one `combat.alive=False` entity, assert `alive_count == 1`), 7
  (`world_day` derivation — assert `state.tick = 4800` → `world_day == 2`, a tick count chosen
  specifically because it distinguishes `//2400` from `//100`, per test_plan.md's own guard rationale).
- `test_engine_manager.py`: tests 8 (`_total_spawned` incremented by exactly `len(new_ids)` — drive
  the diff-and-increment code path directly with a controlled before/after `state.entities` key set,
  not the real background loop, since `RaidService`'s real spawn cadence is 500 ticks per
  investigation.md lines 294-304), 9 (same for `_total_deaths`), 10 (`reset()` zeroes both counters),
  11 (counters non-decreasing across multiple controlled diff-drive steps).

All four files follow `tests/unit/api/test_economy_route.py`'s existing `_make_app_with_state`/
`MagicMock`-manager pattern (bare `FastAPI()`, `app.include_router(router, prefix="/api/v1")`,
`deps.set_engine_manager(MagicMock(latest_state=state))`, `TestClient`) for route-level tests, and
`tests/unit/api/test_engine_manager.py`'s existing pattern for manager-level tests.

**Do NOT touch:** `tests/unit/api/test_state_presenter.py` (must stay green, unmodified — proves
`present_map`/`present_static` logic itself wasn't altered), `tests/unit/api/test_economy_route.py`,
`tests/unit/api/test_dependencies.py`, `tests/unit/api/test_read_model_cache.py`,
`tests/unit/api/test_read_model_service.py`.

**Verify:**
```
.venv/bin/python3 -m pytest tests/unit/api/ tests/architecture/test_api_read_model_guard.py -v
```

### Step 6 — Extend `test_api_rest_parity` with new endpoint assertions

**Files:** `tests/api/test_rest_parity.py`

**Change:** Append `requests.get` calls for `/api/v1/map`, `/api/v1/static`, `/api/v1/stats` inside
the **existing** `try:` block of `test_api_rest_parity`, against the same already-running server
subprocess instance the existing `/health`, `/api/v1/state`, `/api/v1/control/pause`,
`/api/v1/control/resume` assertions already use. Assert 200 status and top-level key presence only
(`width`/`height`/`grid`; `buildings`/`resource_nodes`/`treasure_chests`/`regions`;
`tick`/`world_day`/`alive_count`/`total_spawned`/`total_deaths`/`running`/`paused`) — this is a smoke
check that the routes are wired end-to-end, not exhaustive shape validation (that belongs to Step 5's
unit tests). Do **not** create a new subprocess-spinning test function — the AC explicitly requires
extending this existing function.

**Every other writer to this test function:** `test_api_compression` (same file) boots the same
server binary independently but does not touch `test_api_rest_parity`'s body. `test_manifest_api.py`
(sibling file) has its own separate server-boot fixture. No other test file appends to
`test_api_rest_parity` itself. Run with `PATH=.venv/bin:$PATH` prefixed or invoke via
`.venv/bin/python3 -m pytest` directly — a known, pre-existing, environment-only failure mode exists
when invoked with a bare `python3` lacking `pydantic` on `PATH` (documented in
`tickets/done/TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT.md`'s Test Summary), unrelated to this
ticket's changes.

**Do NOT touch:** the existing `/health`, `/api/v1/state`, `/api/v1/control/pause`,
`/api/v1/control/resume` assertions, `test_api_compression`. Do not add assertions for
`/api/v1/speed` or `/api/v1/clear_events` — Out of Scope.

**Verify:**
```
.venv/bin/python3 -m pytest tests/api/test_rest_parity.py -v
.venv/bin/python3 -m pytest tests/api/test_manifest_api.py -v
```

### Step 7 — Narrow `docs/engine/contracts/frontend.md`'s Known-gap callout

**Files:** `docs/engine/contracts/frontend.md`

**Change:** Read directly at `docs/engine/contracts/frontend.md:12`, the current callout states:
> "the frontend's `useSimulation.ts` hook (§2 below) calls `/map`, `/static`, `/stats`, `/speed`,
> `/clear_events` — none of which exist as routes in `src/api/server.py`"

This is now factually wrong for three of the five once Steps 1-4 land. Replace with wording that
narrows the callout to only the two still-missing routes:
> "the frontend's `useSimulation.ts` hook (§2 below) calls `/map`, `/static`, `/stats`, `/speed`,
> `/clear_events`. As of `TCK-20260821-REST-MAP-STATIC-STATS`, `/map`, `/static`, and `/stats` exist
> as real routes in `src/api/server.py`. `/speed` and `/clear_events` remain missing (explicitly
> out of scope for that ticket, deferred to HUD-tied scope)."

**Do NOT touch:** §2A's `Promise.all` fetch-call list (lines 30-40) — investigation.md confirms
(reading `frontend/src/hooks/useSimulation.ts` directly, lines 179-193) that `/stats` is fetched by
the separate 500ms slow-poll `useEffect`, not `loadInitial()`'s `Promise.all`, so §2A's list does not
need a new entry for this ticket. Do not modify `useSimulation.ts` itself or any other frontend file —
backend-only ticket, frontend already calls these three routes in their expected shapes.

**Verify:** No automated test — doc-only change, confirmed by direct re-read of the edited line
against the actual route registration list in `server.py` after Step 4.

### Step 8 — Add parity ledger entry `INFRA-387`

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Append a new entry, following `INFRA-386`'s exact shape (read directly at
`docs/parity_ledger/infrastructure.yaml:11227-11239`, appended at the end of the file — confirmed
this is the file's chronological-append convention, matching `INFRA-210` at line 2418 for the earlier,
unrelated presenter-layer entry):

```yaml
- id: INFRA-387
  text: 'GET /api/v1/map, /api/v1/static, /api/v1/stats are real registered routes (src/api/routes/map.py,
    static.py, stats.py), wrapping StatePresenter.present_map/present_static/present_stats
    (TCK-20260821-PRESENT-MAP-STATIC, TCK-20260821-REST-MAP-STATIC-STATS). V2EngineManager gains
    _total_spawned/_total_deaths counters incremented once per tick via a new_ids/dead_ids
    set-diff on state.entities.keys() (ported from V1s alive_before/alive_after pattern) and
    explicitly zeroed in reset(). stats.world_day = tick // 2400 per docs/mechanics/05_world_evolution.md
    Sec 1 (Certified Level 1), a deliberate divergence from V1s legacy tick // 100. alive_count
    filters by combat.alive, matching src/api/presenters/economy.py present_health precedent.'
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: src/api/routes/map.py + static.py + stats.py + src/api/presenters/state_presenter.py + src/api/engine_manager.py
  proof_type: null
  test_path: tests/api/test_rest_parity.py::test_api_rest_parity
  divergence_note: world_day uses tick // 2400 (Mechanics Bible canonical day length), not V1's
    tick // 100 -- see docs/engine/contracts/frontend.md and staging_artifacts/TCK-20260821-REST-MAP-STATIC-STATS/plan.md
    Design Decisions for rationale.
  support_boundary: null
```
`priority: P1` matches the subsystem's existing `INFRA-210`/`INFRA-386` entries (both `P1`), per
investigation.md's recommendation.

**Every other writer to this file:** `docs/parity_ledger/infrastructure.yaml` is a shared, append-only
file every closed infrastructure-layer ticket writes to. `INFRA-386` was the highest existing ID at
investigation time (2026-08-24). **Re-verify `INFRA-387` is still the next available ID immediately
before writing this entry** (e.g. `grep -c '^- id: INFRA-' docs/parity_ledger/infrastructure.yaml` or
equivalent) — another concurrently-running ticket in this shared worktree could have claimed it first,
per this project's documented shared-directory concurrency risk pattern (CLAUDE.md's Worktree &
Branch Isolation section).

**Do NOT touch:** any existing entry, including `INFRA-210` and `INFRA-386` — both remain
`status: verified` and unmodified; this ticket only adds a new entry.

**Verify:** No automated test enforces parity ledger shape beyond `validate_frontmatter.py`-adjacent
schema checks (out of this ticket's direct test scope) — confirmed correct by re-reading the entry
against `schema.json` field names after writing.

## Scope Guards

- Do **not** add `/api/v1/speed` or `/api/v1/clear_events` — explicitly Out of Scope on the ticket,
  deferred to HUD-tied scope.
- Do **not** modify `present_map`/`present_static`'s existing logic (`TCK-20260821-PRESENT-MAP-STATIC`'s
  closed territory) — only add the new `present_stats` method.
- Do **not** populate or relocate logic into `src/api/routes/state.py`, `control.py`, `health.py` —
  pre-existing 0-byte stubs, not this ticket's concern.
- Do **not** modify `useSimulation.ts` or any other frontend file.
- Do **not** fix `RaidService.TICKS_PER_DAY`'s divergence from the Mechanics Bible's 2400-tick day —
  real, separate, pre-existing issue, different subsystem (raid/calamity cadence).
- Do **not** fix `_errors_total`'s pre-existing, un-related reset gap (also never zeroed by
  `reset()`/`_build()`) — same latent bug class as the counters this ticket adds, but a different,
  already-existing counter, out of this ticket's scope.
- Do **not** create a new subprocess-spinning test file for the new routes — extend the existing
  `test_api_rest_parity` function only.
- Do **not** reorder or edit any pre-existing router registration line in `server.py`.

## Dependency Map

- Step 1 (presenter) has no dependency on other steps.
- Step 2 (engine manager counters) has no dependency on other steps — independent of Step 1.
- Step 3 (route files) depends on Step 1 (`present_stats` must exist) and Step 2 (`manager
  .total_spawned`/`total_deaths`/`is_running`/`is_paused` must exist for `stats.py`; `map.py` and
  `static.py` only depend on the pre-existing `present_map`/`present_static`, not on Step 2).
- Step 4 (server.py registration) depends on Step 3 (route modules must exist to import).
- Step 5 (unit tests) depends on Steps 1-4 all being in place to exercise.
- Step 6 (rest_parity extension) depends on Step 4 (routes must be registered and reachable via the
  real server subprocess).
- Step 7 (frontend.md doc) depends on Step 4 landing (the callout narrows to reflect the real,
  registered route list).
- Step 8 (parity ledger) depends on Steps 1-6 being complete and verified (the entry documents the
  finished, tested behavior).

Steps 1 and 2 can be implemented in either order or in parallel; everything downstream is linear.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| GET /api/v1/map returns 200 {width,height,grid}, 503 when latest_state is None | Step 3 (map.py) | test_plan.md tests 1, 2 |
| GET /api/v1/static returns 200 StaticData-shaped payload sourced only via present_static | Step 3 (static.py) | test_plan.md tests 3, 4 |
| GET /api/v1/stats returns 200 {tick,world_day,alive_count,total_spawned,total_deaths,running,paused}, counters non-decreasing, reset to 0 after reset() | Steps 1, 2, 3 (stats.py + present_stats) | test_plan.md tests 5, 6, 7, 10, 11 |
| V2EngineManager gains _total_spawned/_total_deaths incremented once per tick by len(new_ids)/len(dead_ids), verified by spawn/death-increase and zero-on-reset tests | Step 2 | test_plan.md tests 8, 9, 10 |
| New assertions added to existing tests/api/test_rest_parity.py::test_api_rest_parity, not a new subprocess test | Step 6 | test_plan.md test 12 |

## Anti-Drift Notes

- **`world_day` must be `tick // 2400`**, never V1's `tick // 100` and never
  `RaidService.TICKS_PER_DAY` (`src/world/raid.py:20`) — see Design Decision 1. Test 7
  (`test_stats_world_day_derivation`) uses `tick=4800` specifically because it distinguishes `//2400`
  (→2) from `//100` (→48); do not weaken that assertion to a value both divisors would satisfy.
- **`alive_count` must filter `combat.alive`**, never silently swapped for `len(state.entities)` —
  see Design Decision 2. The revisit condition (a future "dying" grace-tick state) is documented, not
  something to solve now.
- **`src/api/routes/state.py`/`control.py`/`health.py` are pre-existing empty stub files.** The real
  `/state`/`control/pause`/`control/resume` handlers are inline in `server.py:186-229`. Do not
  interpret this ticket's Related Code Areas listing `state.py` as an instruction to move that inline
  logic there — it isn't, and doing so would be unscoped drive-by work.
- **`reset()` must explicitly zero `_total_spawned`/`_total_deaths`** (Step 2, sub-edit 3) — `_build()`
  alone does not reset arbitrary instance attributes it doesn't touch (confirmed by reading `_build()`
  in full: it never resets `_errors_total` either, a real pre-existing gap in the same class of bug,
  useful confirming signal but out of scope to fix). Skipping the explicit zero in `reset()` would pass
  every test except test 10 (`test_engine_manager_reset_zeroes_spawn_death_counters`) — do not treat
  that test as optional.
- **The diff-and-increment logic belongs inside `_run_loop`'s existing `with self._state_lock:` block**
  (Step 2, sub-edit 2), not a new unlocked write and not a second lock acquisition — reuses the same
  critical section `_tick_times.append(...)` already uses.
- **Route bodies must not iterate `state.entities.values()` and read `.combat.alive` inline** — that
  logic lives in `StatePresenter.present_stats` (Step 1), matching the established
  `EconomyPresenter.present_health` precedent (`src/api/presenters/economy.py:27-29`). This would still
  pass the AST-only import guard test even done inline, but violates the project's actual "routes
  present shaped read models through presenters" architecture rule.
- **`INFRA-387` is a shared, append-only file's next ID as of investigation time (2026-08-24)** — the
  implementer must re-verify it is still unclaimed immediately before writing Step 8's entry, since
  other concurrent tickets in this shared worktree can append to the same file.
- **This is a real addition to the hot tick path** (`_run_loop`'s per-tick set-diff on
  `state.entities.keys()`), not incidental wiring — the ticket's own Assumptions section flags this;
  keep the diff O(entities) and inside the existing lock scope, not a new expensive per-tick operation.

## Deviations

None of the 8 steps' code or docs changes deviated from this plan — implemented exactly as specified,
including both Design Decisions (`world_day = tick // 2400`, `alive_count` filtered by `combat.alive`)
and the three-separate-route-files structure.

One test-only addition beyond the plan's literal step text, still within Step 5's scope: while writing
`test_engine_manager_reset_zeroes_spawn_death_counters` (test_plan.md test 10), discovered during a
solo test run that it leaked 2 `QueueDrainWorker` threads past `tests/conftest.py`'s session-scoped
leak sentinel. Root cause was the test's own cleanup, not `V2EngineManager.reset()`: `reset()` calls
`self._build()`, which constructs a fresh `Kernel` (new worker threads) as part of its normal,
already-plan-specified behavior — the test needed a second `manager.stop()` call after `reset()` to
tear that new kernel down, which the plan's test description did not explicitly call out. Fixed by
moving the test's `manager.stop()` teardown into its `finally:` block so it runs once more after
`reset()`. No production code was affected by this fix.
