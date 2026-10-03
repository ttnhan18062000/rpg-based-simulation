---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260821-LIVE-MAP-PERF-VALIDATION
artifact_type: investigation
tags: [performance, websocket, testing]
---

# Investigation — TCK-20260821-LIVE-MAP-PERF-VALIDATION

## Search-Before-Grep Compliance Note

Both mandated semantic-search tools were attempted first, in order, and both are non-functional in
this specific worktree today — this is an environment gap, not a skipped step:

- `mcp__knowledge-search__search_docs` (called 4x with topic queries) returned
  `{"error": "index not found", "action": "run make knowledge-index"}` for every query. The index
  only exists in the main checkout (`/home/u24desktop/Working/rpg-based-simulation/knowledge-index/`),
  not in this git worktree (`.claude/worktrees/docs-build-lastupdate-metadata-overhead/`) — worktrees
  don't share gitignored generated artifacts.
- `graphify query "<topic>"` first failed identically (`graph file not found:
  .../graphify-out/graph.json` — same worktree-vs-main-checkout gap). Retried with
  `--graph /home/u24desktop/Working/rpg-based-simulation/graphify-out/graph.json` pointed at the
  main checkout's graph, which did work, but the returned graph is **stale relative to this
  worktree's actual code** — e.g. it still shows `useSimulation.ts` importing `fetchJSON`/
  `decodeRLE`/a `MockEventSource`-based test double, not the real WebSocket-based implementation
  this worktree's `useSimulation.ts` actually contains today (confirmed by reading the file
  directly — see below). The main checkout's graph predates tickets 1-6 of this epic landing, or at
  least predates a `graphify update .` run after they landed. Useful only for high-level file/symbol
  discovery (it did correctly point at `src/api/ws/stream.py`, `src/api/read_model_cache.py`,
  `src/perf/long_run_harness.py`, `tests/perf/test_perf_api_snapshot.py`), not for any claim about
  current behavior.
