---
ticket_id: TCK-20260623-TYPE-CHECKER
artifact: investigation
date: 2026-06-23
---

# Investigation: D13 Type Safety — mypy + FastAPI response_model

## 1. pyproject.toml Current State

**File:** `pyproject.toml`

- **Python version target:** `requires-python = ">=3.11"` — use `python_version = "3.11"` in mypy config.
- **Existing `[tool.*]` sections:** Only `[tool.setuptools.packages.find]` and `[tool.pytest.ini_options]`.
- **No `[tool.mypy]` section exists.** No mypy.ini anywhere in the repo.
- **mypy is not listed** in `[project.dependencies]` or any `[project.optional-dependencies]` group.
  - Must add `mypy` to the `dev` optional-dependencies group (or install separately).
- **CI uses Python 3.13**, not 3.11, per `.github/workflows/test.yml`. Both `fast` and `slow` jobs pin `python-version: "3.13"`. The `pyproject.toml` says `>=3.11`. Use `python_version = "3.11"` in mypy config to match the minimum target (safe — 3.13 is a superset). Alternatively use `"3.13"` to match CI exactly. **Recommendation: use `"3.13"` to match CI.**

---

## 2. Makefile Format Reference

- **Indentation:** Hard tabs (real `\t`), not spaces. All recipe lines use a single leading tab.
- **`.PHONY` declaration:** All targets listed on a single long `.PHONY` line at the top.
- **Target structure:**
  ```
  target-name: [prerequisites] ## Help text shown in `make help`
  \t<command>
  ```
- **Existing quality section** (lines 199–205): Contains `lint` and `typecheck` targets.
  - `typecheck` already exists and runs `cd frontend && npx tsc --noEmit` (TypeScript only).
  - The new Python mypy target must be named differently. **Options:**
    1. Add `typecheck-py` as a separate target.
    2. Extend existing `typecheck` to also run Python mypy (risk: changes existing behavior, may surprise TS-only users).
  - **Recommendation:** Add `typecheck-py` as a new target; leave existing `typecheck` alone.
    This also avoids requiring the frontend to be installed in CI for the mypy step.
  - Add `typecheck-py` to the `.PHONY` list at the top.

**Proposed Makefile addition (in Quality section, after existing `typecheck`):**
```
typecheck-py: ## Run Python type checking via mypy (src/ only)
	python3 -m mypy src/ --config-file pyproject.toml
```

---

## 3. CI Workflow Structure

**File:** `.github/workflows/test.yml`

Two jobs:
- `fast` — runs on every PR and push to main. Steps: checkout, setup-python 3.13, pip install, `make lane-all-fast`, `make gate-expansion`, `pytest tests/docs/`.
- `slow` — runs on main only (after `fast`). Steps: checkout, setup-python 3.13, pip install, `make lane-legacy-regression`.

**Where to insert mypy:**
- Add as a new step in the `fast` job, after the existing `Doc integrity` step.
- Use `continue-on-error: true` on first pass (ticket specifies this — avoids blocking PRs until baseline error count is documented).
- mypy must be installed: add to the `pip install -r requirements.txt` step or add explicit `pip install mypy` step before the mypy step.

**Proposed CI addition (in `fast` job after `Doc integrity`):**
```yaml
      - name: Install mypy
        run: pip install mypy

      - name: Type check (mypy)
        run: python3 -m mypy src/ --config-file pyproject.toml
        continue-on-error: true
```

**Note:** `requirements.txt` is not visible here — if mypy is added to `pyproject.toml [project.optional-dependencies] dev`, the CI pip install command would need `-e ".[dev]"` not `pip install -r requirements.txt`. Check `requirements.txt` format before wiring up. Safest first pass: explicit `pip install mypy` step.

---

## 4. Route Inventory: src/api/server.py

All routes are inline `@app.*` decorators inside `create_v2_app()`. There are also 9 routers included via `app.include_router(...)` — those are in `src/api/routes/` and have their own response_model coverage (covered separately below).

Total `@app.*` decorators in server.py: **18**

