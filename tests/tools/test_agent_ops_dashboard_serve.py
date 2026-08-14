"""Tests for src/api/agent_ops_dashboard/serve.py.

Covers TCK-20260716-AGENTOPS-BUILD-SERVE's AC #2-#4: the StaticFiles mount
lives outside main.py, the serve app still exposes main.app's typed routes
unshadowed, dist/-missing produces a clear error, and --port/--host defaults
match the ticket's contract.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.agent_ops_dashboard import main, serve
from src.api.agent_ops_dashboard.serve import DEFAULT_HOST, DEFAULT_PORT, _build_parser, build_app

_SRC_ROOT = Path("src/api/agent_ops_dashboard")


def test_serve_module_does_not_mutate_main_app_at_import_time():
    from starlette.routing import Mount

    source = (_SRC_ROOT / "main.py").read_text(encoding="utf-8")
    assert "StaticFiles(" not in source
    assert ".mount(" not in source
    assert not any(isinstance(route, Mount) for route in main.app.routes)


def test_serve_app_exposes_same_five_routes_as_main_app(tmp_path):
    (tmp_path / "index.html").write_text("<html><body>dashboard</body></html>", encoding="utf-8")

    app = build_app(tmp_path)
    client = TestClient(app)

    response = client.get("/api/health")
    assert response.status_code == 200
    assert "status" in response.json()


def test_serve_app_returns_index_html_for_spa_root(tmp_path):
    index_content = "<html><body>agent ops dashboard spa</body></html>"
    (tmp_path / "index.html").write_text(index_content, encoding="utf-8")

    app = build_app(tmp_path)
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    assert response.text == index_content


def test_serve_app_raises_clear_error_when_dist_dir_missing(tmp_path):
    missing_dir = tmp_path / "nonexistent"

    with pytest.raises(RuntimeError) as excinfo:
        build_app(missing_dir)

    message = str(excinfo.value)
    assert str(missing_dir) in message
    assert "dashboard-build" in message


def test_serve_argparse_port_and_host_defaults():
    parser = _build_parser()

    defaults = parser.parse_args([])
    assert defaults.port == DEFAULT_PORT == 8420
    assert defaults.host == DEFAULT_HOST == "127.0.0.1"

    overridden = parser.parse_args(["--port", "9001"])
    assert overridden.port == 9001


def test_serve_module_has_no_node_npm_invocation():
    source = (_SRC_ROOT / "serve.py").read_text(encoding="utf-8")
    assert "npm" not in source
    assert "node " not in source
    assert "subprocess" not in source
    assert "os.system" not in source
