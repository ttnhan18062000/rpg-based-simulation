---
name: backend-testing
description: 'Writes comprehensive backend unit, integration, and API tests.'
---

# Backend Testing (This Repo)

This repo's real API test convention, for testing `src/api/server.py` and everything under
`src/api/`. Replaced an earlier version of this skill that was 100% Node.js/Express/Jest/Prisma
content with one nominal "Python" example that was still generic FastAPI `TestClient` + SQLAlchemy
CRUD boilerplate — unrelated to how this repo actually tests its API, and describing a
user-auth/JWT/registration flow this repo doesn't have at all.

## The real pattern: live subprocess + `requests`, not `TestClient`

Every real test in `tests/api/` launches the actual server as a subprocess and makes real HTTP
calls against it — **not** FastAPI's in-process `TestClient`. This is the pattern to follow:

```python
import subprocess
import time
import requests

def test_my_endpoint():
    port = 8002  # pick a port not used by another concurrent test file
    cmd = ["python3", "-m", "src", "serve", "--port", str(port), "--log-level", "ERROR"]
    server = subprocess.Popen(cmd)
    time.sleep(3)  # wait for uvicorn to finish starting

    try:
        resp = requests.get(f"http://127.0.0.1:{port}/api/v1/state")
        assert resp.status_code == 200
        data = resp.json()
        assert "tick" in data
    finally:
        server.terminate()
        server.wait()
```

See `tests/api/test_rest_parity.py` and `tests/api/test_live_health_api.py` for real, larger
examples (including `SIM_OBS_MODE` env-var setup and log-file redirection for noisier endpoints).

## The read-model/presenter boundary

Routes under `src/api/routes/`, `src/api/ws/`, and `src/api/server.py` may only consume
`src/api/presenters/*.py` — never a raw `AuthoritativeState`/`EntityState` domain object. This is
a **hard, AST-enforced architecture rule** (`tests/architecture/test_api_read_model_guard.py`,
CLAUDE.md's "Do not expose raw domain models from APIs"), independent of any test you write. When
writing a new endpoint test, assert on the *presenter-shaped* response body, not on internal domain
fields that a presenter wouldn't expose.

## `ReadModelCache` and DirtySet-scoped invalidation

`src/api/read_model_cache.py`'s `ReadModelCache`/`ReadModelInvalidationPolicy` cache API/UI
projection DTOs and invalidate them conservatively, driven by the tick's `DirtySet` ("M12 Law:
Invalidation must be conservative and driven by DirtySet domain tracking" — see the module's own
docstring). If you're testing an endpoint whose data depends on entity state that just changed,
be aware a stale cached read is a real, repo-specific failure mode worth a dedicated test case —
not something a generic Jest/pytest skill would ever tell you to check for.

## Practical checklist for a new API test

- [ ] Pick a `port` not already used by another test file running in the same suite.
- [ ] Launch via `subprocess.Popen(["python3", "-m", "src", "serve", "--port", str(port), ...])`.
- [ ] `time.sleep(3)` (or `4.0` for heavier observability endpoints — see
      `test_live_health_api.py`) before the first request.
- [ ] Always `server.terminate(); server.wait()` in a `finally` block.
- [ ] Assert on presenter-shaped response fields, not raw domain-model internals.
- [ ] If the endpoint reads cached data, consider whether `DirtySet` invalidation is relevant to
      the scenario under test.
