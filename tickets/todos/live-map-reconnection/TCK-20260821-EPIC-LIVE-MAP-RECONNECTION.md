---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260821-EPIC-LIVE-MAP-RECONNECTION
phase: open
date: 2026-08-21
tags: [architecture, api-design]
---

# TCK-20260821-EPIC-LIVE-MAP-RECONNECTION

## Title
Reconnect the existing player-facing live map renderer to the real V2 backend (map data,
static objects, live entity positions, pause/resume) — no HUD/info-display work

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
`frontend/src/components/GameCanvas.tsx` + `frontend/src/hooks/useCanvas.ts` are a real, already-built
live map renderer (pan/zoom, cached minimap, fog-of-war, region/location labels, building icons, entity
dots, hover tooltips). It renders nothing today because its data layer, `useSimulation.ts`, was built
against a contract the real V2 backend never implements: a different streaming transport (SSE vs. the
real WebSocket), 5 missing REST routes, unsupported query params on an existing route, and — the deeper
finding — no per-tick entity-position broadcast exists in any shape today. The user explicitly chose to
reconnect this existing frontend (not build a new client against the separate server-owned rendering core
idea) and explicitly scoped this to the live map only: "focus on rendering live map first, don't need to
sculpt the HUD for information displaying now, using simple is enough."

**Major follow-up finding (2026-08-21 git archaeology)**: this contract isn't a design gap — it's
**already-built, already-measured V1 code** (`src_legacy/api/routes/map.py`, `state.py`, `stream.py`,
`presenters/state_presenter.py`, `presenters/world_presenter.py`, `schemas.py`), deleted wholesale by
commit `677abbfb` and never re-ported to V2. `useSimulation.ts`'s exact query params
(`?since_tick=&selected=`) and payload shape (`{tick,changed,removed,events}`) match V1's real, tested,
measured implementation (91% payload-size reduction, documented in
`docs/archive/performance/performance-report-api-payload.md`) precisely — this was never speculative
frontend code. Every deleted file is recoverable via `git show 677abbfb^:<path>` and is the concrete
reference this epic's child tickets port and adapt (transport modernized to V2's real WebSocket; payload
design reused as-is). Full trace: `docs/plans/live_map_reconnection_epic.md`.

## Scope
- New `StatePresenter` methods serializing existing live `AuthoritativeState` fields (`terrain`,
  `buildings`, `resource_nodes`, `chests`, `ground_items`) into the frontend's `MapData`/`StaticData`
  shapes — ported from `src_legacy/api/routes/map.py` and
  `src_legacy/api/presenters/world_presenter.py::to_static_data_response`.
