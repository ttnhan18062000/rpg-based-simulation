---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260821-LIVE-MAP-PERF-VALIDATION
artifact_type: plan
tags: [performance, websocket, testing]
---

# Implementation Plan — TCK-20260821-LIVE-MAP-PERF-VALIDATION

## Summary

This ticket measures and reports, it does not fix or build production behavior. The plan builds two
standalone harness scripts (backend WS payload-size measurement, frontend Playwright render-timing
harness), runs each at CLASS_C-scale (500 entities) as the sandbox-trustworthy primary result, makes
one best-effort, explicitly-caveated attempt at CLASS_B-scale (2500 entities) with a hard resource
abort guard, and writes a single report artifact under `staging_artifacts/` that states Scoped Claims
discipline (Runtime Profile/Hardware Class/Scenario/Execution Mode/RuntimeMode), the true CLASS_C
hardware classification of this sandbox regardless of entity count used, the interpolation
factual-finding (already fully verified in investigation.md), and any budget miss with a root-cause
hypothesis deferred to a future ticket. Two open questions from investigation.md are resolved here,
not left to Implement: (1) the Playwright WS-constructor-rewrite + header-injection technique is
IN SCOPE as harness-only code; (2) the CLASS_B(2500) run is attempted once, resource-bounded, with a
pre-declared fallback to CLASS_C-only reporting if it OOMs or the machine can't sustain it — this is
decided now, not improvised mid-Implement under memory pressure.

## Resolution of Open Questions (binding on Implement)

### Open Question 1 — Playwright WS-rewrite + header-injection technique: IN SCOPE

**Decision: yes, build it as harness-only code.**

Reasoning: investigation.md's "Auth gate" and "Dev-proxy `ws: true` gap" sections (lines 113-176)
establish that (a) the technique touches zero files under `frontend/src/` or `src/` — it is a
Playwright `page.route()` interceptor and a `window.WebSocket` constructor override injected via
`addInitScript`, both of which live entirely in harness code outside the app's own source tree; (b)
it does not bypass `src/api/auth.py`'s validation — the key is still checked normally by
`require_api_key_ws` (`src/api/auth.py:110-125`), the harness only supplies a legitimately-seeded key
the same way `tests/api/test_ws_protocol.py` already does over a raw `websockets` client
(`additional_headers={"X-API-Key": raw_key}`, proven in `tickets/done/TCK-20260823-LIVE-TEST-API-KEY-AUTH.md`);
(c) it does not touch `frontend/vite.config.ts` — it routes *around* the proxy's missing `ws: true`
by having the injected script rewrite the WS target host before construction, which
`src/api/ws/stream.py` permits (no `Origin` header check, confirmed by investigation.md's full read
of that file). This is the same class of technique as the already-shipped
`additional_headers` pattern, applied at the browser/page level instead of the Python-client level.
Building the render-timing harness without this technique is not possible in this sandbox (no static
frontend build served from the backend's own origin exists — investigation.md confirmed no
`StaticFiles`/`mount()` in `src/api/server.py`), so declining this would make AC1 (render FPS)
entirely unmeasurable with live data, which is a worse outcome than using well-scoped harness-only
instrumentation.

### Open Question 2 — CLASS_B(2500) attempt strategy: resource-bounded best-effort, CLASS_C is primary

**Decision: run CLASS_C(500) first as the sandbox-trustworthy primary result for both ACs. Attempt
CLASS_B(2500) exactly once, after CLASS_C succeeds, with a hard pre-flight and in-flight memory guard.
If it fails the guard, abort cleanly and report CLASS_B as "not attempted — sandbox resource guard
tripped" rather than reporting numbers produced under memory pressure.**

Reasoning: investigation.md measured ~1.2GB available RAM with swap already at 4.0Gi/4.0Gi (Risk #2).
A 2500-entity `AuthoritativeState` plus a concurrent headless Chromium instance is a real OOM risk
that would produce swap-thrashing latency spikes indistinguishable from genuine render cost in the
p50/p95/p99 numbers — i.e., a "successful" CLASS_B run under these conditions could silently produce
garbage data reported as if it were signal, which is worse than an honest "not attempted." A pure
skip (never trying CLASS_B at all) would under-deliver against the ticket's own scope line ("at
CLASS_B (2500 entities) and separately CLASS_C (500 entities)") without giving Verify/the report
reader any real evidence either way. The middle path — one bounded, guarded attempt, with a
pre-declared exact abort condition and honest reporting either way — is the only option that respects
both the ticket's scope (attempt the number the AC names) and the resource-honesty rule (don't launder
thrashing as signal). Concrete guard, to be implemented in Step 5:
- Pre-flight: `free -m` available memory must show >=2500MB before the CLASS_B backend process is
  even started (2500-entity `AuthoritativeState` + FastAPI + uvicorn + Chromium headless realistically
  need this much headroom on top of the ~1.2GB baseline measured in investigation). If pre-flight
  fails, do not start the CLASS_B run at all; report "not attempted — pre-flight memory check failed,
  Xmb available < 2500MB required" with the measured number.
- In-flight: the backend measurement script (Step 2) and the Playwright harness (Step 4) each poll
  `free -m`'s available column once every 50 sampled ticks/frames; if available memory drops below
  300MB at any check, abort the run immediately, kill the child backend/browser process, and record
  "aborted at sample N — memory guard tripped" rather than continuing to collect increasingly noisy
  samples. Kill by process group, not a single PID: launch the subprocess with `start_new_session=True`
  (or equivalent) and terminate via `os.killpg(pid, SIGTERM)`, escalating to `SIGKILL` after a short
  grace period if it hasn't exited — `uvicorn` and headless Chromium both spawn their own child
  processes that a plain `Popen.terminate()`/`kill()` on the parent PID alone would leave running and
  still holding memory, defeating the guard's purpose.
