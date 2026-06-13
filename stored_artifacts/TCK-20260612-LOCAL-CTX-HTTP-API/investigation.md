# Investigation — TCK-20260612-LOCAL-CTX-HTTP-API
## Local FastAPI Search Server for Agent Tool Use (`POST /api/search`)

PHASE_TS: 2026-06-12T15:05:32Z

---

## 1. Current Behavior

### 1.1 What exists today

`tools/knowledge_search.py` is the sole knowledge-search entry point. It is a CLI-only tool invoked via:

```
python3 tools/knowledge_search.py query "<q>" [--top-k N] [--mode hybrid|vector|keyword]
```

There is no HTTP interface. Agents that want to call the search must use a subprocess, parse tab-separated stdout, and handle missing-index conditions themselves.

The `Makefile` has a `knowledge-index:` target (line 164) that builds the index via `python3 tools/knowledge_search.py build`. There is no `search-server` target yet.

`CLAUDE.md` `## Proactive Tool Use` table (lines 289–311) has entries only for graphify tools. No entry for the HTTP search server or the CLI fallback exists yet.

### 1.2 Relevant existing code — file:line refs

| Symbol / Concern | File | Lines |
|---|---|---|
| `_DEFAULT_DB` path constant | `tools/knowledge_search.py` | 33 |
| `_MODEL_NAME` constant | `tools/knowledge_search.py` | 34 |
| `_collect_corpus()` | `tools/knowledge_search.py` | 118–198 |
| `_collect_docs_chunks()` | `tools/knowledge_search.py` | 222–433 |
| `_serialize_f32()` | `tools/knowledge_search.py` | 440–442 |
| `_load_bm25()` | `tools/knowledge_search.py` | 476–500 |
| `_hybrid_score()` | `tools/knowledge_search.py` | 503–527 |
| `_compute_boosts()` | `tools/knowledge_search.py` | 530–549 |
| `_tokenize()` | `tools/knowledge_search.py` | 449–455 |
| `cmd_query()` — full search logic | `tools/knowledge_search.py` | 673–797 |
| `cmd_query()` — sqlite-vec vector path | `tools/knowledge_search.py` | 726–768 |
| `cmd_query()` — keyword-only path | `tools/knowledge_search.py` | 769–789 |
| `cmd_query()` — output loop (tab-sep) | `tools/knowledge_search.py` | 791–796 |
| `knowledge-index:` Makefile target | `Makefile` | 164–166 |
| `## Proactive Tool Use` section | `CLAUDE.md` | 289–311 |
| `### Always auto-invoke` table | `CLAUDE.md` | 293–302 |
| `fastapi` in core deps | `pyproject.toml` | 12 |
| `uvicorn[standard]` in core deps | `pyproject.toml` | 13 |
| `knowledge` optional-deps group | `pyproject.toml` | 34–38 |
| `requirements.txt` (installed env) | `requirements.txt` | — (fastapi==0.128.4, uvicorn==0.40.0 present) |

### 1.3 Index format — knowledge-index/

The `cmd_build()` function writes two files under `knowledge-index/` (relative to the working directory, i.e. the repo root):

- `knowledge-index/knowledge.db` — SQLite database with two tables:
  - `knowledge_docs (rowid INTEGER PK, doc_id TEXT, path TEXT, text TEXT, source_type TEXT, heading TEXT, section TEXT)`
  - `knowledge_vec` — sqlite-vec virtual table, `embedding float[384]` (dim from all-MiniLM-L6-v2)
- `knowledge-index/bm25.pkl` — pickle of `(BM25Okapi, list[str])` where `list[str]` is `[doc["id"] for doc in corpus]` (parallel to DB rowids)

The `knowledge.db` rowids are assigned 0..N-1 sequentially (matching corpus order), and the BM25 row indices are the same ordering. This is the bridging invariant that `cmd_query()` relies on at line 757: `if bm25_raw is not None and rowid < len(bm25_raw)`.

### 1.4 What cmd_query() returns (wire format today)