- Fallback `python3 tools/knowledge_search.py query ...` also failed: `sentence-transformers` isn't
  installed for the bare `python3` in this worktree; retried with
  `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` (the project's real venv,
  pointed at the main checkout's built `knowledge-index/knowledge.db`), which has the package but
  failed differently — `all-MiniLM-L6-v2` isn't cached locally and `HF_HUB_OFFLINE=1` blocks the
  live download (`OSError: We couldn't connect to huggingface.co ... local_files_only`). This
  matches a previously-recorded finding (`TCK-20260817-KGMCP-SEARCH-MCP-TEST-REQUIRES-UNBUILT-CI-INDEX`,
  confirmed still present in `docs/REGISTRY.yaml`) — not new, but re-confirmed live here.

All three tools were tried, in the mandated order, before any grep/Read. What follows is grep/Read
verification against the actual worktree source, which is what this investigation's claims are
based on — not the stale graph output.

## Current Behavior

### Frontend live-map data flow (as it exists in this worktree today)

- `frontend/src/hooks/useSimulation.ts` — confirmed **not** the stale `fetchJSON`/`decodeRLE`-poll
  shape the graph showed. It fetches `/map`, `/static`, `/manifest` once (lines 91-121), then opens
  a real `WebSocket` to `${wsBase()}/ws` (`wsBase()` builds the URL from `window.location.protocol`
  + `window.location.host`, line 6-9; connection at line 141). On `onmessage` it applies
  `{tick, changed, removed, events}` deltas directly into React state (lines 147-205) — no
  intermediate buffering. A secondary 500ms `fallbackPoll` (line 221-300) still exists for
  `/stats`, the full-detail selected entity, and ground items/resource/building dynamic fields — the
  live map's *entity position/HP/state* stream is WS-only, but selection detail and a few dynamic
  object fields are still REST-polled.
- No API key or `?key=`/`X-API-Key` is attached anywhere in this file — confirmed by reading every
  `fetch`/`WebSocket` call site. This matches the disclosed blocker.

### Frontend render path — confirmed NO interpolation exists

- `grep -rniE "requestAnimationFrame|\blerp\b|deltaTime|interpolat" frontend/src/` → **zero matches**,
  repo-wide, not just in the three files named in the ticket's Related Code Areas.
- `frontend/src/hooks/useCanvas.ts`: the entity-drawing effect (line 95-425) is a plain React
  `useEffect` keyed on `[entities, groundItems, buildings, resourceNodes, selectedEntityId,
  selectedEntity]` (line 425) — it redraws synchronously, once, every time React state changes
  (i.e. every WS message that changes `entities`). Entities are drawn at `ent.x * CELL_SIZE`,
  `ent.y * CELL_SIZE` (lines 262-263) — the raw current coordinate from the latest delta, with no
  stored previous position, no `Date.now()`/`performance.now()` reference, and no per-frame redraw
  loop. `frontend/src/components/GameCanvas.tsx`'s minimap effects (lines 254-383) are the same
  pattern — plain `useEffect`s keyed on state, no `requestAnimationFrame` anywhere in the file.
- **Confirmed factual finding, independently verified, not just trusted from the ticket text**:
  entities snap to the latest position on every data update; there is no interpolation, no
  delta-time tweening, and no per-frame render loop of any kind in the frontend today. This is
  exactly what the ticket's Request Summary already asserted — verification found no daylight
  between the claim and the code.
- Practical consequence for "measure render FPS": there is no existing rAF loop to sample from.
  "Render FPS" in this codebase, as it stands, means "how much wall-clock time does one
  `useCanvas` redraw effect take per incoming WS delta message" — a harness has to *impose* rAF
  sampling around the existing event-driven redraw, not observe a loop that's already there.

### Backend broadcast path

- `src/api/ws/stream.py::stream_ws` (`/ws` route, line 18): accepts, does a JSON handshake, then
  loops `payload = await queue.get()` → `websocket.send_json` (or `send_bytes(msgpack.packb(...))`
  if `format == "msgpack"`). The frontend's handshake (`useSimulation.ts` line 144) hardcodes
  `format: 'json'` — **today's live map never actually exercises the msgpack path**, even though
  the server supports it. Any msgpack payload-size number this ticket produces is a secondary,
  hypothetical data point, not a measurement of what production traffic actually does.
- The queue is fed by `V2EngineManager.add_tick_listener` (`src/api/engine_manager.py` line 94),
  called from `_run_loop` (line 282-314): every engine tick, `_update_latest_state` (line 152) calls
  `self._read_cache.compute_tick_delta(state, dirty_set, force_full, state.tick)`
  (`src/api/read_model_cache.py` line 118-151), and `_notify_listeners` fires **only if the result
  isn't `None`** (line 305). `compute_tick_delta` returns `None` on a quiet tick unless
  `tick % 20 == 0` (line 148) — i.e. there's a forced heartbeat/full-scan-equivalent at least every
  20 ticks even with zero changes, and every genuinely dirty tick broadcasts immediately. So
  broadcast cadence is tick-driven, not time-driven — there is no independent "every N ms" throttle
  on the WS send path.
- `compute_tick_delta`'s `changed` list is built only from `candidate_ids` returned by
  `ReadModelInvalidationPolicy.get_dirty_entity_ids(dirty_set, ..., force_full_scan)` — on a normal
  tick this is a small dirty subset, not all entities; on a `force_full_scan` tick (which the
  `tick % 20` heartbeat forces via `state_full` semantics from the kernel, confirmed by the
  `force_full` local in `_update_latest_state`) it's every alive entity. This is the mechanism a
  measurement harness should use to capture a "full-state-equivalent" WS payload for like-for-like
  comparison against the V1 REST baseline (see "V1 baseline" section below) — force or wait for a
  `tick % 20 == 0` tick and measure that message specifically, separately from steady-state
  small-delta messages.

### Auth gate — confirmed fail-closed, no bypass, but a legitimate working key IS obtainable

`src/api/auth.py` (read in full):
- `configure_api_keys(profile)` (line 31) parses `profile.api_key_hashes` (a `RuntimeProfile` field,
  default `""`) into a module-level `_client_keys: Dict[hash, client_id]`.
- `_resolve_client_id` (line 65-81) does a constant-time scan of `_client_keys`; if the dict is
  empty (no keys configured) **every** raw key — including an empty one — fails to match and
  returns `None`. There is no "no keys configured → allow all" fallback anywhere. Confirmed
  fail-closed with zero bypass, exactly as the ticket's disclosed blocker states.
- `require_api_key_ws` (line 110-125, used by `stream.router`'s WS routes via
  `src/api/server.py` line 101: `dependencies=[Depends(require_api_key_ws), Depends(require_admission_ws)]`)
  accepts the key via **either** the `X-API-Key` header **or** a `?key=` query param (line 111-112) —
  explicitly because, per its own docstring, "a browser's native `WebSocket()` constructor also
  cannot set headers." So a real browser connecting to `/api/v1/ws` MUST use `?key=`.
- **This is not an unbreakable wall.** `RuntimeProfile.api_key_hashes` is a normal, settable field
  (`src/config/profiles.py` line 56-68: `'client_id:sha256hex'` pairs, parsed by
  `_parse_api_key_hashes`). A harness that boots its own backend process can set a known raw key's
  SHA-256 hash into that field (or the `RPG_API_KEY_HASHES` env var — see `_run_serve`,
  `src/cli/entry.py` line 279, which threads `args.api_key_hashes` into `cli_overrides`) and then
  legitimately present the matching raw key. This exact pattern is already proven working end to
  end in `tickets/done/TCK-20260823-LIVE-TEST-API-KEY-AUTH.md` (see "Prior Work" below) —
  `subprocess.Popen(["python3", "-m", "src", "serve", ...])` with `RPG_API_KEY_HASHES` seeded in
  the subprocess env, then a real Python `websockets` client connects to `/api/v1/ws` with
  `additional_headers={"X-API-Key": raw_key}` and passes. That ticket's own file list includes
  `tests/api/test_ws_protocol.py` connecting to the exact same `/api/v1/ws` route this ticket needs.
- **What "frontend has zero API-key wiring" actually means, concretely**: `useSimulation.ts`'s
  `WebSocket(...)` call and `fetch(...)` calls never attach a key anywhere — confirmed above. This
  ticket is Out-of-Scope-barred from editing that file. A **test harness** (not production code) can
  still legitimately supply the key without editing `useSimulation.ts`: a real headless-browser
  harness (e.g. Playwright) can inject `X-API-Key` on REST calls via network-route interception
  (`page.route(...)`, rewriting outgoing request headers — standard technique, doesn't touch app
  source) and can rewrite the browser's `WebSocket` constructor via an `addInitScript` to append
  `?key=<raw>` to the URL before constructing the real `WebSocket` — again, a page-level init-script
  injected by the test harness, not a change to any file under `frontend/src/`. This is judged **in
  scope** for a genuine live-frontend-in-a-browser test (it's how the harness authenticates itself,
  analogous to `additional_headers` in the already-shipped Python `websockets` test pattern), not a
  bypass of the auth mechanism itself (the key is still validated normally, no shortcut in
  `src/api/auth.py`). Flagged as a judgment call for the Plan phase to confirm, not silently assumed.

### Dev-proxy `ws: true` gap — confirmed, and confirmed there is no other route through the dev proxy

`frontend/vite.config.ts` (read in full, lines 13-33): `server.proxy['/api']` sets `target` and
`changeOrigin` only — no `ws: true`. Vite's dev-server proxy is `http-proxy`-based; without
`ws: true` the proxy middleware does not attach an `upgrade` event handler, so a WS upgrade request
to `http://localhost:5173/api/v1/ws` will not be forwarded to the backend at all (the HTTP `/api/*`
REST calls work fine without it — only the WS upgrade handshake needs it). Confirmed no static
mount of the frontend build exists in the backend either (`grep -n "StaticFiles\|mount(" 
src/api/server.py` → no hits), so there's no way to serve the frontend from the backend's own
origin and sidestep the proxy that way.

**A harness-only path around this exists without touching `vite.config.ts`**: the frontend computes
its WS target from `window.location.host` at runtime (`useSimulation.ts` line 6-9), so a Playwright
`addInitScript` override of `window.WebSocket` can rewrite the *host* in the constructed URL from
`localhost:5173` to the real backend's `host:port` before invoking the native `WebSocket`,
connecting directly to the backend and bypassing the Vite proxy for the WS leg entirely (REST calls
stay on the working, unmodified proxy). `src/api/ws/stream.py` performs no `Origin` header check
(confirmed by reading the full file — no `websocket.headers.get("origin")` or similar anywhere), so
a direct cross-port browser-native WebSocket connection is not blocked server-side either.

**This is real engineering, not a one-line fix.** Both the API-key injection and the WS-host
rewrite are legitimate, but they are exactly the "minimal frontend perf/e2e measurement harness"
the ticket's own Scope already calls out as needing to be built — they are not optional polish on
top of a simpler harness, they are load-bearing parts of it. The Plan phase should size this
honestly rather than treating "add rAF sampling" as the whole job.

### No headless browser tooling exists today

`frontend/package.json` (read in full): dependencies are React/Radix/Tailwind; devDependencies are
`vitest`, `jsdom`, `@testing-library/react`, `eslint`, `typescript`, `vite` — **no `playwright` or
`puppeteer`**, confirmed absent from `frontend/node_modules` too
(`ls frontend/node_modules | grep -iE "playwright|puppeteer"` → no match). `vite.config.ts`'s `test`
block uses `jsdom` (line 34-38) — jsdom has no real paint/compositor pipeline, and this worktree
does not have the optional `canvas` npm package installed (`frontend/package-lock.json` references
`"canvas": "^3.0.0"` only as jsdom's own optional peer dependency, not installed —
`frontend/node_modules` has no `canvas` directory). So `HTMLCanvasElement.getContext('2d')` under
the current `vitest`+`jsdom` setup cannot do real pixel drawing, and jsdom's `requestAnimationFrame`
is a `setTimeout` shim with no relationship to real display refresh timing — **jsdom cannot be used
to measure real render FPS, only to unit-test hook logic** (which is exactly what
`useSimulation.test.tsx` already does, and all it does — confirmed by reading it in full: it mocks
`globalThis.WebSocket`, never touches `useCanvas`/`GameCanvas`, and asserts on hook state, not on
any pixel or timing output).

- **npm registry is reachable** from this sandbox: `curl -sI https://registry.npmjs.org/playwright`
  → `HTTP/2 200`. Playwright's browser-binary CDN also resolves and redirects successfully:
  `curl -sI https://playwright.azureedge.net` → `HTTP/2 307` → `location:
  https://playwright.download.prss.microsoft.com/...`. **This was a connectivity check only — no
  `npm install`/`npx playwright install` was actually run** (out of scope for an investigation-only
  pass, and installing ~300MB of Chromium unasked is not this phase's call). Disk has 9.1GB free
  (`df -h .`), which is enough headroom if Plan/Implement decides to install it. This is a real
  contrast with the `search_docs`/`knowledge_search.py` failure above, where the HuggingFace CDN
  really is blocked (`LocalEntryNotFoundError`/offline-mode error) — playwright's CDN is not
  similarly blocked, at least at the DNS/TLS-handshake level tested here.

### Real host hardware does not certify as CLASS_B — this materially affects what can be reported

`nproc` → **4**. `free -h` → **5.8Gi total RAM**, and at the moment this was checked, **138Mi free /
1.2Gi available**, with **swap 4.0Gi used out of 4.0Gi (essentially full)**. Compare against
`docs/engine/contracts/certification_contract.md` §3 (read in full, lines 30-34):
```
CLASS_A: >= 16 Logical Cores AND >= 32GB Total RAM.
CLASS_B: >= 4 Logical Cores AND >= 8GB Total RAM.
CLASS_C: All other systems.
```
This sandbox has 4 cores (meets the CLASS_B core count) but **5.8GB total RAM, which fails the
>=8GB requirement** — under this contract's AND-rule, this machine is **CLASS_C**, not CLASS_B, full
stop. It also currently shows severe memory pressure (swap nearly exhausted), independent of the
classification question — running a 2500-entity synthetic scenario plus a headless browser
concurrently on a host already at ~1.2GB available is a real risk of OOM or heavy swap thrashing
that would itself invalidate any "measured" p50/p95/p99 numbers as noise, not signal.

`docs/performance/perf_baseline_policy.md` §2.2 (read in full) gives the entity-count *targets*
this ticket's AC literally quotes verbatim — `CLASS_B: 2,500 entities`, `CLASS_C: 500 entities` —
and self-documents its own conflict with the certification contract's AND-rule in an inline note
(lines 30-35), attributing it to `TCK-20260702-OBSISO-ISOLATION-PROOF`, "flagged, not fixed."

**Resolving which definition is "genuinely correct" for this ticket (not just repeating the
pre-existing flag)**: these two documents answer two different questions, and the apparent conflict
is really a labeling collision, not two answers to the same question:
- `perf_baseline_policy.md` §2.2 answers "how many entities should a CLASS_B/CLASS_C-**named**
  benchmark scenario contain" — a benchmark-authoring convention. This is the number this ticket's
  own AC needs (2500 / 500), and no other doc defines it, so it is the correct source for entity
  counts regardless of the labeling conflict.
- `certification_contract.md` §3 answers "given a real machine's actual core count and RAM, which
  class does *that machine* certify as" — and is explicitly marked "(Proof-Stable)," i.e. it's the
  definition an automated certification/proof check would use. Per CLAUDE.md's own precedence
  (`docs/engine/` is one of the two "definitive sources," `docs/performance/` is not on that list),
  this is the more authoritative rule for classifying *actual hardware*.
- Consequence: use `perf_baseline_policy.md`'s entity counts for scenario sizing (2500 for the
  "CLASS_B-scale" run, 500 for the "CLASS_C-scale" run), but use `certification_contract.md`'s
  AND-rule to honestly report **this sandbox's own hardware class** in the Scoped Claims disclosure
  — which is CLASS_C. This means a "2500-entity, CLASS_B-scale scenario measured on CLASS_C-actual
  hardware" is the honest framing this environment can produce; it must not be reported as "CLASS_B
  performance" without that caveat, since Scoped Claims discipline (the ticket's own AC) requires
  stating Hardware Class truthfully, and `docs/testing/test_taxonomy.md` line 154 independently
  confirms hardware class is currently **self-declared only** (`PERF_HARDWARE_CLASS` env var,
  informational, not verified against real specs) — so nothing else in this repo's tooling would
  catch a mislabeled claim; it's on this ticket's own reporting discipline to get it right.

### World/entity-count scaffolding that exists today

- No production world-generation config or scenario file produces exactly 2500 or 500 entities —
  `grep -rn "2500" src/perf/ tests/perf/ tools/` found nothing relevant, and
  `docs/scenarios/phase1/scenario5_perf.yaml` / `docs/archive/profiling_performance/performance_scenarios.md`
  are older/archived, not sized to this ticket's counts.
- `src/perf/scenarios.py::build_idle_state(entity_count: int, seed: int = 42)` (read in full,
  lines 17-53) is a parametrized synthetic `AuthoritativeState` builder that takes an arbitrary
  `entity_count` directly — no world-compiler/content-resolution pass involved. This is the cleanest
  existing building block for constructing a 2500-entity or 500-entity state without needing new
  world-authoring content, and several existing perf tests already use the same
  direct-`AuthoritativeState`-construction pattern (`tests/perf/test_api_projection_perf.py`
  instantiates `V2EngineManager(profile=PROD_DEFAULT, entities_count=200)` directly).
- **`src/cli/entry.py`'s `serve` subcommand has a real, load-bearing gap**: its argument parser
  defines `--entities` and `--seed` flags (lines 26-25 in the `srv` sub-parser block), but
  `_run_serve` (line 267-290) never reads `args.entities` or `args.seed` at all — only
  `args.workers` and `args.api_key_hashes` are threaded into `cli_overrides`. `grep -n
  "args.entities\|args.seed\|args.world" src/cli/entry.py` confirms these two are used only by the
  unrelated `cli` subcommand (lines 206, 211), never by `serve`. So `python3 -m src serve
  --entities 2500` **silently ignores** `--entities` today.
- `src/api/server.py` line 36 confirms why: `create_v2_app` unconditionally does
  `manager = V2EngineManager(profile)` — and `V2EngineManager.__init__`
  (`src/api/engine_manager.py` line 22) defaults `entities_count: int = 10`. Booting the real server
  via the documented CLI path (`python3 -m src serve`) today always produces a **10-entity** world,
  regardless of profile or CLI flags.
- **Workable path that needs no production code change**: a harness-owned Python script (not under
  `src/`) can call `create_v2_app(profile)` for the FastAPI app object, then explicitly build and
  install its own `V2EngineManager(profile, entities_count=2500)` via
  `src.api.dependencies.set_engine_manager(...)` before handing the app to `uvicorn.run(...)` — the
  same "construct `V2EngineManager` directly with a custom `entities_count`" pattern several
  existing perf tests already use (`tests/perf/test_api_projection_perf.py`,
  `tests/observability/test_metrics_export.py`). This sidesteps the broken CLI flag entirely without
  touching `src/cli/entry.py` or `src/api/server.py`.

### V1 baseline — confirmed exact definition, and confirmed it is NOT the same shape as the new WS delta

`docs/archive/performance/performance-report-api-payload.md` (read in full): the ~75KB number is
`GET /api/v1/state` (no `?selected=`), **polled every ~80ms**, measured over **10 ticks at ~360
entities**, and is a **full-state snapshot** of all entities' slim schema (`EntitySlimSchema`, ~200
bytes/entity) plus ground items — not a delta of only-changed entities. `/static` (buildings,
resource nodes, treasure chests, regions, ~47KB) and `/map` (RLE-compressed grid, ~270KB) are both
one-time fetches, separate from the 75KB recurring number.

