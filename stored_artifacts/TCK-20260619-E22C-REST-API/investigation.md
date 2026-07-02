# Investigation — TCK-20260619-E22C-REST-API

**Ticket:** Epic 2.2C — REST API for decision trace endpoints
**Phase:** Investigate
**Date:** 2026-06-20

---

## Current Behavior

The decision-trace pipeline (E22A/E22B) already writes and indexes trace data. No REST surface exists yet — this ticket creates it.

### Key source file:line references

| Class / Symbol | File | Lines |
|---|---|---|
| `DecisionTraceIndex.__init__` | `src/observability/cognition/tick_index.py:30-33` | Takes `run_dir: str`; derives `decision_trace.jsonl` and `decision_trace_index.json` paths |
| `DecisionTraceIndex.lookup(tick)` | `src/observability/cognition/tick_index.py:92-119` | Returns `List[dict]` for a tick; returns `[]` if tick absent; O(1) seek via sidecar |
| `sanitize_id` | `src/observability/reporting/history_query.py:13-20` | Regex `^[a-zA-Z0-9_\-]+$`; raises `ValueError` on mismatch — maps to HTTP 400 |
| `RunArtifactRepository.__init__` | `src/observability/reporting/artifact_repository.py:37` | `base_dir` defaults to `"data/runs"` (resolved to abs path) |
| `RunArtifactRepository.resolve_path` | `src/observability/reporting/artifact_repository.py:59-84` | Returns `os.path.join(base_dir, run_id, filename)` — `decision_trace.jsonl` is NOT in the key dict; route must build path directly |
| `StatePresenter` (presenter pattern) | `src/api/presenters/state_presenter.py` | Static methods; returns shaped dicts; no raw domain objects |
| `behavior.py` router pattern | `src/api/routes/behavior.py:1-11` | `router = APIRouter(prefix="...", tags=[...])`, `sanitize_id` imported from `history_query` |
| `test_cognition_history_api.py` | `tests/api/test_cognition_history_api.py:1-30` | `@pytest.mark.anyio`, direct handler import, `patch("src.api.routes.<module>.<symbol>")` |

### run_dir resolution pattern

`DecisionTraceIndex` takes a raw `run_dir` string. Since `decision_trace.jsonl` is not registered in `RunArtifactRepository.resolve_path`'s key dict (keys cover only behavior/manifest artifacts), the decisions route must build the path directly:

```python
run_dir = os.path.join("data/runs", sanitize_id(run_id))
```

This matches `RunArtifactRepository.__init__` default (`base_dir = "data/runs"`). The route does NOT need to import `RunArtifactRepository` — a plain `os.path.join` is sufficient and consistent with how `DecisionTraceIndex.__init__` itself constructs internal paths.

### sanitize_id contract

`sanitize_id` raises `ValueError` (not `HTTPException`). Routes must catch `ValueError` and re-raise as `HTTPException(status_code=400)`. This is the established pattern (confirmed in `history.py` and `behavior.py`).

### Missing-file / empty-tick guards

`DecisionTraceIndex.lookup(tick)` returns `[]` when the tick is absent — not an error. Routes must distinguish:
- `run_dir` does not exist → 404
- tick absent from index → 200 with empty list (not 404)
- `decision_trace.jsonl` absent → `lookup()` returns `[]` silently (index load falls through); route should guard `os.path.exists(run_dir)` before constructing index

---

## Mechanics / Engine Constraints

- **No raw domain models from APIs** (Architecture Rule, Hard Rules). All three endpoints must return shaped read models via `src/api/presenters/decisions.py`. Raw `DecisionTraceIndex` dicts must never be returned directly.
- **INFRA-210** (parity ledger) mandates that no API route imports `AuthoritativeState` or `EntityState` outside `TYPE_CHECKING`. The decisions presenter must use only plain dicts and primitives — no domain entity imports.
- `DecisionTraceIndex` is read-only from the API perspective. The route must never call `append_entry()` or `rebuild()`.

---

## Parity Ledger Overlap

