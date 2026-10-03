---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260821-LIVE-MAP-PERF-VALIDATION
artifact_type: test_plan
tags: [performance, websocket, testing]
---

# Test Plan — TCK-20260821-LIVE-MAP-PERF-VALIDATION

## Regression Surface

This ticket adds a measurement harness and produces a report; it does not change
`frontend/src/hooks/useSimulation.ts`, `frontend/src/hooks/useCanvas.ts`,
`frontend/src/components/GameCanvas.tsx`, or `src/api/ws/stream.py`. The regression surface is
therefore "prove nothing broke while building/running the harness," not "prove a behavior change is
correct."

- unit (frontend): `cd frontend && npx vitest run src/test/useSimulation.test.tsx` — must stay
  10/10 passing, unchanged, exactly as ticket 6 left it. This is the existing mocked-WebSocket
  regression guard; it should not need to change for this ticket.
- unit (frontend): `cd frontend && npm run build` (`tsc -b && vite build`) — must stay a clean
  0-error build. Any new harness code that imports frontend types must not break this.
- integration (backend, already-shipped auth pattern this ticket reuses): the 9 test functions in
  `tickets/done/TCK-20260823-LIVE-TEST-API-KEY-AUTH.md`'s Scope, most relevantly
  `tests/api/test_ws_protocol.py::test_ws_json_handshake` and `::test_ws_msgpack_handshake`
  (they exercise the exact `/api/v1/ws` route and auth pattern this ticket's own backend-side
  measurement reuses) — run these to confirm the auth/WS mechanism this ticket depends on hasn't
  regressed before building on top of it:
  `.venv/bin/python3 -m pytest tests/api/test_ws_protocol.py -v` (must run under the
  pydantic-capable `.venv/bin/python3`, not the bare worktree `python3` — see investigation.md's
  "Search-Before-Grep Compliance Note" and "Prior Work" for why).
- backend unit: `pytest tests/unit/api/test_read_model_cache.py` — covers `compute_tick_delta`,
  the function this ticket's payload-size measurement reads from; must stay green as a precondition,
  not something this ticket touches.
- backend unit: `pytest tests/unit/api/test_engine_manager.py` — covers `V2EngineManager`
  construction with a custom `entities_count`, the exact mechanism the harness reuses to reach
  2500/500 entities; must stay green.

## New Tests / Artifacts Required

This ticket's "tests" are mostly measurement scripts producing a report, not pytest assertions —
per Out of Scope ("measurement and reporting only"), there is no new pass/fail gate to add to CI.
Where a genuine automatable check is possible, it's listed below; everything else is a one-shot
harness script whose *output* (the report) is the deliverable.

