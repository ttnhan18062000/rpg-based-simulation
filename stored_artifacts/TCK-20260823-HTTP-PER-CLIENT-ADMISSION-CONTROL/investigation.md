---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL
artifact_type: investigation
tags: [architecture, observability, api-design]
---

# Investigation — TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL

## Search-Before-Grep Note

`mcp__knowledge-search__search_docs` was called first (query: "HTTP admission control per-client
rate limiting NORMAL PRESSURE DEGRADED SURVIVAL ObservabilityMode"), per the Context Scan hard
rule. It returned `{"error":"index not found","action":"run make knowledge-index"}` — the same
confirmed, persistent outage the parent epic investigation hit. No retry was attempted; proceeded
straight to `graphify query` per the fallback ordering (two calls: `"per-client admission control
rate limiting HTTP"`, `"ObservabilityMode ResourceGovernor hysteresis"`). These surfaced
`ObservabilityController`/`ObservabilityMode` (`src/observability/event_recorder.py`),
`ResourceGovernor`/`RuntimeMode` (`src/engine/governor.py`, `src/core/governance.py`),
`RuntimeProfile` (`src/config/profiles.py`), the already-shipped `src/api/auth.py` and
`tests/api/test_api_key_auth.py` from the sibling ticket, and — critically — a **second, unrelated
`ObservabilityMode` class** at `src/observability/config.py:8` (community=12, distinct from the
`ObservabilityMode` at `event_recorder.py:23`, community=377/9). This second hit is a real, novel
finding this investigation's own graphify pass surfaced that the parent epic investigation did not
flag — see Anti-Drift Hazards. All further findings below come from reading the actual source and
docs these queries pointed at, plus the two prior artifacts named in this ticket's own dispatch
(parent epic investigation.md, sibling auth ticket's plan.md — both read first per instruction, not
re-derived here).

## Current Behavior

**`src/api/server.py::create_v2_app()`** (now ships auth, post `TCK-20260823-HTTP-API-KEY-AUTH`,
confirmed by direct read): `configure_api_keys(profile)` runs first inside `create_v2_app()`
(server.py:26). All 10 `include_router()` calls and 17 of 18 inline route decorators carry
`dependencies=[Depends(require_api_key)]` (9 routers + 14 inline routes),
`dependencies=[Depends(require_api_key_ws)]` (`stream.router`, the 10th router), or
`dependencies=[Depends(require_api_key_header_or_query)]` (3 dashboard routes). `/health` is the
sole exemption (no `dependencies=` kwarg, server.py:132). Middleware stack is unchanged from the
parent epic's findings: `CORSMiddleware` then `GZipMiddleware` — **no rate-limit or
admission-control middleware exists today.**

**`src/api/auth.py`** (real, shipped code — read in full):
- `ClientIdentity` — frozen (`ConfigDict(frozen=True)`) Pydantic `BaseModel`, one field
  (`client_id: str`). Frozen pydantic v2 models with hashable fields auto-generate `__hash__`, so
  `ClientIdentity` instances are usable as dict keys with zero extra code — confirmed by the
  sibling ticket's own `test_client_identity_exposes_client_id` (`{ci: 1}[ci] == 1`).
- `require_api_key(x_api_key: Header) -> ClientIdentity`, `require_api_key_header_or_query(header
  or query) -> ClientIdentity`, `require_api_key_ws(header or query) -> ClientIdentity` — all three
  raise (`HTTPException(401)` or `WebSocketException(1008)`) on failed resolution, otherwise return
  a `ClientIdentity`.
- `_client_keys: Dict[str, str]` — module-level `{sha256hex: client_id}` map, sole writer
  `configure_api_keys()`, called once per `create_v2_app()` invocation. **The set of possible
  `client_id` values is therefore bounded by the operator-configured `RuntimeProfile.api_key_hashes`
  string** — a fixed, finite, small set decided at process-startup time, not attacker-controlled
  (an unauthenticated/invalid-key request 401s inside `require_api_key` *before* any
  `ClientIdentity` is ever constructed — it never reaches a hypothetical admission-control
  dependency positioned after auth in the chain). This materially tempers (but does not eliminate)
  the "unbounded growth" framing in this ticket's own Scope/AC — see Risks and Open Questions.

**No dependency-chaining precedent exists in this repo yet.** Confirmed by
`grep -rn "= Depends(" src/api/`: every existing `Depends()` usage is either (a) at the
`include_router()`/route-decorator call site (`dependencies=[Depends(require_api_key)]`, applied to
the router/route, not threaded to a route parameter) or (b) a route function's own parameter
(`manager: V2EngineManager = Depends(get_engine_manager)`). **No function in this codebase is
itself a `Depends()`-callable that takes another `Depends()`-callable as one of its own parameters**
(e.g. `async def require_admission(identity: ClientIdentity = Depends(require_api_key))`). This is
new to the codebase, not an established pattern being extended — a real, if standard-for-FastAPI,
design choice this ticket introduces first.

**No `evict_expired`/TTL bounded-state precedent exists in `src/api/` that fits this ticket's
timing model.** `src/api/read_model_cache.py::ReadModelCache` implements the `ICacheable` protocol
(`src/engine/cache_registry.py`: `get_metrics()`, `evict_expired(current_tick, policy)`, `clear()`)
with FIFO-by-key eviction gated on `CacheBudgetPolicy.max_read_dtos`. **However, `ReadModelCache` is
never registered with a `CacheRegistry`** (`grep -rn "register_cache\|CacheRegistry("` across
`src/` shows only `movement_plan_cache` registered, in `src/engine/kernel.py:98,747`) — its
`evict_expired()` is dead code in practice, and the whole `ICacheable`/`CacheRegistry` mechanism is
keyed by `current_tick`, i.e. the *engine's* tick counter, swept from inside the kernel's own tick
loop. HTTP admission-control state is driven by wall-clock HTTP request arrival, asynchronously
from the engine tick loop, and the ticket's own Out-of-Scope/parent-investigation Anti-Drift
Hazards forbid the API layer from reaching into engine internals directly — so tying eviction to
`CacheRegistry`'s tick-based sweep is both mechanically awkward (nothing calls it for API-owned
caches today) and architecturally the wrong boundary to cross.

