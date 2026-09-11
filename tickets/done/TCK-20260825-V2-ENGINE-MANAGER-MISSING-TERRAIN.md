---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260825-V2-ENGINE-MANAGER-MISSING-TERRAIN
phase: done
date: 2026-08-25
tags: [rendering, websocket]
---

# TCK-20260825-V2-ENGINE-MANAGER-MISSING-TERRAIN

## Title
`V2EngineManager` never loaded a real compiled world -- `GET /api/v1/map` has always returned an
empty map through the real running server

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P0

## Request Summary
Building a real, headless-browser Playwright end-to-end check of the live map (per direct user
instruction, to make this verifiable by an agent repeatably rather than requiring manual checking)
surfaced a root-cause bug far more severe than anything found earlier this session: **the live
map's terrain has never actually rendered through the real running API server, independent of and
predating every WS-proxy/auth/metadata fix already shipped in
`TCK-20260825-LIVE-MAP-DEV-AUTH-AND-WS-PROXY-FIX`.**

Live-reproduced: `curl http://127.0.0.1:8000/api/v1/map` (with a valid key, against a real running
server) returns `200 {"width": 0, "height": 0, "grid": []}`. Root cause, confirmed by reading
`src/api/engine_manager.py::V2EngineManager._build()`: it constructs
`AuthoritativeState(tick=0, seed=self._seed, entities=entities)` with **no `terrain` argument at
all** -- `AuthoritativeState.terrain` defaults to an empty dict
(`field(default_factory=dict)`, `src/core/state.py:1126`) when not supplied. `_build()` never calls
`WorldCompiler`/`WorldRepository` -- it only spawns a hero and some goblins directly into an
otherwise-bare state. Every tool used earlier this session to inspect rendering/world data
(`tools/calibrate_rendering.py`, `tools/review_pipeline_check.py`, the perf harness's
`--internal-serve` monkeypatch mode) calls `WorldCompiler.compile()` directly, bypassing
`V2EngineManager` entirely -- which is exactly why this was never caught by any of that work.
Entities/ticks were confirmed live-working correctly (the WS delta stream is real) -- specifically
terrain was missing.

## Scope
- `src/api/engine_manager.py`: `V2EngineManager.__init__` gains a `world_id: str = "dungeon_crawl"`
  parameter. `_build()` now calls `WorldRepository("data/worlds").load_world(self._world_id)` then
  `WorldCompiler.compile(spec, seed=self._seed)`, and merges the compiled world's terrain/regions/
  statics with the pre-existing hero+goblin-diagonal entity-spawn logic via
  `dataclasses.replace(compiled_state, tick=0, seed=self._seed, entities=entities)` -- the compiled
  world's own entities (quest-givers, NPCs, etc.) are deliberately discarded in favor of that
  existing, already-tested spawn logic (entities_count semantics,
  `TCK-20260817-STANDARD-SPAWN-PLACEMENT-COLLISION-HERO-MONSTER-DIAGONAL`'s collision fix) --
  only the terrain layer was missing, entity-spawning behavior/contract must not change.
- `src/api/server.py::create_v2_app` gains optional `seed`/`entities_count`/`world_id` override
  parameters (`None`-default, backward compatible with every existing caller -- ~20+ call sites
  across `tests/api/`, `tests/observability/`, `tools/perf/`) threaded into `V2EngineManager(...)`.
- `src/cli/entry.py`: the `serve` subcommand's pre-existing `--seed`/`--entities` flags (defined
  but silently never used by `_run_serve`) are now actually threaded through; a new `--world` flag
  is added for the same purpose.
- Verify live, end-to-end, through the real `make dev` command and the Playwright e2e check
  (`frontend/e2e/live_map.spec.ts`): real terrain must render (non-blank canvas pixels), not just
  entities/ticks.

## Out of Scope
- Changing the hero+goblin-diagonal entity-spawn logic itself, or the compiled world's own entities
  -- deliberately discarded, not merged in; a future ticket could explore using the world's real
  entity population instead, but that is a materially bigger behavior change than this fix.
- Any change to `WorldCompiler`/`WorldRepository` themselves -- already correct, used as-is.
- Caching/pre-warming the compiled world across `V2EngineManager` instantiations for test-suite
  speed -- measured actual impact (12 `test_engine_manager.py` tests: 7.26s: `tests/api/` full
  suite: 68s) and judged acceptable; revisit only if it becomes a real problem.
- `TCK-20260825-METADATA-API-BACKEND-MISSING` -- a separate, unrelated missing-backend-routes gap,
  already filed.

## Acceptance Criteria
- [x] `V2EngineManager._build()` loads a real compiled world; `GET /api/v1/map` returns non-zero
      width/height and a real RLE grid through the actual running server
- [x] Existing hero+goblin-diagonal entity-spawn behavior and its collision-avoidance fix are
      unchanged (same entities_count semantics, same hero_pos, same monster placement logic)
- [x] `create_v2_app`'s new parameters are backward compatible -- every pre-existing caller (bare
      `create_v2_app(profile)`) continues to work unchanged
- [x] `--seed`/`--entities`/new `--world` CLI flags actually take effect
- [x] Live-verified end-to-end via the real Playwright e2e check
      (`frontend/e2e/live_map.spec.ts`) -- passes, with a real non-blank rendered-terrain
      screenshot as evidence
