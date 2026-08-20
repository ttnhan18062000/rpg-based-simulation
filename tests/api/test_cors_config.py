"""
CORS middleware configuration guard (TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG).

The CORS spec forbids combining a wildcard `Access-Control-Allow-Origin: *` with
`Access-Control-Allow-Credentials: true` -- a credentialed request cannot legally use a wildcard
origin. Uses an in-process TestClient (no subprocess) to verify the real response headers a
credentialed cross-origin request actually receives, not just the middleware's constructor args.
"""
from fastapi.testclient import TestClient

from src.api.server import create_v2_app
from src.config.profiles import PROD_DEFAULT


def test_cors_never_combines_wildcard_origin_with_credentials():
    app = create_v2_app(PROD_DEFAULT)
    with TestClient(app) as client:
        resp = client.get(
            "/health",
            headers={"Origin": "https://example.com"},
        )
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == "*"
        assert "access-control-allow-credentials" not in resp.headers


def test_cors_preflight_never_combines_wildcard_origin_with_credentials():
    app = create_v2_app(PROD_DEFAULT)
    with TestClient(app) as client:
        resp = client.options(
            "/health",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == "*"
        assert "access-control-allow-credentials" not in resp.headers