This is a materially different shape from the new WS `compute_tick_delta` payload
(`{tick, changed, removed, events}`), which on a normal tick only contains entities whose dirty bits
fired that specific tick — typically a small subset, not all ~2500/~500 entities. **A raw
byte-for-byte comparison of "one WS delta message" against "75KB" would be comparing different
things and is explicitly what the ticket's AC warns against** ("comparing like-for-like
(full-state-equivalent, not naive per-delta)"). The correct like-for-like comparison, given the
mechanism (see "Backend broadcast path" above): capture a WS message on a `tick % 20 == 0`
heartbeat/force-full-scan tick specifically (which contains every alive entity, the same
"full snapshot" shape the V1 baseline measured), and compare *that* message's size against a
75KB-at-360-entities baseline scaled by entity count (i.e. report both the raw byte count and a
per-entity-normalized figure), while separately and honestly reporting steady-state per-tick delta
size (expected much smaller) as its own, differently-labeled number — not blended into the "vs. V1
baseline" comparison.

GZip note: `docs/parity_ledger/infrastructure.yaml` INFRA-052 documents GZip middleware for "large
metadata responses" — this applies to HTTP responses only; WebSocket frames are not passed through
FastAPI's `GZipMiddleware`. So WS payload-size numbers should be reported as raw
JSON/msgpack bytes, with no compression assumption, whereas the V1 75KB REST baseline may have had
GZip in the response path depending on client `Accept-Encoding` — worth stating explicitly which
was measured (uncompressed body size) so the comparison isn't silently apples-to-oranges on
compression too.

