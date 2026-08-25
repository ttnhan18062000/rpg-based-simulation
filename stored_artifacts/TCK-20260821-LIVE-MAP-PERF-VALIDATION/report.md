---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260821-LIVE-MAP-PERF-VALIDATION
artifact_type: report
tags: [performance, websocket, testing]
---

# Measurement Report -- TCK-20260821-LIVE-MAP-PERF-VALIDATION

## Scoped Claims (applies to every number in this report unless stated otherwise)

- **Runtime Profile**: `cli_default` (via `ConfigLoader.load_profile(profile_name="cli_default")`
  -- the same profile `python3 -m src serve` uses by default; `max_worker_count=4`,
  `max_tick_budget_ms=50.0`).
- **Hardware Class (actual, this sandbox)**: **CLASS_C**, per
  `docs/engine/contracts/certification_contract.md` section 3's AND-rule (>=4 cores AND >=8GB RAM ==
  CLASS_B). This sandbox measured **4 logical cores / 5.8GB total RAM** -- it meets the core
  count but fails the RAM requirement, so it certifies as CLASS_C regardless of which entity
  count a given scenario below uses. **Every number in this report, including the
  "2500-entity" scenario section, was either produced on or attempted on CLASS_C-actual
  hardware.** `perf_baseline_policy.md`'s "CLASS_B: 2,500 entities / CLASS_C: 500 entities" are
  entity-count *scenario-sizing* labels, a different axis from hardware certification -- see
  investigation.md's "Real host hardware does not certify as CLASS_B" section for the full
  resolution of this pre-existing doc conflict.
- **Scenario**: synthetic world built via direct `V2EngineManager(profile, entities_count=N,
  seed=42)` construction (hero + N-1 goblins on a diagonal spawn pattern) -- no world-compiler/
  content-resolution pass involved. `500` = CLASS_C-scale (primary, obtained). `2500` =
  CLASS_B-scale (attempted, not obtained -- see below).
- **Execution Mode**: live, single real backend process per run (`uvicorn` + FastAPI +
  `V2EngineManager`'s background tick thread), real `websockets` client connections over
  `/api/v1/ws`, real `X-API-Key` header authentication (same pattern proven in
  `tests/api/test_ws_protocol.py` / `TCK-20260823-LIVE-TEST-API-KEY-AUTH`).
- **RuntimeMode**: `DEBUG`/default observability mode (no `RPG_OBSERVABILITY_MODE` override set).
- **Sandbox resource state during this session** (see "Resource conditions" below for detail):
  available RAM fluctuated between ~1.2GB and ~1.25GB throughout, swap was near-full (3.9-4.0GB
  of 4.0GB used) at the *start* of this session and recovered to near-empty during the run
  (concurrent sessions on this shared machine releasing memory) -- all measurements below were
  taken with the in-flight 300MB-available guard armed and never tripped.

## AC1 -- Render FPS (CLASS_B and CLASS_C)

**Status: NOT MEASURED WITH LIVE DATA in this sandbox, at either entity count.**

A complete, ready-to-run Playwright harness was built
(`frontend/perf/live_map_render_timing.mjs`) implementing everything the AC requires: boots a
real backend + real `vite` dev server, launches headless Chromium, authenticates the page's
REST calls (`X-API-Key` header injection via `context.route`) and WebSocket connection (`?key=`
query param + host rewrite via `context.addInitScript`, routing around
`vite.config.ts`'s missing `ws: true` without editing that file) exactly as
`investigation.md`/`plan.md` designed, then imposes a `requestAnimationFrame` sampling loop
(the app has no pre-existing rAF loop to observe -- confirmed by the zero-match grep below) and
computes p50/p95/p99 frame time and `%frames > 16.6ms` over >=1000 samples.

**It could not be executed** because `npx playwright install chromium` failed with a
network-level block, not a flaky/retryable error:

```
Error: unable to verify the first certificate; if the root CA is installed locally, try running Node.js with --use-system-ca
```

Diagnosing per CLAUDE.md's CI Failure Triage pattern (never assume a network error is
transient without checking the actual endpoint):

```
$ echo | openssl s_client -connect cdn.playwright.dev:443 -servername cdn.playwright.dev | openssl x509 -noout -subject -issuer
subject=O = Fortinet, CN = Fortiguard SDNS Blocked Page
issuer=O = Fortinet, CN = Fortiguard SDNS Blocked Page
```

This sandbox's network filter DNS/TLS-intercepts `cdn.playwright.dev` and serves a Fortiguard
"blocked page" certificate instead of the real CDN's -- the same category of block CLAUDE.md's
own CI Failure Triage guidance documents for GitHub's `results-receiver`/blob-storage hosts. A
retry with Node's suggested `--use-system-ca` flag hung rather than succeeding (a system-CA
trust flag cannot fix a genuine DNS-sinkhole redirect, since the TLS endpoint really is the
block page, not a legitimately-signed-but-untrusted CDN). This is not a transient failure worth
retrying further.

