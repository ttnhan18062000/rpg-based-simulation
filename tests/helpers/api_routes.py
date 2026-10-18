"""Walk every route a FastAPI app serves, including the ones `include_router` registers.

From starlette 1.x `app.routes` holds one `_IncludedRouter` node per `include_router` call instead of the flattened
routes (and `app.routes[i].path` raises on it); the effective routes sit behind `effective_candidates()`, and a
websocket route carries its path on `starlette_route` (the effective context's own `path` is empty). On earlier
starlette `app.routes` is already flat. One walker for both, so a route test never silently sees only part of the app.
"""
from __future__ import annotations

from typing import Any, Iterator


def walk_routes(app: Any) -> Iterator[Any]:
    """Every effective route of the app (leaf routes only, no router nodes)."""
    def _walk(routes: Any) -> Iterator[Any]:
        for route in routes:
            candidates = getattr(route, "effective_candidates", None)
            if candidates is not None:
                yield from _walk(candidates())
            else:
                yield route
    yield from _walk(app.routes)


def route_path(route: Any) -> str:
    """The route's URL path, wherever the starlette version keeps it."""
    inner = getattr(route, "starlette_route", None) or route
    return getattr(route, "path", "") or getattr(inner, "path", "")


def is_websocket_route(route: Any) -> bool:
    inner = getattr(route, "starlette_route", None) or route
    return type(inner).__name__.endswith("WebSocketRoute")


def route_dependant(route: Any) -> Any:
    """The route's FastAPI `Dependant` (its resolved dependency tree), or None. On starlette 1.x a websocket route's
    effective context has `dependant = None` and keeps the real one, with the auth dependencies, on `starlette_route`."""
    dependant = getattr(route, "dependant", None)
    if dependant is None:
        dependant = getattr(getattr(route, "starlette_route", None), "dependant", None)
    return dependant