| # | Method | Path | Handler Name | Has response_model? | Notes |
|---|--------|------|--------------|---------------------|-------|
| 1 | GET | `/metrics` | `get_metrics` | NO | Returns raw `Response(Prometheus text)` — `response_model` N/A; special case |
| 2 | GET | `/health` | `health_check` | NO | Returns `{"status","version","timestamp"}` |
| 3 | GET | `/api/v1/observability/live/status` | `get_live_status` | NO | Returns `LiveSnapshotProvider.get_status()` |
| 4 | GET | `/api/v1/observability/live/snapshot` | `get_live_snapshot` | NO | Returns `LiveSnapshotProvider.get_snapshot()` |
| 5 | GET | `/api/v1/observability/live/entities/{entity_id}` | `inspect_live_entity` | NO | Returns `EntityInspector.inspect_entity()` dataclass/model |
| 6 | GET | `/api/v1/state` | `get_state` | NO | Returns `manager.get_state()` → `Dict[str, Any]` |
| 7 | GET | `/api/v1/inspect` | `inspect_state` | NO | Returns `manager.get_full_snapshot()` → `Dict[str, Any]` |
| 8 | GET | `/api/v1/entities` | `get_entities` | NO | Returns `manager.get_entities_paged()` → `Dict[str, Any]` |
| 9 | GET | `/api/v1/entities/{entity_id}` | `get_entity` | NO | Returns `manager.get_entity()` → `Optional[Dict[str, Any]]` |
| 10 | POST | `/api/v1/control/pause` | `pause_sim` | NO | Returns `{"status":"paused"}` |
| 11 | POST | `/api/v1/control/resume` | `resume_sim` | NO | Returns `{"status":"resumed"}` |
| 12 | POST | `/api/v1/test/publish_event` | `publish_test_event` | NO | Returns `{"status":"published"}` |
| 13 | GET | `/api/v1/observability/live/health` | `get_live_health` | NO | Returns `counter.calculate_health()` |
| 14 | GET | `/api/v1/observability/live/stream-health` | `get_stream_health` | NO | Returns `adapter.health()` |
| 15 | GET | `/api/v1/observability/history/runs/{run_id}/report` | `get_run_report` | NO | Returns `Response(markdown text)` — special case |
| 16 | GET | `/api/v1/observability/ui` | `get_observability_ui` | response_class=HTMLResponse | HTMLResponse — no response_model needed |
| 17 | GET | `/observability/ui` | `redirect_ui` | NO | Returns `RedirectResponse` — special case |
| 18 | GET | `/api/v1/observability/live/ui` | `redirect_live_ui` | NO | Returns `RedirectResponse` — special case |

**Routes needing `response_model=` (or explicit acknowledgment):**
- Routes 2–14: 13 routes with dict/typed returns → add `response_model=Dict[str, Any]` as typed placeholder
- Route 1: `/metrics` — skip; raw `Response` with Prometheus MIME type
- Routes 15, 17, 18: skip; raw `Response`, `RedirectResponse` — `response_model` incompatible

**Actionable count:** 13 routes in server.py need `response_model=Dict[str, Any]` added (routes 2–14). Routes 1, 15, 16, 17, 18 are special-case (raw Response/Redirect/HTMLResponse).

**Note on F2 "18 routes":** The audit count of 18 matches the total `@app.*` decorators. The 5 special-case routes cannot take a `response_model` without breaking behavior. The ticket says "add `response_model=` to each, using `Dict[str, Any]` as a temporary typed placeholder" — this applies to the 13 actionable ones only.

### Route coverage in src/api/routes/ (for completeness)

The included routers already have partial `response_model` coverage:
- `chronicle.py` — has typed `response_model=ChronicleResponse` / `ErasSummaryResponse` (good)
- `history.py` — has `response_model=List[dict]` / `response_model=dict` (weak types, but present)
- `search.py` — has `response_model=List[dict]` (present)
- `campaigns.py` — has `response_model=CampaignHistoryResponse` (good)
- `economy.py` — has `response_model=Dict[str, Any]` (placeholder, present)
- `behavior.py` — has `response_model=List[dict]` (present)
- `decisions.py`, `scenarios.py`, `control.py`, `state.py`, `health.py` — not checked in this pass

The F2 finding from D13 audit was specifically about `server.py`'s inline routes. Routers in `routes/` have varying coverage but are not the primary target of this ticket.

---

## 5. engine_manager.py Methods to Annotate

**File:** `src/api/engine_manager.py`

The 4 target state-query methods:

| Method | Current signature | Current return type | Proposed signature |
|--------|------------------|--------------------|--------------------|
| `get_state()` | `def get_state(self)` | `Dict[str, Any]` (declared) | `def get_state(self) -> Dict[str, Any]` |
| `get_full_snapshot()` | `def get_full_snapshot(self)` | `Dict[str, Any]` (declared) | `def get_full_snapshot(self) -> Dict[str, Any]` |
| `get_entities_paged()` | `def get_entities_paged(self, offset: int = 0, limit: int = 100)` | `Dict[str, Any]` (declared) | `def get_entities_paged(self, offset: int = 0, limit: int = 100) -> Dict[str, Any]` |
| `get_entity()` | `def get_entity(self, entity_id: int)` | `Optional[Dict[str, Any]]` (declared) | `def get_entity(self, entity_id: int) -> Optional[Dict[str, Any]]` |