**The actual close analog is `src/observability/alerts/deduplicator.py::AlertDeduplicator`** — a
thread-safe (`threading.RLock()`), wall-clock (`time.time()`), string-keyed
(`Dict[str, float]`), lazy-prune-on-access sliding-window tracker:
`should_suppress()` calls `self.prune(current_time)` before every lookup, `prune()` computes
`expired_keys = [k for k, ts in ... if (current_time - ts) >= window]` and deletes them. No
separate sweep thread, no engine-tick dependency — pruning happens for free on the request path
that already needs the lock. This is the shape to follow for per-client admission state: prune
stale client entries lazily on every admission check, keyed on wall-clock idle time since last
request, under a lock (module-level state, mirroring `_client_keys`'/`_engine_manager`'s existing
process-global pattern in this same package).

**`src/domains/optimization/cache_strategy.py`** additionally shows this repo's established LRU
idiom (`CacheStrategy`, lines 10-33) — useful as the secondary, hard-cap backstop (see Scope
below), separate from the primary idle-TTL prune. **Correction (orchestrator, independently
re-read the real file): this is NOT an `OrderedDict`-based idiom** — the earlier draft of this
section mischaracterized it. The real implementation uses a plain `Dict[CacheKey, Any]` (`_cache`)
plus a parallel `List[CacheKey]` (`_keys_order`) that's manually kept in recency order via
`.remove(key)` + `.append(key)` on access (move-to-end) and `.pop(0)` on overflow (evict-oldest) —
`cache_strategy.py:17-33`. This repo has no existing `collections.OrderedDict`/`.move_to_end()`
usage to reuse; Plan should either mirror this exact dict+list pattern (matching real repo
convention) or use `OrderedDict` as a genuinely new-to-this-repo choice, but must not describe it
as "reusing an existing `OrderedDict` idiom" since no such precedent exists.

## Mechanics / Engine Constraints

