"""Flat view of a FastAPI app's route table.

FastAPI 0.143 keeps ``include_router`` routers lazy: ``app.routes`` holds ``_IncludedRouter`` nodes whose
real routes are only reachable through ``effective_candidates()``, which yields ``_EffectiveRouteContext``
objects (no flattened ``.path``; the mounted path and the merged ``dependant`` are on ``starlette_route``). Before 0.143 ``app.routes`` was already flat.
Tests that need every route's mounted path and ``dependant`` use ``flat_routes`` so they do not depend on which
FastAPI layout is installed.
"""
from __future__ import annotations

from typing import Any, Iterator, NamedTuple, Optional


class FlatRoute(NamedTuple):
    path: Optional[str]
    dependant: Any


def flat_routes(app: Any) -> Iterator[FlatRoute]:
    def walk(routes: Any) -> Iterator[Any]:
        for route in routes:
            candidates = getattr(route, "effective_candidates", None)
            if callable(candidates):
                yield from walk(candidates())
            else:
                yield route

    for route in walk(app.routes):
        mounted = getattr(route, "starlette_route", None)
        path = getattr(mounted, "path", None) if mounted is not None else getattr(route, "path", None)
        # The mounted starlette route carries the dependant with the include-level dependencies merged in.
        dependant = getattr(mounted, "dependant", None) if mounted is not None else getattr(route, "dependant", None)
        yield FlatRoute(path, dependant)
