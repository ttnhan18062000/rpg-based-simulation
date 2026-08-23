---
status: active
layer: architecture
authority: P1
audience: developer
---

# HTTP Admission Control

This document describes the per-client, in-memory admission-control mechanism
layered onto `src/api/server.py::create_v2_app()`'s HTTP and WebSocket routes,
added by `TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL`. It is item 2 of 2
extracted from `docs/plans/http_admission_control_epic.md`; item 1,
`TCK-20260823-HTTP-API-KEY-AUTH` (`docs/architecture/http_api_key_authentication.md`),
establishes the `ClientIdentity` object this mechanism keys its own per-client
state off of.

---

## 1. Mechanism

Admission control is implemented as FastAPI `Depends()`-callables
(`src/api/admission_control.py`), not middleware — the same reasoning as the
sibling auth ticket: middleware cannot see the already-resolved
`ClientIdentity` without re-implementing key resolution.

- **Composition**: three wrappers — `require_admission`, `require_admission_header_or_query`,
  `require_admission_ws` — each take the corresponding, already-shipped auth
  dependency (`require_api_key`, `require_api_key_header_or_query`,
  `require_api_key_ws`) as their own parameter (e.g.
  `identity: ClientIdentity = Depends(require_api_key)`), so the resolved
  `ClientIdentity` chains through FastAPI's own parameter-dependency graph.
  This makes the auth-then-admission ordering an explicit, FastAPI-guaranteed
  data dependency rather than incidental `dependencies=[...]` list order.
  At 23 of `server.py`'s 27 protected route sites, the admission dependency
  **replaces** the auth-only entry in place (`dependencies=[Depends(require_admission)]`).
  At the 4 sites using the weaker header-or-query/WebSocket auth channel (the
  3 dashboard routes and `stream.router`'s 1 wiring site backing 3 WebSocket
  routes), the admission dependency is **appended alongside** the original
  auth dependency instead
  (`dependencies=[Depends(require_api_key_header_or_query), Depends(require_admission_header_or_query)]`) —
  a deviation from the pure-replace strategy, recorded in
  `staging_artifacts/TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL/plan.md`'s
  "Deviations" section, required to keep
  `tests/api/test_api_key_auth.py::test_only_dashboard_and_websocket_routes_use_weaker_auth_channel`
  (a pinned anti-drift test this ticket does not edit) green: that test inspects
  each route's top-level dependant graph for the auth dependency's name, which a
  pure replace would move one level deeper. Either way, FastAPI caches a
  resolved dependency per request keyed by the callable itself
  (`dependant.cache_key`), so the auth dependency is computed exactly once per
  request regardless of how many places reference it.
- **Signal**: a per-client in-memory token bucket (30-token capacity, 3
  tokens/second refill, 1 token consumed per admission-check call) produces a
  `fill_ratio` in `[0.0, 1.0+]` — `0.0` when the bucket is full (client has
  been quiet), approaching/exceeding `1.0` when the client is sustained above
  the refill rate. This is directly analogous to
  `ObservabilityController.evaluate()`'s `queue_fill_ratio` input.
- **Per-mode behavior**: only `SURVIVAL` mode rejects a request.
  `NORMAL`/`PRESSURE`/`DEGRADED` all admit — mirroring
  `ObservabilityController`'s own real per-mode behavior, where `PRESSURE`/
  `DEGRADED` reduce event volume but never hard-stop, and only `SURVIVAL` is a
  full stop. `PRESSURE`/`DEGRADED` are still visible via `admission_status()`
  so an operator/dashboard can see a client trending toward being shed.