**Actual current state (from reading the file):**
- `get_state()` at line 176: signature is `def get_state(self) -> Dict[str, Any]:` — **already has return annotation**.
- `get_full_snapshot()` at line 183: `def get_full_snapshot(self) -> Dict[str, Any]:` — **already annotated**.
- `get_entities_paged()` at line 191: `def get_entities_paged(self, offset: int = 0, limit: int = 100) -> Dict[str, Any]:` — **already annotated**.
- `get_entity()` at line 198: `def get_entity(self, entity_id: int) -> Optional[Dict[str, Any]]:` — **already annotated**.

**Surprise finding:** All 4 methods in engine_manager.py already have explicit return type annotations. The D13 audit's F3 finding ("returns `Dict[str, Any]`") was accurate about the *type* used, but the annotation itself is present. F3 work is effectively: verify the annotations are correct (they are), and ensure mypy doesn't flag them when run.

**What remains for F3:** The `metrics_registry` property returns `-> Any` (line 61). Other methods like `get_metrics_snapshot()` already return `Dict[str, Any]`. The main value from F3 in this ticket is adding Pydantic response schemas for the 4 methods — not adding the annotations (already done).

---

## 6. src/api/schemas.py — Exists or Create?

**Result: Does NOT exist.** `ls src/api/` output: `__pycache__`, `dependencies.py`, `engine_manager.py`, `presenters/`, `read_model_cache.py`, `read_model_service.py`, `routes/`, `server.py`, `ws/`.

No `schemas.py` in `src/api/`. Must **create** `src/api/schemas.py`.

For this ticket's scope (minimal typed schemas for the 4 highest-risk engine_manager routes):

Proposed contents:
- `StateResponse(TypedDict)` or Pydantic BaseModel — covers `get_state()` return shape
- `EntityPagedResponse(TypedDict)` — covers `get_entities_paged()` return shape
- `EntityResponse(TypedDict)` — covers `get_entity()` return shape
- Simple `Dict[str, Any]` placeholder acceptable for routes without stable shape contracts

Since the ticket says "minimal typed `TypedDict` or Pydantic response schemas", and `engine_manager.py` is already well-typed with `Dict[str, Any]`, the pragmatic approach is:
1. Create `src/api/schemas.py` with a handful of `TypedDict` classes for the 4 target routes.
2. Wire these as `response_model=` on the 4 corresponding routes in `server.py`.
3. For the remaining 9 actionable routes: use `response_model=Dict[str, Any]` inline.

---

## 7. Risks and Open Questions

### R1: `typecheck` target name collision
The Makefile already has `typecheck` (TypeScript). Adding a Python variant requires a new name (`typecheck-py`) or renaming the existing one. Renaming breaks any scripts or docs referencing `make typecheck`. **Decision: add `typecheck-py`.**

### R2: mypy not in requirements.txt
mypy is not in `pyproject.toml` dependencies. The CI `pip install -r requirements.txt` may not install it. Two paths:
- Add `mypy` to `[project.optional-dependencies] dev` in `pyproject.toml` and update the CI install step.
- Add an explicit `pip install mypy` step in CI before the mypy step.
The safest low-risk option for first pass: explicit CI step only. Add to `dev` extras to help local dev.

### R3: `continue-on-error: true` on mypy CI step
The ticket specifies this to avoid blocking PRs. This means mypy errors will not fail the build on first merge. A follow-up ticket should document the baseline error count and remove `continue-on-error`.

### R4: engine_manager methods already annotated (F3 scope shrinkage)
The 4 state-query methods already have return type annotations. F3 is partially pre-satisfied. The remaining value is: creating `src/api/schemas.py` with Pydantic/TypedDict schemas and wiring as `response_model=` on the 4 highest-risk routes in `server.py`. The annotation work in `engine_manager.py` itself is minimal.

### R5: Python version mismatch (pyproject: 3.11, CI: 3.13)
Use `python_version = "3.13"` in `[tool.mypy]` to match CI, or `"3.11"` to match the minimum target. Either is valid. Using `"3.11"` is more conservative (won't rely on 3.12/3.13-only type narrowing). **Recommendation: `"3.11"` — matches minimum constraint in pyproject.toml.**

### R6: `get_observability_ui` returns `HTMLResponse` with `response_class=HTMLResponse`
This route uses `response_class=` not `response_model=`. This is the correct FastAPI pattern for HTML responses. No change needed.

### R7: `/metrics`, report, and redirect routes cannot use response_model
Routes returning raw `Response`, `RedirectResponse`, or `HTMLResponse` must not be given a `response_model` — FastAPI will attempt to validate/serialize the return value and fail. These 5 routes are excluded from the response_model addition.