## Mechanics / Engine Constraints

- `docs/engine/performance_contract.md` §3.1 "Scoped Claims" (read in full, lines 35-42): every
  performance claim must state Runtime Profile, Hardware Class, Scenario, Execution Mode, and
  RuntimeMode — this is the exact discipline the ticket's AC quotes, and is the binding format for
  how this ticket's eventual report must be written.
- §3.2 "measurement Protocol": minimum 100 warmup ticks before recording, minimum 1000 sampled
  ticks for a baseline — the ticket's own AC ("≥1000 sampled render frames") mirrors this at the
  render layer, not just the engine-tick layer; both windows should be respected independently (100
  warmup ticks for the engine before the browser starts sampling frames, then ≥1000 render-frame
  samples on top).
- `docs/testing/test_taxonomy.md` line 90 and 145-154: existing `tests/perf/` infrastructure
  (`perf_budget` fixture, `perf_baselines.json`, `PERF_HARDWARE_CLASS` env var) is backend-tick-cost
  focused and does not currently cover frontend render timing or WS wire-payload size at all — this
  ticket is extending perf coverage into a domain (`frontend/`, live WS wire bytes) the existing
  harness was never built for, not just adding one more `tests/perf/` case in the existing style.

## Docs Requiring Update

None as a required-change item for *this* ticket. This ticket is measurement-and-reporting only
(explicitly Out of Scope: "Any change to production frontend/backend code paths," and no behavior
changes are proposed) — its own findings belong in a new report artifact (see Test Plan), not as an
edit to any existing mechanics/engine/parity doc.

