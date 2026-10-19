"""Guard for the request-duration histogram (issue #622, R2): no router prefix may hold a path parameter.

`http_metrics.route_template` takes the include prefix from the RAW request path (FastAPI 0.143 gives a lazily included route only its
own prefix-less path). A prefix such as "/worlds/{world_id}" would therefore put the raw world id into the `route` label of every
request under it, an unbounded label set. Every `APIRouter(prefix=...)` and `include_router(..., prefix=...)` under src/ must be a plain
string literal without "{". This reads the source (not the FastAPI internals), so it holds on every FastAPI version.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterator, Tuple

SRC = Path(__file__).resolve().parents[3] / "src"
WHY = ("A router prefix with a path parameter would leak raw ids into the request-duration histogram's `route` label "
       "(unbounded label cardinality, issue #622 R2, src/api/http_metrics.py route_template). Put the parameter on the route, not on the prefix.")


def _prefixes() -> Iterator[Tuple[str, int, ast.expr]]:
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            if name not in ("APIRouter", "include_router"):
                continue
            for keyword in node.keywords:
                if keyword.arg == "prefix":
                    yield str(path.relative_to(SRC.parent)), node.lineno, keyword.value


def test_the_guard_sees_the_routers_it_is_meant_to_guard():
    assert sum(1 for _ in _prefixes()) >= 10


def test_no_router_prefix_holds_a_path_parameter():
    bad = []
    for where, line, value in _prefixes():
        if not (isinstance(value, ast.Constant) and isinstance(value.value, str)):
            bad.append(f"{where}:{line} prefix is not a string literal, so it cannot be checked")
        elif "{" in value.value:
            bad.append(f"{where}:{line} prefix {value.value!r} holds a path parameter")
    assert not bad, WHY + "\n" + "\n".join(bad)
