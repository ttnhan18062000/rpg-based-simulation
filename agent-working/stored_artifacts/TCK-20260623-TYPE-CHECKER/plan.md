---
ticket_id: TCK-20260623-TYPE-CHECKER
artifact: plan
date: 2026-06-23
status: ready
---

# Implementation Plan: D13 Type Safety — mypy + FastAPI response_model

## Summary

This plan resolves findings F1, F2, and F3 from audit D13 (`docs/audits/D13_type_safety.md`):

- **F1 (15/15 risk):** No mypy configuration exists anywhere in the repo.
- **F2 (11/15 risk):** `src/api/server.py` has 13 actionable inline routes with no `response_model=`
  (5 additional routes are special-case Response/Redirect routes — excluded by design).
- **F3 (10/15 risk):** The 4 state-query methods in `engine_manager.py` already carry `-> Dict[str, Any]`
  annotations (pre-satisfied); the remaining value is creating `src/api/schemas.py` and wiring typed
  response schemas on the 4 highest-risk routes.

All questions from investigation.md are resolved. No unresolved design choices remain.

---

## Ordered Steps

### Step 1 — Add mypy to pyproject.toml

**File:** `pyproject.toml`

Two changes in one edit pass:

1a. Add `mypy` to `[project.optional-dependencies]`. The file currently has no `dev` group — create it:

```toml
[project.optional-dependencies]
dev = [
    "mypy",
]
```

If a `dev` group already exists at read time, append `"mypy"` to it.

1b. Append a new `[tool.mypy]` section (no such section currently exists — confirmed in investigation):

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

**Rationale for `python_version = "3.11"`:** matches `requires-python = ">=3.11"` in `pyproject.toml`;
conservative choice — does not rely on 3.12/3.13-only type narrowing. CI runs 3.13, which is a superset
and will not cause false negatives.

**Read `pyproject.toml` before editing** to confirm exact structure of existing `[project.optional-dependencies]`
block and append position.

---

### Step 2 — Add `typecheck-py` target to Makefile

**File:** `Makefile`

**Do not touch or rename the existing `typecheck` target** — it runs `cd frontend && npx tsc --noEmit`
(TypeScript) and is referenced by existing tooling.

Add a new `typecheck-py` target in the Quality section (after existing `typecheck`):

```makefile
typecheck-py: ## Run Python type checking via mypy (src/ only, informational first pass)
	python3 -m mypy src/ --config-file pyproject.toml --no-error-summary || true
```

Key details:
- **Real tab character** (not spaces) before the recipe command — matches Makefile indentation convention
  confirmed in investigation.
- `|| true` so the target exits 0 on mypy errors (first-pass informational mode — avoids breaking
  local `make` runs before the error baseline is documented).
- `--no-error-summary` suppresses the "Found N errors" summary line that can clutter CI output.
- Add `typecheck-py` to the `.PHONY` list at the top of the Makefile.

**Read the relevant Makefile region** (Quality section and `.PHONY` line) before editing to find the
exact insertion point and copy the surrounding formatting.

---

### Step 3 — Wire mypy into `.github/workflows/test.yml`

**File:** `.github/workflows/test.yml`

**Read the file first** to confirm the exact job/step structure. From investigation, the `fast` job is
the target (runs on every PR and push to main).

Insert two consecutive steps in the `fast` job, after the existing `Doc integrity` step:

```yaml
      - name: Install mypy
        run: pip install mypy

      - name: Type check (mypy)
        run: python3 -m mypy src/ --config-file pyproject.toml
        continue-on-error: true
```

**`continue-on-error: true` is mandatory for this first pass** — the ticket explicitly requires it
so PRs are not blocked until the error baseline is documented in a follow-up ticket.

Add a comment above the mypy step (in the YAML) documenting the intent:

```yaml
      # mypy runs informational on first pass. Remove continue-on-error once
      # baseline error count is documented in follow-up ticket (open_audit_findings_backlog §1G).
      - name: Type check (mypy)
        run: python3 -m mypy src/ --config-file pyproject.toml
        continue-on-error: true
```

**Do not add mypy to the `slow` job** — it is redundant and the slow job runs on main only.

---

### Step 4 — Create `src/api/schemas.py`