- Either way (full completion or guarded abort), CLASS_B's outcome is reported as a secondary,
  clearly-labeled data point. CLASS_C(500)'s result is what the report calls the primary,
  sandbox-trustworthy measurement for both AC1 and AC2.

## Steps

### Step 1 — Backend WS payload-size measurement script (CLASS_C scale, 500 entities)
**Files:** New file `tools/perf/live_map_ws_payload_measure.py` (new directory `tools/perf/` — no
existing `tools/perf/` directory found; `tools/` itself exists per investigation.md's citation of
`tools/knowledge_search.py`, `tools/tag_registry.py`, etc. as siblings).
**Change:** A standalone script (not a pytest test — test_plan.md's item 1 explicitly calls this a
"standalone script, since it needs to run against a purpose-built 500/2500-entity world, which is not
a CI-appropriate fixture size"). Structure:
1. Parse `--entities` (default 500) and `--seed` (default 42) CLI args.
2. Seed a known raw API key + its SHA-256 hash, following the exact pattern
   `tickets/done/TCK-20260823-LIVE-TEST-API-KEY-AUTH.md` already proved (`RPG_API_KEY_HASHES` env var
   into a subprocess, per investigation.md lines 127-137, citing `src/config/profiles.py:56-68`'s
   `_parse_api_key_hashes` and `src/cli/entry.py:279`'s `_run_serve` threading `args.api_key_hashes`).
3. Boot a backend subprocess via `python3 -m src serve` (NOT `--entities`, which is confirmed dead
   code — investigation.md lines 264-270, citing `src/cli/entry.py`'s `_run_serve` never reading
   `args.entities`). Do not pass `--entities` at all; instead the script must construct its own
   `V2EngineManager(profile, entities_count=<N>)` and install it via
   `src.api.dependencies.set_engine_manager(...)` before `uvicorn.run(...)`, reusing the pattern from
   `tests/perf/test_api_projection_perf.py` (cited in investigation.md lines 276-283 and test_plan.md
   lines 52-58). This requires the script's own small `serve`-equivalent entrypoint (calling
   `create_v2_app(profile)` then overriding the engine manager) rather than shelling out to the CLI's
   broken `serve --entities` flag — the script owns this boot logic itself, it does not patch
   `src/cli/entry.py`.
4. Wait for 100 warmup engine ticks (per `docs/engine/performance_contract.md` §3.2, cited in
   investigation.md line 322-326) before recording any sample.
5. Connect a raw Python `websockets` client to `/api/v1/ws` with
   `additional_headers={"X-API-Key": raw_key}` (JSON handshake first; msgpack handshake as a second,
   separate connection labeled secondary/hypothetical per investigation.md's "V1 baseline" section
   and Risk #6 — the real frontend hardcodes `format: 'json'`, confirmed at `useSimulation.ts` line
   144 per investigation.md line 90-91).
6. **Architecture-review correction to investigation.md's `tick % 20 == 0` claim (independently
   re-verified against source during Plan-review — investigation.md's claim is FALSE and must not be
   implemented as written)**: `src/api/read_model_cache.py:148`'s `tick % 20 != 0` check only prevents
   `compute_tick_delta` from returning `None` — it guarantees some message (possibly with empty
   `changed`/`removed`/`events`) at least every 20 ticks. It does NOT force `changed` to include all
   entities. That requires `force_full_scan=True`, which is set once at `Kernel.__init__` from a
   `flags` dict (`src/engine/kernel.py:84`) and is never toggled per-tick based on `state.tick`.
   `V2EngineManager._build()` constructs its `Kernel` with no `flags` argument
   (`src/api/engine_manager.py:148`), so `force_full_scan` stays `False` for the entire life of any
   `V2EngineManager`-backed process — including this script's own normal boot — and `status.dirty_set`
   is populated per-tick from the real pipeline output (not `None`) in normal operation, so
   `get_dirty_entity_ids` returns only the tick's real dirty subset, never all entities, regardless of
   `tick % 20`. Record byte length of every received message over >=1000 sampled ticks in the normal
   (steady-state) run as a single bucket — do not look for or expect a "tick % 20 == 0 == full scan"
   sub-bucket inside this run; it will not occur.
