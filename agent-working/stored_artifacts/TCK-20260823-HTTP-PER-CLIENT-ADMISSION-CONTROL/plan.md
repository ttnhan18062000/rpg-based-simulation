---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL
artifact_type: plan
tags: [architecture, observability, api-design]
---

# Implementation Plan — TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL

## Summary

Add `src/api/admission_control.py`, a new module holding a per-client, in-memory token-bucket
admission controller that reuses `ObservabilityMode`/`ObservabilityController` (imported, never
modified, from `src.observability.event_recorder` — explicitly NOT `src.observability.config`'s
unrelated same-named class) as the mode vocabulary and pure threshold function, and reimplements
`ResourceGovernor`'s real escalation/recovery hysteresis (`src/engine/governor.py:43-56,103-146`)
adapted to a single per-client 0.0–1.0+ signal instead of `ResourceGovernor`'s four
`PressureSignals` fields. Three new `Depends()`-callables — `require_admission`,
`require_admission_header_or_query`, `require_admission_ws` — each take the corresponding,
already-shipped auth dependency (`require_api_key`, `require_api_key_header_or_query`,
`require_api_key_ws`) as their own parameter, so the resolved `ClientIdentity` chains through
FastAPI's own parameter-dependency graph (never relying on `dependencies=[...]` list order).
`server.py`'s existing 27 `dependencies=[Depends(require_api_key*)]` entries (23
`require_api_key`, 3 `require_api_key_header_or_query`, 1 `require_api_key_ws` — corrected count,
see Decision 1) are each **replaced in place** with the corresponding
`require_admission*` entry, not appended alongside the auth entry, since the admission
dependency's own parameter already forces auth to resolve first and FastAPI's per-request
dependency cache means `require_api_key` is still computed exactly once either way. Per-client
state is bounded by two independent, source-precedented mechanisms: a lazy idle-TTL
prune-on-access (mirroring `AlertDeduplicator.prune()`, `src/observability/alerts/
deduplicator.py:37-48`) and a max-entries LRU hard cap using a plain `Dict` + parallel `List`
kept in recency order (mirroring `CacheStrategy`'s real dict+list idiom, `src/domains/
optimization/cache_strategy.py:10-34` — confirmed NOT `OrderedDict`-based). Only `SURVIVAL` mode
actually rejects a request (`429 Too Many Requests`, `Retry-After` header); `NORMAL`/`PRESSURE`/
`DEGRADED` all admit the request (mirroring `ObservabilityController`'s own real per-mode
behavior, where `PRESSURE`/`DEGRADED` reduce event volume but never hard-stop, and only
`SURVIVAL` is a full stop) — this is a deliberate scope-bounding decision, not an oversight; see
Decision 5. `/health` stays exempt (no dependency added at all, matching its existing zero-auth
exemption). New test file `tests/api/test_admission_control.py` covers every test named in
test_plan.md. Five doc files get updates (matching investigation.md's five parseable `- \`docs/
...\`` bullets exactly, for `check_docs_to_update_coverage`'s coverage check) plus one new
doc, `docs/architecture/http_admission_control.md` (its investigation.md bullet does not parse as
a required path — see Anti-Drift Notes — but it is still built, per the Hard Rule that new
logic/features/settings get their own doc). One new parity ledger entry, `INFRA-378`.

## Key Decisions

**Decision 1 — Route-count correction (source-verified, not from investigation.md).**
`grep -n "dependencies=\[Depends(" src/api/server.py` returns **27** matches, not the ticket's
"up to 28": 1 `require_api_key_ws` (server.py:90, `stream.router`), 23 `require_api_key`
(server.py:93,96,99,102,105,108,111,114,117 — 9 routers — plus server.py:122,138,148,158,172,
179,187,196,207,212,217,239,250,256 — 14 inline routes), and 3 `require_api_key_header_or_query`
(server.py:280,2375,2379 — the 3 dashboard routes). This plan's Step 2 enumerates all 27 by line
number and touches every one; `/health` (server.py:132, confirmed by direct read, no
`dependencies=` kwarg) remains the sole exemption, unchanged.

**Decision 2 — Composition mechanism: replace the existing `Depends(require_api_key*)]` entry
in-place with `Depends(require_admission*)`, do not append a second list entry.**
Investigation left this explicitly open, flagging FastAPI's dependency-caching behavior as the
deciding factor. Confirmed: FastAPI/Starlette caches a resolved dependency per request keyed by
the callable itself (`dependant.cache_key`), so whether `require_api_key` is referenced directly
in the `dependencies=[...]` list, transitively through `require_admission`'s own `identity:
ClientIdentity = Depends(require_api_key)` parameter, or both, it is computed exactly once per
request either way — investigation's own conclusion, reconfirmed here. Given that, appending a
second list entry (`dependencies=[Depends(require_api_key), Depends(require_admission)]`) would
be redundant, not incorrect. This plan chooses **replace** because: (a) it keeps every
`dependencies=[...]` list at length 1, a strictly smaller diff at all 27 sites than growing every
list to length 2; (b) it makes the auth-then-admission ordering an explicit, FastAPI-guaranteed
data dependency (the exact mechanism investigation's own Anti-Drift Hazards recommends — "the
safest, most explicit mechanism is exactly the `identity: ClientIdentity = Depends(require_api_key)`
parameter-chain shape") rather than relying on incidental list-order or redundant duplication.
`require_admission`'s own body always resolves and returns the underlying `ClientIdentity`
unchanged on success, so callers see identical behavior to today's `require_api_key`-only wiring,
plus the new admission check.

**Decision 3 — Three parallel admission wrappers, mirroring the three existing auth
dependencies, not one generic one.** `require_api_key_ws` (`src/api/auth.py:110-125`) raises
`starlette.exceptions.WebSocketException`, never `fastapi.HTTPException`, because FastAPI's
websocket dependency resolution (`fastapi/routing.py::get_websocket_app`) runs before
`websocket.accept()` and only `WebSocketException` is safely converted to a clean
`websocket.close()` by Starlette's `ExceptionMiddleware` (confirmed by the sibling auth ticket's
plan.md Decision 4, itself confirmed by direct source read — not re-derived here). The same
constraint applies to any admission-control rejection on `stream.router`'s 3 websocket routes:
`require_admission_ws` must raise `WebSocketException`, not `HTTPException(429)`, on `SURVIVAL`.
`require_admission_header_or_query` exists only because it must chain
`Depends(require_api_key_header_or_query)` instead of `Depends(require_api_key)` for the 3
dashboard routes (server.py:280,2375,2379) — its admission logic (token bucket, hysteresis,
`429` on `SURVIVAL`) is otherwise identical to `require_admission`. All three share the same
underlying per-client state store and hysteresis implementation (private helper functions);
only the wrapped auth dependency and the rejection exception type differ.

**Decision 4 — Concrete token-bucket signal parameters (module-level constants, not new
`RuntimeProfile` fields).** No existing token-bucket or sliding-window rate-limiting
implementation exists anywhere in `src/` to reuse (confirmed by investigation's own grep).
This plan picks: **capacity = 30 tokens** (burst allowance), **refill rate = 3.0 tokens/second**
(sustained throughput), consumed 1 token per admitted admission-check call. `fill_ratio =
1.0 - (tokens_remaining / capacity)` after consumption — 0.0 when the bucket is full (client
has been quiet), approaching/exceeding 1.0 when the client is sustained above the refill rate,
directly analogous to `ObservabilityController.evaluate()`'s `queue_fill_ratio` input (0.0 =
empty/no pressure, 1.0 = at/over capacity). These are conservative defaults suited to this
codebase's admin/telemetry-and-control REST+WebSocket surface (not a high-QPS public data API);
they are hardcoded module constants (`_BUCKET_CAPACITY`, `_BUCKET_REFILL_PER_SECOND`) rather than
new `RuntimeProfile` fields, since (a) investigation explicitly offered "hardcode a documented
constant" as a valid alternative to new profile fields, and (b) no test in test_plan.md requires
operator-tunability of the rate itself (only of the reused `RuntimeProfile.recovery_watermark`/
`dwell_time_ticks`/`confidence_window_ticks` hysteresis knobs, which this plan does reuse
as-is per Scope). A future ticket can promote these to profile fields if real traffic data
warrants it — not this ticket's scope to anticipate.

**Decision 5 — Only `SURVIVAL` mode rejects a request; `NORMAL`/`PRESSURE`/`DEGRADED` all admit.**
`ObservabilityController`'s own real per-mode behavior (`src/observability/event_recorder.py:
151-224`, confirmed by direct read) is: `PRESSURE` samples but still passes some events,
`DEGRADED` drops low-severity events but still passes WARNING+, and only `SURVIVAL` is a hard
stop (counter-only, nothing recorded). This plan mirrors that shape at the HTTP layer: `PRESSURE`/
`DEGRADED` are visible in `admission_status()` (so an operator/dashboard can see a client
trending toward being shed) but every request is still admitted through those two modes; only
`SURVIVAL` returns `429`. This is deliberate, not an oversight — it satisfies every named test in
test_plan.md (none requires a `PRESSURE`/`DEGRADED`-level rejection test) and avoids the Out-of-
Scope-adjacent risk of inventing a graduated multi-tier throttling scheme beyond what the ticket's
own Scope asks for ("a minimal token-bucket or sliding-window counter sufficient to produce a
0.0–1.0+ ratio is the entire scope of the signal layer").

**Decision 6 — `429 Too Many Requests` with a static `Retry-After: 5` header, for HTTP; `1013`
(`WebSocketException`) for the 3 websocket routes.** `429` is the standard HTTP status for
client-rate-limited requests (RFC 6585); `Retry-After` is its standard companion header. Because
`dwell_time_ticks`/`confidence_window_ticks` are redefined as per-client admission-evaluation
*counts*, not wall-clock time (Decision 7), there is no exact wall-clock recovery estimate to
compute — a fixed `Retry-After: 5` (seconds) is a documented, conservative operator hint, not a
computed guarantee. `1013` ("Try Again Later") is the IANA-registered WebSocket close code
matching `429`'s semantics, used by `require_admission_ws` in place of `require_api_key_ws`'s
`1008` (invalid credentials) — a different code so a client can distinguish "your key is wrong"
from "you are being rate-limited."

**Decision 7 — "Tick" redefinition: one `dwell_time_ticks`/`confidence_window_ticks` unit =
one admission-evaluation call for that specific client.** Per investigation's own recommendation
(the most direct literal analog to `ResourceGovernor`'s tick-per-`evaluate()`-call semantics,
requiring no new profile fields and no wall-clock dependency). `RuntimeProfile.dwell_time_ticks`
(default `10`) and `.confidence_window_ticks` (default `5`) are reused as-is (`src/config/
profiles.py:42-44`) — a client must have `dwell_time_ticks` admission-check calls elapse, and its
last `confidence_window_ticks` fill-ratio readings must all be below the recovery-watermark-scaled
threshold, before it steps down one mode level. A client that sends one request per hour "dwells"
for that many requests, which could span hours of wall-clock time — deliberate, not a bug: a
client that rarely calls in poses no sustained pressure to recover from.

**Decision 8 — Recovery-watermark scaling reuses `ObservabilityController`'s own threshold
constants directly.** `ObservabilityController.PRESSURE_THRESHOLD = 0.70`, `.DEGRADED_THRESHOLD =
0.90`, `.SURVIVAL_THRESHOLD = 1.00` (`src/observability/event_recorder.py:39-41`, confirmed by
direct read). Mirroring `ResourceGovernor._can_recover()`'s pattern of scaling each tier's own
escalation threshold by `recovery_watermark` to get its recovery limit (`governor.py:131-134`):
recovery from `SURVIVAL` to `DEGRADED` requires the last `confidence_window_ticks` fill ratios all
below `SURVIVAL_THRESHOLD * recovery_watermark` (`1.00 * 0.8 = 0.80` at the default watermark);
`DEGRADED`→`PRESSURE` requires all below `DEGRADED_THRESHOLD * recovery_watermark` (`0.72`);
`PRESSURE`→`NORMAL` requires all below `PRESSURE_THRESHOLD * recovery_watermark` (`0.56`). This
reuses the imported class's own constants rather than duplicating threshold literals, so a
future change to `ObservabilityController`'s thresholds (out of this ticket's scope, but a real
possibility) automatically propagates without a second edit site.

**Decision 9 — `ObservabilityMode` is `(str, Enum)`, not `IntEnum` — an explicit rank map is
required for magnitude comparisons.** Unlike `RuntimeMode(IntEnum)` (`src/core/governance.py`,
which supports `>`/`<` directly and raises nothing unexpected), `ObservabilityMode` instances
must never be magnitude-compared with a bare Python `>`/`<` operator. **Verified by direct
execution (Architecture-Verify, independently reproduced by the orchestrator): a bare comparison
does NOT raise `TypeError`** — `(str, Enum)` members inherit `str`'s own `__lt__`/`__gt__` from
the MRO, so `ObservabilityMode.DEGRADED > ObservabilityMode.NORMAL` silently evaluates to `False`
(comparing the strings `"DEGRADED"` and `"NORMAL"` alphabetically, not by severity), while
`ObservabilityMode.PRESSURE > ObservabilityMode.DEGRADED` silently evaluates to `True` — both the
wrong answer by severity rank, with no exception to signal the mistake. This is the more
dangerous failure mode, not a safer one: a bare comparison would pass code review, pass a type
checker, and produce plausible-looking (but silently wrong) booleans in production. This plan
defines a private `_MODE_RANK: Dict[ObservabilityMode, int] = {NORMAL: 0, PRESSURE: 1, DEGRADED:
2, SURVIVAL: 3}` in the new module and uses `_MODE_RANK[a] > _MODE_RANK[b]` everywhere
`ResourceGovernor.evaluate()` would use a bare `>` on `RuntimeMode` — a real technical gotcha
this plan resolves explicitly rather than leaving for Implement to discover, or worse, never
discover at all.

**Decision 10 — Parity ledger: new entry `INFRA-378`.** `grep -n "^- id: INFRA-3" docs/
parity_ledger/infrastructure.yaml | tail -5` confirms `INFRA-377` (the sibling auth ticket's,
already landed) is the current last entry — `INFRA-378` is the next free ID, matching
investigation's own finding, reconfirmed by direct read at plan-write time. Implement must
re-check this immediately before appending (this file is shared-write across concurrent
sessions — see Step 6's "Other writers" note).

## Steps

### Step 1 — Create `src/api/admission_control.py`

**Files:** `src/api/admission_control.py` (new)

**Change:** New module. Public/private API, in full:

```python
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException
from starlette.exceptions import WebSocketException

from src.api.auth import (
    ClientIdentity, require_api_key, require_api_key_header_or_query, require_api_key_ws,
)
from src.config.profiles import RuntimeProfile
from src.observability.event_recorder import ObservabilityController, ObservabilityMode
# NOTE: import ObservabilityMode ONLY from src.observability.event_recorder. A second,
# unrelated class of the same name exists at src.observability.config:8 (deployment-verbosity
# modes: OFF/LIGHT/NORMAL/FULL/RESEARCH/DEBUG/CERTIFICATION/LONG_RUN) -- importing from there
# by mistake (e.g. IDE autocomplete) would silently break every mode comparison in this module.

_MODE_RANK: Dict[ObservabilityMode, int] = {
    ObservabilityMode.NORMAL: 0,
    ObservabilityMode.PRESSURE: 1,
    ObservabilityMode.DEGRADED: 2,
    ObservabilityMode.SURVIVAL: 3,
}
_MODE_BY_RANK: Dict[int, ObservabilityMode] = {v: k for k, v in _MODE_RANK.items()}

_BUCKET_CAPACITY: float = 30.0
_BUCKET_REFILL_PER_SECOND: float = 3.0
_IDLE_TTL_SECONDS: float = 1800.0
_MAX_CLIENT_ENTRIES: int = 1000
_RETRY_AFTER_SECONDS: int = 5
_WS_THROTTLE_CLOSE_CODE: int = 1013  # "Try Again Later"

_controller = ObservabilityController()

# Module-level singleton config, mirroring src/api/auth.py's _client_keys pattern.
# Sole writer: configure_admission_control(), called once per create_v2_app() invocation.
_recovery_watermark: float = 0.8
_dwell_time_ticks: int = 10
_confidence_window_ticks: int = 5


@dataclass
class _ClientAdmissionState:
    tokens: float = _BUCKET_CAPACITY
    last_refill_time: float = 0.0
    mode: ObservabilityMode = ObservabilityMode.NORMAL
    dwell_count: int = 0
    recent_fill_ratios: List[float] = field(default_factory=list)
    last_active_time: float = 0.0


# Sole writers: require_admission()/require_admission_header_or_query()/require_admission_ws()
# (this module) and reset_admission_mode() (test-only). Mirrors src/api/auth.py's _client_keys
# module-level singleton pattern.
_client_state: Dict[str, _ClientAdmissionState] = {}
_client_order: List[str] = []  # recency order, oldest first -- mirrors CacheStrategy's
                                 # _keys_order (src/domains/optimization/cache_strategy.py:15),
                                 # NOT collections.OrderedDict (no such precedent in this repo).
_lock = threading.RLock()


def configure_admission_control(profile: RuntimeProfile) -> None:
    """Load the reused ResourceGovernor-pattern hysteresis tunables from profile. Must be
    called once at create_v2_app() time, mirroring configure_api_keys()."""
    global _recovery_watermark, _dwell_time_ticks, _confidence_window_ticks
    _recovery_watermark = profile.recovery_watermark
    _dwell_time_ticks = profile.dwell_time_ticks
    _confidence_window_ticks = profile.confidence_window_ticks


def _touch_lru(client_id: str) -> None:
    """Move client_id to the end (most-recently-active) of _client_order."""
    if client_id in _client_order:
        _client_order.remove(client_id)
    _client_order.append(client_id)


def _prune_idle_clients(current_time: float) -> None:
    """Lazy idle-TTL prune-on-access -- mirrors AlertDeduplicator.prune() exactly
    (src/observability/alerts/deduplicator.py:37-48): compute expired keys, delete them.
    Must be called while holding _lock."""
    expired = [
        cid for cid, state in _client_state.items()
        if (current_time - state.last_active_time) >= _IDLE_TTL_SECONDS
    ]
    for cid in expired:
        del _client_state[cid]
        if cid in _client_order:
            _client_order.remove(cid)


def _evict_lru_if_over_capacity() -> None:
    """Secondary, defense-in-depth max-entries hard cap -- mirrors CacheStrategy.put()'s
    evict-oldest-on-overflow (src/domains/optimization/cache_strategy.py:25-34). Must be called
    while holding _lock, only when about to insert a NEW client_id."""
    while len(_client_state) >= _MAX_CLIENT_ENTRIES and _client_order:
        oldest = _client_order.pop(0)
        _client_state.pop(oldest, None)


def _get_or_create_state(client_id: str, current_time: float) -> _ClientAdmissionState:
    """Must be called while holding _lock, after _prune_idle_clients()."""
    state = _client_state.get(client_id)
    if state is None:
        _evict_lru_if_over_capacity()
        state = _ClientAdmissionState(
            tokens=_BUCKET_CAPACITY, last_refill_time=current_time, last_active_time=current_time,
        )
        _client_state[client_id] = state
    _touch_lru(client_id)
    return state


def _consume_token(state: _ClientAdmissionState, current_time: float) -> float:
    """Refill based on elapsed wall-clock time, consume 1 token (floor 0), return the
    resulting fill_ratio -- 0.0 = bucket full (no pressure), 1.0 = bucket empty (at capacity)."""
    elapsed = max(0.0, current_time - state.last_refill_time)
    state.tokens = min(_BUCKET_CAPACITY, state.tokens + elapsed * _BUCKET_REFILL_PER_SECOND)
    state.last_refill_time = current_time
    state.tokens = max(0.0, state.tokens - 1.0)
    return 1.0 - (state.tokens / _BUCKET_CAPACITY)


def _recovery_limit_for(mode: ObservabilityMode) -> float:
    """Recovery threshold for stepping DOWN out of `mode`: mode's own escalation threshold,
    scaled by recovery_watermark -- mirrors ResourceGovernor._can_recover()'s per-signal
    scaling (src/engine/governor.py:131-134), reusing ObservabilityController's own threshold
    constants directly rather than duplicating literals."""
    if mode is ObservabilityMode.SURVIVAL:
        return _controller.SURVIVAL_THRESHOLD * _recovery_watermark
    if mode is ObservabilityMode.DEGRADED:
        return _controller.DEGRADED_THRESHOLD * _recovery_watermark
    if mode is ObservabilityMode.PRESSURE:
        return _controller.PRESSURE_THRESHOLD * _recovery_watermark
    return 0.0  # NORMAL has no lower tier to recover from


def _can_recover(state: _ClientAdmissionState) -> bool:
    """Mirrors ResourceGovernor._can_recover() (governor.py:103-146): dwell time gate + all
    recent samples in the confidence window below the recovery-scaled threshold."""
    if state.dwell_count < _dwell_time_ticks:
        return False
    if len(state.recent_fill_ratios) < _confidence_window_ticks:
        return False
    limit = _recovery_limit_for(state.mode)
    return all(r <= limit for r in state.recent_fill_ratios[-_confidence_window_ticks:])


def _evaluate(state: _ClientAdmissionState, fill_ratio: float) -> ObservabilityMode:
    """Mirrors ResourceGovernor.evaluate()'s escalation/recovery structure (governor.py:27-63),
    adapted to a single fill_ratio signal (this ticket has no PressureSignals-equivalent
    multi-field input). Mutates state in place; returns the (possibly unchanged) committed mode."""
    indicated = _controller.evaluate(fill_ratio)
    state.recent_fill_ratios.append(fill_ratio)
    if len(state.recent_fill_ratios) > _confidence_window_ticks:
        state.recent_fill_ratios.pop(0)

    indicated_rank = _MODE_RANK[indicated]
    current_rank = _MODE_RANK[state.mode]

    if indicated_rank > current_rank:
        # Escalation Rule: Immediate (governor.py:43-45)
        state.mode = indicated
        state.dwell_count = 0
    elif indicated_rank < current_rank:
        # Recovery Rule: Gated by Dwell Time + Confidence Window (governor.py:46-53)
        if _can_recover(state):
            state.mode = _MODE_BY_RANK[current_rank - 1]  # one level at a time
            state.dwell_count = 0
        else:
            state.dwell_count += 1
    else:
        state.dwell_count += 1

    return state.mode


def _check_admission(client_id: str, current_time: Optional[float] = None) -> ObservabilityMode:
    """Core admission check, shared by all three Depends()-callables below. Returns the
    client's committed mode after evaluation. Raising on SURVIVAL is the caller's job (the
    exception type differs between HTTP and WebSocket callers)."""
    if current_time is None:
        current_time = time.time()
    with _lock:
        _prune_idle_clients(current_time)
        state = _get_or_create_state(client_id, current_time)
        state.last_active_time = current_time
        fill_ratio = _consume_token(state, current_time)
        return _evaluate(state, fill_ratio)


async def require_admission(identity: ClientIdentity = Depends(require_api_key)) -> ClientIdentity:
    """Admission-control dependency for ordinary REST routes. Chains require_api_key so auth
    always resolves first, as an explicit data dependency (never relying on dependencies=[...]
    list order)."""
    mode = _check_admission(identity.client_id)
    if mode is ObservabilityMode.SURVIVAL:
        raise HTTPException(
            status_code=429, detail="Client admission limit exceeded.",
            headers={"Retry-After": str(_RETRY_AFTER_SECONDS)},
        )
    return identity


async def require_admission_header_or_query(
    identity: ClientIdentity = Depends(require_api_key_header_or_query),
) -> ClientIdentity:
    """Admission-control dependency for the 3 dashboard routes -- identical admission logic to
    require_admission; only the chained auth dependency differs (Decision 3)."""
    mode = _check_admission(identity.client_id)
    if mode is ObservabilityMode.SURVIVAL:
        raise HTTPException(
            status_code=429, detail="Client admission limit exceeded.",
            headers={"Retry-After": str(_RETRY_AFTER_SECONDS)},
        )
    return identity


async def require_admission_ws(identity: ClientIdentity = Depends(require_api_key_ws)) -> ClientIdentity:
    """Admission-control dependency for stream.router's 3 websocket routes. MUST raise
    WebSocketException, never HTTPException -- same source-verified reason as
    require_api_key_ws (see docs/architecture/http_api_key_authentication.md, Decision 4)."""
    mode = _check_admission(identity.client_id)
    if mode is ObservabilityMode.SURVIVAL:
        raise WebSocketException(code=_WS_THROTTLE_CLOSE_CODE, reason="Client admission limit exceeded.")
    return identity


def admission_status(client_id: str) -> Dict[str, Any]:
    """Template: observability_status() (event_recorder.py:263-272), scoped per-client. Returns
    a default/NORMAL shape without creating an entry if client_id is unknown -- a status query
    must never itself count as admission activity."""
    with _lock:
        state = _client_state.get(client_id)
        if state is None:
            return {
                "client_id": client_id, "mode": ObservabilityMode.NORMAL.value,
                "fill_ratio": 0.0, "tokens_remaining": _BUCKET_CAPACITY, "dwell_count": 0,
            }
        return {
            "client_id": client_id, "mode": state.mode.value,
            "fill_ratio": state.recent_fill_ratios[-1] if state.recent_fill_ratios else 0.0,
            "tokens_remaining": state.tokens, "dwell_count": state.dwell_count,
        }


def reset_admission_mode(client_id: Optional[str] = None) -> None:
    """Template: reset_mode() (event_recorder.py:274-279). Test-only. client_id=None clears
    every client's state (full reset, for test-file isolation); a given client_id clears only
    that entry."""
    with _lock:
        if client_id is None:
            _client_state.clear()
            _client_order.clear()
        else:
            _client_state.pop(client_id, None)
            if client_id in _client_order:
                _client_order.remove(client_id)
```

**Other writers to shared resources this step touches:** `_client_state`/`_client_order`/`_lock`
are brand-new module-level state, this ticket's sole author — no other code path writes to them.
`ObservabilityController`/`ObservabilityMode` (imported from `src.observability.event_recorder`)
are read-only here: `_controller = ObservabilityController()` constructs a **separate instance**
from the singleton one `EventRecorder` owns internally (`event_recorder.py:80`) — `evaluate()` is
stateless/pure (confirmed by direct read, `event_recorder.py:43-54`, no instance attributes
mutated), so two independent instances calling `evaluate()` concurrently never interact; this
module never touches `EventRecorder`'s own `_obs_mode`/`_obs_controller` attributes, so
`test_obs_backpressure.py` (which tests `EventRecorder`/`ObservabilityController` directly) is
unaffected by construction, not merely by promise.

**Do NOT touch:** `src/observability/event_recorder.py` (read/import only — zero edits, per Out
of Scope), `src/engine/governor.py` (pattern-mirrored, never imported — this module has no
`from src.engine import` statement at all, enforced by Step 3's static architecture-guard test),
`src/observability/config.py` (the second, unrelated `ObservabilityMode` — never imported here),
`src/observability/alerts/deduplicator.py` / `src/domains/optimization/cache_strategy.py`
(pattern-mirrored only, neither imported nor modified).

**Verify:** `test_admission_control_mode_vocabulary_matches_observability`,
`test_first_request_from_new_client_is_admitted`, `test_escalation_is_immediate_on_pressure_signal`,
`test_recovery_is_gated_by_dwell_and_confidence`, `test_idle_client_entry_is_evicted_after_ttl`,
`test_max_entries_cap_evicts_least_recently_active`, `test_eviction_does_not_lose_active_clients`,
`test_admission_status_accessor_shape`, `test_reset_admission_mode_clears_state` (all new, Step 3).

### Step 2 — Wire into `server.py`

**Files:** `src/api/server.py`

**Change:**

1. Add import near the existing `src.api.auth` import (`server.py:11-13`):
   ```python
   from src.api.admission_control import (
       configure_admission_control, require_admission,
       require_admission_header_or_query, require_admission_ws,
   )
   ```
2. As the second statement inside `create_v2_app(profile)`, immediately after
   `configure_api_keys(profile)` (`server.py:26`):
   ```python
   configure_admission_control(profile)
   ```
3. Replace `dependencies=[Depends(require_api_key_ws)]` with
   `dependencies=[Depends(require_admission_ws)]` at the 1 site: `stream.router`
   (`server.py:90`).
4. Replace `dependencies=[Depends(require_api_key)]` with
   `dependencies=[Depends(require_admission)]` at all 23 sites: the 9 `include_router()` calls
   (`server.py:93,96,99,102,105,108,111,114,117` — `history`, `search`, `behavior`, `decisions`,
   `scenarios`, `campaigns`, `chronicle`, `economy`, `quality_routes`) and the 14 inline route
   decorators (`server.py:122` `/metrics`, `:138,148,158` `live/status`, `live/snapshot`,
   `live/entities/{entity_id}`, `:172` `/api/v1/state`, `:179` `/api/v1/inspect`, `:187,196`
   `/api/v1/entities`, `/api/v1/entities/{entity_id}`, `:207,212` `/api/v1/control/pause`,
   `/api/v1/control/resume`, `:217` `/api/v1/test/publish_event`, `:239,250`
   `live/health`, `live/stream-health`, `:256` `observability/history/runs/{run_id}/report`).
5. Replace `dependencies=[Depends(require_api_key_header_or_query)]` with
   `dependencies=[Depends(require_admission_header_or_query)]` at all 3 dashboard-route sites:
   `server.py:280` (`/api/v1/observability/ui`), `:2375` (`/observability/ui`), `:2379`
   (`/api/v1/observability/live/ui`).
6. Leave `/health` (`server.py:132`) completely unchanged — no `dependencies=` kwarg. This is
   the exemption's entire mechanism, matching the auth ticket's own precedent.

Example diff shape (one representative site):
```python
# Before:
app.include_router(history.router, prefix="/api/v1", dependencies=[Depends(require_api_key)])
# After:
app.include_router(history.router, prefix="/api/v1", dependencies=[Depends(require_admission)])
```

**Other writers to `server.py`'s route table:** none — confirmed by the sibling auth ticket's
plan.md (Step 4's own "Other writers" note, reconfirmed here): `server.py` is the sole place
routers/routes are wired in this repo. This step's edits swap one `Depends(...)` callable for
another at 27 already-existing kwarg sites — no route is added, removed, or reordered, and the
~2090-line inline HTML/JS dashboard string (`server.py:282-2369`) is never touched.

**Do NOT touch:** the inline HTML/JS dashboard content; any of `src/api/routes/*.py`,
`src/api/ws/stream.py`, or `src/simulation_quality/api/routes.py`'s own `APIRouter(...)`
constructor calls (the dependency swap happens only at `server.py`'s call sites, exactly as the
auth ticket's own wiring did); `src/api/routes/control.py`, `health.py`, `state.py` (confirmed
still-empty, unwired dead files, unrelated to this ticket).

**Verify:** `test_admission_control_covers_every_authenticated_route`,
`test_admission_dependency_requires_resolved_client_identity`,
`test_per_client_state_is_isolated`, `test_survival_mode_sheds_or_rejects_requests` (all new,
Step 3); plus re-running `tests/api/test_api_key_auth.py` (all 14 tests, especially
`test_only_dashboard_and_websocket_routes_use_weaker_auth_channel`), `tests/api/
test_cors_config.py`, `tests/api/test_health_liveness.py`, `tests/api/
test_scenario_runtime_api.py`, and `tests/observability/test_metrics_export.py` unmodified —
all must stay green.

### Step 3 — New `tests/api/test_admission_control.py`

**Files:** `tests/api/test_admission_control.py` (new)

**Change:** Implement every test named in test_plan.md's "New Tests Required" section, following
`tests/api/test_api_key_auth.py`'s established conventions (real `TestClient`, real response
status/headers, `hashlib.sha256`-derived test keys, `dependant.dependencies` introspection for
architecture guards) — defining a local `_make_profile(**overrides)` helper (do not import
`test_api_key_auth.py`'s copy; each test file in this repo defines its own, per existing
convention across `test_cors_config.py`/`test_health_liveness.py`/`test_api_key_auth.py`), with
`recovery_watermark`/`dwell_time_ticks`/`confidence_window_ticks` overridable to small values
(e.g. `dwell_time_ticks=2`, `confidence_window_ticks=2`) so hysteresis tests don't need hundreds
of requests.

- `test_admission_control_mode_vocabulary_matches_observability`: `from src.api.admission_control
  import ObservabilityMode` (re-exported via the module's own import) and assert `{m.value for m
  in ObservabilityMode} == {"NORMAL", "PRESSURE", "DEGRADED", "SURVIVAL"}`; additionally assert
  `src.api.admission_control.ObservabilityMode is
  src.observability.event_recorder.ObservabilityMode` (identity check — guards against a future
  edit accidentally importing the wrong same-named class from `src.observability.config`).
- `test_first_request_from_new_client_is_admitted`: fresh `TestClient`, one GET to
  `/api/v1/state` with a valid key, assert `200`.
- `test_escalation_is_immediate_on_pressure_signal`: unit-level — import
  `src.api.admission_control` directly, construct a `_ClientAdmissionState()`, call `_evaluate`
  (or drive it via repeated `_check_admission` calls with an injected `current_time` that does
  not advance, so the token bucket empties without needing real wall-clock sleep) until
  `fill_ratio` crosses `PRESSURE_THRESHOLD`; assert mode is `PRESSURE` on the very next
  evaluation, no dwell delay.
- `test_recovery_is_gated_by_dwell_and_confidence`: unit-level — drive a state to `SURVIVAL` via
  `_evaluate`, then feed low `fill_ratio` values; assert mode stays `SURVIVAL` until both
  `dwell_time_ticks` calls have elapsed AND the last `confidence_window_ticks` fill ratios are
  all below `_recovery_limit_for(SURVIVAL)`; assert the step-down is exactly one level
  (`SURVIVAL` → `DEGRADED`, never directly to `NORMAL`) even if `fill_ratio` drops to `0.0`.
- `test_per_client_state_is_isolated`: integration — two distinct valid `X-API-Key` values
  (distinct `client_id`s) via `_make_profile(api_key_hashes="clientA:<hashA>,clientB:<hashB>")`;
  drive client A's admission state to `SURVIVAL` via repeated rapid requests (or by directly
  seeding `admission_control._client_state["clientA"]` before making one more request, whichever
  is more deterministic); assert client B's next request is still `200`.
- `test_survival_mode_sheds_or_rejects_requests`: integration — drive a client to `SURVIVAL`
  (same technique), assert the next request returns `429` with a `Retry-After` header present.
- `test_idle_client_entry_is_evicted_after_ttl`: unit — call `admission_control._check_admission
  ("c1", current_time=1000.0)` to seed an entry, then call `admission_control._prune_idle_clients
  (1000.0 + admission_control._IDLE_TTL_SECONDS + 1)` directly (mirrors
  `AlertDeduplicator.prune(current_time)`'s injectable-clock testable signature); assert
  `"c1" not in admission_control._client_state`.
- `test_max_entries_cap_evicts_least_recently_active`: unit — set
  `admission_control._MAX_CLIENT_ENTRIES` to a small test value via `monkeypatch`, seed that many
  distinct client_ids via `_check_admission(f"c{i}", current_time=float(i))`, then seed one more;
  assert the earliest-seeded (least-recently-active) client_id is evicted, not an arbitrary one.
- `test_eviction_does_not_lose_active_clients`: unit — interleave calls for one "active" client
  (touched every iteration) with many distinct "idle" client_ids churning past the max-entries
  cap; assert the active client's entry is never evicted.
- `test_admission_status_accessor_shape`: unit — seed one client via `_check_admission`, call
  `admission_status(client_id)`, assert the returned dict has exactly the keys `client_id`,
  `mode`, `fill_ratio`, `tokens_remaining`, `dwell_count`.
- `test_reset_admission_mode_clears_state`: unit — seed a client, call
  `reset_admission_mode(client_id)`, assert `admission_status(client_id)["mode"] == "NORMAL"` and
  the entry no longer appears in `admission_control._client_state`; also test the `None` (clear
  all) form.
- `test_admission_dependency_requires_resolved_client_identity`: architecture guard —
  `app.routes[i].dependant.dependencies` introspection (mirrors
  `test_only_dashboard_and_websocket_routes_use_weaker_auth_channel`'s technique): for every
  route whose `dependant.dependencies` contains `require_admission`/
  `require_admission_header_or_query`/`require_admission_ws` by `__name__`, assert that
  dependency's own `dependant.dependencies` (the nested sub-dependant) contains the matching
  `require_api_key*` by name — confirming the parameter-chain composition (Decision 2/3), not a
  standalone reimplementation of identity resolution.
- `test_admission_control_covers_every_authenticated_route`: architecture guard — same
  introspection technique; assert every route carrying any `require_api_key*` dependency name in
  its full dependant graph ALSO carries the matching `require_admission*` name, and `/health` is
  the sole route carrying neither.
- `test_admission_control_does_not_reach_into_governor_internals`: static guard — `ast`-parse
  `src/api/admission_control.py` and assert no `ImportFrom` node has a `module` starting with
  `src.engine.governor` or `src.engine.phase_governor` (mirrors the style of other static
  architecture-guard tests found in `tests/static/`, e.g. `test_ci_narrow_path_filtered_jobs.py`).

**Other writers to this file:** none — new file, this ticket's sole author.

**Do NOT touch:** `tests/api/test_api_key_auth.py`, `tests/api/test_cors_config.py`, `tests/api/
test_health_liveness.py`, `tests/api/test_scenario_runtime_api.py`,
`tests/observability/test_metrics_export.py`, `tests/unit/observability/
test_obs_backpressure.py` — all are re-run for regression confirmation only, never edited by
this ticket.

**Verify:** `pytest tests/api/test_admission_control.py -v` fully green; then the full scoped
command from test_plan.md: `pytest tests/api/ tests/unit/observability/test_obs_backpressure.py
tests/observability/test_metrics_export.py -m "not slow" -v` fully green.

### Step 4 — New doc: `docs/architecture/http_admission_control.md`

**Files:** `docs/architecture/http_admission_control.md` (new)

**Change:** New ADR-shaped doc, mirroring `docs/architecture/http_api_key_authentication.md`'s
and `observability_hot_path_safety_contract.md`'s grain. Required sections: (1) **Mechanism** —
`Depends()`-parameter-chaining onto the existing auth dependencies (Decision 2/3), token-bucket
signal (Decision 4), per-mode behavior (Decision 5), rejection status codes (Decision 6). (2)
**Mode vocabulary and import path** — explicit statement that the vocabulary is
`ObservabilityMode` imported from `src.observability.event_recorder`, reused not modified, and
an explicit warning about the same-named, unrelated class at `src.observability.config:8`. (3)
**Hysteresis** — the "tick" redefinition (Decision 7) and the recovery-watermark scaling
(Decision 8), citing `ResourceGovernor.evaluate()`/`_can_recover()` (`src/engine/governor.py`)
as the mirrored pattern, explicitly correcting the doc-drift hazard that `PhaseBudgetGovernor`
has no hysteresis of its own (do not propagate that mis-attribution here). (4) **Per-client state
bounding** — the two-layer eviction design (idle-TTL prune-on-access + max-entries LRU),
citing `AlertDeduplicator`/`CacheStrategy` as the mirrored precedents and the concrete constants
from Decision 4/this doc. (5) **Relationship to `TCK-20260823-HTTP-API-KEY-AUTH`** — this
mechanism composes with, and depends on, that ticket's `ClientIdentity`/`require_api_key*`
dependencies; cross-reference `docs/architecture/http_api_key_authentication.md` rather than
restating its content.

**Other writers to `docs/architecture/`:** none relevant — new file; no existing doc in that
directory covers HTTP admission control (confirmed by investigation's grep).

**Do NOT touch:** any existing file under `docs/architecture/` in this step — Steps 5 and 7
below are the only existing-file doc edits.

**Verify:** no automated test targets this file's content directly; `tests/docs/
test_doc_integrity.py` (unmodified) confirms frontmatter/registry conformance.

### Step 5 — Update `docs/architecture/observability_hot_path_safety_contract.md` §5

**Files:** `docs/architecture/observability_hot_path_safety_contract.md`

**Change:** §5 ("Dynamic Observability Mode (OBS-BACKPRESSURE, INFRA-199)",
`observability_hot_path_safety_contract.md:67-86`, confirmed by direct read at
Architecture-Verify — corrected from plan-write time's `:67-83`) documents
`ObservabilityMode`/`ObservabilityController` as observability-subsystem-only ("`EventRecorder`
supports four dynamic modes..."). Add one paragraph after the existing "**Accessors**:" line
(`:84`, corrected from `:83`) noting the HTTP layer (`src/api/admission_control.py`) is now also a consumer of this
vocabulary and of `ObservabilityController`'s pure `evaluate()` function — via a **separate
instance**, never `EventRecorder`'s own singleton — so this contract's hot-path rules (§1-§4)
continue to apply only to the engine's own `EventRecorder` usage and do not newly constrain the
HTTP layer's own (non-hot-path) usage. Cross-reference `docs/architecture/
http_admission_control.md` (Step 4) for the full design.

**Other writers to this file:** none currently touching §5 — confirmed by direct read at
plan-write time; this doc is otherwise stable, edited only by tickets that change §5's subject
matter (the last such edit was the original `INFRA-199` ticket, pre-dating this session).

**Do NOT touch:** §1-§4, §6 ("Worker Lifecycle Contract"), or any other section — only the one
new paragraph in §5.

**Verify:** `tests/docs/test_doc_integrity.py` (unmodified) stays green; no other automated test
targets this file's prose.

### Step 6 — New parity ledger entry `INFRA-378`

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Immediately before appending, re-run `grep -n "^- id: INFRA-37" docs/parity_ledger/
infrastructure.yaml | tail` to reconfirm `INFRA-377` is still the last entry (this repo's working
directory can be shared by concurrent sessions per CLAUDE.md's Hard Rules — another session may
append an entry between plan-write time and implementation time; if `INFRA-378` is already taken,
use the next free ID and update this step's own text accordingly, do not silently overwrite).
Append, following the existing 8-field shape:

```yaml
- id: INFRA-378
  text: Per-client HTTP admission control (src/api/admission_control.py) extends
    ObservabilityMode's NORMAL/PRESSURE/DEGRADED/SURVIVAL vocabulary (imported from
    src.observability.event_recorder, never modified) to the HTTP layer, keyed by the
    ClientIdentity INFRA-377's auth mechanism resolves. A per-client in-memory token
    bucket (30-token capacity, 3 tokens/second refill) produces a 0.0-1.0+ fill_ratio
    signal, fed into a hysteresis state machine mirroring ResourceGovernor's real
    escalation/recovery pattern (src/engine/governor.py evaluate()/_can_recover(),
    NOT PhaseBudgetGovernor, which has no hysteresis of its own): escalation is
    immediate, recovery requires RuntimeProfile.dwell_time_ticks admission-evaluation
    calls plus confidence_window_ticks consecutive low-pressure readings, stepping
    down one mode level at a time. Only SURVIVAL rejects a request (HTTP 429 with a
    Retry-After header; WebSocket close code 1013 on stream.router's 3 routes) --
    NORMAL/PRESSURE/DEGRADED all admit. Per-client state is bounded by a lazy
    idle-TTL prune-on-access (1800 seconds, mirroring AlertDeduplicator.prune())
    plus a 1000-entry max-entries LRU hard cap (mirroring CacheStrategy's dict-plus-
    list idiom). require_admission/require_admission_header_or_query/
    require_admission_ws compose with require_api_key/require_api_key_header_or_query/
    require_api_key_ws via a Depends() parameter chain, replacing (not appending to)
    the auth-only dependency at all 27 protected route sites in server.py; /health
    remains the sole exemption.
  status: verified
  priority: P1
  v2_evidence: src/api/admission_control.py, src/api/server.py
  test_path: tests/api/test_admission_control.py::test_first_request_from_new_client_is_admitted
  divergence_note: null
  proof_type: contract
```

`priority: P1`, matching `INFRA-199`'s and `INFRA-377`'s own P1 precedent — this is a live,
request-path behavioral contract gating a "public internet, multi-tenant" deployment, per the
ticket's own framing.

**Other writers to this file:** `docs/parity_ledger/infrastructure.yaml` is a single YAML list
appended to by every ticket that lands a new infrastructure-layer parity fact — the same
shared-resource caveat the sibling auth ticket's own Step 9 already documented for this exact
file. `INFRA-377` is the immediately preceding entry and is already merged (no concurrent-write
race against it at plan-write time; re-check per the instruction above before appending).

**Do NOT touch:** any existing entry in this file, including `INFRA-199` (`ObservabilityMode`'s
own entry — read/cited, never edited) and `INFRA-377` (the auth ticket's entry — cross-referenced
by ID in the new entry's text, never edited).

**Verify:** `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/
infrastructure.yaml'))"` parses without error; the cited `test_path` must exist and pass before
this entry can honestly claim `status: verified`.

### Step 7 — Update `docs/plans/http_admission_control_epic.md`

**Files:** `docs/plans/http_admission_control_epic.md`

**Change:** This file still attributes the hysteresis pattern to "`PhaseBudgetGovernor`'s
threshold-crossing-with-cooldown approach" (confirmed still present at line ~29 by investigation's
direct read). Correct this line to name `ResourceGovernor.evaluate()`/`_can_recover()`
(`src/engine/governor.py`) as the real mechanism, matching Decision 8/this plan's own Step 1.
This mirrors the sibling auth ticket's own precedent of editing this same epic doc's stale
content during its Document-Update phase (see that ticket's plan.md "Deviations" section — a
real, already-established precedent for this exact file, reconfirmed here as in-scope for this
ticket specifically since the mis-attribution is about the admission-control mechanism this
ticket delivers).

**Other writers to this file:** the sibling auth ticket already edited this file once (struck
through its "At least one auth mechanism gates the API surface" bullet, per that ticket's own
plan.md Deviations section) — confirmed via `git log --follow -- docs/plans/
http_admission_control_epic.md`. This step's edit targets a different line (the
`PhaseBudgetGovernor` mis-attribution) and does not conflict with or re-touch the auth ticket's
prior edit. After this step, add a corresponding strikethrough/resolved note on this epic doc's
own "HTTP requests are admitted/throttled/shed per-client" acceptance line, citing this ticket
and `INFRA-378`.

**Do NOT touch:** any other section of this file, including the auth ticket's own
already-resolved bullet.

**Verify:** `tests/docs/test_doc_integrity.py` (unmodified) stays green.

### Step 8 — Update `docs/engine/known_limitations.md`

**Files:** `docs/engine/known_limitations.md`

**Change:** `grep -n "admission" docs/engine/known_limitations.md` returns zero hits (confirmed
by investigation and reconfirmed here) — there is no existing "no admission control" line to
edit; this is a pure addition, not a strikethrough. Add one bullet under `## 2. Runtime /
Performance Constraints` (the section covering execution/contention/phase-isolation boundaries,
`known_limitations.md:80-` per direct read) noting: per-client HTTP admission control now exists
(`src/api/admission_control.py`, `INFRA-378`) — the previously-unbounded "no rate limiting on the
HTTP API surface" boundary this doc's own purpose is to track is resolved as of this ticket,
scoped to single-process in-memory state (no distributed/multi-worker-process rate-limit
coordination — a real, still-current limitation worth stating explicitly for an operator planning
a multi-worker-process deployment).

**Other writers to this file:** none confirmed touching the Runtime/Performance section
concurrently — this is a single new bullet addition, not a structural edit.

**Do NOT touch:** `## 1. Gameplay / Mechanics Limitations`, `## 3. Tooling / Observability`, or
any other existing bullet in `## 2` — only one new bullet is added.

**Verify:** `tests/docs/test_doc_integrity.py` (unmodified) stays green.

### Step 9 — Ticket close-out and epic finalization

**Files:** `tickets/inprogress/TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL.md` (moves to
`tickets/done/`), `tickets/todos/http-admission-control/TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC.md`

**Change:** Standard Finalize-phase ticket close-out for this ticket (fill Implementation
Notes/Test Summary/Files Changed/Completion Summary, move to `tickets/done/`, append
`tickets/working_log.csv`, move `staging_artifacts/TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL/`
to `stored_artifacts/`). Additionally, since this is the 2nd of 2 child tickets extracted from
`TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC` and the epic's own Completion Summary states it
"closes once both ... reach `tickets/done/`": check off the epic's remaining `[ ]` acceptance
criterion ("HTTP requests are admitted/throttled/shed per-client..."), add this ticket's ID and
`INFRA-378` to the epic's Related Stored Artifacts/Completion Summary, and move the entire
`tickets/todos/http-admission-control/` folder (preserving `SEQUENCE.md`) to
`tickets/done/http-admission-control/` — mirroring the CLAUDE.md workflow rule ("When all
tickets in the folder are done, move the entire folder... Never leave a completed folder's
skeleton in `tickets/todos/`") and the same pattern this session already applied to the
codebase-health-observatory-tooling batch's own epic closure.

**Other writers to the epic ticket file:** none since its 2026-08-23 split edit (confirmed by
direct read at plan-write time) — this step's edit is the epic's final close-out, not a
concurrent one.

**Do NOT touch:** `TCK-20260823-HTTP-API-KEY-AUTH` (already in `tickets/done/`, not reopened by
this ticket) or `tickets/todos/http-admission-control/SEQUENCE.md`'s content beyond what the
folder move itself requires (no content edit, just relocation).

**Verify:** `done-checker` agent's full Definition-of-Done pass for this ticket; manual
confirmation the epic folder no longer exists under `tickets/todos/`.

## Scope Guards

Must NOT be touched or introduced by this ticket, per the ticket's Out of Scope, investigation's
Anti-Drift Hazards, and this plan's own decisions:

- **No new distributed/shared rate-limit infrastructure** (Redis-backed or otherwise) — `redis`
  being an existing dependency is not license to use it here; `_client_state` (Step 1) is
  single-process, in-memory only.
- **Do not modify `src/observability/event_recorder.py`, `src/engine/governor.py`,
  `src/engine/phase_governor.py`, or `src/core/governance.py`** — read/reuse pattern and import
  only; zero edits to any of these four files. `test_obs_backpressure.py` stays untouched and
  green by construction.
- **Do not import from `src.observability.config`** anywhere in `src/api/admission_control.py`
  or its tests — the correct `ObservabilityMode` import is always `from
  src.observability.event_recorder import ObservabilityMode`.
- **Do not attach admission-control logic to FastAPI middleware** — `Depends()`-parameter-
  chaining only (Decision 2/3), for the same reason the auth ticket rejected middleware:
  middleware cannot see the already-resolved `ClientIdentity` without re-implementing key
  resolution, creating a second, divergence-prone copy of security-sensitive logic.
- **Do not let `require_admission`/`require_admission_header_or_query`/`require_admission_ws`
  run before their corresponding auth dependency** — enforced by the parameter-chain shape
  itself (Decision 2), not by `dependencies=[...]` list order.
- **Do not tie per-client eviction to `src/engine/cache_registry.py`'s `CacheRegistry`/
  `ICacheable`/tick-based sweep** — it is engine-tick-keyed and swept from inside the kernel's
  own tick loop; this ticket's eviction is wall-clock-driven and lazy, per Step 1.
- **Do not silently widen `_DASHBOARD_AND_WS_PATHS`** (`tests/api/test_api_key_auth.py:32-39`) —
  admission control layers onto the same 6 routes without changing which routes use which *auth*
  channel; `test_only_dashboard_and_websocket_routes_use_weaker_auth_channel` must stay green
  unmodified.
- **Do not build a general-purpose, multi-tier throttling scheme** — only `SURVIVAL` rejects
  (Decision 5); do not add `PRESSURE`/`DEGRADED`-level request shedding, priority queuing, or
  per-route rate differentiation beyond what this plan specifies.
- **Do not add new `RuntimeProfile` fields for the token-bucket capacity/refill rate, idle-TTL,
  or max-entries cap** — these are hardcoded module constants (Decision 4), reusing only the
  three already-existing `recovery_watermark`/`dwell_time_ticks`/`confidence_window_ticks`
  fields.
- **Do not touch `src/api/routes/control.py`, `health.py`, `state.py`** — confirmed still-empty,
  unwired dead files, unrelated to this ticket.
- **Do not reopen or edit `TCK-20260823-HTTP-API-KEY-AUTH`** (already in `tickets/done/`) or its
  stored artifacts — only cross-referenced by ID.

## Dependency Map

- Step 1 (`src/api/admission_control.py`) has no dependencies on other steps; it is first
  (everything else imports from it or documents it).
- Step 2 (`server.py` wiring) depends on Step 1 (imports its dependency functions and
  `configure_admission_control`).
- Step 3 (new test file) depends on Steps 1-2 being complete; it exercises the full stack.
- Step 4 (new architecture doc) depends on Steps 1-2's decisions being finalized (documents the
  shipped mechanism, not a proposal) — can be written in parallel with Step 3.
- Step 5 (`observability_hot_path_safety_contract.md` §5) depends on Step 1's decision to import
  `ObservabilityController` as a separate instance — independent of Steps 2-4.
- Step 6 (parity ledger) depends on Step 3 passing, since the new entry's `test_path` cites a
  specific test that must exist and pass before the entry can honestly claim `status: verified`.
- Step 7 (epic doc correction) is independent of Steps 1-6; can be done any time.
- Step 8 (`known_limitations.md`) is independent of Steps 1-7; can be done any time.
- Step 9 (close-out) depends on all prior steps being complete and Step 3's tests green.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| HTTP requests are admitted/throttled/shed per-client, keyed by the authenticated client identity from `TCK-20260823-HTTP-API-KEY-AUTH` | Step 1 (`_client_state` keyed by `identity.client_id`), Step 2 (wiring onto every protected route) | `test_first_request_from_new_client_is_admitted`, `test_per_client_state_is_isolated`, `test_survival_mode_sheds_or_rejects_requests` |
| The mode vocabulary is exactly `NORMAL/PRESSURE/DEGRADED/SURVIVAL` (matching `ObservabilityMode`), never `RuntimeMode`'s `CONSTRAINED` naming or a third invented vocabulary | Step 1 (imports `ObservabilityMode` directly from `src.observability.event_recorder`, never redefines it) | `test_admission_control_mode_vocabulary_matches_observability` |
| Escalation is immediate; recovery is gated by dwell-time + confidence-window, one mode level at a time — mirroring `ResourceGovernor`'s real hysteresis pattern | Step 1 (`_evaluate`/`_can_recover`/`_recovery_limit_for`, Decisions 7-9) | `test_escalation_is_immediate_on_pressure_signal`, `test_recovery_is_gated_by_dwell_and_confidence` |
| Per-client state has an explicit, tested eviction/TTL policy — no unbounded growth from an ever-increasing set of distinct client IDs | Step 1 (`_prune_idle_clients`, `_evict_lru_if_over_capacity`, Decision 4) | `test_idle_client_entry_is_evicted_after_ttl`, `test_max_entries_cap_evicts_least_recently_active`, `test_eviction_does_not_lose_active_clients` |
| `tests/unit/observability/test_obs_backpressure.py` stays green | Step 1 (zero edits to `event_recorder.py`, separate `ObservabilityController` instance) | Full `test_obs_backpressure.py` re-run, unmodified |
| `tests/api/` gains real, in-process `TestClient`-based tests covering per-client throttling across at least 2 distinct simulated clients | Step 3 (`tests/api/test_admission_control.py`) | `test_per_client_state_is_isolated` and the full new test file |

## Anti-Drift Notes

- **A third, unrelated `ObservabilityMode` class exists at `src/observability/config.py:8`**
  (`OFF/LIGHT/NORMAL/FULL/RESEARCH/DEBUG/CERTIFICATION/LONG_RUN` — deployment-verbosity modes,
  completely unrelated to backpressure/admission). The correct import for this ticket's vocabulary
  is always `from src.observability.event_recorder import ObservabilityMode`. Step 1's module
  docstring/comment states this explicitly, and `test_admission_control_mode_vocabulary_matches_
  observability`'s identity-check assertion (`... is src.observability.event_recorder.
  ObservabilityMode`) makes this a hard, automated guard, not just a code-review convention.
- **`ObservabilityMode` is `(str, Enum)`, not `IntEnum`** — do not attempt `mode_a > mode_b`
  directly; use `_MODE_RANK` (Decision 9). A future edit that "simplifies" this back to a bare
  comparison will NOT raise `TypeError` — it inherits `str`'s own ordering and silently compares
  the mode names alphabetically (`"DEGRADED" < "NORMAL" < "PRESSURE" < "SURVIVAL"`), producing
  wrong-but-plausible booleans with no exception to catch the mistake. This is the more dangerous
  of the two possible failure modes, which is exactly why `_MODE_RANK` is a hard requirement here,
  not a style preference.
- **`check_docs_to_update_coverage` parses investigation.md's "## Docs Requiring Update" section
  via a strict `- \`docs/...\`` bullet regex** (`tools/gate_checks/done_checker_static.py:308,
  385-405`, confirmed by direct read). Investigation.md's five bullets for
  `observability_hot_path_safety_contract.md`, `infrastructure.yaml`,
  `http_admission_control_epic.md`, `http_api_key_authentication.md` (already shipped, cited
  only), and `known_limitations.md` all match this format and ARE gate-enforced (Steps 5, 6, 7,
  8 must touch these exact paths or the coverage check fails). Investigation.md's sixth bullet
  ("A new `docs/architecture/` doc for the admission-control mechanism itself...") does **NOT**
  start with `- \`docs/` — it starts with "A new" — so it does **not** parse as a required path
  and the coverage checker will not fail if it's skipped. This plan still builds it (Step 4,
  `docs/architecture/http_admission_control.md`) because the Hard Rule ("new logic/features/
  settings" need a doc) requires it regardless of gate enforcement — do not treat the checker's
  silence on this one bullet as license to skip Step 4.
- **Do not attribute the hysteresis mechanism to `PhaseBudgetGovernor`** in any new code comment,
  docstring, or doc prose this ticket adds — `PhaseBudgetGovernor.evaluate()`
  (`src/engine/phase_governor.py`) is a pure consumer of an already-decided mode with no
  hysteresis of its own; `ResourceGovernor.evaluate()`/`_can_recover()` is the real mechanism.
  Step 7 exists specifically to correct this mis-attribution where it already exists in
  `docs/plans/http_admission_control_epic.md` — do not reintroduce it elsewhere.
- **Route count is 27, not 28.** The ticket text says "up to 28... confirm real current count";
  direct `grep -n "dependencies=\[Depends(" src/api/server.py` returns 27 matches (Decision 1).
  Do not add a 28th `dependencies=[...]` site to make the count match a number from the ticket's
  own uncertain phrasing — 27 is the confirmed, source-verified count as of plan-write time
  (re-verify at Implement time in case the sibling ticket's own file has drifted further, though
  no such drift is expected since that ticket is already in `tickets/done/`).

## Deviations (recorded during Implement)

- **Decision 2's "replace in place" strategy was amended to "append" at exactly 4 of the 27
  sites** — the 3 dashboard routes (`server.py`, now `/api/v1/observability/ui`,
  `/observability/ui`, `/api/v1/observability/live/ui`) and `stream.router`'s 1 site (backing its
  3 WebSocket routes). At these 4 sites, `dependencies=[...]` now reads
  `[Depends(require_api_key_header_or_query), Depends(require_admission_header_or_query)]`
  (or the `_ws` equivalent) — both the original auth dependency AND the new admission dependency
  listed, not the admission dependency alone. The other 23 plain `require_api_key` sites remain
  pure **replace**, exactly as Decision 2 specified.
  - **Why**: running the full `tests/api/` regression suite after Step 2 (pure replace at all 27
    sites, per the plan as written) surfaced that
    `tests/api/test_api_key_auth.py::test_only_dashboard_and_websocket_routes_use_weaker_auth_channel`
    — a test this ticket is explicitly forbidden to edit ("regression surface only, re-run not
    edited") and which Step 2's own Verify section requires to "stay green unmodified" — failed.
    That test inspects each route's **top-level** `dependant.dependencies` for
    `require_api_key_header_or_query`/`require_api_key_ws` by name. Decision 2's replace strategy
    moves those names one level deeper (into `require_admission_header_or_query`/
    `require_admission_ws`'s own nested parameter-chain sub-dependant), so they no longer appear
    at the top level the pinned test inspects — a real gap in the plan's own verification claim
    that neither round of architecture review caught, since it only manifests when the full
    existing regression suite (not just the new test file) is actually executed.
  - **Why append, not edit the pinned test**: CLAUDE.md's Hard Rules forbid editing an artifact
    (here, a test) to make a gate pass instead of fixing the underlying substance, and this
    ticket's own instructions list `test_api_key_auth.py` as re-run-only. Appending the original
    auth dependency back at just these 4 sites is a same-behavior fix, not a workaround: FastAPI
    caches a resolved dependency per request keyed by the callable itself (`dependant.cache_key`)
    — this is Decision 2's own cited mechanism — so `require_api_key_header_or_query`/
    `require_api_key_ws` are still computed exactly once per request whether referenced directly
    in the list, transitively through `require_admission_header_or_query`/`require_admission_ws`'s
    own parameter, or (as now) both. No new behavior, no double execution, no ordering change —
    only the mechanical shape of these 4 `dependencies=[...]` lists changed from length 1 back to
    length 2 (matching what plain "append" would have looked like everywhere, per Decision 2's
    own acknowledged-but-rejected alternative), scoped to only the 4 sites where it was actually
    required to keep the pinned regression test's real intent (weak auth channel usage stays
    scoped to exactly its 6 known routes) satisfied.
  - **Verification**: `tests/api/test_api_key_auth.py` (all 14 tests, including
    `test_only_dashboard_and_websocket_routes_use_weaker_auth_channel`) passes unmodified after
    this change. `tests/api/test_admission_control.py`'s own architecture-guard tests
    (`test_admission_dependency_requires_resolved_client_identity`,
    `test_admission_control_covers_every_authenticated_route`) also pass unaffected, since both
    inspect the full (not just top-level) dependant graph and tolerate the auth dependency
    appearing at both the top level and nested.
- **Document-Update phase (not Implement): 3 further upstream doc edits found and made, beyond
  the plan's own Step 7/Step 8 scope.** `tickets/todos/http-admission-control/TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC.md`
  (the epic's own tracking ticket, distinct from `docs/plans/http_admission_control_epic.md`
  which Step 7 already covered), `docs/plans/architecture_resilience_remediation_roadmap.md`
  (the master roadmap doc, a level above the epic doc), and
  `tickets/todos/codebase-health-resilience/TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC.md`
  (the grandparent tracking ticket) all independently mirror Epic F's own status/priority/tier and
  were still stale (pre-2026-08-23 "gated/deferred/trusted-network-only" framing) after the
  plan's own scoped doc edits landed — the same multi-level epic-tracking-chain staleness pattern
  already found and fixed twice this session on the sibling codebase-health-observatory-tooling
  batch's own tickets. All 3 were updated to reflect the real current state (gate fired
  2026-08-23, tier reverted standard→epic, both child tickets' real status), without claiming
  premature full closure since this ticket is still mid-pipeline. Caught by Architecture-Verify
  as a ticket-hygiene Files-Changed omission and fixed directly.