The current output loop (lines 791–796) emits one tab-separated line per result:
```
{doc_id}\t{path}\t{heading}\t{section}\t{final:.4f}\t{semantic:.4f}\t{keyword:.4f}\t{snippet}
```
(8 fields, as implemented by TCK-20260612-LOCAL-CTX-HYBRID-SEARCH)

`search_server.py` must parse this output — or better, directly reuse the internal query logic instead of subprocess-calling the CLI. The ticket requirement is explicit: "import retrieval logic — avoid duplication".

### 1.5 Import strategy from search_server.py

`tools/` is not a Python package (no `__init__.py`). The correct import pattern (mirroring the test in `tests/tools/test_knowledge_search.py` lines 28–43) is:

```python
import importlib.util, sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent  # tools/search_server.py → repo root
_KS_PATH = _REPO_ROOT / "tools" / "knowledge_search.py"
spec = importlib.util.spec_from_file_location("knowledge_search", _KS_PATH)
_ks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_ks)
```

Alternatively — and more simply — if `search_server.py` lives at `tools/search_server.py`, it can do a direct relative import as a module by adding the repo root to `sys.path` then doing `import tools.knowledge_search as _ks` (works if tools/ is on path and there is an `__init__.py`, or via `importlib`). The safest pattern matching existing conventions is the `importlib.util` approach used in `tests/tools/test_knowledge_search.py`.

Functions to import from `knowledge_search.py` for use in `search_server.py`:
- `_DEFAULT_DB` (Path constant)
- `_MODEL_NAME` (str constant)
- `_tokenize(text) -> list[str]`
- `_serialize_f32(vector) -> bytes`
- `_load_bm25(bm25_path) -> tuple[BM25Okapi|None, list[str]]`
- `_hybrid_score(semantic, keyword, title_boost, heading_boost, code_boost) -> float`
- `_compute_boosts(query_tokens, doc_id, heading, text) -> tuple[float, float, float]`

The server must NOT call `cmd_query()` directly — it returns results via print/stdout, not as data structures. The server should replicate the query logic using the above primitives (which are pure functions with no side effects) and return structured dicts.

---

## 2. Mechanics / Engine Constraints

N/A — this is developer tooling only. No simulation state is involved, no durable world mutation, no tick-path code. The server reads the pre-built `knowledge-index/` artifacts but never writes to them.

---

## 3. Parity Ledger Overlap

**Primary file:** `docs/parity_ledger/infrastructure.yaml`

No existing INFRA-* entry covers a local HTTP knowledge search server. The closest entries are:
- `INFRA-180` (`tools/validate_frontmatter.py`) — same pattern: doc tooling, stdlib-only, `support_boundary: "Doc tooling only"`
- `INFRA-181` (Docusaurus scaffold with `make docs-serve`) — same pattern: Makefile target for a local dev server

A new entry **INFRA-188** should be added after completion:
```yaml
- id: INFRA-188
  text: >
    Local FastAPI search server (tools/search_server.py) exposes POST /api/search
    and GET /api/health on localhost:8765. Loads knowledge-index/ artifacts built
    by knowledge_search.py. Fails fast with actionable error if index missing.
    make search-server target available. CORS restricted to localhost.
  status: verified
  priority: P2
  v2_evidence: >
    tools/search_server.py + Makefile (search-server target) +
    CLAUDE.md (Proactive Tool Use table update) +
    tests/tools/test_search_server.py
  test_path: tests/tools/test_search_server.py
  support_boundary: "Developer tooling only — no simulation behavior involved."
```

This entry should be written during finalization, not during investigation.

---

## 4. Prior Work

### 4.1 TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH (DONE)
**Stored artifact:** `stored_artifacts/TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH/`

Delivered `tools/knowledge_search.py` with `build` and `query` subcommands. Established `knowledge-index/knowledge.db` (sqlite-vec) as the vector store. Added `sentence-transformers` and `sqlite-vec` to `[knowledge]` optional deps.

