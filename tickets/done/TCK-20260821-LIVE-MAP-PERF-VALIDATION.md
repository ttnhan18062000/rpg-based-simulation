---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260821-LIVE-MAP-PERF-VALIDATION
phase: done
date: 2026-08-21
tags: [performance, websocket, testing]
---

# TCK-20260821-LIVE-MAP-PERF-VALIDATION

## Title
Measure live-map render FPS and broadcast payload size at CLASS_B/CLASS_C scale

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
The author wants an explicit, measured validation step once the live map is actually connected to real data: observed FPS/update latency against a running world at CLASS_B and CLASS_C hardware-class scale, confirming broadcast payload size stays near the V1-measured ~75KB baseline, and confirming/documenting whether the frontend's interpolation math is genuinely delta-time-based -- investigation found no interpolation exists at all today, so this becomes a factual-finding item rather than a verification of an existing mechanism.

## Scope
- Run a measured session of >=1000 sampled render frames under bounded-viewport load at CLASS_B (2500 entities) and separately CLASS_C (500 entities), reporting p50/p95/p99 frame time and %frames>16.6ms, with full Scoped Claims discipline (Runtime Profile/Hardware Class/Scenario/Execution Mode/RuntimeMode stated)
- Measure per-update broadcast payload size (JSON and msgpack if the delta broadcast routes through it) at both classes, compared like-for-like against the ~75KB V1 baseline (stating explicitly that the V1 baseline was a full-state poll of ~360 entities, not a per-tick delta)
- Build the minimal frontend perf/e2e measurement harness needed (headless browser + rAF sampling + percentile aggregation) since none exists today (vitest only)
- Confirm and document whether interpolation exists in the frontend rendering path; investigation already found it does not (zero lerp/deltaTime/requestAnimationFrame hits in frontend/src/) -- report that entities currently snap to latest position on each data update, with no interpolation, as a factual finding
- Document any budget miss as a finding with root-cause hypothesis, explicitly deferred to a separate future ticket

## Out of Scope
- Fixing any performance issue this ticket finds (measurement and reporting only)
- Building an interpolation/lerp system -- none exists today; building one is new feature work, not in scope here
- Any change to production frontend/backend code paths

## Acceptance Criteria
- [ ] with a live world at CLASS_B (2500 entities) and separately CLASS_C (500 entities), a measured session of >=1000 sampled render frames under bounded-viewport load reports p50<=8ms,p95<=12ms,p99<=16.6ms plus %frames>16.6ms, reported with full Scoped Claims discipline (NOT achieved -- see Implementation Notes: Playwright Chromium install blocked by a network filter, no live data obtained at either entity count)
- [ ] measured per-update broadcast payload size (JSON and msgpack if the delta broadcast routes through it) at both classes stays within an explicitly stated tolerance of the ~75KB V1 baseline, comparing like-for-like (full-state-equivalent, not naive per-delta) (PARTIAL -- CLASS_C(500) fully measured and compared with full Scoped Claims discipline; CLASS_B(2500) not attempted, pre-flight memory guard correctly tripped -- see Implementation Notes)
- [x] report explicitly states that no interpolation system exists in the frontend today (entities snap to latest position on data update) as a factual finding, without proposing or building one
- [x] any budget miss is documented as a finding with root-cause hypothesis, explicitly deferred to a separate future ticket

## Related Tickets
- TCK-20260821-PRESENT-MAP-STATIC
- TCK-20260821-WS-ENTITY-DELTA-BROADCAST
- TCK-20260821-REST-MAP-STATIC-STATS
- TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET
- TCK-20260821-EPIC-LIVE-MAP-RECONNECTION
- TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE (filed at Verify to carry AC4 Finding 1's actionable
  engine bug forward -- `_refresh_dirty_set`/`force_full_scan` fix, deferred from this ticket's own
  Out of Scope)