- [x] `tests/unit/api/test_engine_manager.py`, `tests/api/` (full), `tests/unit/api/`,
      `tests/observability/test_metrics_export.py`, `tests/api/test_scenario_runtime_api.py` all
      still pass

## Related Tickets
- TCK-20260825-LIVE-MAP-DEV-AUTH-AND-WS-PROXY-FIX (the two prior fixes -- WS proxy `ws: true`, dev
  API key wiring -- were real and necessary but insufficient on their own; this ticket's bug is
  independent and predates both)
- TCK-20260817-STANDARD-SPAWN-PLACEMENT-COLLISION-HERO-MONSTER-DIAGONAL (the entity-spawn
  collision-avoidance logic this fix deliberately preserves unchanged)
- TCK-20260821-EPIC-LIVE-MAP-RECONNECTION (built the frontend consumer of `/api/v1/map`; never
  caught this because the epic's own live testing never got past the browser boundary at the time)

## Related Docs
None updated -- no existing doc claimed `V2EngineManager` loads real terrain (the gap was a
silent omission, not a documented-then-broken claim).

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- src/api/engine_manager.py (`V2EngineManager.__init__`, `_build()`)
- src/api/server.py (`create_v2_app`)
- src/cli/entry.py (`serve` subcommand argparse, `_run_serve`)
- src/worldbuilding/compiler.py, src/worldbuilding/repository.py (used as-is)
- frontend/e2e/live_map.spec.ts (the check that caught this)

## Assumptions / Open Questions
- `world_id` defaults to `"dungeon_crawl"` -- the same world used throughout this session's other
  live testing/calibration work, real and well-populated. No signal exists yet for what a
  "production" default should be; this is a reasonable default-for-dev choice, not a considered
  product decision.
- `hero_pos = (64.0, 64.0)` was confirmed live to be a `PLAIN`, unblocked tile in `dungeon_crawl`
  seed 42 before this fix landed -- not derived/validated dynamically against the loaded world, so
  a future `world_id` change could reintroduce a hero-spawns-on-a-wall risk this fix doesn't guard
  against. Flagging, not fixing -- out of this ticket's narrow scope.

## Implementation Notes
Investigated by reading `V2EngineManager.__init__`/`_build()`/`.start()`/`.reset()` directly, then
confirmed the empty-terrain hypothesis with a standalone script constructing
`WorldCompiler.compile(spec, seed=42)` and checking `terrain.get((64,64))` == `"PLAIN"` and
`(64,64) not in blocked_tiles` before touching any code, to de-risk the hero-spawn-position
question ahead of implementation.

`dataclasses.replace(compiled_state, tick=0, seed=self._seed, entities=entities)` was chosen over
constructing a fresh `AuthoritativeState` by hand (which would silently drop every non-entity field
the compiled world populates -- regions, resource nodes, buildings, etc., the same
bare-construction-vs-`dataclasses.replace` class of bug this session already found and fixed once
before in `TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE`).

`create_v2_app`'s three new parameters use a `manager_kwargs` dict built only from non-`None`
values, rather than always passing all three, so `V2EngineManager`'s own class defaults (not a
duplicated set of defaults in `create_v2_app`) remain the single source of truth.

The parity ledger entry was originally authored as `INFRA-389`; merging this branch with
`origin/main` (which had, in the meantime, independently landed `INFRA-389`/`390`/`391` from a
concurrent session) surfaced the exact next-available-id collision `INFRA-391`'s own text already
documents as a known, expected pattern -- renumbered to `INFRA-392`, real content unaffected.

## Test Summary
- `tests/unit/api/test_engine_manager.py` -- 12/12 passing (7.26s)
- `tests/api/` (full suite) -- 120/120 passing (68.13s)
- `tests/unit/api/` (full suite) -- 53/53 passing (7.78s)
- `tests/observability/test_metrics_export.py` + `tests/api/test_scenario_runtime_api.py` --
  21/21 passing
- `tests/unit/api/test_map_route.py`, `tests/api/test_rest_parity.py` -- 4/4 passing (these
  construct their own fake state directly, bypassing `_build()` -- confirmed unaffected, proving
  the route/presenter logic itself was already correct; only `V2EngineManager`'s real boot path
  was broken)
- **Live, real end-to-end**: `frontend/e2e/live_map.spec.ts` run against the actual `make dev`
  command -- passes. Screenshot evidence (`frontend/e2e-artifacts/live_map_render.png`, not
  committed) shows a real rendered map, a live-incrementing tick counter, and a real 10-entity
  roster with HP bars, through an actual headless Chromium browser.
- `docs/parity_ledger/infrastructure.yaml`'s `INFRA-392` entry added and validated
  (`tools/parity_index.py build` succeeded, `tests/tools/test_parity_ledger_schema.py` and
  `tests/integrity/test_parity_guards.py` pass).

## Files Changed
- `src/api/engine_manager.py`
- `src/api/server.py`
- `src/cli/entry.py`
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-392` added)

## Completion Summary
Fixed the real root cause of the live map's terrain never rendering: `V2EngineManager` never
loaded a compiled world at all. This was independent of, and predates, every WS-proxy/auth/metadata
fix shipped earlier in this session -- those were all real and necessary, but none of them could
have made the map itself render terrain, since the channel was structurally empty from the start.
Live-verified end-to-end through a real headless-browser Playwright check against the actual
`make dev` golden path -- the map now genuinely renders.
