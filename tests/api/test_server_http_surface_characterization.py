"""Characterization of the HTTP surface `create_v2_app` exposes, pinned before `src/api/server.py` is split.

The snapshot in `tests/fixtures/api_server_http_surface.json` records, for the default profile and for a profile with
both optional routers on:

* every route (HTTP, WebSocket, and the ones `include_router` registers) in registration order, with its path, methods,
  endpoint `__name__`, route `name`, `response_class`, `response_model`, `include_in_schema` and the flattened
  dependency callables. FastAPI serves the first route that matches, so the order is behaviour;
* the full `app.openapi()` document, canonical JSON with sorted keys;
* the user middleware stack, outermost first, with its options;
* the responses of the routes whose bytes a move could change: the observability UI page (status, content type and
  sha256 of the body, requested without gzip), its two redirects, `/metrics` with and without a key, and a CORS
  preflight.

A move that keeps behaviour leaves the fixture byte-identical. Regenerate it only when a change intends to alter the
surface, with `UPDATE_API_SURFACE_FIXTURE=1 pytest tests/api/test_server_http_surface_characterization.py` and review
the diff of the fixture in the same commit. A refactor that needs the regeneration has changed behaviour.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterator

import pytest
from fastapi.testclient import TestClient

import src.api.admission_control as admission_control
from src.api.metrics_port import METRICS_PORT_ENV
from src.api.server import create_v2_app
from src.config.profiles import PROD_SMALL, HardwareClass, RuntimeProfile
from tests.helpers.api_routes import (
    is_websocket_route,
    route_dependant,
    route_path,
    walk_routes,
)

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "api_server_http_surface.json"
_UPDATE_ENV = "UPDATE_API_SURFACE_FIXTURE"

_RAW_KEY = "surface-characterization-key"
_KEY_HASH = hashlib.sha256(_RAW_KEY.encode("utf-8")).hexdigest()
_AUTH = {"X-API-Key": _RAW_KEY}
_PLAIN = {"X-API-Key": _RAW_KEY, "Accept-Encoding": "identity"}  # no gzip: the body bytes are the page itself


@pytest.fixture(autouse=True)
def _clean_admission_state() -> Iterator[None]:
    admission_control.reset_admission_mode()
    yield
    admission_control.reset_admission_mode()


@pytest.fixture(autouse=True)
def _no_ambient_cors_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    """A developer's or CI's BACKEND_CORS_ORIGINS must not change what the default app answers."""
    monkeypatch.delenv("BACKEND_CORS_ORIGINS", raising=False)


def _profile(**overrides: Any) -> RuntimeProfile:
    base: dict[str, Any] = dict(
        name="surface-characterization", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=256, max_cpu_percent=100.0, max_worker_count=0,
        max_queue_depth=100, max_replay_buffer_kb=64,
        max_observability_budget_percent=5.0, max_tick_budget_ms=200.0,
        api_key_hashes=f"surface:{_KEY_HASH}",
    )
    base.update(overrides)
    return RuntimeProfile(**base)


def _qualified(obj: Any) -> str:
    return f"{getattr(obj, '__module__', '?')}.{getattr(obj, '__qualname__', repr(obj))}"


def _flatten_dependencies(dependant: Any) -> list[str]:
    """Pre-order list of the dependency callables of a route: router-level, route-level and nested ones."""
    out: list[str] = []
    for sub in getattr(dependant, "dependencies", None) or []:
        out.append(_qualified(sub.call))
        out.extend(_flatten_dependencies(sub))
    return out


def _response_class(route: Any) -> str | None:
    response_class = getattr(route, "response_class", None)
    response_class = getattr(response_class, "value", response_class)  # FastAPI wraps the default in DefaultPlaceholder
    return None if response_class is None else _qualified(response_class)


def _describe_route(route: Any) -> dict[str, Any]:
    inner = getattr(route, "starlette_route", None) or route
    endpoint = getattr(route, "endpoint", None) or getattr(inner, "endpoint", None)
    response_model = getattr(route, "response_model", None)
    return {
        "kind": "ws" if is_websocket_route(route) else "http",
        "path": route_path(route),
        "methods": sorted(getattr(route, "methods", None) or []),
        "endpoint": getattr(endpoint, "__name__", None),
        "name": getattr(route, "name", None) or getattr(inner, "name", None),
        "response_class": _response_class(route),
        "response_model": None if response_model is None else repr(response_model),
        "include_in_schema": getattr(route, "include_in_schema", None),
        "dependencies": _flatten_dependencies(route_dependant(route)),
    }


def _describe_middleware(app: Any) -> list[dict[str, Any]]:
    """`user_middleware[0]` is the outermost: `add_middleware` inserts at the front."""
    return [
        {"class": _qualified(m.cls), "options": {k: repr(v) for k, v in sorted(m.kwargs.items())}}
        for m in app.user_middleware
    ]


def _routes_and_openapi(**profile_overrides: Any) -> dict[str, Any]:
    app = create_v2_app(_profile(**profile_overrides))
    return {
        "routes": [_describe_route(r) for r in walk_routes(app)],
        "middleware": _describe_middleware(app),
        "openapi": app.openapi(),
    }


def _cors_headers(response: Any) -> dict[str, str]:
    return {k: v for k, v in sorted(response.headers.items()) if k.startswith("access-control-")}


def _responses(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    monkeypatch.setenv(METRICS_PORT_ENV, "0")  # a free port; the default may be taken on a developer machine
    profile = PROD_SMALL.model_copy(update={"api_key_hashes": f"surface:{_KEY_HASH}"})
    app = create_v2_app(profile, seed=42, world_id="sandbox_world")
    out: dict[str, Any] = {}
    with TestClient(app) as client:
        ui = client.get("/api/v1/observability/ui", headers=_PLAIN)
        out["ui"] = {
            "status": ui.status_code,
            "content_type": ui.headers.get("content-type"),
            "content_encoding": ui.headers.get("content-encoding"),
            "bytes": len(ui.content),
            "sha256": hashlib.sha256(ui.content).hexdigest(),
        }
        for key, path in (("redirect_ui", "/observability/ui"), ("redirect_live_ui", "/api/v1/observability/live/ui")):
            response = client.get(path, headers=_AUTH, follow_redirects=False)
            out[key] = {"status": response.status_code, "location": response.headers.get("location")}
        unauthenticated = client.get("/metrics")
        authenticated = client.get("/metrics", headers=_AUTH)
        out["metrics"] = {
            "without_key": unauthenticated.status_code,
            "with_key": authenticated.status_code,
            "with_key_content_type": authenticated.headers.get("content-type"),
        }
        preflight = client.options(
            "/api/v1/state",
            headers={
                "Origin": "https://example.test",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "x-api-key",
            },
        )
        out["cors_preflight"] = {"status": preflight.status_code, "headers": _cors_headers(preflight)}
    return out


def build_surface(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Everything the fixture records, for both profiles and the live responses."""
    return {
        "default_profile": _routes_and_openapi(),
        "optional_routers_on": _routes_and_openapi(enable_behavior_analytics_api=True, enable_campaign_chronicle_api=True),
        "responses": _responses(monkeypatch),
    }