- TCK-20260825-LIVE-MAP-TPS-BUDGET-RECHECK (filed at Verify round 2 to carry AC4 Finding 3's
  ~7.9-TPS-vs-20-TPS-nominal budget miss forward -- re-measure on uncontended hardware to
  disentangle genuine engine cost from this sandbox's severe resource contention)

## Related Docs
- docs/performance/perf_baseline_policy.md
- docs/engine/performance_contract.md
- docs/archive/performance/performance-report-api-payload.md

## Related Stored Artifacts
None.

## Related Code Areas
- frontend/src/hooks/useSimulation.ts
- frontend/src/hooks/useCanvas.ts
- frontend/src/components/GameCanvas.tsx
- frontend/src/test/useSimulation.test.tsx
- src/api/ws/stream.py

## Assumptions / Open Questions
- perf_baseline_policy.md's CLASS_B/CLASS_C thresholds conflict with certification_contract.md §3's AND-rule (cores AND RAM) -- pre-existing unresolved conflict, not this ticket's job to fix, just state which definition was used
- fully blocked on the other four tickets landing -- nothing to measure until the live connection exists

## Implementation Notes

Followed plan.md's 10 steps. Two corrections were made during Implement, beyond investigation.md's
own Step-1-point-6 correction already baked into the approved plan; both are recorded in full in
`staging_artifacts/TCK-20260821-LIVE-MAP-PERF-VALIDATION/plan.md`'s new "Deviations" section:

1. **`force_full_scan`'s "Phase 17 Law" is dead code.** Plan Step 1 point 7 expected a dedicated
   `Kernel(flags={"force_full_scan": True})` boot to make the WS delta's `changed` list include
   every entity, via `src/engine/pipeline.py::AuthoritativeApplyPipeline._refresh_dirty_set`. A
   full-repo grep found that method has exactly one reference in the whole codebase -- its own
   definition -- it is never called. Live-verified (not just source-read) via a direct in-process
   repro: a dedicated force_full_scan boot produces the same small, mostly-empty per-tick deltas
   as a normal boot. `tools/perf/live_map_ws_payload_measure.py` therefore computes its `full_scan`
   bucket synthetically and in-process (no second server), through the same
   `StatePresenter.present_entity_slim` + `jsonable_encoder` + `json.dumps`/`msgpack.packb` code
   path the real WS handler uses, clearly labeled as a synthetic estimate, not a live capture. This
   is reported as AC4 Finding 1 (report.md), deferred to a new ticket -- not fixed here
   (`src/engine/pipeline.py` changes are barred by this ticket's Out of Scope).
2. **Harness-script-only bug**: `tools/perf/live_map_ws_payload_measure.py`, run as a script file
   (not `python3 -c`), had `sys.path[0]` resolve to its own directory, which has no `src/` package
   -- Python fell through to this venv's editable-install finder, which points at the *main
   checkout's* `src/`, a different (and in this case behaviorally divergent -- it lacks
   `present_entity_slim`) git worktree. Fixed by inserting the script's own computed `REPO_ROOT`
   (via `Path(__file__).resolve().parents[2]`) at the front of `sys.path` before any `src.*` import,
   applied uniformly to both the driver process and the `--internal-serve` subprocess since both
   re-execute the same file. Caught via a smoke-test AttributeError before any numbers were
   reported, not after.

Execution results:

- **CLASS_C (500 entities), backend payload size: fully obtained.** Steady-state (100 warmup +
  1000 sampled real per-tick deltas, live WS capture): JSON p50=8,435B / p95=71,300B /
  p99=71,309B / mean=17,561B (highly bimodal -- see AC4 Finding 2); msgpack secondary sample
  384-489B (different, later time window than the JSON sample -- see report.md's caveat).
  Full-scan (synthetic, all 500 entities): JSON 68,907B (137.8B/entity), msgpack 47,680B. Scaled
  to V1's measured 360-entity baseline, V2's full-scan JSON is ~49.6KB, 34% smaller than V1's
  ~75KB -- outside an explicitly-stated +/-25% tolerance band, but in the safe direction.
- **CLASS_B (2500 entities), backend: not attempted.** Pre-flight guard correctly tripped (1234MB
  available < 2500MB required) -- exactly the outcome plan.md's Open Question 2 anticipated given
  this sandbox's tight, shared-machine memory budget (as low as ~125-240MB free / ~1.2GB available
  throughout this session, swap 3.9-4.0/4.0GB used at session start).
- **Frontend render-timing harness: built, not executed.** `frontend/perf/live_map_render_timing.mjs`
  is a complete, ready-to-run Playwright implementation (backend+frontend boot, `X-API-Key`
  injection via `context.route`, WS host/key rewrite via `context.addInitScript` -- routes around
  `vite.config.ts`'s missing `ws: true` without editing that file -- imposed rAF sampling loop,
  percentile computation, resource guards). `npm install -D playwright` succeeded;
  `npx playwright install chromium` failed with a genuine network-level block, confirmed via
  `openssl s_client -connect cdn.playwright.dev:443` returning a Fortinet/Fortiguard "SDNS Blocked
  Page" certificate rather than the real CDN's -- not a flaky/retryable error, and not
  worked around by fabricating frame-timing numbers, per plan.md's own disclosed Gap #3 and this
  ticket's explicit instructions. AC1 (render FPS) is therefore not measured with live data at
  either entity count.
- Interpolation finding (AC3) and both engine findings beyond the dead-code one (AC4 Findings 2
  and 3: steady-state payload bimodality; observed ~7.9 TPS vs. 20 TPS nominal at 500 entities)
  are documented in full in `staging_artifacts/TCK-20260821-LIVE-MAP-PERF-VALIDATION/report.md`.
- No orphaned `uvicorn`/Chromium/`vite` processes remained after any run (process-group kill via
  `start_new_session=True`+`os.killpg` in Python, `detached: true`+`process.kill(-pid, 'SIGTERM')`
  in Node; confirmed with `ps aux` at the end of the session).

## Test Summary

Build Gate List (plan.md), all run under `.venv/bin/python3` where required:

- `pytest tests/unit/api/test_read_model_cache.py tests/unit/api/test_engine_manager.py -q` --
  **24/24 passed.**
- `pytest tests/api/test_ws_protocol.py -v` and `pytest tests/api/ -k "ws or websocket" -v` --
  **corrected during Test phase verification (was misreported here as 6 failed/4 passed):**
  those tests' own `subprocess.Popen(["python3", "-m", "src", "serve", ...])` spawns a child that
  resolves bare `python3` via the inherited `PATH`, not `sys.executable` -- so running pytest
  itself under `.venv/bin/python3` does not fix the child's own lookup.
  `tickets/done/TCK-20260823-LIVE-TEST-API-KEY-AUTH.md` already diagnosed this exact symptom in
  this exact file and established the correct fix: prepend `.venv/bin` to `PATH` before invoking
  pytest, matching CI's `setup-python` resolution. Applying that established fix (`export
  PATH="/home/u24desktop/Working/rpg-based-simulation/.venv/bin:$PATH"` then `pytest
  tests/api/test_ws_protocol.py -v`) gives **5 passed, 0 failed**; the `-k "ws or websocket"`
  filter gives **10 passed, 0 failed, 110 deselected**. Independently re-confirmed twice (Test
  phase, then orchestrator). The original 6-failed/4-passed number was an artifact of not applying
  TCK-20260823's already-established PATH fix, not a real or pre-existing gap -- this ticket
  introduces no WS regression. This ticket's own `tools/perf/live_map_ws_payload_measure.py`
  avoids the same trap by using `sys.executable` for its `--internal-serve` subprocess.
- `cd frontend && npx vitest run src/test/useSimulation.test.tsx` -- **10/10 passed**, unchanged,
  re-run after both the Playwright devDependency install and the `frontend/perf/` harness file
  were added.
- `cd frontend && npm run build` -- **clean 0-error build.** `frontend/perf/live_map_render_timing.mjs`
  is outside `tsconfig.app.json`'s `include: ["src"]`, confirmed not to participate in `tsc -b`.
- `grep -rniE "requestAnimationFrame|\blerp\b|deltaTime|interpolat" frontend/src/` -- **zero
  matches**, re-confirmed immediately before writing report.md.
- `git diff --stat -- frontend/src/hooks/useSimulation.ts frontend/src/hooks/useCanvas.ts
  frontend/src/components/GameCanvas.tsx src/api/ws/stream.py` -- **empty**, confirmed at the end
  of implementation. All four Out-of-Scope files are untouched.

## Files Changed

- `tools/perf/live_map_ws_payload_measure.py` (new) -- backend WS payload-size measurement
  harness (Step 1).
- `staging_artifacts/TCK-20260821-LIVE-MAP-PERF-VALIDATION/raw/ws_payload_500.json` (new) --
  CLASS_C measurement output (Step 2).
- `staging_artifacts/TCK-20260821-LIVE-MAP-PERF-VALIDATION/raw/ws_payload_2500_ABORTED.json`
  (new) -- CLASS_B pre-flight-guard-tripped marker (Step 3).
- `frontend/package.json`, `frontend/package-lock.json` (modified) -- added `playwright` as a
  devDependency only (Step 4).
- `frontend/perf/live_map_render_timing.mjs` (new) -- frontend Playwright render-timing harness,
  built but not executed in this sandbox (Step 5).
- `staging_artifacts/TCK-20260821-LIVE-MAP-PERF-VALIDATION/report.md` (new) -- the ticket's
  measurement/reporting deliverable (Step 10).
- `staging_artifacts/TCK-20260821-LIVE-MAP-PERF-VALIDATION/plan.md` (modified) -- added a
  "Deviations" section documenting the two corrections made during Implement.
- `tools/validate_frontmatter.py` (modified) -- added `"report"` to `ARTIFACT_TYPE_VALUES`
  (previously only `investigation`/`plan`/`test_plan`), needed so `report.md`'s
  `artifact_type: report` frontmatter (a new kind of staging deliverable -- a post-implementation
  findings/measurement report, not a pre-implementation planning artifact) validates. Flagged as
  missing from this section during Verify round 3 and added here to match the actual `git diff`.
- `tickets/inprogress/TCK-20260821-LIVE-MAP-PERF-VALIDATION.md` (this file, modified) --
  Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary.

Note: `staging_artifacts/TCK-20260821-LIVE-MAP-PERF-VALIDATION/investigation.md` and `test_plan.md`
were already present (written during this ticket's earlier Investigate/Plan phases, before this
Implement run started) and were not modified by this Implement pass.

## Completion Summary

Built two standalone, resource-guarded measurement harnesses (`tools/perf/live_map_ws_payload_measure.py`
for backend WS payload size, `frontend/perf/live_map_render_timing.mjs` for frontend render
timing) and ran the backend one live against a real server at CLASS_C scale (500 entities),
obtaining full steady-state and synthetic full-scan payload-size numbers compared against the V1
baseline with Scoped Claims discipline. CLASS_B (2500 entities) was correctly not attempted per
its own pre-flight memory guard, and the frontend harness could not be executed because
Playwright's Chromium download is blocked by this sandbox's network filter (confirmed via
`openssl s_client`, not assumed) -- both are honestly disclosed rather than worked around. The
interpolation factual finding (AC3) and three engine/measurement findings (AC4), including a
newly-discovered dead-code gap in `src/engine/pipeline.py`'s `force_full_scan` full-scan logic,
are fully documented in `report.md`. The four Out-of-Scope files show an empty `git diff --stat`.
AC4 Finding 1's actionable engine bug was filed as a concrete follow-up ticket at Verify time --
`tickets/todos/TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE.md` -- rather than left as a bare "deferred"
promise with no filed ticket, per the Verify pass's own finding that this repo's convention
requires a citable ticket ID, not just a stated intent. Verify round 2 found the same gap applied
to Finding 3's TPS budget miss (`report.md` had used identical "deferred to a new ticket" prose with
no ticket actually filed); fixed the same way --
`tickets/todos/TCK-20260825-LIVE-MAP-TPS-BUDGET-RECHECK.md` now carries that finding forward.
Finding 2 (steady-state payload bimodality) was reviewed and judged not to need the same treatment:
its own text is phrased as an open observation ("a future ticket **could** correlate...") rather
than a stated budget miss with a definite deferral, so it does not fall under AC4's "any budget
miss ... explicitly deferred" requirement the way Findings 1 and 3 do.