7. To obtain the full-state-equivalent message needed for a like-for-like comparison against the V1
   75KB baseline, run a SEPARATE, short, dedicated measurement pass at the same entity count: construct
   the script's `Kernel` a second time with `flags={"force_full_scan": True}` passed through to
   `Kernel.__init__` — the same documented pattern `src/perf/profile_governance.py:27` already uses —
   which makes `src/engine/pipeline.py`'s Phase 17 law (`pipeline.py:371-372`) force the dirty set to
   include every entity on every tick of that dedicated run. Capture one (or a few, for
   averaging/stability) message(s) from this dedicated full-scan run as the full-state-equivalent data
   point. Do NOT blend this dedicated run's messages into the steady-state per-tick delta statistics —
   every message in `force_full_scan=True` mode is a full scan by construction, not representative of
   real production traffic, and must be reported as its own clearly-labeled number (same treatment as
   the msgpack secondary/hypothetical label per Risk #6).
8. Apply the Step 1 in-flight memory guard (poll `free -m` every 50 sampled ticks/messages across both
   the steady-state run and the dedicated full-scan run; abort + record partial results if available
   memory < 300MB) when `--entities 2500` is passed.
9. Write raw output (per-message byte counts: steady-state bucket from the normal run, full-scan bucket
   from the dedicated `force_full_scan=True` run, JSON vs. msgpack) to a JSON file under
   `staging_artifacts/TCK-20260821-LIVE-MAP-PERF-VALIDATION/raw/` for the report-writing step to
   consume.
**Do NOT touch:** `src/cli/entry.py` (leave `--entities`/`--seed` dead as-is — fixing that flag is
production code change, barred by Out of Scope), `src/api/server.py`, `src/api/ws/stream.py`,
`src/api/read_model_cache.py`, `src/config/profiles.py`.
**Other writers to the resource this step touches:** this step does not write to any shared registry,
counter, or log — it constructs its own isolated `V2EngineManager` instance in its own subprocess and
writes only to a new file under `staging_artifacts/.../raw/`, which no other code path reads or
writes concurrently. The one shared resource it *reads from* without writing is
`src/api/dependencies.py`'s module-level engine-manager singleton (`set_engine_manager`) — this is
safe because the script's subprocess is a fresh Python process with its own module state, not sharing
memory with any other running instance of the app; no other writer exists in this ticket's scope.
**Verify:** `.venv/bin/python3 -m pytest tests/api/test_ws_protocol.py -v` (precondition, must be
green before this script is trusted to reuse the same auth/WS mechanism) — from test_plan.md's Scoped
Pytest Commands. Manual verification: run the script with `--entities 500` and confirm it produces a
non-empty JSON output file with both the steady-state bucket (from the normal run) and the full-scan
bucket (from the dedicated `force_full_scan=True` run) populated.

### Step 2 — Run Step 1's script at CLASS_C scale (500 entities) — primary, sandbox-trustworthy result
**Files:** None (execution step, produces `staging_artifacts/TCK-20260821-LIVE-MAP-PERF-VALIDATION/raw/ws_payload_500.json`).
**Change:** Execute `tools/perf/live_map_ws_payload_measure.py --entities 500 --seed 42`. This is the
primary payload-size evidence for AC2. No memory guard concern expected at this scale (500 entities is
well within the ~1.2GB available RAM measured in investigation.md), but the guard code from Step 1
still runs (harmless no-op if never triggered).
**Do NOT touch:** Nothing — pure execution.
**Verify:** Output JSON file exists, has >=1000 sampled steady-state tick entries, and the file
produced by the dedicated `force_full_scan=True` pass (Step 1, point 7) contains at least one
full-scan message.

### Step 3 — Attempt Step 1's script at CLASS_B scale (2500 entities) — secondary, resource-guarded
**Files:** None (execution step, produces `staging_artifacts/TCK-20260821-LIVE-MAP-PERF-VALIDATION/raw/ws_payload_2500.json` OR a `ws_payload_2500_ABORTED.json` partial-results marker file).
**Change:** Per the Open Question 2 resolution above: run `free -m` first. If available memory
>=2500MB, execute `tools/perf/live_map_ws_payload_measure.py --entities 2500 --seed 42` with its
in-flight guard active. If pre-flight fails, skip execution entirely and write a marker file stating
"not attempted — pre-flight memory check failed, Xmb available < 2500MB required" with the measured
number, for the report step to cite verbatim.
**Do NOT touch:** Nothing — pure execution, and this step must not be allowed to crash or hang the
overall harness run; wrap the subprocess call with a timeout and treat any nonzero exit / timeout the
same as a guard trip (partial/aborted result, not a silent failure).
**Verify:** Either a complete `ws_payload_2500.json` with >=1000 samples, or an honestly-labeled
aborted/not-attempted marker — both are valid pass conditions for this step; a silent hang or crash
with no output file is the only failure mode.

### Step 4 — Playwright installation and verification
**Files:** `frontend/package.json` (add `playwright` as a new devDependency only — no existing
dependency/devDependency is removed or altered; investigation.md confirmed lines 180-182 that
`frontend/package.json`'s current devDependencies are `vitest`, `jsdom`, `@testing-library/react`,
`eslint`, `typescript`, `vite`, with no `playwright`/`puppeteer` present).
**Change:** Run `cd frontend && npm install -D playwright && npx playwright install chromium`. This
is Risk #4 from investigation.md — connectivity was confirmed reachable (npm registry `HTTP/2 200`,
Playwright CDN `HTTP/2 307` redirect) but the actual ~300MB binary download was never attempted. This
step must actually attempt it and record the real outcome (success, partial failure, or disk/network
failure) rather than assuming success from the connectivity check. If the install genuinely fails
(not just slow), this blocks Step 6 entirely and the report must say so per the "Known, Disclosed
Gaps" section below — do not substitute a fake/mocked measurement.
**Do NOT touch:** `frontend/vite.config.ts`, any other `frontend/package.json` dependency version,
`frontend/src/`.
**Other writers to the resource this step touches:** `frontend/package.json` and
`frontend/package-lock.json` are the shared dependency manifest for the whole frontend — this is the
one production-adjacent file this ticket legitimately modifies (adding a devDependency only, which
does not affect production `vite build` output since devDependencies are not bundled). No other
concurrent ticket in this worktree is known to be editing `frontend/package.json` at the same time
(per CLAUDE.md's Hard Rules on shared working directories, check `git status`/`git log` immediately
before this step to confirm no other in-flight session has pending changes to this file before
running `npm install`).
**Verify:** `npx playwright --version` succeeds and `ls frontend/node_modules/.cache/ms-playwright/` (or
equivalent Playwright browser cache path) shows a chromium binary present. `cd frontend && npx vitest
run src/test/useSimulation.test.tsx` still passes 10/10 after the install (test_plan.md's Anti-Drift
Test Guards — confirms the new devDependency doesn't change vitest's resolution).

