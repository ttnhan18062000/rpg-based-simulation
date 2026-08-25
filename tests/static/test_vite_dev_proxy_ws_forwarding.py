"""Static, source-text-only guard over frontend/vite.config.ts for
TCK-20260825-LIVE-MAP-DEV-AUTH-AND-WS-PROXY-FIX.

Live-reproduced during that ticket: without `ws: true` on the `/api` proxy entry,
Vite's dev-server proxy (http-proxy under the hood) never forwards a WebSocket
upgrade request at all -- a client connecting to ws://127.0.0.1:5173/api/v1/ws
(the exact URL frontend/src/hooks/useSimulation.ts constructs) times out during
the opening handshake, even with a healthy, unauthenticated backend. This guard
prevents that regression from silently reappearing on a future edit to the
proxy block.
"""
from __future__ import annotations

import re
from pathlib import Path

_VITE_CONFIG = Path("frontend/vite.config.ts")


def _api_proxy_block() -> str:
    text = _VITE_CONFIG.read_text(encoding="utf-8")
    match = re.search(r"'/api':\s*\{([^}]*)\}", text, re.DOTALL)
    assert match is not None, "frontend/vite.config.ts has no '/api' proxy entry to check"
    return match.group(1)


def test_api_proxy_entry_exists():
    assert _VITE_CONFIG.exists(), "frontend/vite.config.ts not found"
    _api_proxy_block()  # raises AssertionError via the regex match check if missing


def test_api_proxy_forwards_websocket_upgrades():
    block = _api_proxy_block()
    assert re.search(r"\bws\s*:\s*true\b", block), (
        "frontend/vite.config.ts's '/api' proxy entry is missing `ws: true` -- "
        "without it, Vite's dev-server proxy silently drops every WebSocket "
        "upgrade request to /api/v1/ws, breaking the live map's real-time stream "
        "through `make dev` even though plain REST calls through the same proxy "
        "entry keep working. See TCK-20260825-LIVE-MAP-DEV-AUTH-AND-WS-PROXY-FIX."
    )


def test_api_proxy_still_targets_backend_port_8000():
    block = _api_proxy_block()
    assert "127.0.0.1:8000" in block, (
        "frontend/vite.config.ts's '/api' proxy target changed -- if the backend "
        "dev port moved, Makefile's `dev` target and this test both need updating "
        "together, not just one of them."
    )
