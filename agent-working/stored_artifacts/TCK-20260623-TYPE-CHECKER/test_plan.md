---
ticket_id: TCK-20260623-TYPE-CHECKER
artifact: test_plan
date: 2026-06-23
---

# Test Plan: D13 Type Safety — mypy + FastAPI response_model

## 1. Regression Surface (existing tests that must still pass)

These tests exercise the routes and engine_manager methods being annotated. All must pass after adding `response_model=` and type annotations.

### API route tests (primary surface)

| Test file | What it covers | Risk from this ticket |
|-----------|---------------|----------------------|
| `tests/api/test_rest_parity.py` | `/health`, `/api/v1/state`, `/api/v1/control/pause`, `/api/v1/control/resume` — full server start, response shape assertions | Adding `response_model=Dict[str, Any]` to these routes; FastAPI will validate response against model at test time |
| `tests/api/test_live_entity_inspection.py` | `/api/v1/observability/live/entities/{entity_id}` route | Same — response_model validation at test time |
| `tests/api/test_ws_protocol.py` | WebSocket stream (not directly affected) | Low risk |
| `tests/api/test_observability_websocket.py` | WebSocket observability events (not directly affected) | Low risk |
| `tests/api/test_decision_api.py` | Decision API routes (in routes/ submodule, not server.py inline) | Low risk |
| `tests/api/test_phase27_behavior_query_api.py` | Behavior routes (in routes/ submodule) | Low risk |
| `tests/api/test_chronicle_api.py` | Chronicle routes (already have typed response_model) | Low risk |
| `tests/api/test_scenario_runtime_api.py` | Scenario routes (in routes/ submodule) | Low risk |
| `tests/api/test_campaign_history_api.py` | Campaign routes (already have typed response_model) | Low risk |

**Highest-risk tests:** `test_rest_parity.py` and `test_live_entity_inspection.py`. These call the exact inline routes in `server.py` that will receive `response_model=`. If the actual return value violates the schema, FastAPI will raise a 500 validation error at response serialization time (visible only during TestClient execution, not at import time).

### Key concern: response_model validation failures
FastAPI validates route return values against `response_model` when `response_model` is set. Adding `response_model=Dict[str, Any]` is permissive (any dict passes). Adding a typed `TypedDict` or Pydantic model means FastAPI will coerce/validate — if the actual return has extra fields or wrong types, this will raise a 422 or 500.

For `Dict[str, Any]` placeholders: no risk of breakage.
For typed Pydantic schemas on the 4 engine_manager routes: run tests immediately after adding schemas to catch shape mismatches.

---

## 2. Verification: mypy must run without crashing

### V1 — mypy basic execution check
```bash
python3 -m mypy src/ --config-file pyproject.toml
```
**Pass criterion:** exits with any code but does NOT crash with `SystemExit(2)` or an internal mypy error. Errors in annotated code (exit code 1) are acceptable on first pass. A crash indicates a bad config or syntax error in `[tool.mypy]`.

### V2 — make typecheck-py runs
```bash
make typecheck-py
```
**Pass criterion:** the Makefile target invokes mypy and produces output (not a `make` error about unknown target or missing tab).

### V3 — mypy does not crash on excluded modules
The `[tool.mypy]` config will exclude `src/ai/`, `src/town/`, `src/quests/`, `src/entities/`, `src/progression/`. Verify these exclusions actually suppress errors from those directories:
```bash
python3 -m mypy src/ --config-file pyproject.toml 2>&1 | grep -c "src/ai/"
```
Expected output: `0` (no errors from excluded paths).

### V4 — mypy reports on api/ modules
```bash
python3 -m mypy src/api/ --config-file pyproject.toml
```
Confirms the API boundary is being checked. Any errors here are real findings for follow-up; the first-pass acceptance criterion is no crash.

---

## 3. Scoped pytest Command

Run only the API tests to confirm route annotation changes did not break response shapes:
```bash
pytest tests/api/ -v --tb=short
```

For a broader regression sweep (architecture guards and API):
```bash
pytest tests/api/ tests/architecture/ -v --tb=short -m "not slow"
```

**Do NOT run the full suite** (`pytest tests/`) — out of scope per Testing Rule.

**Expected:** all existing `tests/api/` tests pass. Any failure in `test_rest_parity.py` or `test_live_entity_inspection.py` after adding `response_model=` is a schema mismatch that must be fixed before declaring the ticket done.

---

## 4. Anti-Drift Guards

### G1: mypy config must live in pyproject.toml only
Do not create a standalone `mypy.ini` or `.mypy.ini`. The `[tool.mypy]` section in `pyproject.toml` is the single source of truth. If a separate ini file is added later, it takes precedence over `pyproject.toml` and will silently override config.

### G2: excluded paths must be explicit
The `exclude` list in `[tool.mypy]` must use the pattern format mypy expects (regex strings). Verify by running mypy and confirming excluded paths produce no output. Example config:
```toml
[tool.mypy]
python_version = "3.11"
strict = false
ignore_missing_imports = true
warn_return_any = true
warn_unused_ignores = true
exclude = [
    "src/ai/",
    "src/town/",
    "src/quests/",
    "src/entities/",
    "src/progression/",
]
```

### G3: response_model on redirect/raw Response routes must NOT be added
Routes returning `RedirectResponse`, `Response` (raw), or using `response_class=HTMLResponse` must not receive `response_model=`. FastAPI's schema validation would attempt to serialize the Response object through the model, causing a 500. Current identified exclusions:
- `GET /metrics` → returns `Response(content=Prometheus_text)`
- `GET /api/v1/observability/history/runs/{run_id}/report` → returns `Response(content=markdown)`
- `GET /api/v1/observability/ui` → uses `response_class=HTMLResponse`
- `GET /observability/ui` → returns `RedirectResponse`
- `GET /api/v1/observability/live/ui` → returns `RedirectResponse`

### G4: parity ledger entry INFRA-TYPE-001 must be added
After implementation, `docs/parity_ledger/infrastructure.yaml` must contain a new entry with `id: INFRA-TYPE-001` covering the mypy gate. This is part of the ticket's acceptance criteria and must be verified at done-check time.

### G5: continue-on-error must be documented
The `continue-on-error: true` on the CI mypy step is a deliberate first-pass decision. A comment in the workflow or in `docs/plans/open_audit_findings_backlog.md` must note: "mypy runs informational on first pass; remove continue-on-error once baseline error count is documented in follow-up ticket."

### G6: working_log.csv and agent-monitoring entries required
Per project workflow rules, a working log CSV entry must be appended (never inserted) and agent-monitoring run/event entries must be written. Monitoring write failure must never fail the workflow.
