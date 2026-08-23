from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Dict, Optional

from fastapi import Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from starlette.exceptions import WebSocketException

from src.config.profiles import RuntimeProfile

logger = logging.getLogger(__name__)

# Sole writer: configure_api_keys(), called once per create_v2_app() invocation
# (src/api/server.py). Mirrors src/api/dependencies.py's set_x/get_x singleton
# pattern (server.py:11-14) -- same last-call-wins semantics across multiple
# create_v2_app() calls in one process as the existing _engine_manager global.
_client_keys: Dict[str, str] = {}


class ClientIdentity(BaseModel):
    """Resolved identity of an authenticated API caller. Reusable by
    TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL to key its own per-client
    state. Keep this small and stable -- do not add auth-only fields here."""
    model_config = ConfigDict(frozen=True)
    client_id: str


def configure_api_keys(profile: RuntimeProfile) -> None:
    """Parse profile.api_key_hashes into the module-level key store. Must be
    called once at create_v2_app() time, before any request is served."""
    global _client_keys
    _client_keys = _parse_api_key_hashes(profile.api_key_hashes)


def _parse_api_key_hashes(raw: str) -> Dict[str, str]:
    """'client_id:sha256hex,client_id2:sha256hex2' -> {sha256hex: client_id}.
    Malformed entries are skipped with a logged warning (never the raw entry
    content), never raised -- one bad config entry must not crash startup."""
    result: Dict[str, str] = {}
    if not raw:
        return result
    for index, entry in enumerate(raw.split(",")):
        entry = entry.strip()
        if not entry:
            continue
        if ":" not in entry:
            logger.warning("Skipping malformed api_key_hashes entry at index %d (missing ':')", index)
            continue
        client_id, _, key_hash = entry.partition(":")
        client_id, key_hash = client_id.strip(), key_hash.strip()
        if not client_id or not key_hash:
            logger.warning("Skipping malformed api_key_hashes entry at index %d (empty half)", index)
            continue
        result[key_hash] = client_id
    return result


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _resolve_client_id(raw_key: str) -> Optional[str]:
    """Constant-time lookup across configured key hashes. Never raises --
    an empty/malformed raw_key simply fails to match and returns None. Uses
    hmac.compare_digest per entry (not a dict __contains__ shortcut), so no
    entry is ever ruled out by a plain hash-equality/dict-membership check.
    Exits on the first match rather than scanning every remaining entry --
    security-reviewer-confirmed non-issue for this threat model (the raw key
    is SHA-256-hashed before any comparison, so an attacker cannot influence
    which bytes are compared; the 200-vs-401 response itself is already a far
    stronger signal than any residual iteration-count timing variance)."""
    if not raw_key:
        return None
    candidate_hash = _hash_key(raw_key)
    for stored_hash, client_id in _client_keys.items():
        if hmac.compare_digest(candidate_hash, stored_hash):
            return client_id
    return None


async def require_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> ClientIdentity:
    """Strict header-only auth dependency for ordinary REST routes."""
    client_id = _resolve_client_id(x_api_key or "")
    if client_id is None:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
    return ClientIdentity(client_id=client_id)


async def require_api_key_header_or_query(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    key: Optional[str] = Query(default=None),
) -> ClientIdentity:
    """Header-or-query-param auth, scoped ONLY to the 3 browser-facing dashboard
    routes (see docs/architecture/http_api_key_authentication.md, Decision 3) --
    a plain browser navigation cannot attach a custom header. Keys can appear in
    URLs/access logs/browser history via this channel; do not reuse this
    dependency on any non-dashboard route."""
    raw = x_api_key or key or ""
    client_id = _resolve_client_id(raw)
    if client_id is None:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
    return ClientIdentity(client_id=client_id)


async def require_api_key_ws(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    key: Optional[str] = Query(default=None),
) -> ClientIdentity:
    """WebSocket-scoped auth for stream.router's 3 websocket routes. MUST raise
    WebSocketException, never HTTPException -- see plan.md Decision 4 for the
    source-verified reason (fastapi/routing.py's get_websocket_app() resolves
    dependencies before websocket.accept(); starlette's ExceptionMiddleware only
    safely closes a websocket connection for WebSocketException, not
    HTTPException). Same header-or-query channel as the dashboard dependency,
    since a browser's native WebSocket() constructor also cannot set headers."""
    raw = x_api_key or key or ""
    client_id = _resolve_client_id(raw)
    if client_id is None:
        raise WebSocketException(code=1008, reason="Invalid or missing API key.")
    return ClientIdentity(client_id=client_id)