1. **Backend WS payload-size measurement script** (not a pytest test — a standalone script, since
   it needs to run against a purpose-built 2500/500-entity world, which is not a CI-appropriate
   fixture size)
   - What it does: boots a `V2EngineManager(profile, entities_count=2500)` (and separately `=500`)
     directly (reusing the pattern from `tests/perf/test_api_projection_perf.py` /
     `tests/observability/test_metrics_export.py` — no CLI `--entities` flag needed, since that flag
     is confirmed dead code for `serve` — see investigation.md), installs it via
     `src.api.dependencies.set_engine_manager`, starts it, and connects a raw Python `websockets`
     client to `/api/v1/ws` using the same `additional_headers={"X-API-Key": raw_key}` +
     `RPG_API_KEY_HASHES`-seeded pattern `TCK-20260823-LIVE-TEST-API-KEY-AUTH` already proved works.
   - Captures: byte length of every received WS message (`json.dumps`/raw `send_json` body length,
     and separately a `format: 'msgpack'` handshake run for the secondary msgpack data point), over
     ≥1000 sampled ticks after ≥100 warmup ticks (per `docs/engine/performance_contract.md` §3.2).
   - Specifically flags and separately reports messages on `tick % 20 == 0` (the full-scan/heartbeat
     shape) vs. steady-state delta messages — do not blend these into one number (see
     investigation.md's "Anti-Drift Hazards").
   - Where it lives: `tools/` or `tests/perf/` (a location decision for Plan — since it needs a
     synthetic 2500-entity world and isn't meant to run in normal CI, `tools/` with a `--help`-documented
     one-off script is likely the better fit than `tests/perf/`, which today runs in CI per
     `docs/testing/test_taxonomy.md`).
   - Category: integration / manual-measurement script, not a CI-gating unit test.

2. **Frontend headless-browser render-timing harness** (new infrastructure — the ticket's own
   "Build the minimal frontend perf/e2e measurement harness ... since none exists today" item)
   - Prerequisite (Plan/Implement must verify, not assume — see investigation.md's Risk #4):
     `npm install -D playwright && npx playwright install chromium` actually succeeds in this
     environment. Connectivity checks passed; the real download was not attempted in this
     investigation pass.
   - What it does: launches a real Chromium instance via Playwright, navigates to the running
     `npm run dev` frontend, uses an `addInitScript` to (a) rewrite outgoing `X-API-Key` headers on
     `/api/v1/*` REST calls via `page.route(...)`, and (b) rewrite the `window.WebSocket`
     constructor to append `?key=<raw>` and redirect the target host to the real backend port
     (bypassing the `vite.config.ts` proxy's missing `ws: true` — see investigation.md). Confirmed
     safe: `src/api/ws/stream.py` performs no `Origin` header check.
   - Samples real paint timing via `requestAnimationFrame` callbacks injected into the page
     (measuring wall-clock delta between consecutive rAF callbacks as a proxy for frame time, since
     the app itself has no rAF loop to hook — the harness must impose the sampling loop, not
     observe an existing one; see investigation.md's "Frontend render path" finding).
   - Collects ≥1000 samples under "bounded-viewport load" (i.e., with the canvas visible and the
     WS delta stream actively driving redraws — not an idle/paused simulation) at CLASS_B(2500) and
     separately CLASS_C(500) backend scale (reusing script #1's server-boot mechanism).
   - Reports p50/p95/p99 frame time and `%frames > 16.6ms`, per the AC.
   - Category: new e2e/perf harness, `frontend/` (a new directory, e.g. `frontend/perf/` or
     `frontend/e2e/` — not `frontend/src/test/`, since it needs a real browser + real backend, not
     jsdom + mocks, and should not run under the existing `vitest` config's `jsdom` environment).
   - This is the single largest new-engineering item in this ticket. If Plan decides the
     WebSocket-rewrite/header-injection technique is out of bounds (see investigation.md's Open
     Question #1), this entire item becomes infeasible in this sandbox and the render-FPS AC cannot
     be met with real live data — that determination should be made explicitly, not discovered
     mid-implementation.

3. **Interpolation factual-finding write-up** (already fully verified in investigation.md — no new
   test needed, since the claim is "no interpolation exists," proven by an exhaustive repo-wide
   grep with zero hits plus a full read of both render-loop files). The only "test" here is citing
   the grep command and file:line evidence in the final report, which investigation.md already has.

4. **Architecture guard (optional, low-cost, recommended)**: a `grep`-based check (or a small
   pytest/vitest assertion) that `frontend/src/` contains zero `requestAnimationFrame`/`lerp`/
   `deltaTime` hits, wired as a lightweight regression guard so a *future* PR that silently adds
   interpolation doesn't invalidate this ticket's factual finding without anyone noticing. Judgment
   call for Plan: this is adjacent scope-creep-adjacent (it's a guard *for* the finding, not part of
   measuring it) — include only if Plan agrees it's cheap enough to be worth it; not a hard
   requirement of this ticket's AC.

## Scoped Pytest Commands

```bash
# Auth/WS mechanism precondition (must be green before building on top of it)
.venv/bin/python3 -m pytest tests/api/test_ws_protocol.py -v

# compute_tick_delta / read-model-cache precondition
pytest tests/unit/api/test_read_model_cache.py -v

# V2EngineManager construction-with-custom-entity-count precondition
pytest tests/unit/api/test_engine_manager.py -v

# Existing WS-related regression guard already covering src/api/ws/stream.py more broadly
pytest tests/api/ -k "ws or websocket" -v
```

```bash
# Frontend regression guard
cd frontend && npx vitest run src/test/useSimulation.test.tsx
cd frontend && npm run build
```

Never `pytest tests/` (full suite) and never a bare `npx vitest run` (full frontend suite) — both
scoped to the domains this ticket's harness sits on top of, per CLAUDE.md's Testing Rule.

## Anti-Drift Test Guards

- Re-run `cd frontend && npx vitest run src/test/useSimulation.test.tsx` after building the
  Playwright harness to confirm the harness's Playwright/e2e additions to `frontend/package.json`
  (new devDependency) don't change vitest's resolution or break the existing mocked-WS suite.
- Re-run `grep -rniE "requestAnimationFrame|\blerp\b|deltaTime|interpolat" frontend/src/` immediately
  before writing the final report — if this ticket's own harness work accidentally touches
  `frontend/src/` (it shouldn't; harness code belongs outside `frontend/src/`), this guard catches
  the report's central factual claim silently going stale.
- Confirm `git diff --stat -- frontend/src/hooks/useSimulation.ts frontend/src/hooks/useCanvas.ts frontend/src/components/GameCanvas.tsx src/api/ws/stream.py`
  is empty at the end of this ticket — these four files are explicitly Out of Scope for
  modification; any diff here is scope creep, full stop.
- If script #1 (backend payload measurement) is added under `tests/perf/`, confirm it does **not**
  get silently picked up by `tests/perf/test_perf_regression_baseline.py`'s existing baseline
  comparison machinery (which per `docs/performance/perf_baseline_policy.md` §3's correction note
  compares `avg_tick_compute_ms`, not payload bytes) — a mismatch there would fail CI for an
  unrelated reason. Prefer `tools/` for this reason unless Plan explicitly confirms `tests/perf/`
  isolation is safe.
- Confirm the final report explicitly states Hardware Class = CLASS_C for this sandbox
  (`certification_contract.md`'s AND-rule; 4 cores / 5.8GB RAM measured) regardless of which entity
  count (2500 or 500) was used in a given scenario run — grep the draft report text for the literal
  string "CLASS_B" and manually verify every occurrence is scoped to "scenario entity-count target,"
  never to "this machine's certified hardware class," before treating the report as final.
