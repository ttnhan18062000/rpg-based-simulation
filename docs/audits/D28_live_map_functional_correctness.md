---
status: historical
layer: frontend
authority: P1
audience: developer
tags: [audit, live-map, websocket]
---

# D28 — Live Map Functional Correctness

## Summary

First-ever audit pass for whether the live map (`frontend/src/components/GameCanvas.tsx` +
`useSimulation.ts`, streamed from `src/api/ws/stream.py` via `src/api/engine_manager.py`) actually
works end-to-end through its real, documented golden path (`make dev` -> open
`http://localhost:5173`), as opposed to whether its individual pieces pass unit/component tests in
isolation. The `live-map-reconnection` epic (`TCK-20260821-EPIC-LIVE-MAP-RECONNECTION`, 8 child
tickets, DONE 2026-08-21) built the real WS delta-broadcast/REST bootstrap pipeline and reconnected
the existing frontend to it, but its own live testing never got past the browser boundary at the
time. Three independent, real, severe bugs were found and fixed in this session
(2026-08-25) by building a genuine headless-browser verification loop and driving it to a real
pass — none of them were caught by the epic's own unit/integration test suite, because none of them
are unit-testable in isolation; each one only manifests when the real frontend, real proxy, and
real backend are running together.

**State as of this audit: the live map genuinely renders real terrain and live-updating entity
state through the real `make dev` golden path, confirmed by an actual headless-Chromium screenshot
— for the first time in this feature's documented history.**

## Dimension Profile