- **`ObservabilityMode(str, Enum)`** — confirmed at `src/observability/event_recorder.py:23-27`:
  exactly `NORMAL`, `PRESSURE`, `DEGRADED`, `SURVIVAL`. `ObservabilityController.evaluate(
  queue_fill_ratio, event_rate_per_tick=0.0) -> ObservabilityMode` (event_recorder.py:43-54) is a
  **pure**, stateless threshold function: `>=0.70 -> PRESSURE`, `>=0.90 -> DEGRADED`, `>=1.00 ->
  SURVIVAL`, else `NORMAL`. It has **no hysteresis of its own** — `EventRecorder.record()`
  (event_recorder.py:159-168) calls `evaluate()` fresh on every single event and reassigns
  `self._obs_mode` immediately, with no dwell/confidence gating at all. This is the "mode
  vocabulary" half of the pattern this ticket must extend (names + thresholds-as-a-pure-function
  shape), but **not** the hysteresis half — that lives elsewhere (below). `observability_status()`
  (event_recorder.py:263-272) returns `{mode, queue_fill_ratio, events_dropped, survival_counts}`;
  `reset_mode()` (event_recorder.py:274-279) resets to `NORMAL` and clears counters — both
  confirmed as the literal accessor-pair template for this ticket's own
  `admission_status()`/`reset_admission_mode()`.
- **`ResourceGovernor.evaluate()`/`_can_recover()`** — confirmed at `src/engine/governor.py:27-146`
  as the real hysteresis mechanism (not `PhaseBudgetGovernor`, which `governor.py:61-63` shows is
  called *by* `ResourceGovernor.evaluate()` as a pure budget-derivation step, with no mode-transition
  logic of its own — the parent investigation's correction is confirmed by direct read). Exact
  mechanics: `indicated_mode = self._get_indicated_mode(...)`; if `indicated_mode > current_mode`,
  escalate immediately via `status.reset_dwell(indicated_mode, current_tick)` (governor.py:43-45,
  no gating at all on escalation); if `indicated_mode < current_mode`, only recover if
  `_can_recover()` returns `True`, and even then only `RuntimeMode(current_mode - 1)` — one level at
  a time (governor.py:46-51, "Law: Monotonic recovery"); if equal, `status.increment_dwell()`
  (governor.py:55-56). `_can_recover()` (governor.py:103-146) requires BOTH (a)
  `status.mode_dwell_ticks >= profile.dwell_time_ticks` and (b) the last
  `profile.confidence_window_ticks` samples in `status.get_recent_history(window_size)` are *all*
  below `recovery_watermark`-scaled thresholds (if fewer than `window_size` samples exist yet,
  `_can_recover()` returns `False` — "if we don't even have enough samples yet, stay safe").
- **`RuntimeProfile` tunables** (`src/config/profiles.py:42-44`, confirmed real fields with real
  current defaults, not placeholders): `recovery_watermark: float = 0.8` (range `[0.5, 0.95]`),
  `dwell_time_ticks: int = 10` (`>= 0`), `confidence_window_ticks: int = 5` (`>= 0`). These are
  reused as-is by all four `PROD_*` profiles (no override), and by the already-shipped
  `api_key_hashes: str = ""` field added immediately below them
  (`src/config/profiles.py:56-68`) by the sibling auth ticket. **These fields are "ticks" in the
  literal sense of `ResourceGovernor`'s engine-tick-driven evaluation loop.** HTTP admission control
  has no engine tick to count against — each client's `evaluate()`-equivalent call happens once per
  incoming HTTP request for that client, asynchronously and at whatever rate that client sends
  requests. **Reusing these three fields' *values* is straightforward (Scope already mandates it);
  reusing "ticks" as the *unit* requires redefining "tick" as "one admission-check call for this
  client"** (i.e., `dwell_time_ticks`/`confidence_window_ticks` count admission-evaluations for that
  specific client, not engine ticks or wall-clock seconds) — the most direct, literal analog to
  `ResourceGovernor`'s own semantics (each `evaluate()` call = one unit of dwell), and avoids
  introducing a wall-clock-vs-tick-count unit mismatch against fields whose descriptions and
  existing profile defaults were tuned for a tick-counted context. This is a Plan decision to make
  explicit and record, not something Investigate can silently assume — flagged as an Open Question.
- **The rate/pressure *signal* itself has no ready-made source.** `ResourceGovernor` is fed
  `PressureSignals` (`src/core/governance.py`) built from real engine telemetry (tick compute time,
  memory, worker/queue utilization, work debt). `ObservabilityController` is fed a queue fill ratio.
  Per-client HTTP admission control has neither — Scope's own "single-process in-memory
  token-bucket/sliding-window limiter" is the source signal this ticket must build: each client's
  own request-rate utilization (current rate / configured limit, a 0.0–1.0+ ratio) becomes the
  `queue_fill_ratio`-analog input into a per-client `evaluate()`-shaped mode function, which then
  needs the dwell/confidence gating layered on top per the ticket's Scope. This two-layer shape
  (rate signal -> indicated mode -> hysteresis-gated committed mode) is the natural composition of
  the two reused patterns and is not itself present anywhere in the codebase pre-built.

