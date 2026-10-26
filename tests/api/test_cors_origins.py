"""The API answers CORS only for the local dev origins or BACKEND_CORS_ORIGINS, never ``*`` (Semgrep alert #228)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.cors import CORS_ORIGINS_ENV, DEFAULT_CORS_ORIGINS, cors_origins_from_env
from src.api.server import create_v2_app
from src.config.profiles import PROD_SMALL


@pytest.fixture(autouse=True)
def _no_ambient_cors_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    """A developer's or CI's BACKEND_CORS_ORIGINS must not change what the default app answers."""
    monkeypatch.delenv("BACKEND_CORS_ORIGINS", raising=False)


def test_default_is_the_local_dev_origins():
    assert cors_origins_from_env({}) == list(DEFAULT_CORS_ORIGINS)
    assert "*" not in DEFAULT_CORS_ORIGINS
    assert "http://localhost:5173" in DEFAULT_CORS_ORIGINS  # frontend/vite.config.ts
    assert "http://localhost:8080" in DEFAULT_CORS_ORIGINS  # compose frontend (FRONTEND_PORT)


def test_comma_list_is_split_trimmed_and_normalised():
    env = {CORS_ORIGINS_ENV: " https://a.example , https://b.example:8443/ ,,"}
    assert cors_origins_from_env(env) == ["https://a.example", "https://b.example:8443"]


@pytest.mark.parametrize("raw", ["", "   ", " , ,, ", "*", " * , "])
def test_empty_whitespace_or_wildcard_only_gives_the_default(raw):
    assert cors_origins_from_env({CORS_ORIGINS_ENV: raw}) == list(DEFAULT_CORS_ORIGINS)


def test_wildcard_next_to_a_real_origin_is_dropped():
    assert cors_origins_from_env({CORS_ORIGINS_ENV: "*,https://a.example"}) == ["https://a.example"]


def _preflight(origin: str, monkeypatch: pytest.MonkeyPatch, configured: str | None = None):
    if configured is None:
        monkeypatch.delenv(CORS_ORIGINS_ENV, raising=False)
    else:
        monkeypatch.setenv(CORS_ORIGINS_ENV, configured)
    app = create_v2_app(PROD_SMALL)
    client = TestClient(app)  # no lifespan: the CORS middleware answers a preflight before any route
    return client.options(
        "/api/v1/state",
        headers={"Origin": origin, "Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "x-api-key"},
    )


def test_preflight_from_a_dev_origin_is_allowed(monkeypatch):
    response = _preflight("http://localhost:5173", monkeypatch)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-credentials" not in response.headers


def test_preflight_from_a_configured_origin_is_allowed(monkeypatch):
    response = _preflight("https://ops.example", monkeypatch, configured="https://ops.example")
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://ops.example"


def test_preflight_from_an_unlisted_origin_is_refused(monkeypatch):
    response = _preflight("https://example.test", monkeypatch)
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