| ID | Text summary | Status | Relation to E22C |
|---|---|---|---|
| INFRA-210 | All API read paths shaped through presenters; no raw domain model exposure | verified | Governs decisions presenter — shaped dicts only |
| INFRA-211 | Decision trace writer writes 8-field score breakdown per entity | verified | Defines the data shape the API will surface |
| INFRA-212 | Tick-index sidecar enables O(1) lookup | verified | Direct dependency — decisions route instantiates `DecisionTraceIndex` |
| **INFRA-213** | *(to be added)* REST endpoints for decision trace: single-tick, range, summary histogram | — | **New entry to create in `docs/parity_ledger/infrastructure.yaml`** |

INFRA-213 must be added in the same session as implementation. Its `test_path` will be `tests/api/test_decision_api.py`. Status starts as `verified` once tests pass.

---

## Prior Work

| Artifact | Location | Relation |
|---|---|---|
| E22A implementation | `stored_artifacts/TCK-20260619-E22A-DECISION-TRACE/` | Wrote `DecisionTraceWriter`, `OBS_DECISION_TRACE` config, phase integration |
| E22B implementation | `stored_artifacts/TCK-20260619-E22B-TICK-INDEX/` (expected) | Wrote `DecisionTraceIndex`, sidecar lifecycle, `test_tick_index_o1_lookup` |
| Presenter pattern | `src/api/presenters/state_presenter.py` | Template for `decisions.py` presenter — static methods, shaped dicts |
| Behavior route pattern | `src/api/routes/behavior.py` | Template for `decisions.py` route — APIRouter, sanitize_id, HTTPException handling |
| Test pattern | `tests/api/test_cognition_history_api.py` | `@pytest.mark.anyio`, direct handler calls, `patch` on module-level symbols |

---

## Risks and Open Questions

### Risk 1 — run_dir resolution (RESOLVED)
`decision_trace.jsonl` is not a registered key in `RunArtifactRepository.resolve_path`. Resolution: build `run_dir = os.path.join("data/runs", sanitize_id(run_id))` directly in the route. This is safe and mirrors `RunArtifactRepository.__init__` default behavior.

### Risk 2 — Missing file 404 guard (MUST IMPLEMENT)
`DecisionTraceIndex.lookup()` silently returns `[]` when `decision_trace.jsonl` doesn't exist (the `_load` path checks `os.path.exists` on the index file, not the JSONL). Routes must guard:
```python
if not os.path.isdir(run_dir):
    raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
```
This guard goes before constructing `DecisionTraceIndex`.

### Risk 3 — entity_id filtering (OPEN)
`DecisionTraceIndex.lookup(tick)` returns ALL entities for a tick. The route path includes `entity_id`. The presenter must post-filter by entity_id. Confirm whether empty result after filter → 404 or 200-empty. Established pattern in history routes: 200-empty list is preferred.

### Risk 4 — Range query upper bound (OPEN)
Endpoint 2 (`/decisions/range?from=A&to=B`) requires iterating ticks A through B. `DecisionTraceIndex` has no range API — the route must loop `lookup(tick)` for each tick in range. Large ranges risk slow responses. Impose a max-range cap (e.g. 100 ticks) with HTTP 400 if exceeded.

### Risk 5 — Summary histogram shape (OPEN)
Endpoint 3 (`/decisions/summary`) is described as a histogram. The shape is unspecified in the ticket. Proposed shape: `{"entity_id": str, "total_decisions": int, "ticks_with_data": int, "top_routes": [{"route": str, "count": int}]}`. Derive from iterating all ticks in the index (exposed via `DecisionTraceIndex._index` after `_load()`). Confirm presenter shape before coding.

---

## Anti-Drift Hazards

1. **Do not expose raw `DecisionTraceIndex` dicts** — always pass through `DecisionsPresenter` static methods.
2. **Do not call `rebuild()` or `append_entry()` from the API route** — read-only path only.
3. **Do not add `decision_trace` to `RunArtifactRepository.resolve_path`** — it is not a behavior artifact; the current separation is intentional.
4. **Do not use `anyio` in tests without `@pytest.mark.anyio`** — all async test functions require the marker.
5. **INFRA-210 guard**: the test `tests/architecture/test_api_read_model_guard.py::test_no_api_route_directly_imports_authoritative_state` will fail if the decisions route imports any domain entity type outside `TYPE_CHECKING`.