The `docs/performance/perf_baseline_policy.md` §2.2 CLASS_B/CLASS_C vs
`docs/engine/contracts/certification_contract.md` §3 AND-rule conflict (path:
`docs/performance/perf_baseline_policy.md`, and path: `docs/engine/contracts/certification_contract.md`)
is not required to change for this ticket: it is a pre-existing, already-self-documented conflict
(`docs/performance/perf_baseline_policy.md` lines 30-35 already name
`TCK-20260702-OBSISO-ISOLATION-PROOF` as the ticket that flagged it and explicitly deferred fixing
it), and this ticket's own scope is measurement/reporting, not doc reconciliation — resolving the
conflict for real would mean editing one or both docs' hardware-class tables, which is a separate,
larger, cross-cutting doc-accuracy ticket, not something a single perf-validation ticket should do
as a side effect.

The `docs/parity_ledger/infrastructure.yaml` entries `INFRA-050`/`INFRA-051` (path:
`docs/parity_ledger/infrastructure.yaml`) are not required to change for this ticket either: they
assert WS payload *shape* compatibility (already `status: verified`), not payload *size*/performance
— this ticket doesn't change or newly verify shape, only measures size and frame timing of the
already-shipped shape.

## Parity Ledger Overlap

- `docs/parity_ledger/infrastructure.yaml`: `INFRA-049` (msgpack handshake support,
  `status: legacy_verified`, P0, `test_path: null`), `INFRA-050` (initial post-handshake payload
  shape, `status: verified`, P0, `test_path: null`), `INFRA-051` (tick/entity/event payload shape,
  `status: verified`, P0, `test_path: null`) all directly cover the same WS route
  (`/api/v1/ws`) this ticket measures. **Flag**: all three are P0 with `test_path: null`, which
  per CLAUDE.md's Authoritative Mechanics Rule technically means they lack the passing test_path a
  P0 entry requires — but this is a pre-existing gap unrelated to this ticket's own scope (shape
  compatibility, not size/performance); this ticket's own measurement harness could incidentally
  exercise those routes but doing so does not substitute for a real `test_path` addition to those
  ledger entries, and adding one is not this ticket's job. Reported as an observation, not
  something this ticket will fix.