def _canonical(surface: dict[str, Any]) -> str:
    return json.dumps(surface, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def test_http_surface_matches_the_recorded_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    """The surface is byte-identical to the recorded fixture."""
    current = _canonical(build_surface(monkeypatch))
    if os.environ.get(_UPDATE_ENV):
        FIXTURE.write_text(current, encoding="utf-8")
    recorded = FIXTURE.read_text(encoding="utf-8")
    if current != recorded:
        current_doc, recorded_doc = json.loads(current), json.loads(recorded)
        changed = [k for k in current_doc if current_doc[k] != recorded_doc.get(k)]
        pytest.fail(f"the HTTP surface changed in: {changed}; regenerate only for an intended change (see the module docstring)")


def test_the_snapshot_covers_both_conditional_router_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    """The default and the all-optional-routers profiles differ, so both conditional branches are pinned."""
    surface = json.loads(_canonical(build_surface(monkeypatch)))
    default_paths = {r["path"] for r in surface["default_profile"]["routes"]}
    on_paths = {r["path"] for r in surface["optional_routers_on"]["routes"]}
    assert default_paths < on_paths, "the optional routers add routes"
    assert any(r["kind"] == "ws" for r in surface["default_profile"]["routes"])
    assert surface["default_profile"]["middleware"][0]["class"].endswith("RequestDurationMiddleware")


def test_the_snapshot_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    """Two builds in one process render the same canonical text."""
    assert _canonical(build_surface(monkeypatch)) == _canonical(build_surface(monkeypatch))