### 4.2 TCK-20260612-LOCAL-CTX-DOCS-CORPUS (DONE)
**Stored artifact:** `stored_artifacts/TCK-20260612-LOCAL-CTX-DOCS-CORPUS/`

Extended the corpus to include `docs/` via `_collect_docs_chunks()`. Establishes the `section` field (immediate subdirectory of `docs/`) used by the `section` filter in `POST /api/search`. The `source_path` returned in the API response maps to the `path` column in `knowledge_docs`.

### 4.3 TCK-20260612-LOCAL-CTX-HYBRID-SEARCH (DONE)
**Stored artifact:** `stored_artifacts/TCK-20260612-LOCAL-CTX-HYBRID-SEARCH/`
**Investigation note (§4, Output Format Change):** Output format is now 8 tab-separated fields.

Delivered:
- `_tokenize()`, `_build_bm25_index()`, `_load_bm25()` in `knowledge_search.py`
- `_hybrid_score()`, `_compute_boosts()` in `knowledge_search.py`
- BM25 build path in `cmd_build()` writing `knowledge-index/bm25.pkl`
- Hybrid/keyword/vector mode routing in `cmd_query()`
- `rank-bm25>=0.2.2` added to `[knowledge]` optional deps

This ticket (HTTP-API) is a direct consumer of all of the above. **The dependency chain is fully satisfied.**

### 4.4 No tools/search/ directory exists
`tools/search/` does NOT exist. The new server file goes directly at `tools/search_server.py` — flat alongside `tools/knowledge_search.py`.

---

## 5. Risks and Open Questions

### 5.1 fastapi/uvicorn dependency status
**Resolved:** `fastapi>=0.115.0` and `uvicorn[standard]>=0.30.0` are already in `[project.dependencies]` in `pyproject.toml` (lines 12–13). They are also present in `requirements.txt` (`fastapi==0.128.4`, `uvicorn==0.40.0`). **No new dependency declarations needed.**

### 5.2 Port 8765 conflict
Port 8765 is explicitly chosen to avoid conflicts with ports 3000 (Docusaurus), 8000 (backend engine), 5173 (frontend dev server). No evidence of any other process on this port in the codebase. Acceptable.