## Docs Requiring Update

- `docs/architecture/observability_hot_path_safety_contract.md`: §5 ("Dynamic Observability Mode
  (OBS-BACKPRESSURE, INFRA-199)", `observability_hot_path_safety_contract.md:67`) documents
  `ObservabilityMode`/`ObservabilityController` as observability-subsystem-only. If this ticket
  literally reuses the class (parameterized per-client, e.g. instantiating one
  `ObservabilityController` and threading a per-client mode dict around it) rather than a fully
  parallel HTTP-side copy, §5 needs a line noting the HTTP layer is now also a consumer of the
  *pure threshold function* — reusing the parent investigation's exact recommendation, reconfirmed
  here by direct read of the actual (unmodified-by-this-ticket, per Out of Scope) class shape.
- `docs/parity_ledger/infrastructure.yaml`: new entry required (next free ID confirmed
  `INFRA-378` — `INFRA-377`, the sibling auth ticket's entry, is the current last entry). Must cite
  a real `test_path` since the ticket's own AC set (per-client eviction policy, hysteresis
  mirroring `ResourceGovernor`) is P1-adjacent behavior gating a "public internet, multi-tenant"
  deployment, matching `INFRA-199`'s and `INFRA-377`'s own P1 precedent.
- `docs/plans/http_admission_control_epic.md`: still attributes the hysteresis pattern to
  "`PhaseBudgetGovernor`'s threshold-crossing-with-cooldown approach" (confirmed still present,
  line ~29, by direct read — not yet corrected despite the parent investigation and this
  investigation both confirming `ResourceGovernor.evaluate()`/`_can_recover()` is the real
  mechanism). This ticket's own Plan/Document-Update phase should correct this mis-attribution
  when it lands, consistent with the sibling auth ticket's own precedent of editing this same
  epic doc's stale content during its Document-Update phase (see that ticket's plan.md
  "Deviations" section — a real, already-established precedent for this exact file, not a novel
  scope-creep risk).
- Reference only, not a doc this ticket edits: `docs/architecture/http_api_key_authentication.md`
  (new, shipped by the sibling ticket) — §5 ("`ClientIdentity`'s reuse contract") already commits
  this ticket to keying its own per-client state off `ClientIdentity` without narrowing its shape.
  This ticket's own new doc (see below) should cross-reference it, not restate it, and this ticket
  does not modify the sibling's file itself.
- `docs/engine/known_limitations.md`: parent investigation flagged this as needing a line update
  once HTTP admission control ships (the "no admission control" boundary condition is now
  resolved); confirmed still unmentioned by direct grep (`grep -n "admission" docs/engine/
  known_limitations.md` — no hits). In scope for this ticket specifically (not the auth-only
  sibling), since admission control is what actually closes this limitation.
- A new `docs/architecture/` doc for the admission-control mechanism itself (exact filename is a
  Plan decision, mirroring `docs/architecture/http_api_key_authentication.md`'s freshly-established
  precedent and grain) — this is a brand-new feature/mechanism, not a modification of existing
  documented behavior, so it needs its own doc per CLAUDE.md's "new logic/features/settings" rule,
  not just a footnote elsewhere.

## Parity Ledger Overlap

- `INFRA-199` (`infrastructure.yaml:10682`) — `verified`, **P1**. The exact
  `NORMAL/PRESSURE/DEGRADED/SURVIVAL` vocabulary and `record()`/`observability_status()`/
  `reset_mode()` behavior this ticket extends. Confirmed `test_path:
  tests/unit/observability/test_obs_backpressure.py` exists and covers exactly what
  `event_recorder.py` implements today (mode enum values, `evaluate()` thresholds at
  0.69/0.70/0.85/0.90/0.95/1.00/1.10, per-mode `record()` drop/sample/pass behavior,
  `observability_status()`/`reset_mode()` accessor correctness) — read the full file; **this
  suite tests `ObservabilityController`/`EventRecorder` directly via their real class names and
  does not mock/stub around a seam this ticket could accidentally widen.** If this ticket
  instantiates a bare `ObservabilityController()` per-client (reusing the *class*, not copying its
  source) without modifying `event_recorder.py` itself, this suite is unaffected and stays out of
  this ticket's regression surface *by construction*, not merely by promise — confirmed, not
  assumed.
