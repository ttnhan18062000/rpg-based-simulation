"""API-boundary architecture guards for src/api/agent_ops_dashboard/.

Covers TCK-20260716-AGENTOPS-DASHBOARD-BACKEND's AC #1 (typed response models
only, never raw dict — the src/api/routes/history.py pattern this module
deliberately does not mirror) plus two scope guards named in the ticket's own
test plan: no StaticFiles/frontend-serving mount, and no write path into
tickets/**/agent-monitoring/*.jsonl.
"""
from __future__ import annotations

import ast
import typing
from pathlib import Path

from fastapi.routing import APIRoute
from pydantic import BaseModel

from src.api.agent_ops_dashboard import main

_SRC_ROOT = Path("src/api/agent_ops_dashboard")


def _response_model_names():
    for route in main.app.routes:
        if isinstance(route, APIRoute):
            yield route.path, route.response_model


def test_typed_response_models_not_dict():
    seen = list(_response_model_names())
    assert seen, "expected at least one route on the dashboard app"

    for path, response_model in seen:
        assert response_model is not None, f"{path} declares no response_model"
        assert response_model is not dict, f"{path} uses raw dict as response_model"

        origin = typing.get_origin(response_model)
        if origin in (list, typing.List):
            (inner,) = typing.get_args(response_model)
            assert inner is not dict, f"{path} uses List[dict] as response_model"
            assert isinstance(inner, type) and issubclass(inner, BaseModel), (
                f"{path}'s List[...] element is not a Pydantic model"
            )
        else:
            assert isinstance(response_model, type) and issubclass(response_model, BaseModel), (
                f"{path}'s response_model is not a Pydantic model"
            )


def test_all_declared_routes_present():
    """Renamed from test_all_five_routes_are_declared (TCK-20260718-AGENTOPS-STATS-API added a
    6th route, TCK-20260718-TICKET-CORPUS-REPORT added a 7th, TCK-20260718-GLOSSARY-API added an
    8th) — the exact-set assertion below is the actual regression guard; keep the function name
    generic so it doesn't itself go stale the next time a route is added."""
    paths = {path for path, _ in _response_model_names()}
    assert paths == {
        "/api/tickets",
        "/api/runs",
        "/api/runs/{run_id}",
        "/api/runs/{run_id}/timeline",
        "/api/stats/agent-monitoring",
        "/api/stats/tickets",
        "/api/glossary",
        "/api/health",
    }


def test_main_mounts_no_static_files():
    from starlette.routing import Mount

    source = (_SRC_ROOT / "main.py").read_text(encoding="utf-8")
    assert "StaticFiles(" not in source
    assert ".mount(" not in source
    assert not any(isinstance(route, Mount) for route in main.app.routes)


def test_agent_ops_dashboard_module_has_no_write_path():
    """Read-only contract: never write to agent-monitoring/*.jsonl or tickets/**."""
    forbidden_calls = {"write_text", "write_bytes", "open"}
    violations = []
    for py_file in _SRC_ROOT.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in forbidden_calls:
                violations.append(f"{py_file}:{node.lineno} calls .{node.attr}(...)")
    assert not violations, "\n".join(violations)


def test_agent_ops_dashboard_does_not_import_workflow_orchestrator():
    for py_file in _SRC_ROOT.glob("*.py"):
        source = py_file.read_text(encoding="utf-8")
        assert ".claude/workflows" not in source
        assert "implement-ticket.js" not in source