- A new lightweight per-tick entity-delta broadcast (using the tick loop's existing `DirtySet` tracking)
  carrying `{tick, changed, removed, events}` over the real `/api/v1/ws` WebSocket connection — payload
  design ported from `src_legacy/api/routes/stream.py::compute_delta()`, transport modernized from V1's
  Redis-Streams/SSE to V2's existing WebSocket tick-listener path. Use the already-negotiated-but-unused
  `msgpack` wire format (`src/api/ws/stream.py`'s handshake already supports it).
- New REST routes: `/api/v1/map`, `/api/v1/static`, `/api/v1/stats` (ported `SimulationStats` shape:
  `tick, world_day, alive_count, total_spawned, total_deaths, running, paused`). `total_spawned`/
  `total_deaths` need two new counters on `V2EngineManager` — confirmed absent today; V1's pattern
  (`self._total_spawned`/`self._total_deaths`, incremented per tick by `len(new_ids)`/`len(dead_ids)`) is
  the proven reference.
- `present_static`'s region serialization needs real design work, not a lookup: `RegionRecipeSpec`
  (`src/worldbuilding/recipe.py`) has no `center`/`radius`/`locations`/`difficulty`/`name` fields at all —
  confirmed absent from the entire worldbuilding/worldassembly tree and the real compiled
  `data/worlds/sandbox_world/world.yaml`. `center`/`radius` must be derived from `grid_bounds` at
  presentation time; `locations`/`difficulty`/`name` need a source identified or dropped from scope.
- Rewire `useSimulation.ts` (only) from `EventSource`/`/api/v1/stream` to the real WebSocket protocol at
  `/api/v1/ws`; map its `sendControl` calls onto the two real existing `/control/pause`/`/control/resume`
  routes.
- A real performance-validation pass once connected: observe actual FPS/update latency at both `CLASS_B`
  (2,500 entities, <40ms/tick) and `CLASS_C` (500 entities, <30ms/tick) per
  `docs/performance/perf_baseline_policy.md`'s registered hardware classes, and confirm broadcast payload
  size lands near the V1-measured ~75KB/update baseline (not the pre-optimization ~800KB–1.6MB) as a
  concrete regression check. Reported per `docs/engine/performance_contract.md`'s scoped-claims discipline
  — not assumed, not a bare number. Any real optimization need this surfaces is a separate future ticket.
- Give the new broadcast message an explicit schema-version marker and treat its shape as additive-only
  from day one — cheap now, expensive to retrofit once a second client type depends on it (see plan doc's
  "Real-Time Transfer & Multi-Client Design Guidance").

## Out of Scope
- Any new UI panel beyond what `GameCanvas.tsx` already renders (its minimap + locations panel is
  map-navigation, not HUD, and stays as-is).
- Wiring the real, already-existing HUD components (`Sidebar.tsx`, `EntityList.tsx`, `EventLog.tsx`,
  `InspectPanel.tsx`, `ControlPanel.tsx`, `BuildingPanel.tsx`, `LootPanel.tsx`, `ClassHallPanel.tsx`,
  `Legend.tsx`) to real data — they exist as code, rendered by `App.tsx` alongside `GameCanvas`; connecting
  their specific information-display needs is deferred per direct user instruction.
- `/api/v1/speed` UI polish (route wiring can ride along if trivial; no new widget) and `/api/v1/clear_events`
  (route + UI both deferred, tied to the World Log HUD feature).
- Any speculative rendering-performance rewrite not driven by this epic's own real measurement pass.
- Building a new client against `docs/plans/world_rendering/idea_world_rendering_core.md`'s "Option C"
  server-owned rendering core — explicitly ruled out this session in favor of reconnecting the existing
  frontend.

## Acceptance Criteria
- [ ] A documented, ordered child-ticket breakdown exists (this ticket + its plan doc) that a later
      `/create-tickets` pass can use directly
- [ ] Each child ticket, when opened, references this epic and `docs/plans/live_map_reconnection_epic.md`
- [ ] No implementation happens directly on this epic ticket or its plan doc

## Related Tickets
- `TCK-20260820-EPIC-WORLD-RENDERING-CORE` — a distinct, unrelated sibling system (server-side batch/QA
  measurement renderer for visual-quality scoring, not a player-facing live view). Neither epic depends on
  the other.

## Related Docs
- `docs/plans/live_map_reconnection_epic.md` — this epic's full plan doc, investigation trail, and the
  full `src_legacy` git-archaeology findings
- `docs/engine/contracts/frontend.md` — the existing "Known gap (2026-07-16)" this epic's investigation
  confirms and extends
- `docs/plans/world_rendering/idea_world_rendering_core.md` — the alternative architecture explicitly not
  chosen
- `docs/engine/performance_contract.md`, `docs/performance/perf_baseline_policy.md` — scoped-claims
  methodology and `CLASS_B`/`CLASS_C` hardware-class targets for the performance-validation criterion
- `docs/archive/performance/performance-report-api-payload.md` — the measured V1 payload-size baseline
  (~75KB post-optimization) this epic's own performance criterion is grounded against
- `tickets/done/infra-04-realtime-state-streaming.md` — the historical ticket whose incomplete step 4 is
  this epic's root cause

## Related Stored Artifacts
None.

## Related Code Areas
- `src/api/presenters/state_presenter.py` — new `present_map`/`present_static` methods
- `src/api/read_model_cache.py`, `src/api/engine_manager.py` — per-tick delta broadcast plumbing
- `src/api/ws/stream.py` — the real WebSocket protocol the frontend must speak
- `src/core/state.py` (`AuthoritativeState`) — source of the real `terrain`/`buildings`/`resource_nodes`/
  `chests`/`ground_items` runtime data
- `src/api/server.py` — new REST route registration
- `frontend/src/hooks/useSimulation.ts` — the only frontend file this epic's child tickets touch
- `frontend/src/types/api.ts` — target shapes (`MapData`, `StaticData`, `SimulationStats`, `WorldState`)
- `frontend/src/components/GameCanvas.tsx`, `frontend/src/hooks/useCanvas.ts` — read-only reference for
  the target contract; not modified by this epic
- `src_legacy/api/routes/map.py`, `state.py`, `stream.py`, `src_legacy/api/presenters/state_presenter.py`,
  `world_presenter.py`, `src_legacy/api/schemas.py` — deleted by commit `677abbfb`, recoverable via
  `git show 677abbfb^:<path>`; the proven reference implementation each child ticket ports from

## Assumptions / Open Questions
- **Region spatial data — fully resolved, and it's a real gap.** `RegionRecipeSpec` has no `center`,
  `radius`, `locations`, `difficulty`, or `name` field — confirmed by reading it in full and grepping the
  entire worldbuilding/worldassembly tree plus the real compiled `sandbox_world/world.yaml`. V1 had the
  same *pattern* (spatial regions separate from governance state) but its version actually had these
  fields; V2 doesn't. The relevant child ticket must derive `center`/`radius` from `grid_bounds` and either
  find a source for `locations`/`difficulty`/`name` or drop them from the ported schema — real design work,
  not a lookup.
- **`total_spawned`/`total_deaths` — fully resolved.** V1's exact pattern found
  (`src_legacy/api/engine_manager.py` L73-74/221-222/400-405) and confirmed absent from
  `V2EngineManager` today via direct grep. The relevant child ticket adds the same two simple counters.
- Whether the new per-tick delta broadcast extends the existing `/ws` payload or registers as a separate
  message type is an implementation-detail decision left to that child ticket's own investigation — V1's
  fully-separate-transport precedent shows both approaches are legitimate.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