### Step 5 — Frontend headless-browser render-timing harness (structure)
**Files:** New directory `frontend/perf/` (test_plan.md item 2 recommends `frontend/perf/` or
`frontend/e2e/`, explicitly not `frontend/src/test/` since it needs a real browser + real backend, not
jsdom+mocks). New file `frontend/perf/live_map_render_timing.spec.ts` (or `.mjs` if Playwright's
non-test-runner API is used directly — implementer's choice, but must not register itself as a
`vitest` test file, to avoid Anti-Drift risk of the jsdom suite trying to execute it).
**Change:** A Playwright script that:
1. Launches the backend via Step 1's script's boot logic (import/reuse it, or shell out to it) at
   the entity count under test, waiting for 100 warmup ticks.
2. Launches `npm run dev` for the Vite frontend (or confirms it's already running) on its normal
   `localhost:5173`.
3. Launches headless Chromium via Playwright.
4. Before navigation, installs `page.route('**/api/v1/**', ...)` to inject `X-API-Key: <raw_key>` on
   outgoing REST requests (per Open Question 1's resolution above — investigation.md lines 141-144).
5. Before navigation, installs `page.addInitScript(...)` that overrides `window.WebSocket` to (a)
   rewrite the target host from `localhost:5173` to the real backend host:port, and (b) append
   `?key=<raw_key>` to the URL, before constructing the real native `WebSocket` (investigation.md
   lines 163-170 — confirmed safe because `src/api/ws/stream.py` performs no `Origin` header check).
6. Navigates to the frontend's live-map page.
7. Injects a `requestAnimationFrame`-based sampling loop into the page (via `page.evaluate` or another
   `addInitScript`) that records `performance.now()` deltas between consecutive rAF callbacks — this
   *imposes* the sampling loop since, per investigation.md's "Frontend render path" finding
   (lines 64-84, independently re-verified by this plan's own re-read below), no rAF loop exists in
   the app to observe; the harness measures wall-clock time per WS-delta-triggered `useCanvas` redraw
   this way.
8. Collects >=1000 samples under "bounded-viewport load" — canvas visible, WS delta stream actively
   driving redraws (not paused).
9. Computes p50/p95/p99 frame time and `%frames > 16.6ms`.
10. Applies the same Step-5-described in-flight memory guard (poll `free -m` every 50 samples; abort
    if available < 300MB) when running at 2500-entity scale.
11. Writes results to `staging_artifacts/TCK-20260821-LIVE-MAP-PERF-VALIDATION/raw/render_timing_<N>.json`.
**Do NOT touch:** `frontend/src/hooks/useSimulation.ts`, `frontend/src/hooks/useCanvas.ts`,
`frontend/src/components/GameCanvas.tsx`, `frontend/vite.config.ts`, `src/api/ws/stream.py` — all four
are explicitly Out of Scope per the ticket and must show an empty `git diff --stat` at the end (test_plan.md's Anti-Drift Test Guards).
**Other writers to the resource this step touches:** none — writes only to its own new output file
under `staging_artifacts/.../raw/`, which no other code path reads or writes.
**Verify:** Manual confirmation the harness produces a populated `render_timing_500.json` with >=1000
samples and computed percentiles. `cd frontend && npm run build` still exits 0 after this new
directory is added (test_plan.md's frontend regression guard — confirms `frontend/perf/` files, if
they use frontend TS types, don't break the `tsc -b` build; if this file is intentionally excluded
from the `tsconfig` build set, verify that exclusion is correct rather than assumed).

### Step 6 — Run Step 5's harness at CLASS_C scale (500 entities) — primary, sandbox-trustworthy result
**Files:** None (execution step).
**Change:** Execute the Step 5 harness against the Step 1 backend booted with `entities_count=500`.
This is the primary render-FPS evidence for AC1.
**Do NOT touch:** Nothing — pure execution.
**Verify:** `render_timing_500.json` contains >=1000 samples with computed p50/p95/p99 and
`%frames>16.6ms`.

### Step 7 — Attempt Step 5's harness at CLASS_B scale (2500 entities) — secondary, resource-guarded
**Files:** None (execution step, produces `render_timing_2500.json` or an aborted/not-attempted marker).
**Change:** Same guarded-attempt logic as Step 3, applied to the frontend harness. Run only if Step 3
(the backend-only 2500-entity attempt) succeeded or at least didn't hard-OOM — if Step 3 already
tripped the memory guard, do not additionally attempt Step 7 with a concurrent Chromium instance on
top of an already-strained backend; instead record "skipped — Step 3's 2500-entity backend attempt
already tripped the resource guard, compounding with a concurrent headless browser was judged
unsafe" as the reported reason. If Step 3 succeeded cleanly, proceed with the same pre-flight
(>=2500MB available, adjusted if Step 3's process is still running and holding memory — prefer running
Step 7 as a fresh process after Step 3's backend has been torn down) and in-flight (300MB floor, checked
every 50 samples) guards as Step 3.
**Do NOT touch:** Nothing — pure execution.
**Verify:** Either a complete `render_timing_2500.json` with >=1000 samples, or an honestly-labeled
aborted/skipped/not-attempted marker with the specific reason recorded.

### Step 8 — Interpolation factual-finding re-verification
**Files:** None (verification-only step; no new file).
**Change:** Re-run `grep -rniE "requestAnimationFrame|\blerp\b|deltaTime|interpolat" frontend/src/`
immediately before writing the final report (test_plan.md's Anti-Drift Test Guards) to confirm zero
matches still holds and that none of Steps 1-7's harness code accidentally landed inside
`frontend/src/` (it must not — all harness code lives in `frontend/perf/` and `tools/perf/`). This is
not new investigation — investigation.md already fully verified this finding (lines 64-84, citing the
exhaustive grep and a full read of `useCanvas.ts` lines 95-425 and `GameCanvas.tsx` lines 254-383) —
this step is a mechanical re-confirmation gate, not new research.
**Do NOT touch:** `frontend/src/` — this step must produce zero diff.
**Verify:** The grep re-run returns zero matches, and `git diff --stat -- frontend/src/` is empty.

### Step 9 — Precondition regression tests
**Files:** None (test execution only).
**Change:** Run, in this order, before Steps 2/3/6/7 are trusted as valid measurements (these
preconditions should actually run early — logically before Step 2, but listed here for clarity on
what must stay green throughout; the Dependency Map below states the real ordering):
- `.venv/bin/python3 -m pytest tests/api/test_ws_protocol.py -v`
- `pytest tests/unit/api/test_read_model_cache.py -v`
- `pytest tests/unit/api/test_engine_manager.py -v`
- `pytest tests/api/ -k "ws or websocket" -v`
- `cd frontend && npx vitest run src/test/useSimulation.test.tsx`
- `cd frontend && npm run build`
All six commands are from test_plan.md's "Scoped Pytest Commands" / frontend regression guard
sections verbatim. None of Steps 1-8 should cause any of these to fail; if one does, that is a signal
this ticket's harness code has drifted into touching something it shouldn't (see Scope Guards below),
not a signal to edit the test.
**Do NOT touch:** Any of the test files listed, or the source files they cover
(`src/api/ws/stream.py`, `src/api/read_model_cache.py`, `src/api/engine_manager.py`,
`frontend/src/hooks/useSimulation.ts`).
**Verify:** All six commands exit 0.

### Step 10 — Write the final report
**Files:** New file `staging_artifacts/TCK-20260821-LIVE-MAP-PERF-VALIDATION/report.md`.
**Change:** Synthesize Steps 2/3/6/7/8's outputs into one report, structured to directly answer each
of the ticket's 4 ACs (see Acceptance Criteria Map below). Must include:
- Scoped Claims block for every reported number: Runtime Profile (this sandbox's `RuntimeProfile`
  used), Hardware Class (**CLASS_C**, stated explicitly per certification_contract.md's AND-rule —
  4 cores / 5.8GB RAM, regardless of whether the scenario used 500 or 2500 entities), Scenario
  (500-entity / 2500-entity, each labeled separately), Execution Mode, RuntimeMode.
- AC2's payload comparison: report the dedicated `force_full_scan=True` run's message size (full-scan
  shape, per Step 1 point 7's corrected mechanism — NOT a `tick % 20 == 0` heartbeat from the normal
  run, which investigation.md incorrectly assumed contains a full scan; see Step 1's correction note)
  separately from steady-state delta size, and compare only the full-scan number against the V1
  75KB-at-360-entities baseline, scaled per-entity, with an explicitly stated tolerance. State plainly
  that steady-state delta size is a different, smaller number and is not blended into the V1 comparison
  (investigation.md's Anti-Drift Hazards, last bullet), and that the full-scan number itself is a
  dedicated-mode synthetic measurement, not a message the live server ever actually emits during normal
  operation (labeled with the same secondary/hypothetical caveat as msgpack).
- AC3's interpolation finding, citing Step 8's re-confirmed grep result and investigation.md's file:line
  evidence (`useCanvas.ts:262-263`, `GameCanvas.tsx:254-383`).
- AC4: any budget miss (e.g. if 500-entity p95 exceeds 12ms, or payload size exceeds the stated
  tolerance) documented with a root-cause hypothesis and an explicit note that fixing it is deferred
  to a new, separate future ticket — not fixed here.
- The CLASS_B(2500) results section, whichever of Steps 3/7's three outcomes occurred (full success /
  guarded abort / pre-flight skip), reported honestly with the specific reason if not fully completed.
- The "Known, Disclosed Gaps to Live Verification" section (below) copied/adapted into the report so a
  reader doesn't have to cross-reference this plan file separately.
**Do NOT touch:** Any file outside `staging_artifacts/TCK-20260821-LIVE-MAP-PERF-VALIDATION/`.
**Verify:** Manual review — grep the draft report text for the literal string "CLASS_B" and confirm
every occurrence is scoped to "scenario entity-count target," never to "this machine's certified
hardware class" (test_plan.md's Anti-Drift Test Guards, final bullet). Confirm all 4 ACs have a
corresponding, clearly-labeled section.

## Scope Guards

- No change to `frontend/src/hooks/useSimulation.ts`, `frontend/src/hooks/useCanvas.ts`,
  `frontend/src/components/GameCanvas.tsx`, `src/api/ws/stream.py` — final `git diff --stat` on these
  four must be empty.
- No change to `frontend/vite.config.ts` (the `ws: true` gap is routed around by harness code, not
  fixed).
- No change to `src/cli/entry.py` (the dead `--entities`/`--seed` flags on `serve` are routed around
  by harness code directly constructing `V2EngineManager`, not fixed).
- No interpolation/lerp system is built anywhere, including inside the harness code itself (a harness
  developer manually watching jittery snapping entities during Playwright development is a known drift
  temptation per investigation.md's Anti-Drift Hazards — resist it).
- No new pytest CI-gating test is added under `tests/perf/` for the payload-size script (test_plan.md
  explicitly prefers `tools/perf/` to avoid `tests/perf/test_perf_regression_baseline.py`'s existing
  baseline-comparison machinery silently picking it up and failing CI for an unrelated reason).
- No fix to any performance issue this ticket's measurement reveals — findings only, deferred to a new
  ticket per AC4.
- `frontend/package.json`/`frontend/package-lock.json` may gain a `playwright` devDependency (Step 4)
  and nothing else — no version bumps to existing dependencies, no removal of anything.
- `docs/performance/perf_baseline_policy.md` / `docs/engine/contracts/certification_contract.md`'s
  pre-existing CLASS_B/CLASS_C AND-rule conflict is not resolved by this ticket (already flagged,
  deferred to `TCK-20260702-OBSISO-ISOLATION-PROOF` per investigation.md) — do not edit either doc.
- `docs/parity_ledger/infrastructure.yaml` INFRA-049/050/051/052 are not edited by this ticket (shape
  verification, not size/performance — out of this ticket's scope per investigation.md).

## Dependency Map

- Step 1 (backend script) blocks Steps 2 and 3 (both execute it).
- Step 2 (CLASS_C backend run) should run before Step 3 (CLASS_B backend run) — establishes the
  primary result is safely obtainable before attempting the riskier scale-up, and gives a
  known-good baseline to compare Step 3's partial/aborted output against if it trips the guard.
- Step 4 (Playwright install) blocks Step 5 (harness needs Playwright installed to be written/tested)
  and therefore blocks Steps 6 and 7.
- Step 5 (frontend harness) blocks Steps 6 and 7 (both execute it).
- Step 6 (CLASS_C frontend run) should run before Step 7 (CLASS_B frontend run), same reasoning as
  Step 2 before Step 3.
- Step 7 depends on Step 3's outcome (see Step 7's Change text: skip if Step 3 already tripped the
  guard).
- Step 8 (interpolation re-verification) is independent of Steps 1-7 — can run any time, but should
  run immediately before Step 10 per test_plan.md's Anti-Drift Test Guards ordering ("immediately
  before writing the final report").
- Step 9 (precondition regression tests) should run early — logically before Step 2 for the backend
  preconditions (`test_ws_protocol.py`, `test_read_model_cache.py`, `test_engine_manager.py`) and
  before Step 6 for the frontend precondition (`useSimulation.test.tsx`) — and again at the end as a
  final regression confirmation. Running it twice (before building on the mechanism, and again after
  all harness code is in place) is intentional, not redundant — it is what test_plan.md's Anti-Drift
  Test Guards describes ("Re-run ... after building the Playwright harness").
- Step 10 (report) depends on Steps 2, 3, 6, 7, 8, and 9's final re-run all having produced their
  outputs — it is the last step.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| "with a live world at CLASS_B (2500 entities) and separately CLASS_C (500 entities), a measured session of >=1000 sampled render frames under bounded-viewport load reports p50<=8ms,p95<=12ms,p99<=16.6ms plus %frames>16.6ms, reported with full Scoped Claims discipline" | Step 5 (harness structure), Step 6 (CLASS_C run — primary), Step 7 (CLASS_B run — best-effort/guarded), Step 10 (report with Scoped Claims block) | Step 6's `render_timing_500.json` >=1000 samples with computed percentiles; Step 7's outcome (complete or honestly-labeled partial/aborted) documented in Step 10's report |
| "measured per-update broadcast payload size (JSON and msgpack if the delta broadcast routes through it) at both classes stays within an explicitly stated tolerance of the ~75KB V1 baseline, comparing like-for-like (full-state-equivalent, not naive per-delta)" | Step 1 (script structure: steady-state bucketing from the normal run, full-scan bucketing from a dedicated `force_full_scan=True` run — corrected mechanism, see Step 1's correction note), Step 2 (CLASS_C run — primary), Step 3 (CLASS_B run — best-effort/guarded), Step 10 (report with full-scan-vs-baseline comparison, steady-state reported separately) | Step 2's `ws_payload_500.json` (steady-state) plus the dedicated full-scan output with a populated full-scan message; Step 3's outcome documented in Step 10's report |
| "report explicitly states that no interpolation system exists in the frontend today (entities snap to latest position on data update) as a factual finding, without proposing or building one" | Step 8 (re-verification), Step 10 (report section citing Step 8's grep + investigation.md's file:line evidence) | Step 8's zero-match grep re-run; Step 10's report contains the stated finding with citations |
| "any budget miss is documented as a finding with root-cause hypothesis, explicitly deferred to a separate future ticket" | Step 10 (report's budget-miss section, populated only if Steps 2/3/6/7's numbers actually miss budget) | Manual review of Step 10's report for presence of this section if applicable; conditional — no miss means an explicit "no budget miss observed" statement instead |

## Known, Disclosed Gaps to Live Verification

Stated upfront so Verify does not discover these as surprises:

1. **CLASS_B(2500-entity) numbers may not be obtainable as clean signal in this sandbox, or at all.**
   Given ~1.2GB available RAM and swap already at 4.0Gi/4.0Gi (investigation.md, measured live), the
   resource guards in Steps 3 and 7 may trip, producing partial or "not attempted" results instead of
   full 1000-sample runs. If this happens, the report's CLASS_B section will say so honestly rather
   than presenting guard-tripped or swap-thrashed numbers as if they were trustworthy p50/p95/p99
   figures. The CLASS_C(500-entity) result is what this plan treats as the actually-reliable evidence
   for both AC1 and AC2; a reader should not expect this ticket to deliver two equally-trustworthy
   scale points.
2. **No run in this sandbox will ever be reportable as "CLASS_B hardware."** Per
   `certification_contract.md`'s AND-rule (4 cores meets CLASS_B, 5.8GB RAM fails the >=8GB
   requirement), this machine is CLASS_C regardless of entity count used. Every section of the report,
   including the 2500-entity scenario section, will state Hardware Class = CLASS_C. This is expected,
   not a defect to fix.
3. **Playwright's actual ~300MB Chromium download was never attempted before this plan** — only
   connectivity was checked (investigation.md Risk #4). Step 4 is the first real attempt. If it fails
   (network stalls mid-download, disk fills, or another unforeseen failure), AC1 (render FPS) cannot be
   measured with real live data at all in this sandbox, and Step 10's report must say so explicitly
   rather than fabricating or estimating frame-timing numbers. This is a real possibility, not a
   remote one, and Verify should not treat "Playwright install failed" as grounds to reject the whole
   ticket — it is exactly the kind of environment-constraint finding this ticket exists to surface
   honestly.
4. **msgpack payload-size numbers are secondary/hypothetical**, not evidence of live production
   traffic — the real frontend hardcodes `format: 'json'` (`useSimulation.ts:144`, confirmed
   investigation.md line 90-91). Step 1's script measures msgpack only because the AC's own wording
   ("JSON and msgpack if the delta broadcast routes through it") asks for it as a secondary data
   point; the report must label it as such, not as "what the live map sends."
5. **"Render FPS" is an imposed measurement, not an observed one.** Since no rAF loop exists in the
   app today (investigation.md's "Frontend render path" finding, independently re-confirmed at Step 8),
   the frame-timing numbers this ticket produces measure "wall-clock time per WS-delta-triggered
   `useCanvas` redraw, sampled via a harness-injected rAF loop" — not "frames per second of an
   existing render loop," because no such loop exists. The report must describe the measurement this
   way rather than implying a pre-existing FPS counter was read.
6. **The "full-state-equivalent" WS message is a dedicated-mode synthetic measurement, not a message
   the live server ever emits during normal operation.** Investigation.md assumed `tick % 20 == 0`
   ticks in the normal run were full-entity scans; this was independently re-verified as false during
   Plan-review (`src/api/engine_manager.py:148` boots `Kernel` with no `flags`, so `force_full_scan`
   stays `False` permanently for any normally-booted `V2EngineManager` — see Step 1's correction note).
   The corrected mechanism (Step 1 point 7) requires a second, separately-booted
   `force_full_scan=True` run to produce a genuine full-scan message. Report this number labeled
   accordingly — it demonstrates what a full broadcast would cost, not what production traffic
   actually sends on any given tick.

## Build Gate List

All commands below must exit 0 / stay green before this ticket is considered complete (from
test_plan.md's "Scoped Pytest Commands" and frontend regression guard sections verbatim — never run
the full suite):

```bash
.venv/bin/python3 -m pytest tests/api/test_ws_protocol.py -v
pytest tests/unit/api/test_read_model_cache.py -v
pytest tests/unit/api/test_engine_manager.py -v
pytest tests/api/ -k "ws or websocket" -v
cd frontend && npx vitest run src/test/useSimulation.test.tsx
cd frontend && npm run build
```

Plus the Anti-Drift Test Guards (test_plan.md):
```bash
grep -rniE "requestAnimationFrame|\blerp\b|deltaTime|interpolat" frontend/src/   # must be zero matches
git diff --stat -- frontend/src/hooks/useSimulation.ts frontend/src/hooks/useCanvas.ts frontend/src/components/GameCanvas.tsx src/api/ws/stream.py   # must be empty
```

## Anti-Drift Notes

Carried forward from investigation.md's "Anti-Drift Hazards" verbatim, binding on Implement:

- **Do not build an interpolation system.** Watching jittery/snapping entities during manual Playwright
  harness development creates a real pull toward "just add a quick lerp" — this is out-of-scope new
  feature work under any circumstance in this ticket.
- **Do not silently patch `frontend/vite.config.ts` or `src/cli/entry.py`'s dead `--entities` flag.**
  Both are real gaps, but fixing either is a production-code change this ticket's Out of Scope
  explicitly forbids. Route around them with harness-only code exactly as Steps 1 and 5 describe.
- **Do not report a CLASS_C-hardware-actual run as "CLASS_B" performance** just because the scenario
  used 2500 entities. Every report section states Hardware Class = CLASS_C regardless of entity count.
- **Do not treat a mocked-WebSocket vitest pass as evidence of live behavior.** The existing
  `useSimulation.test.tsx` suite mocks `globalThis.WebSocket` entirely — it is a regression guard for
  this ticket's harness-building work, not a substitute for the real-browser measurement Steps 5-7
  produce.
- **Do not blend steady-state per-tick delta size with the full-scan/heartbeat message size** into one
  undifferentiated "payload size" number when comparing against the V1 75KB baseline — Step 1's script
  buckets these separately by design, and Step 10's report must keep them separate in the write-up.

## Deviations (recorded during Implement)

1. **Step 1 point 7's `force_full_scan` dedicated-server mechanism does not work as designed —
   discovered and corrected during Implement, not just at Plan-review.** This plan's own Step 1 point 6
   already corrected investigation.md's original (disproven) `tick % 20 == 0` claim once; a second,
   deeper correction was needed during Implement. A full-repository grep for
   `_refresh_dirty_set` (the method Step 1 point 7 cites as "Phase 17 Law," `pipeline.py:371-372`)
   finds exactly one match — its own definition (`pipeline.py:363`) — it is never called anywhere in
   `refine()`. `force_full_scan=True` does genuinely widen phase-level entity iteration
   (`src/core/dirty.py::get_relevant_entity_ids`) and forces every phase to run
   (`PhaseDependencyGraph.should_run_phase`'s override), but the DirtySet that reaches the WS broadcast
   is built exclusively by `DirtySetBuilder.mark_from_update()` (called at `pipeline.py` lines 261, 296,
   314, 329, 352), which only marks entities with a real per-tick `EntityUpdate`, regardless of
   `force_full_scan`. A live-verified smoke test (`.venv/bin/python3` direct in-process reproduction, not
   just source-reading) confirmed a dedicated `force_full_scan=True` Kernel boot produces the same
   small, mostly-empty delta messages as a normal boot — not an all-entities message. **Resolution**:
   `tools/perf/live_map_ws_payload_measure.py` does not boot a second dedicated server at all. Its
   `full_scan` bucket is computed by `_compute_synthetic_full_scan()` — an in-process, no-server
   construction of a `V2EngineManager` and a direct call through the same presenter/serialization code
   path the real WS handler uses (`StatePresenter.present_entity_slim`, `jsonable_encoder`,
   `json.dumps`/`msgpack.packb`) — clearly labeled `"method": "synthetic in-process construction -- NOT
   a live WS capture"` in its own JSON output. This is both more honest (no live message with this shape
   is actually obtainable today) and lighter on this sandbox's tight memory budget (one fewer server
   subprocess). Reported as AC4 Finding 1 in report.md, deferred to a new ticket, not fixed in
   `src/engine/pipeline.py` here (barred by Out of Scope).
2. **A second, independent bug was found and fixed in the harness scripts themselves (not production
   code): `sys.path[0]` resolution silently ran against the wrong git worktree.** When
   `tools/perf/live_map_ws_payload_measure.py` runs as a script file (not `python3 -c`), Python sets
   `sys.path[0]` to the script's own directory, not the invocation cwd. Since that directory has no
   `src/` package, `import src...` fell through to this venv's editable-install finder
   (`site-packages/__editable__.rpg_based_simulation-*.pth`), which resolves to the **main checkout's**
   `src/` — a different, potentially-diverged git worktree — not this worktree's own. Confirmed live:
   the main checkout's `src/api/presenters/state_presenter.py` lacks `present_entity_slim`, a method
   this worktree's branch added, causing an `AttributeError` the first time `_compute_synthetic_full_scan`
   ran. Fixed by inserting `str(REPO_ROOT)` (computed from `Path(__file__).resolve().parents[2]`, always
   correct regardless of invocation cwd) at the front of `sys.path` before any `src.*` import, at the top
   of the script — applies uniformly to both the driver process and the `--internal-serve` subprocess,
   since both re-execute the same file. Without this fix, every number in this ticket's report would
   have silently reflected the main checkout's code, not this worktree's — caught before any numbers
   were reported, not after.
3. **Step 1's originally-planned separate `format: 'msgpack'` handshake run for the steady-state bucket
   was kept, but executed as a second connection to the *same already-running* server** (not a second
   server subprocess) — an implementation simplification not explicitly specified by Step 1's text, made
   for resource economy given this sandbox's tight memory budget. Documented in report.md's AC2 section
   as a measurement caveat: the msgpack sample was captured over a later, different tick window than the
   JSON sample, so the two are not a strict message-for-message pair.
4. **Steps 3 and 7's CLASS_B(2500) attempts**: Step 3 (backend) was attempted and cleanly failed its
   pre-flight guard (1234MB available < 2500MB required), exactly as this plan's Open Question 2
   anticipated. Step 7 (frontend) was not separately attempted at all — per Step 7's own text ("if Step 3
   already tripped the memory guard, do not additionally attempt Step 7"), and moot regardless since AC1
   could not be measured at any entity count (Playwright's Chromium binary download failed — see below).
5. **AC1 (render FPS) could not be measured with live data at either entity count** — `npx playwright
   install chromium` failed with a network-level block (`cdn.playwright.dev` DNS/TLS-intercepted by this
   sandbox's Fortiguard filter, confirmed via `openssl s_client`), not a flaky/retryable error. This was
   plan.md's own disclosed "Known, Disclosed Gaps to Live Verification" item 3, materializing exactly as
   anticipated. `frontend/perf/live_map_render_timing.mjs` was still built as a complete, ready-to-run
   implementation (Step 5's full scope: backend+frontend boot, auth injection, WS host/key rewrite via
   `addInitScript`, imposed rAF sampling loop, percentile computation, resource guards) — it could not be
   executed in this sandbox, and no frame-timing numbers are fabricated or estimated in its place. Named
   `.mjs` (Playwright's plain script API, not `@playwright/test`'s runner) rather than plan.md's
   alternative `.spec.ts` naming specifically to avoid vitest's default `*.spec.ts` include glob picking
   it up if the full (unscoped) `vitest run` were ever invoked elsewhere in this repo's history — plan.md
   itself flagged this as a live risk ("must not register itself as a vitest test file").