- `INFRA-052` (GZip middleware for large metadata responses, `status: legacy_verified`, P0): relevant
  context for correctly stating whether measured payload bytes are compressed or not (see V1
  baseline section above) — not itself something this ticket changes.
- No `town_resource.yaml`/`combat_movement.yaml`/etc. entries overlap; this ticket doesn't touch
  gameplay mechanics.

## Prior Work

- `tickets/done/TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET.md` (ticket 6 of this epic): its Test
  Summary is the source of both disclosed blockers this ticket inherits, verbatim-confirmed against
  the actual code in this investigation (auth gate: `src/api/auth.py`; proxy gap:
  `frontend/vite.config.ts`). Also confirms `useCanvas.ts`/`GameCanvas.tsx` were **not** touched by
  that ticket (`git diff --stat` empty for both) — so this investigation's read of those two files
  reflects their true, unmodified-since-before-the-epic state.
- `tickets/done/TCK-20260823-LIVE-TEST-API-KEY-AUTH.md`: the single most directly reusable prior
  artifact for this ticket. It already proves, end to end, that a real backend process
  (`subprocess.Popen(["python3", "-m", "src", "serve", ...])`) can be booted with a seeded
  `RPG_API_KEY_HASHES` and connected to over a real WebSocket (`websockets.connect(...,
  additional_headers={"X-API-Key": raw_key})`) against the exact `/api/v1/ws` route this ticket
  needs (`tests/api/test_ws_protocol.py`), under `.venv/bin/python3` (this repo's real, pydantic-capable
  interpreter — confirmed present at `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3`,
  absent from this worktree, same gap that ticket's own Implementation Notes recorded). This proves
  the **backend-side** half of this ticket's measurement (payload size over a real WS connection) is
  fully achievable today with zero new engineering — only the entity-count scale-up
  (`V2EngineManager(profile, entities_count=2500)`) is new.
- `tickets/done/TCK-20260823-HTTP-API-KEY-AUTH.md`: origin of the auth mechanism itself
  (`docs/architecture/http_api_key_authentication.md`), confirms `require_api_key_ws`'s
  header-or-query design decision (Decision 4) is intentional and documented, not an oversight this
  ticket could route around some other way.
- No prior stored artifact addresses frontend render-FPS measurement or a headless-browser harness
  — this genuinely does not exist yet anywhere in the repo's history, confirming the ticket's own
  Scope framing ("Build the minimal frontend perf/e2e measurement harness ... since none exists
  today").

## Risks and Open Questions

1. **Open question requiring a Plan-phase decision, not assumed here**: is the
   WebSocket-constructor-rewrite + fetch-header-injection Playwright technique (see "Dev-proxy
   `ws: true` gap" above) acceptable as "harness code, not production code" under this ticket's
   Out-of-Scope clause ("Any change to production frontend/backend code paths")? This investigation's
   judgment is yes (no file under `frontend/src/` or `src/` changes; it's page-level test
   instrumentation, directly analogous to the already-shipped Python `websockets`
   `additional_headers` pattern), but it's non-trivial engineering and should be explicitly
   confirmed at Plan, not silently built.
2. **Real, current resource risk**: this sandbox is at ~1.2GB available RAM with swap nearly
   exhausted (measured live, see hardware section). A 2500-entity synthetic world plus a headless
   Chromium instance running concurrently is a real OOM/thrashing risk that could produce garbage
   timing numbers (swap-induced latency spikes, not genuine render cost) rather than a clean failure
   — Plan should decide whether to attempt CLASS_B(2500) scale at all given this, or to explicitly
   report CLASS_C(500)-scale as the only sandbox-trustworthy number and document the CLASS_B attempt
   as best-effort/caveat-heavy.
3. **Hardware-class mislabeling risk**: as detailed above, this sandbox is CLASS_C by
   `certification_contract.md`'s AND-rule, not CLASS_B, regardless of which entity count is used in
   the scenario. Any report produced here must state this explicitly per Scoped Claims discipline —
   silently calling a run "CLASS_B" because it used 2500 entities would misrepresent the actual
   hardware class of the machine it ran on.
4. **Playwright install not actually attempted** — network reachability was checked (both npm
   registry and Playwright's browser-binary CDN resolve/redirect successfully), but the real
   `npm install -D playwright && npx playwright install chromium` step was not run in this
   investigation pass. There remains a real chance the actual binary download stalls or fails partway
   even though the initial redirect succeeded; Plan/Implement must verify this directly rather than
   trust this investigation's connectivity-only check.
5. **`--entities`/`--seed` CLI flags are dead code today** for the `serve` subcommand (confirmed
   above) — this is a real, independently-discoverable gap unrelated to this ticket's core ask, not
   introduced or required to be fixed by this ticket (Out of Scope bars production code changes).
   Flagging it here so Plan doesn't accidentally assume `python3 -m src serve --entities 2500` works
   as written — it silently doesn't.
6. **msgpack is not exercised by the real frontend today** (hardcoded `format: 'json'` in
   `useSimulation.ts`) — any msgpack payload-size number this ticket produces must be labeled as a
   secondary/hypothetical measurement (achievable via a raw `websockets` client sending a
   `format: 'msgpack'` handshake), not as "what the live map actually sends," since it isn't.

## Anti-Drift Hazards

- **Do not build an interpolation system.** The ticket's Out of Scope explicitly bars this, and the
  "no interpolation exists" finding is meant to be reported as a fact, not treated as a bug to
  quietly fix while building the measurement harness. A tempting drift: once a harness developer
  sees jittery/snapping entity movement during manual observation, there's a real pull toward "just
  add a quick lerp to make the demo look better" — that is new feature work, explicitly out of scope
  here.
- **Do not silently patch `frontend/vite.config.ts` or `src/cli/entry.py`'s dead `--entities` flag**
  to make the harness's life easier. Both are real, legitimate gaps this investigation found, but
  fixing either is a production-code change this ticket's Out of Scope explicitly forbids. Route
  around them with harness-only code (direct `V2EngineManager` construction, WS-constructor
  rewriting via Playwright init script) instead, exactly as described above.
- **Do not report a CLASS_C-hardware-actual run as "CLASS_B" performance** just because the scenario
  used 2500 entities. Entity count and hardware certification are two different axes (see above);
  conflating them is the single easiest way this ticket's own AC (Scoped Claims discipline) could be
  violated without anyone noticing.
- **Do not treat a mocked-WebSocket vitest pass as evidence of live behavior.** The existing
  `useSimulation.test.tsx` suite (10 passing tests, confirmed via ticket 6's Test Summary) mocks
  `globalThis.WebSocket` entirely and never touches `useCanvas`/`GameCanvas` — it is not a substitute
  for the real-browser measurement this ticket requires, and should not be cited as if it were.
- **Do not blend steady-state per-tick delta size with the full-scan/heartbeat message size** into
  one undifferentiated "payload size" number when comparing against the V1 75KB baseline — they are
  structurally different messages (see V1 baseline section) and reporting only one, unlabeled,
  would misrepresent what's actually happening on the wire.