**File:** `src/api/schemas.py` (does not exist — confirmed in investigation)

Create with typed schemas for the 4 highest-risk engine_manager routes and import-ready `Dict` alias
for the remaining 9 routes:

```python
"""
Response schemas for src/api/server.py inline routes.

TypedDict classes are used as response_model= targets for the 4 highest-risk
engine_manager routes. Dict[str, Any] is used as a typed placeholder for
the remaining 9 actionable inline routes.

Do not use strict Pydantic validation here until the actual response shapes
are fully contract-tested (tracked in open_audit_findings_backlog §1G).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class WorldStateResponse(TypedDict, total=False):
    """Shape for /api/v1/state (engine_manager.get_state())."""
    tick: int
    status: str
    entity_count: int
    region_count: int
    metadata: Dict[str, Any]


class EntityPageResponse(TypedDict, total=False):
    """Shape for /api/v1/entities (engine_manager.get_entities_paged())."""
    entities: List[Dict[str, Any]]
    total: int
    offset: int
    limit: int


class EntityDetailResponse(TypedDict, total=False):
    """Shape for /api/v1/entities/{entity_id} (engine_manager.get_entity())."""
    id: int
    name: str
    attributes: Dict[str, Any]
    metadata: Dict[str, Any]
```

**Design notes:**
- `total=False` on all TypedDicts — the actual engine_manager responses may omit fields depending
  on simulation state; `total=False` avoids TypedDict validation failures at mypy check time.
- FastAPI does not validate TypedDict fields at runtime when used as `response_model` in the same
  strict way Pydantic models do — this is intentional for the first pass (informational gate only).
- `from __future__ import annotations` ensures compatibility with Python 3.11.
- `typing_extensions.TypedDict` is used for `total=False` on Python 3.11 compatibility; if
  `typing_extensions` is not a project dependency, use `typing.TypedDict` and accept that `total=False`
  defaults all keys to optional.

**Read `src/api/engine_manager.py` before writing schemas** to confirm the actual keys returned by
`get_state()`, `get_entities_paged()`, and `get_entity()` — adjust TypedDict fields to match real
shape. This avoids immediate mypy complaints from mismatched signatures.

---

### Step 5 — Add `response_model=` to 13 routes in `src/api/server.py`

**File:** `src/api/server.py`

**Read the full file before editing** to confirm current decorator syntax for each route.

Add `response_model=` to exactly 13 routes (routes 2–14 in the investigation route inventory table):

| Route # | Path | Handler | response_model to add |
|---------|------|---------|----------------------|
| 2 | `GET /health` | `health_check` | `Dict[str, Any]` |
| 3 | `GET /api/v1/observability/live/status` | `get_live_status` | `Dict[str, Any]` |
| 4 | `GET /api/v1/observability/live/snapshot` | `get_live_snapshot` | `Dict[str, Any]` |
| 5 | `GET /api/v1/observability/live/entities/{entity_id}` | `inspect_live_entity` | `Dict[str, Any]` |
| 6 | `GET /api/v1/state` | `get_state` | `WorldStateResponse` (from schemas.py) |
| 7 | `GET /api/v1/inspect` | `inspect_state` | `Dict[str, Any]` |
| 8 | `GET /api/v1/entities` | `get_entities` | `EntityPageResponse` (from schemas.py) |
| 9 | `GET /api/v1/entities/{entity_id}` | `get_entity` | `Optional[EntityDetailResponse]` (from schemas.py) |
| 10 | `POST /api/v1/control/pause` | `pause_sim` | `Dict[str, Any]` |
| 11 | `POST /api/v1/control/resume` | `resume_sim` | `Dict[str, Any]` |
| 12 | `POST /api/v1/test/publish_event` | `publish_test_event` | `Dict[str, Any]` |
| 13 | `GET /api/v1/observability/live/health` | `get_live_health` | `Dict[str, Any]` |
| 14 | `GET /api/v1/observability/live/stream-health` | `get_stream_health` | `Dict[str, Any]` |

Add import at the top of `server.py`:

```python
from src.api.schemas import WorldStateResponse, EntityPageResponse, EntityDetailResponse
```

And ensure `Dict`, `Any`, `Optional` are imported from `typing` (check existing imports first).