- **Rejection**: `HTTPException(429)` with a static `Retry-After: 5` header for
  ordinary REST/dashboard routes; `WebSocketException(code=1013)` ("Try Again
  Later") for `stream.router`'s 3 WebSocket routes — a different code from
  `require_api_key_ws`'s `1008` (invalid credentials), so a client can
  distinguish "your key is wrong" from "you are being rate-limited."
- **`/health`**: stays completely exempt — no `dependencies=` kwarg at all,
  matching its existing zero-auth exemption. This is the sole exemption.

---

## 2. Mode Vocabulary and Import Path

The mode vocabulary is `ObservabilityMode` (`NORMAL`/`PRESSURE`/`DEGRADED`/
`SURVIVAL`), imported — never redefined or modified — from
`src.observability.event_recorder`. `src/api/admission_control.py` constructs
its own `ObservabilityController()` instance (`_controller`), separate from
`EventRecorder`'s own singleton; `ObservabilityController.evaluate()` is a
pure function with no instance attributes mutated, so the two independent
instances never interact.

**A second, unrelated class of the same name exists at
`src/observability/config.py:8`** (`OFF`/`LIGHT`/`NORMAL`/`FULL`/`RESEARCH`/
`DEBUG`/`CERTIFICATION`/`LONG_RUN` — deployment-verbosity modes, completely
unrelated to backpressure/admission). The correct import for this module's
vocabulary is always `from src.observability.event_recorder import
ObservabilityMode`. `tests/api/test_admission_control.py::test_admission_control_mode_vocabulary_matches_observability`
asserts `src.api.admission_control.ObservabilityMode is
src.observability.event_recorder.ObservabilityMode` as a hard, automated guard
against a future accidental import from the wrong module.

`ObservabilityMode` is `(str, Enum)`, not `IntEnum`. A bare `>`/`<` comparison
between two `ObservabilityMode` members does **not** raise `TypeError` — it
silently inherits `str`'s own ordering and compares the mode *names*
alphabetically (`"DEGRADED" < "NORMAL" < "PRESSURE" < "SURVIVAL"`), producing
wrong-but-plausible booleans with no exception to catch the mistake. This
module never compares `ObservabilityMode` members directly; it defines a
private `_MODE_RANK: Dict[ObservabilityMode, int]` and compares via
`_MODE_RANK[a] > _MODE_RANK[b]` everywhere magnitude comparison is needed.

---

## 3. Hysteresis

Escalation/recovery reuses `ResourceGovernor`'s real hysteresis pattern
(`src/engine/governor.py::evaluate()`/`_can_recover()`, `governor.py:27-146`)
— **not** `PhaseBudgetGovernor` (`src/engine/phase_governor.py`), which is a
pure consumer of an already-decided mode with no hysteresis logic of its own.
`docs/plans/http_admission_control_epic.md` previously mis-attributed this
pattern to `PhaseBudgetGovernor`; that mis-attribution is corrected as part of
this ticket (see that doc's own updated text).

- **"Tick" redefinition**: one `dwell_time_ticks`/`confidence_window_ticks`
  unit = one admission-evaluation call for that specific client (the most
  direct literal analog to `ResourceGovernor`'s tick-per-`evaluate()`-call
  semantics). `RuntimeProfile.dwell_time_ticks` (default `10`) and
  `.confidence_window_ticks` (default `5`) are reused as-is
  (`src/config/profiles.py:42-44`) — no new profile fields are introduced.
- **Escalation** is immediate on any mode increase — no dwell delay.
- **Recovery** requires `dwell_time_ticks` admission-evaluation calls to have
  elapsed since the last mode change, *and* the last `confidence_window_ticks`
  fill-ratio readings to all be below the recovery-scaled threshold, before a
  client steps down exactly one mode level.
- **Recovery-watermark scaling** reuses `ObservabilityController`'s own
  threshold constants directly (`PRESSURE_THRESHOLD=0.70`,
  `DEGRADED_THRESHOLD=0.90`, `SURVIVAL_THRESHOLD=1.00`,
  `event_recorder.py:39-41`), each scaled by
  `RuntimeProfile.recovery_watermark` (default `0.8`) to get that tier's
  recovery limit — mirroring `ResourceGovernor._can_recover()`'s per-signal
  scaling (`governor.py:131-134`). A future change to
  `ObservabilityController`'s thresholds automatically propagates without a
  second edit site.

---

## 4. Per-Client State Bounding

Per-client state (`_client_state: Dict[str, _ClientAdmissionState]`) is new,
previously-unbounded state, bounded by two independent mechanisms:

- **Lazy idle-TTL prune-on-access** (`_prune_idle_clients`, 1800 seconds) —
  mirrors `AlertDeduplicator.prune()` exactly
  (`src/observability/alerts/deduplicator.py:37-48`): on every admission
  check, compute every client whose `last_active_time` is older than the TTL
  and delete those entries.
- **Max-entries LRU hard cap** (`_evict_lru_if_over_capacity`, 1000 entries) —
  mirrors `CacheStrategy`'s dict-plus-parallel-list idiom
  (`src/domains/optimization/cache_strategy.py:10-34` — a plain `Dict` +
  `List` kept in recency order, not `collections.OrderedDict`): when about to
  insert a new client and the store is at capacity, evict the
  least-recently-active entry first.

Both constants (`_IDLE_TTL_SECONDS`, `_MAX_CLIENT_ENTRIES`), along with the
token-bucket capacity/refill rate (`_BUCKET_CAPACITY=30.0`,
`_BUCKET_REFILL_PER_SECOND=3.0`), are hardcoded module constants, not new
`RuntimeProfile` fields — no existing token-bucket or rate-limiting
implementation exists elsewhere in `src/` to reuse, and no test requires
operator-tunability of the rate itself. A future ticket can promote these to
profile fields if real traffic data warrants it.

---

## 5. Relationship to `TCK-20260823-HTTP-API-KEY-AUTH`

This mechanism composes with, and depends on, that ticket's `ClientIdentity`/
`require_api_key*` dependencies (`src/api/auth.py`) — admission-control state
is keyed by `identity.client_id`, the same identity object auth resolves. See
`docs/architecture/http_api_key_authentication.md` for the full auth mechanism
and route classification; this document does not restate that content.