- `INFRA-377` (`infrastructure.yaml:10946`) — `verified`, P1. The sibling auth ticket's entry;
  its own text explicitly names this ticket ("a reusable identity object for the sibling
  per-client admission-control ticket"). Not reopened by this ticket, but the new admission-control
  entry (next free ID `INFRA-378`) should cross-reference it the same way.
- `INFRA-365` (`infrastructure.yaml:10717`) — `verified`, P2. `GovernorPolicy.from_mode()` /
  `RuntimeMode` — the vocabulary this ticket must explicitly NOT extend (per Scope/parent
  investigation). Confirmed unaffected; cited here only as the boundary this ticket's own new
  parity entry should mention by name to make the non-conflation explicit and discoverable.
- No parity entry currently exists for HTTP-layer admission control/rate limiting — this is a
  pure documentation-and-implementation gap, matching the parent investigation's finding.

## Prior Work

- `TCK-20260823-HTTP-API-KEY-AUTH` (done, shipped): delivered exactly what this ticket depends
  on — `ClientIdentity`, `require_api_key`/`require_api_key_header_or_query`/`require_api_key_ws`,
  and the `dependencies=[Depends(...)]` wiring convention at every `include_router()`/route-decorator
  call site in `server.py`. Its `plan.md` Decision 1-9 and Anti-Drift Notes are authoritative for
  how `server.py` is now shaped; **this ticket's own wiring must follow the same
  per-call-site-kwarg convention**, not a middleware rewrite of the existing structure (see Risks
  below for the concrete middleware-vs-`Depends()`-chaining tradeoff analysis).
- `tests/api/test_api_key_auth.py::test_only_dashboard_and_websocket_routes_use_weaker_auth_channel`
  is a directly reusable **pattern**, not just precedent: it introspects `app.routes[i].dependant
  .dependencies` by `dep.call.__name__` to assert exactly which routes carry which
  `Depends()`-callable, rather than trusting source-reading. This is the right template for an
  admission-control anti-drift guard test (e.g., "every route that requires `require_api_key`/
  `require_api_key_header_or_query`/`require_api_key_ws` also requires the admission-control
  dependency, with no route silently exempted").
- `TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG` (done) — cited only for its
  `tests/api/test_cors_config.py` pattern (in-process `TestClient`, real response assertions), the
  same template `test_api_key_auth.py` and this ticket's own new test file should follow.
- `TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC` (parent, tracking): its investigation.md is
  authoritative for the `ObservabilityMode`/`RuntimeMode` vocabulary distinction and the
  `PhaseBudgetGovernor`/`ResourceGovernor` mis-attribution correction — both reconfirmed by this
  investigation's own direct reads, not re-derived independently.

## Risks and Open Questions

- **Open — "tick" unit redefinition for `dwell_time_ticks`/`confidence_window_ticks` at the HTTP
  layer.** As detailed in Mechanics/Engine Constraints, these fields are semantically engine-tick
  counters in `ResourceGovernor`'s context. Recommend: redefine "tick" as "one admission-evaluation
  call for this specific client" (i.e., increment per-client dwell/confidence-window counters once
  per request from that client, not once per engine tick or per wall-clock second) — the most
  direct analog, requiring no new profile fields and no wall-clock dependency. This is a real
  design decision Plan must state explicitly and is not free of judgment calls (e.g., a client that
  sends one request per hour would "dwell" for `dwell_time_ticks` *requests*, which could span
  hours of wall-clock time — arguably correct, since a client that rarely calls in poses no
  sustained pressure to recover *from*, but worth stating as a deliberate tradeoff, not an
  oversight).
- **Open — the per-client rate/pressure *signal* has no precedent to reuse and must be designed
  fresh (token bucket vs. sliding window), then wired as the "indicated mode" input.** Scope names
  both "token-bucket" and "sliding-window" as acceptable Plan choices; this investigation found no
  existing implementation of either pattern anywhere in `src/` to reuse (confirmed by the
  eviction/TTL grep above turning up cache/expiry patterns, not rate-limiting algorithms) — this is
  genuinely new code, not a reuse-and-adapt case. Recommend token bucket (simpler continuous-rate
  model, natural fit for a 0.0–1.0+ "fill ratio" analog feeding straight into an
  `ObservabilityController.evaluate()`-shaped function) over sliding-window (requires a rolling
  timestamp list per client, more memory per entry, harder to reason about at the escalation
  boundary) — but this is a recommendation for Plan to confirm, not a foreclosed decision.
- **Open, but substantially informed by this investigation — the eviction/TTL design.** Given (a)
  the confirmed `AlertDeduplicator` precedent (lazy, prune-on-access, wall-clock idle-TTL, no
  separate sweep thread/thread pool needed) and (b) the confirmed fact that `client_id` values are
  bounded by the operator-configured key set (not attacker-inflatable), the recommended design is:
  **primary mechanism = lazy idle-TTL prune-on-access** (mirroring `AlertDeduplicator.prune()`,
  called at the top of the admission-control dependency under the same lock that reads/writes
  per-client state; a client with no activity for `N` seconds/minutes has its entry evicted on the
  *next* unrelated request's prune pass — no entry lingers forever, and no background thread is
  needed) **plus a secondary, defense-in-depth max-entries hard cap** (mirroring
  `src/domains/optimization/cache_strategy.py`'s real dict+ordered-list move-to-end-on-access LRU
  idiom — see the Prior Work correction above; this repo's actual pattern is a plain `Dict` plus a
  parallel `List` kept in recency order, not `collections.OrderedDict`) that
  evicts the least-recently-active entry if a *new* client_id would push the dict past the cap —
  belt-and-suspenders even though the primary source of entries (the configured key set) is
  normally small and finite. This directly satisfies the AC's literal wording ("no unbounded growth
  from an ever-increasing set of distinct client IDs") regardless of how bounded the common case
  actually is, and gives Plan two concrete, source-precedented mechanisms rather than an invented
  one. Concrete TTL/cap *values* (idle-seconds threshold, max-entries number) are not decided by
  this investigation — no existing config field covers them, so Plan must either add new,
  narrowly-scoped fields (following `RuntimeProfile.api_key_hashes`'s own just-shipped pattern of a
  new field with a safe, documented default) or hardcode a documented constant; this is a genuine
  open call for Plan, not something Investigate should silently pick.
- **Resolved (with a concrete recommendation) — middleware vs. `Depends()`-chaining wiring.**
  Investigated directly against this repo's installed FastAPI 0.128.4/Starlette 0.52.1 (same
  versions the sibling ticket's plan.md already confirmed) and the real execution-order contract:
  FastAPI/Starlette middleware (`app.add_middleware(...)`) runs **before** route-level dependency
  resolution for every request, on the raw ASGI scope, with no access to the already-resolved
  `ClientIdentity` a `Depends()` chain produces — middleware would have to **re-implement**
  `require_api_key`'s exact key-resolution/hashing/comparison/401-vs-WebSocketException logic
  itself to know which client is calling, duplicating the sibling ticket's Step 1 entirely and
  creating two independently-maintained copies of the same security-sensitive comparison logic (a
  direct violation of "Do not create hidden or implicit durable behavior" in spirit — divergence
  between the two copies would be a silent security bug). **Recommendation: `Depends()`-chaining, not
  middleware.** A new `require_admission(identity: ClientIdentity = Depends(require_api_key)) ->
  ClientIdentity` (or similar) dependency, added as an *additional* entry in each existing
  `dependencies=[Depends(require_api_key), Depends(require_admission)]` list (or the
  `_header_or_query`/`_ws` equivalents for the 6 already-special-cased routes) at every
  `include_router()`/route-decorator call site `server.py` already carries. This is real,
  additional editing work at all 28 already-touched call sites (confirmed count from the sibling
  ticket's plan.md Decision 1) — the tradeoff Scope's own wording anticipates ("doubling that
  ticket's edits") — but it is a mechanical, low-risk, per-line kwarg addition (the sibling ticket's
  own Step 4 precedent), not a design risk, and it correctly reuses the already-resolved
  `ClientIdentity` for free via FastAPI's own dependency-caching (a `Depends()` callable resolved
  once per request is cached and reused by every other dependency needing the same call in the same
  request — `require_api_key`'s result is not computed twice). Middleware remains theoretically
  possible only if it re-derived identity independently, which this investigation recommends against
  as a duplicated-logic/silent-divergence risk with no compensating benefit at this codebase's
  current single-process scale.
- **Open, flagged not decided — whether admission-control state should use `ObservabilityController`
  as a literal reused class instance (one instance, called per-client with per-client state tracked
  externally) or a fully parallel HTTP-side class.** The Scope/ticket's own Assumptions section
  leaves this open; this investigation confirms both are mechanically viable (the class's
  `evaluate()` is pure/stateless, so a single shared instance called with different per-client
  inputs is safe and requires no modification to `event_recorder.py`, satisfying Out of Scope) but
  does not have a strong basis to force one recommendation — Plan should weigh "reuse the literal
  class + a per-client dict of dwell/confidence state" (less new code, clearer lineage to
  `ObservabilityMode`) against "a fully parallel `AdmissionController` class with its own thresholds"
  (clean naming, no accidental coupling to the observability module's own evolution). Given the
  ticket's own Scope text says "reuse the mode names and the accessor-pattern *shape*... as the
  *template*," not "reuse the class," a parallel class following the same shape is at least as
  consistent with the ticket's own wording as literal reuse — Plan's call.

## Anti-Drift Hazards

- **A third, unrelated `ObservabilityMode` class exists in this codebase, at
  `src/observability/config.py:8`** (`OFF/LIGHT/NORMAL/FULL/RESEARCH/DEBUG/CERTIFICATION/
  LONG_RUN` — a deployment-verbosity-mode enum, driving `ObservabilityConfig`'s feature-flag
  resolution, completely unrelated to backpressure/admission). This is a genuine, previously-
  unflagged naming collision this investigation's own graphify pass surfaced (not caught by the
  parent epic investigation, which only distinguished `ObservabilityMode` from `RuntimeMode`). Do
  not import from `src.observability.config` when reaching for the backpressure vocabulary — the
  correct import is always `from src.observability.event_recorder import ObservabilityMode`. A
  future editor or IDE autocomplete could easily grab the wrong one; this ticket's own new module
  and any doc it writes should name the exact import path explicitly to prevent this.
- **Do not attach admission-control logic to FastAPI middleware** — see Risks above for the full
  analysis; middleware cannot see the already-resolved `ClientIdentity` without re-implementing
  auth's key-resolution logic, which would create a second, divergence-prone copy of
  security-sensitive comparison code.
- **Do not modify `src/observability/event_recorder.py` or `src/engine/governor.py`** (Out of
  Scope, reconfirmed by this investigation's full read of both) — even if literally instantiating
  `ObservabilityController` per-client, this must be import-and-use only, zero edits to that
  module, so `test_obs_backpressure.py` stays untouched and its regression status stays
  unambiguous.
- **Do not tie per-client eviction to `src/engine/cache_registry.py`'s `CacheRegistry`/
  `ICacheable`/tick-based sweep.** It is engine-tick-keyed, swept from inside the kernel's own tick
  loop, and reaching into it from `src/api/` would be a new API/engine boundary crossing this
  repo's layering doesn't currently have (confirmed: `ReadModelCache` implements `ICacheable` but
  is never actually registered/swept — do not treat its mere existence in `src/api/` as evidence
  this is the right precedent to extend).
- **Do not let `require_admission` (or equivalent) run before `require_api_key` in any
  `dependencies=[...]` list.** Admission control needs a resolved `ClientIdentity` to key its own
  state — if ordered first, it would have no identity to key on (FastAPI does not guarantee
  declared-order execution across sibling `Depends()` entries in all versions/configurations
  without a direct parameter-chain dependency; the safest, most explicit mechanism is exactly the
  `identity: ClientIdentity = Depends(require_api_key)` parameter-chain shape recommended above,
  which makes the ordering an explicit data dependency FastAPI's own resolver guarantees, not an
  implicit list-order assumption).
- **Do not silently widen the `_DASHBOARD_AND_WS_PATHS` weaker-auth-channel set** (`tests/api/
  test_api_key_auth.py:32-39`) while wiring admission control onto the same 6 routes — the sibling
  ticket's own anti-drift guard test pins this set exactly; admission control is an independent
  concern layered on top and must not require changing which routes use which *auth* channel.
- **Do not scope-creep the rate-limit signal design into a general-purpose rate-limiting
  framework** (Out of Scope explicitly excludes this, and the epic doc's own "cautionary example"
  language about infrastructure added ahead of need applies directly) — a minimal token-bucket or
  sliding-window counter sufficient to produce a 0.0–1.0+ ratio is the entire scope of the signal
  layer.