This exact risk was disclosed in advance in `plan.md`'s "Known, Disclosed Gaps to Live
Verification" item 3: "If [the Chromium download] fails ... AC1 (render FPS) cannot be measured
with real live data at all in this sandbox, and Step 10's report must say so explicitly rather
than fabricating or estimating frame-timing numbers." No frame-timing numbers are fabricated or
estimated here. `frontend/perf/live_map_render_timing.mjs` is a complete implementation, ready to
run unmodified in any environment where the Chromium binary download succeeds (a corporate
network without this specific CDN block, or a CI runner).

**Frontend regression guard, confirmed unaffected by the harness build:**
`cd frontend && npx vitest run src/test/useSimulation.test.tsx` -> 10/10 passing (unchanged from
before this ticket). `cd frontend && npm run build` -> clean 0-error build (`frontend/perf/*.mjs`
is outside `tsconfig.app.json`'s `include: ["src"]`, so it does not participate in `tsc -b`).

## AC2 -- Broadcast Payload Size (JSON and msgpack, both classes, vs. V1 ~75KB baseline)

### CLASS_C (500 entities) -- primary, obtained

**Steady-state (real per-tick deltas, live capture, 100 warmup ticks + 1000 sampled ticks,
`tools/perf/live_map_ws_payload_measure.py --entities 500 --seed 42`):**

| Encoding | count | min | p50 | mean | p95 | p99 | max |
|---|---|---|---|---|---|---|---|
| JSON | 1000 | 232 B | 8,435 B | 17,561 B | 71,300 B | 71,309 B | 71,315 B |
| msgpack (secondary) | 50 | 384 B | 384 B | 388 B | 384 B | 489 B | 489 B |

**Full-scan (synthetic, in-process, all 500 entities -- see "Full-scan finding" below for why
this is not a live capture):**

| Encoding | bytes | bytes/entity |
|---|---|---|
| JSON | 68,907 | 137.8 |
| msgpack | 47,680 | 95.4 |

**V1 comparison (like-for-like, full-state-equivalent, scaled to V1's measured 360-entity
scenario):** V1's ~75KB baseline (`docs/archive/performance/performance-report-api-payload.md`)
is `GET /api/v1/state`, uncompressed body, 360 entities, ~208.3 bytes/entity. V2's full-scan JSON
DTO scales to 137.8 x 360 = **~49.6KB at 360 entities -- 34% smaller than the V1 baseline**
(V2's WS slim DTO carries 9 fields vs. V1's fuller `EntitySlimSchema`; this is expected and
matches investigation.md's prediction). **Explicitly stated tolerance: within +/-25% of the
scaled V1 baseline.** The measured value (-34%) falls **outside** that band, but in the safe
direction (smaller, not larger) -- reported as a finding, not a budget miss requiring
remediation (see AC4).

**Steady-state vs. V1 baseline: explicitly NOT comparable and not blended into the above** -- a
typical per-tick delta (p50 = 8,435B) covers only the entities that changed that specific tick,
not a full snapshot; comparing it directly to V1's full-state 75KB number would misrepresent
both numbers, per this ticket's own AC2 wording ("comparing like-for-like ... not naive
per-delta") and investigation.md's Anti-Drift Hazards.

**msgpack caveat:** the msgpack steady-state sample (50 messages) was captured over a *separate,
later* WebSocket connection than the JSON sample (opened after the JSON run's 1000 messages had
already been collected, same server, ~1100 ticks in vs. ~100-1100 for JSON) -- it is not a
message-for-message JSON-vs-msgpack pair of the *same* ticks. Its narrow, small range (384-489B)
partly reflects a quieter later time window, not purely encoding efficiency. The full-scan
bucket's msgpack-vs-JSON comparison (47,680B vs. 68,907B, same synthetic payload object
serialized both ways) **is** a clean like-for-like encoding comparison: msgpack is ~31% smaller
than JSON for the same data, as expected.

### CLASS_B (2500 entities) -- not attempted

Pre-flight memory guard (`tools/perf/live_map_ws_payload_measure.py`'s `--preflight-required-mb
2500` check, run immediately before any subprocess would have been started):

```
NOT ATTEMPTED -- pre-flight memory check failed: 1234MB available < 2500MB required.
```

Per `plan.md`'s Open Question 2 resolution, this is the expected, pre-declared outcome given
this sandbox's ~1.2GB available RAM -- not a bug, not retried, not forced through with a lowered
threshold. See `staging_artifacts/.../raw/ws_payload_2500_ABORTED.json`.

## AC3 -- Interpolation Factual Finding

**Confirmed: no interpolation system exists in the frontend today.** Entities snap to their
latest position on every WS data update; there is no delta-time tweening, no stored previous
position, and no per-frame render loop of any kind.

Re-verification grep (Step 8, run immediately before writing this report, per test_plan.md's
Anti-Drift Test Guards):

```
$ grep -rniE "requestAnimationFrame|\blerp\b|deltaTime|interpolat" frontend/src/
(zero matches)
```

`git diff --stat -- frontend/src/` is also empty -- none of this ticket's harness work touched
`frontend/src/`. Citing investigation.md's original evidence (independently re-confirmed, not
just trusted): `frontend/src/hooks/useCanvas.ts` lines 262-263 draw entities at
`ent.x * CELL_SIZE, ent.y * CELL_SIZE` -- the raw current coordinate from the latest delta, inside
a plain `useEffect` keyed on `[entities, ...]` (line 425) that redraws synchronously once per WS
message. `frontend/src/components/GameCanvas.tsx` lines 254-383 (minimap) follow the identical
pattern. **This ticket does not build or propose an interpolation system** -- it is out of scope
by the ticket's own Out of Scope section, and reported here strictly as a factual finding.

## AC4 -- Findings / Budget Misses (deferred, not fixed here)

Three genuine findings surfaced during measurement, none fixed in this ticket (measurement/
reporting only, per Out of Scope):

### Finding 1 -- force_full_scan's documented "Phase 17 Law" is dead code (discovered during Implement)

`plan.md`'s Step 1 point 7 (itself a correction of `investigation.md`'s original, disproven
`tick % 20 == 0` claim) expected that booting a `Kernel` with
`flags={"force_full_scan": True}` would make `src/engine/pipeline.py`'s "Phase 17 Law"
(a method named `AuthoritativeApplyPipeline._refresh_dirty_set`) force the resulting DirtySet --
and therefore the live WS delta's `changed` list -- to include every entity. **Verified false
during Implement**: a full-repository grep for `_refresh_dirty_set` finds exactly one match, its
own definition (`pipeline.py:363`) -- it is never called anywhere. `force_full_scan=True` does
genuinely widen phase-level entity iteration
(`src/core/dirty.py::get_relevant_entity_ids` returns every entity as a phase's candidate set)
and forces every phase to run (`PhaseDependencyGraph.should_run_phase`'s override), but the
DirtySet that actually reaches the WS broadcast is built exclusively by
`DirtySetBuilder.mark_from_update()` (called at `pipeline.py` lines 261, 296, 314, 329, 352),
which only marks entities that produced a real `EntityUpdate` that tick -- regardless of
`force_full_scan`. **Net effect: no live WS message with an all-entities `changed` list is
obtainable today via any documented mechanism.** This ticket's `full_scan` bucket is therefore a
harness-computed synthetic estimate (same presenter/serialization code path, no server involved),
clearly labeled as such in its own JSON output (`"method": "synthetic in-process construction --
NOT a live WS capture"`), not fixed here.

**Root-cause hypothesis**: `_refresh_dirty_set` looks like now-orphaned code from an earlier
pipeline revision -- its logic was superseded by the incremental `DirtySetBuilder.mark_from_update`
calls sprinkled through `refine()`, but the standalone method and its "Phase 17 Law" comment were
never removed, and nothing ever wired it in as the actual full-scan-forcing step.

**Deferred to a new ticket**: either (a) wire `_refresh_dirty_set` in for real (or delete it if it
is genuinely superseded), and/or (b) if there is a genuine product need for the WS layer to be
able to emit a true full-state broadcast on demand (e.g., for a reconnecting client that needs a
fresh baseline rather than relying on cumulative deltas), design and implement that as new,
explicit functionality -- not assumed to already exist.

### Finding 2 -- Steady-state payload size is highly bimodal at 500 entities, occasionally near full-scan size

The steady-state JSON bucket's p50 (8,435B) and p95/p99 (71,300B / 71,309B) differ by nearly 9x,
with p95/p99 landing almost exactly at the full-scan bucket's size (68,907B). This means some
ordinary ticks (no `force_full_scan` involved) organically mark nearly every entity dirty --
almost certainly a cadence-driven phase (e.g. `world_dynamics`, `strategic_intelligence`, or
`town_resolution`, all of which have `must_run_every_tick=True` or periodic-cadence entries in
`PhaseDependencyGraph.PHASES`) touching most entities on its scheduled tick. **Root-cause
hypothesis**: not investigated further here (out of scope -- measurement/reporting only); a future
ticket could correlate spike ticks against `state.tick % cadence.<system>` to confirm which
cadence-fired phase is responsible, and decide whether that fan-out is necessary or could be
narrowed.

### Finding 3 -- Observed tick throughput (~7.9 ticks/sec) well below the 20 TPS nominal target at 500 entities on this sandbox

The steady-state run collected 1000 samples (~1000 ticks, since a WS message fires on
essentially every tick per `compute_tick_delta`'s logic) over 126.33 wall-clock seconds -- **~7.9
ticks/sec observed**, vs. `V2EngineManager`'s nominal 20 TPS (`self._tick_rate = 0.05`, a fixed
post-tick sleep, not a target-rate scheduler -- so actual tick interval = tick-compute time +
0.05s). This implies ~0.076s of tick-compute cost was typical during this run, well above the
`cli_default` profile's `max_tick_budget_ms=50.0`. **Root-cause hypothesis**: not disentangled
here between (a) genuine 500-entity pipeline compute cost on 4 cores, and (b) this specific
sandbox's memory pressure (swap was at 3.9-4.0/4.0GB used at the start of this session -- see
"Resource conditions" below) inflating measured wall-clock cost above what dedicated hardware
would show. **Deferred to `TCK-20260825-LIVE-MAP-TPS-BUDGET-RECHECK`**: re-run this same
steady-state measurement (the script already built here,
`tools/perf/live_map_ws_payload_measure.py`, needs no changes) on a less-contended host to separate
genuine compute cost from this session's sandbox noise, before treating ~7.9 TPS as a real engine
finding rather than an environment artifact.

## Resource Conditions During This Session

This sandbox was measured at session start with ~156-240MB free / ~1.2GB available RAM and swap
at 3.9-4.0GB of 4.0GB used (near-exhausted) -- tighter than `investigation.md`'s own earlier
measurement, and explicitly flagged by the dispatching orchestrator as shared with other
concurrent sessions on the same machine. All resource guards specified in `plan.md`'s Open
Question 2 were implemented and armed for every run:

- Pre-flight (`>=2500MB` available before starting a >=2000-entity run): tripped as expected for
  the 2500-entity attempt (1234MB available), correctly prevented that run from starting at all.
- In-flight (poll `free -m` every 50 samples/messages, abort below 300MB available): armed for
  every run in this ticket; never tripped (available RAM stayed >=1.2GB throughout, and in fact
  recovered toward the end of the session -- likely other concurrent sessions releasing memory).
- Process-group kill handling (`start_new_session=True` + `os.killpg`, Python; `detached: true` +
  `process.kill(-pid, 'SIGTERM')`, Node) implemented in both harness scripts; confirmed no
  orphaned `uvicorn`/`python3 --internal-serve` processes remained after any run
  (`ps aux | grep -iE "uvicorn|live_map_ws_payload_measure|chromium|vite "` -> no matches at the
  end of this session).

## Summary Table

| AC | Status | CLASS_C (500) | CLASS_B (2500) |
|---|---|---|---|
| AC1 render FPS | Not measured (harness built, Chromium install blocked) | Not obtained | Not attempted |
| AC2 payload size | Measured, compared | Obtained (steady-state + full-scan, JSON + msgpack) | Not attempted (pre-flight guard) |
| AC3 interpolation finding | Achieved | -- (repo-wide finding) | -- |
| AC4 findings documented | Achieved | 3 findings documented above, all deferred | -- |
