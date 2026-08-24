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