**Routes explicitly excluded (do not add response_model=):**

| Route # | Path | Reason |
|---------|------|--------|
| 1 | `GET /metrics` | Returns raw `Response` with Prometheus MIME type — `response_model` incompatible |
| 15 | `GET /api/v1/observability/history/runs/{run_id}/report` | Returns raw `Response(markdown)` |
| 16 | `GET /api/v1/observability/ui` | Uses `response_class=HTMLResponse` — no `response_model` needed |
| 17 | `GET /observability/ui` | Returns `RedirectResponse` |
| 18 | `GET /api/v1/observability/live/ui` | Returns `RedirectResponse` |

FastAPI will raise a 500 at response serialization time if `response_model` is added to any of these
five routes — they must remain without `response_model`.

---

### Step 6 — Update parity ledger `docs/parity_ledger/infrastructure.yaml`

**File:** `docs/parity_ledger/infrastructure.yaml`

**Read the file first** to understand current entry format (schema defined in `docs/parity_ledger/schema.json`).

Append a new entry at the bottom of the YAML list:

```yaml
  - id: INFRA-TYPE-001
    text: >
      mypy type checking gate is configured for src/ (excluding V1 modules).
      The gate runs on every PR via CI (continue-on-error on first pass).
      Response model annotations are present on all actionable inline routes in server.py.
    status: verified
    priority: P1
    v2_evidence: >
      [tool.mypy] section in pyproject.toml; make typecheck-py target in Makefile;
      mypy step in .github/workflows/test.yml; response_model= on 13 inline routes
      in src/api/server.py; src/api/schemas.py created with typed response schemas.
    test_path: make typecheck-py
    divergence_note: ""
```

**Read the schema.json** to confirm field names and required/optional fields match before writing.

---

### Step 7 — Update `docs/audits/D13_type_safety.md`

**File:** `docs/audits/D13_type_safety.md`

**Read the file first** to find the F1 section.

Update the F1 finding status from its current unresolved state to resolved. Specific changes:

- Change F1 status marker to RESOLVED (or whatever the audit doc convention uses — match existing
  resolved-finding format in the document).
- Add a resolution note under F1:
  ```
  Resolution (TCK-20260623-TYPE-CHECKER): [tool.mypy] added to pyproject.toml; make typecheck-py
  target added to Makefile; mypy step wired into CI (continue-on-error first pass).
  ```
- If F2 and F3 have separate status fields, update them to RESOLVED as well:
  - F2: `response_model=` added to 13 of 18 inline routes in server.py (5 excluded — incompatible).
  - F3: `engine_manager.py` return annotations already present; `src/api/schemas.py` created with
    typed schemas for the 4 highest-risk routes.

---

### Step 8 — Update `docs/plans/open_audit_findings_backlog.md` Section 1G

**File:** `docs/plans/open_audit_findings_backlog.md`

**Read the file first** to find Section 1G (D13 / type safety entry).

Mark Section 1G as resolved:
- Change status from open/pending to RESOLVED.
- Add resolution line: `Resolved by TCK-20260623-TYPE-CHECKER (2026-06-23).`
- Retain the original finding text (do not delete — the backlog is a historical record).
- Add a note: "mypy CI step uses continue-on-error; remove once baseline error count is documented
  in follow-up ticket."

---

### Step 9 — Run `make knowledge-index-update`

After all doc changes are complete, run:

```bash
make knowledge-index-update
```

This regenerates the knowledge search index to include the updated docs and new `src/api/schemas.py`.
Per project rule: required whenever files under `docs/` are created or modified in the same session.

Also run `graphify update .` to refresh the AST graph for the new type annotations and new file:

```bash
graphify update .
```

Per project rule: required after modifying files under `src/`.

---

## Pre-flight Checks (before starting implementation)

These reads must happen before touching any file — they anchor exact line numbers and content:

1. **Read `pyproject.toml`** — confirm `[project.optional-dependencies]` structure before adding `dev` group.
2. **Read `Makefile` lines 1–20** (`.PHONY`) and the Quality section (~lines 199–210) — confirm insertion point and tab formatting.
3. **Read `.github/workflows/test.yml`** — find exact step order in `fast` job; confirm there is no existing mypy step.
4. **Read `src/api/engine_manager.py` lines 155–210** — confirm `get_state()`, `get_full_snapshot()`,
   `get_entities_paged()`, `get_entity()` signatures and returned dict keys (to inform TypedDict fields).