| Axis | Value |
|---|---|
| **Group** | New — no existing dimension covers this. `D26` (Visual Quality Module Integration) audits the server-side batch/QA renderer's geometric-metric correctness against `AuthoritativeState` — explicitly not the live player-facing canvas. `D27` (Frontend HUD & Visual Design Quality) audits chrome/panel design quality (color, typography, WCAG) — explicitly not the map canvas's own functional correctness either (see D27's own "the live-canvas gap" section). This dimension is the third, previously-missing piece: does the live map's real-time data + render pipeline actually work at all. |
| **State** | `done` — the golden path now genuinely works, live-verified. Two known, disclosed gaps remain open (see Findings F6/F7) that are explicitly out of this dimension's own scope. |
| **Impact** | 5 / 5 — this is the player-facing core deliverable of the entire live-map-reconnection epic; its absence (as found) meant the feature's central promise — "open a browser, see the simulation live" — never actually worked, regardless of how much of the underlying pipeline was individually unit-tested |
| **Interest** | 4 / 5 — the specific failure pattern (multiple independently-correct-looking layers combining into a fully broken whole, invisible to any single layer's own tests) is a real, generalizable lesson for this project's testing strategy, not just a one-off bug list |
| **Priority** | 9 (Impact + Interest) |
| **Method** | code-read + live-run + real headless-browser verification (`frontend/e2e/live_map.spec.ts` via Playwright, `tools/review_pipeline_check.py`'s sibling pattern for the rendering pipeline) |
| **Audit history** | `2026-08-25 (first pass — see Findings Summary)` |

**Related dimensions:**

| Dimension | Relationship |
|---|---|
| D26 (Visual Quality Module Integration) | Sibling, not overlapping — D26 audits the server-side batch/QA renderer (`src/rendering/`), this dimension audits the live player-facing canvas (`frontend/src/components/GameCanvas.tsx`) and its real-time data pipeline. Different code, different consumers, different failure modes. |
| D27 (Frontend HUD & Visual Design Quality) | Sibling, not overlapping — D27 audits whether the HUD chrome is *well-designed* (color, typography, consistency); this dimension audits whether the live map *functions at all*. A perfectly-designed HUD around a blank, disconnected canvas would pass D27's eventual checks and fail this dimension's, and vice versa. |
| D17 (Documentation Currency) | This audit's own trigger was partly a documentation-currency failure: `TCK-20260825-HOTFIX-MAKEFILE-DEV-LIVE-MAP-DOC` documented "Open http://localhost:5173 to view the live map" without live-verifying it actually worked — exactly the class of gap D17 exists to catch, just not caught by D17 itself this time. |

---

## Findings Summary

| # | Finding | Severity | Status |
|---|---|---|---|
| F1 | `frontend/vite.config.ts`'s `/api` dev-proxy entry was missing `ws: true` — Vite silently drops every WebSocket upgrade request without it, so the live map's WS stream had never actually worked through the real `npm run dev` dev server at any point in this feature's history, independent of auth | High | **CLOSED** — `TCK-20260825-LIVE-MAP-DEV-AUTH-AND-WS-PROXY-FIX` |
| F2 | `TCK-20260823-HTTP-API-KEY-AUTH` added fail-closed API-key auth to every route the live map needs, after the live-map-reconnection epic had already finished; the frontend never sent a key anywhere, and `make dev` configured none — every REST call 401'd, the WS connect got HTTP 403 | High | **CLOSED** — same ticket. `make dev` now configures a fixed dev key; the frontend sends it as a byte-identical no-op when unset |
| F3 | `frontend/src/main.tsx` wraps the *entire app* in `<MetadataProvider>`, which hard-blocked rendering (`<App/>` never mounted, live map included) on any failure of 8 unrelated `/api/v1/metadata/*` routes that turned out to never exist on the backend at all (404, not an auth issue) | High | **CLOSED (mitigated)** — `TCK-20260825-METADATA-PROVIDER-NONBLOCKING-FALLBACK` made the failure non-blocking. The real gap (the 8 missing backend routes) is filed separately and deliberately *not* fixed here: `TCK-20260825-METADATA-API-BACKEND-MISSING`, routed to the not-yet-built HUD epics, since that data feeds HUD detail panels, not the map itself |
| F4 | **Root cause, most severe**: `V2EngineManager._build()` constructed `AuthoritativeState` with no `terrain` argument at all (defaulting to an empty dict) — `GET /api/v1/map` has always returned `width=0/height=0/grid=[]` through the real running server, predating and independent of F1-F3. Every earlier tool used to inspect rendering/world data in this project's history bypassed `V2EngineManager` entirely by calling `WorldCompiler.compile()` directly, which is exactly why this was never caught | Critical | **CLOSED** — `TCK-20260825-V2-ENGINE-MANAGER-MISSING-TERRAIN` wires `WorldCompiler`/`WorldRepository` into `_build()`, preserving the existing hero+goblin-diagonal entity-spawn logic unchanged |
| F5 | No repeatable, agent-invokable way existed to verify the live map actually renders in a real browser — every prior verification in this feature's history stopped at the backend/component-test boundary, explicitly disclosed as a caveat each time | Medium | **CLOSED** — `frontend/e2e/live_map.spec.ts` (Playwright, headless Chromium, real `make dev` golden path) added, `TCK-20260825-LIVE-VERIFICATION-TOOLING`. Re-run any time via `npm run test:e2e` in `frontend/` |
| F6 | 500-entity tick throughput measured at ~7.8-7.9 ticks/sec against a 20 TPS nominal target, roughly 2.6x over the `cli_default` profile's 50ms tick budget | Unconfirmed | **OPEN, DISCLOSED** — re-measured twice (`TCK-20260821-LIVE-MAP-PERF-VALIDATION`, `TCK-20260825-LIVE-MAP-TPS-BUDGET-RECHECK`); this agent could not obtain a genuinely uncontended host to confirm whether this is real engine cost or sandbox swap-pressure noise. Explicitly out of this dimension's own scope — no fix attempted |
| F7 | The dirty-rect/layered rendering-performance rewrite and broadcast-filtering interest-management scaling work (roadmap milestones M2/M3) are entirely unbuilt | Known, planned | **OPEN, DISCLOSED, NOT STARTED** — tracked as their own separate epics (`live-map-rendering-performance`, `live-map-interest-management`), both still `tickets/todos/`, deliberately out of this epic's own scope from the start |

---

## Why None of This Was Caught by Existing Tests

Worth stating explicitly, since it is the generalizable lesson (see Interest rating above): F1
(proxy config), F2 (auth wiring), F3 (unrelated blocking dependency), and F4 (missing terrain load)
are each individually invisible to the test suites that existed before this audit:

- Backend `pytest` suites (`tests/api/`, `tests/unit/api/`) construct `V2EngineManager`/
  `create_v2_app` directly or via `TestClient`, never through the real `npm run dev` Vite proxy —
  F1 cannot manifest there.
- Frontend `vitest` component tests (`useSimulation.test.tsx`, `MetadataContext.test.tsx`) mock
  `fetch`/`WebSocket` entirely — F1, F2, and F3's real HTTP/WS failure modes cannot manifest there
  either.
- Every prior tool used to exercise `src/rendering/`/world-compilation logic
  (`tools/calibrate_rendering.py`, `tools/review_pipeline_check.py`, the perf harness's
  `--internal-serve` mode) calls `WorldCompiler.compile()` directly, bypassing
  `V2EngineManager._build()` — F4 cannot manifest there.

Only a real, live, end-to-end run — real backend process, real `npm run dev` proxy, and (for F4) a
real headless browser reading real canvas pixel data — exercises the actual seams where these bugs
lived. This is the concrete case for why `frontend/e2e/live_map.spec.ts` (F5's fix) is a durable,
not one-off, addition to this project's verification surface.

## Related Documents

| Document | Role |
|---|---|
| `docs/audits/D26_visual_quality_integration.md` | Sibling audit — server-side batch/QA renderer, not the live canvas |
| `docs/audits/D27_frontend_hud_visual_design_quality.md` | Sibling audit — HUD chrome design quality, not functional correctness |
| `docs/architecture/http_api_key_authentication.md` | Section 6 documents the dev-key convention F2's fix introduced |
| `tickets/done/TCK-20260825-LIVE-MAP-DEV-AUTH-AND-WS-PROXY-FIX.md` | F1, F2, F3 |
| `tickets/done/TCK-20260825-METADATA-PROVIDER-NONBLOCKING-FALLBACK.md` | F3 |
| `tickets/todos/TCK-20260825-METADATA-API-BACKEND-MISSING.md` | The real, still-open fix behind F3, deliberately not built as part of this dimension |
| `tickets/done/TCK-20260825-V2-ENGINE-MANAGER-MISSING-TERRAIN.md` | F4 |
| `tickets/done/TCK-20260825-LIVE-VERIFICATION-TOOLING.md` | F5 |
| `tickets/done/TCK-20260825-LIVE-MAP-TPS-BUDGET-RECHECK.md` | F6 |
| `docs/audits/audit_dimensions.md` | The original 18-dimension audit programme's master index — this file intentionally does not add an entry there, matching the precedent D19-D27 already set |
