"""Every registered HTTP and WebSocket route rejects an unauthenticated caller.

The walk covers the routes `include_router` registers, not only the top-level `app.routes`: from starlette 1.x
the app holds one `_IncludedRouter` per `include_router` call, so a walker that reads `app.routes[i].path` sees
none of the included routes, and ws routes carry their path on `starlette_route` (the effective context's own
`path` is empty). A cross-check against the OpenAPI document fails the test if the walk misses an HTTP route.
"""
from __future__ import annotations

import hashlib
import re

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from src.api.server import create_v2_app
from src.config.profiles import HardwareClass, RuntimeProfile
from tests.helpers.api_routes import is_websocket_route, route_path, walk_routes

_RAW_KEY = "all-routes-key"
_KEY_HASH = hashlib.sha256(_RAW_KEY.encode("utf-8")).hexdigest()

# Routes that are public by design: the liveness probe and FastAPI's own documentation endpoints. Pinned exactly: a
# new public route must be added here on purpose.
_PUBLIC_HTTP = {
    ("GET", "/health"),
    ("GET", "/openapi.json"),
    ("GET", "/docs"),
    ("GET", "/docs/oauth2-redirect"),
    ("GET", "/redoc"),
}
_HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


def _app():
    profile = RuntimeProfile(
        name="all-routes-auth", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=256, max_cpu_percent=100.0, max_worker_count=0,
        max_queue_depth=100, max_replay_buffer_kb=64,
        max_observability_budget_percent=5.0, max_tick_budget_ms=200.0,
        api_key_hashes=f"all-routes:{_KEY_HASH}",
    )
    return create_v2_app(profile)


def _registered_routes(app):
    """(kind, method, path) for every registered route, `include_router` routes included."""
    found = set()
    for route in walk_routes(app):
        path = route_path(route)
        if is_websocket_route(route):
            found.add(("ws", "WS", path))
            continue
        for method in sorted((getattr(route, "methods", None) or set()) & _HTTP_METHODS):
            found.add(("http", method, path))
    return found


def _concrete(path: str) -> str:
    return re.sub(r"\{[^}/]+\}", "1", path)


def test_walk_finds_every_http_route_the_openapi_document_lists():
    app = _app()
    walked = {(m, p) for kind, m, p in _registered_routes(app) if kind == "http"}
    documented = {
        (method.upper(), path)
        for path, item in app.openapi()["paths"].items() for method in item if method.upper() in _HTTP_METHODS
    }
    assert documented, "the OpenAPI document lists no routes"
    assert documented <= walked, f"routes the walk cannot see: {sorted(documented - walked)}"
    assert any(kind == "ws" for kind, _, _ in _registered_routes(app)), "the walk found no websocket route"


def test_every_registered_route_rejects_an_unauthenticated_caller():
    app = _app()
    client = TestClient(app, raise_server_exceptions=False)
    reachable = []
    for kind, method, path in sorted(_registered_routes(app)):
        target = _concrete(path)
        if kind == "ws":
            try:
                with client.websocket_connect(target):
                    reachable.append(("WS", path, "accepted"))
            except WebSocketDisconnect as exc:
                if exc.code != 1008:
                    reachable.append(("WS", path, f"closed {exc.code}"))
            continue
        if (method, path) in _PUBLIC_HTTP:
            continue
        status = client.request(method, target).status_code
        if status != 401:
            reachable.append((method, path, status))
    assert not reachable, f"reachable without a valid API key: {reachable}"