5. **Read `src/api/server.py`** — confirm all 18 route decorators and their current parameter lists
   before adding `response_model=` arguments.
6. **Read `docs/parity_ledger/infrastructure.yaml`** — confirm entry format and last entry position.
7. **Read `docs/audits/D13_type_safety.md`** — confirm F1/F2/F3 status field format.
8. **Read `docs/plans/open_audit_findings_backlog.md`** — find Section 1G exact location.

---

## Scope Guards (enforced — no exceptions)

| Guard | Rule |
|-------|------|
| `make typecheck` | Do NOT rename or modify — it runs TypeScript |
| `typecheck-py` target | New target only; does not replace `typecheck` |
| mypy strict mode | Do NOT enable — `strict = false` is required on first pass |
| V1 module annotation | Do NOT annotate `src/ai/`, `src/town/`, `src/quests/`, `src/entities/`, `src/progression/` |
| Special routes | Do NOT add `response_model=` to `/metrics`, `/history/runs/{id}/report`, `/observability/ui`, `RedirectResponse` routes |
| Route behavior | Do NOT change any route's business logic — annotations only |
| CI blocking | Do NOT remove `continue-on-error: true` from the mypy CI step |

---

## Test Checkpoints

After Step 5 (route annotations):
```bash
pytest tests/api/ -v --tb=short
```
All tests must pass. A failure in `test_rest_parity.py` or `test_live_entity_inspection.py`
indicates a response shape mismatch from the new TypedDict schema — fix the schema before proceeding.

After Step 1 (mypy config):
```bash
python3 -m mypy src/ --config-file pyproject.toml
```
Must exit without a crash (exit code 0 or 1 — not 2). Exit code 2 = config or syntax error.

After Step 2 (Makefile):
```bash
make typecheck-py
```
Must invoke mypy and produce diagnostic output (not a `make: *** No rule to make target` error).

---

## Unresolved Questions

**None.** All questions from investigation.md are resolved:

| Question | Resolution |
|----------|------------|
| Python version for mypy config | `"3.11"` — matches `requires-python = ">=3.11"` in pyproject.toml |
| Makefile target name conflict | Add `typecheck-py`; leave existing `typecheck` (TypeScript) untouched |
| mypy installation in CI | Explicit `pip install mypy` step before the mypy run step |
| `src/api/schemas.py` existence | Does not exist — must create |
| Route count (18 vs 13) | 18 total decorators; 13 actionable; 5 special-case excluded |
| engine_manager.py annotation status | All 4 methods already annotated — F3 work is schema creation only |
| CI blocking concern | `continue-on-error: true` required on first pass per ticket spec |
| `get_observability_ui` `response_class=` | Correct FastAPI pattern for HTML — no change needed |

---

## Files to Change (in order)

1. `pyproject.toml` — add `[project.optional-dependencies] dev` group with mypy; add `[tool.mypy]` section
2. `Makefile` — add `typecheck-py` to `.PHONY` and Quality section
3. `.github/workflows/test.yml` — add Install mypy + Type check steps in `fast` job
4. `src/api/schemas.py` — create with `WorldStateResponse`, `EntityPageResponse`, `EntityDetailResponse`
5. `src/api/server.py` — add `response_model=` to 13 inline routes; add schemas import
6. `docs/parity_ledger/infrastructure.yaml` — append `INFRA-TYPE-001` entry
7. `docs/audits/D13_type_safety.md` — mark F1/F2/F3 resolved
8. `docs/plans/open_audit_findings_backlog.md` — mark Section 1G resolved

Post-implementation:
- `make knowledge-index-update`
- `graphify update .`
- `tickets/working_log.csv` — append entry
- `agent-monitoring/runs.jsonl` + `agent-monitoring/events.jsonl` — write monitoring entries
- Move ticket to `tickets/done/TCK-20260623-TYPE-CHECKER.md`
- Delete source from `tickets/todos/` if it originated there