### 5.3 CORS scope
The ticket requires CORS restricted to `localhost` origins. FastAPI/Starlette `CORSMiddleware` accepts an `allow_origins` list. The correct values to cover all localhost variants: `["http://localhost", "http://localhost:8765", "http://127.0.0.1", "http://127.0.0.1:8765"]` plus `null` (for file:// origins used by some agent tools). Be conservative — restrict to HTTP localhost only.

### 5.4 Model loading at startup vs. first request
The ticket states "model is loaded once at startup". This means the `SentenceTransformer` initialization goes in a FastAPI `@app.on_event("startup")` or `lifespan` context manager, not on the first request. The `lifespan` pattern is preferred in FastAPI >= 0.93 (replaces deprecated `on_event`). However, `on_event` still works in 0.128.4 — either is fine, `lifespan` is the forward-compatible choice.

### 5.5 Missing index fast-fail behavior
The ticket requires: if `knowledge-index/` does not exist, server exits immediately with: `"knowledge index not found — run make knowledge-index first"`. This should happen at import time (module-level startup check) — not at first request — so the uvicorn worker fails before binding. The practical approach: check inside the lifespan/startup hook and call `sys.exit(1)` with the error message printed to stderr.

### 5.6 `include_text` field default
Ticket specifies `include_text: boolean, default false`. When false, the `text` key should be absent from result objects (not null). This is a schema design decision: Pydantic `Optional[str] = None` with response exclusion via `exclude_none=True` is the cleanest approach.

### 5.7 `doc_id` in response vs. `id` in knowledge_docs
The `knowledge_docs` table stores `doc_id` (document-level identifier, e.g. `mechanics/02_combat_laws`) and the chunk-level `id` (e.g. `mechanics/02_combat_laws#damage-formula-001`) is stored in the `doc_id` column at index build time (see `_collect_docs_chunks()` line 292: `"id": f"{doc_id}#body-000"`). Clarification: the `knowledge_docs.doc_id` column actually stores the chunk-level `id` from the corpus dict (confirmed by `cmd_build()` line 638). The API response field `doc_id` should use this value directly.

### 5.8 `title` field in response
The ticket response schema includes `"title": "Combat Laws"`. The `knowledge_docs` table does not have a `title` column — the closest is `doc_id` (e.g. `mechanics/02_combat_laws`) from which a human-readable title can be derived by taking the stem after the last `/` and reformatting. Alternatively, the `title` can be derived from the heading or left as the `doc_id` stem. This is an implementation decision: derive `title` from the last path component of `doc_id`, replacing underscores with spaces and stripping leading numbering (e.g. `02_combat_laws` → `Combat Laws`). Document this decision in `## Implementation Notes` of the ticket.

---

## 6. Anti-Drift Hazards

1. **Do not duplicate search logic.** `search_server.py` must import and call private functions from `knowledge_search.py`, not copy them. Any future fix to scoring or tokenization must only require changes in `knowledge_search.py`.

2. **Index path must match `_DEFAULT_DB`.** The server must use `knowledge_search._DEFAULT_DB` (resolved relative to repo root, i.e. `Path("knowledge-index/knowledge.db")`), not a hardcoded string. The server should resolve this to an absolute path at startup using the repo root derived from `__file__`.

3. **`bm25.pkl` path must be derived from `_DEFAULT_DB.parent / "bm25.pkl"`,** consistent with `cmd_build()` line 651 and `cmd_query()` line 708.

4. **CLAUDE.md edit must stay within the `### Always auto-invoke` table** (lines 293–302). Do not add entries to the `### Require explicit user opt-in` section or outside the table.

5. **The `make search-server` target must not conflict with `make knowledge-index`.** They are independent targets. The `search-server` target should be under the `# ── Knowledge Search` section in the Makefile (after line 166).

6. **fastapi and uvicorn are already core deps** — do not add them again to `[knowledge]` optional-deps. Only add to `pyproject.toml` if something genuinely new is needed (nothing is for this ticket).

7. **Tests must use `httpx` + FastAPI `TestClient`** (not `requests`, not live subprocess). `httpx>=0.27.0` is already in `[dev]` optional-deps (`pyproject.toml` line 30). `TestClient` is re-exported from `fastapi.testclient`.

---

## 7. Key Findings Summary

| Finding | Detail |
|---|---|
| `tools/search/` directory | Does NOT exist. New file is `tools/search_server.py` (flat) |
| fastapi/uvicorn | Already in core `[project.dependencies]` — no new dep needed |
| `knowledge` optional group | Already has `sentence-transformers`, `sqlite-vec`, `rank-bm25` — complete |
| Import path for knowledge_search | Use `importlib.util.spec_from_file_location` pattern from `tests/tools/test_knowledge_search.py:35-43` |
| Functions to import | `_DEFAULT_DB`, `_MODEL_NAME`, `_tokenize`, `_serialize_f32`, `_load_bm25`, `_hybrid_score`, `_compute_boosts` |
| Index format | `knowledge-index/knowledge.db` (sqlite-vec) + `knowledge-index/bm25.pkl` (pickle of `(BM25Okapi, list[str])`) |
| DB schema | `knowledge_docs(rowid, doc_id, path, text, source_type, heading, section)` + `knowledge_vec(rowid, embedding float[384])` |
| Makefile insertion point | After line 166 (the `knowledge-index:` target block), before the `# ── Cleanup` section |
| CLAUDE.md insertion point | Inside `### Always auto-invoke` table, lines 293–302 (append new row before the table closing line) |
| Existing tests file | `tests/tools/test_knowledge_search.py` — must remain passing; no changes needed |
| New test file location | `tests/tools/test_search_server.py` (new) |
| Parity ledger | Add INFRA-188 to `docs/parity_ledger/infrastructure.yaml` at finalization |
