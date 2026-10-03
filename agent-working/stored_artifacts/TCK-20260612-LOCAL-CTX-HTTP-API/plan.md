# Implementation Plan — TCK-20260612-LOCAL-CTX-HTTP-API
## Local FastAPI Search Server for Agent Tool Use (`POST /api/search`)

PHASE_TS: 2026-06-12T15:09:51Z

---

## Overview

Seven ordered steps. Each step is independently verifiable. No step mutates simulation state. All work is developer tooling only.

**Acceptance criteria cross-reference** is listed per step. Steps 2–7 have an explicit verify command.

---

## Scope Guards (What NOT to Touch)

- `src/` — zero changes. No simulation code involved.
- `pyproject.toml` — **no changes**. `fastapi` and `uvicorn[standard]` are already in `[project.dependencies]` (lines 12–13). `httpx` is already in `[dev]` optional-deps (line 30). Do not add them again to `[knowledge]`.
- `tools/knowledge_search.py` — **read-only**. Import from it; never copy-paste its logic.
- `tests/tools/test_knowledge_search.py` — must remain passing, no edits.
- `tests/tools/test_validate_frontmatter.py` — must remain passing, no edits.
- `docs/parity_ledger/infrastructure.yaml` — INFRA-188 entry is written during **finalization** (separate phase), not here.
- `tools/search/` (directory) — **does not exist and must not be created**. All new files are flat in `tools/`.

---

## Dependency Map

```
Step 1 (pyproject.toml audit — no-op) → informational only
Step 2 (tools/search_server.py) → depends on Step 1 confirmation
Step 3 (tools/search/Dockerfile) → depends on Step 2 (image wraps the server)
Step 4 (tools/search/docker-compose.yml) → depends on Step 3 (compose references Dockerfile)
Step 5 (Makefile targets) → depends on Steps 2 and 4
Step 6 (CLAUDE.md update) → depends on Step 2 (references the server and its port)
Step 7 (tests/tools/test_search_server.py) → depends on Step 2 (tests the FastAPI app)
```

Steps 3 and 4 are sequentially dependent on each other; Steps 5, 6, and 7 are independent of each other (all depend on Step 2 only).

---

## Step 1 — pyproject.toml Audit (NO CHANGES)

**Purpose:** Explicitly confirm no dependency changes are needed and document the finding so no future agent re-adds these deps.

**Action:** Read-only verification. Write the finding as an `## Implementation Notes` entry in the ticket.

**Finding to record:**
- `fastapi>=0.115.0` is at `pyproject.toml:12` — already in `[project.dependencies]`
- `uvicorn[standard]>=0.30.0` is at `pyproject.toml:13` — already in `[project.dependencies]`
- `httpx>=0.27.0` is at `pyproject.toml:30` — already in `[dev]` optional-deps (used by TestClient)
- `sentence-transformers`, `sqlite-vec`, `rank-bm25` are in `[knowledge]` optional-deps — complete

**Files changed:** none.

**Verify:** `grep -E "fastapi|uvicorn" pyproject.toml` returns two hits in `[project.dependencies]`.

**AC mapped:** N/A (enables AC for all other steps by confirming environment).

---

## Step 2 — Create `tools/search_server.py`

**Purpose:** The primary deliverable. A FastAPI app on port 8765 exposing `POST /api/search` and `GET /api/health`, importing all retrieval logic from `knowledge_search.py` via `importlib`.

**File to create:** `/home/vboxuser/Work/rpg-based-simulation/tools/search_server.py`

### 2.1 Module-level import of knowledge_search

Use the `importlib.util` pattern established in `tests/tools/test_knowledge_search.py:35-43` (not `sys.path.insert`):

```python
import importlib.util
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_KS_PATH = _REPO_ROOT / "tools" / "knowledge_search.py"
_spec = importlib.util.spec_from_file_location("knowledge_search", _KS_PATH)
_ks = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ks)
```

Symbols imported from `_ks`:
- `_DEFAULT_DB` (Path constant — resolve to absolute using `_REPO_ROOT`)
- `_MODEL_NAME` (str)
- `_tokenize(text) -> list[str]`
- `_serialize_f32(vector) -> bytes`
- `_load_bm25(bm25_path) -> tuple[BM25Okapi|None, list[str]]`
- `_hybrid_score(semantic, keyword, title_boost, heading_boost, code_boost) -> float`
- `_compute_boosts(query_tokens, doc_id, heading, text) -> tuple[float, float, float]`

The server must NOT call `_ks.cmd_query()` — that function writes to stdout, not data structures.

### 2.2 Constants

```python
_PORT = 8765
_INDEX_DIR = (_REPO_ROOT / "knowledge-index").resolve()
_DB_PATH = _INDEX_DIR / "knowledge.db"
_BM25_PATH = _INDEX_DIR / "bm25.pkl"
```

### 2.3 Pydantic models

```python
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=8, ge=1, le=100)
    filters: dict[str, str] = Field(default_factory=dict)
    include_text: bool = False

class SearchResult(BaseModel):
    doc_id: str
    title: str
    heading: str
    source_path: str
    section: str
    score: float
    semantic_score: float
    keyword_score: float
    excerpt: str
    text: Optional[str] = None  # excluded from response when None via exclude_none=True

class SearchResponse(BaseModel):
    query: str
    top_k: int
    results: list[SearchResult]
```

**`title` derivation rule:** take `doc_id` stem after the last `/` (e.g. `mechanics/02_combat_laws` → `02_combat_laws`), strip leading `NN_` numbering prefix, replace remaining underscores with spaces, title-case result. Example: `02_combat_laws` → `Combat Laws`, `authoritative_pipeline` → `Authoritative Pipeline`.

### 2.4 App-level state (module-level singleton)

```python
@dataclass
class _AppState:
    model: SentenceTransformer
    conn: sqlite3.Connection
    bm25: BM25Okapi | None
    bm25_ids: list[str]
    doc_count: int
    chunk_count: int
    index_version: str  # ISO8601 mtime of knowledge.db

_APP_STATE: _AppState | None = None
```

The module-level variable `_APP_STATE` is the only mutable state. Tests patch this directly.

### 2.5 Lifespan context manager (FastAPI startup/shutdown)

Use `@asynccontextmanager` lifespan pattern (NOT deprecated `@app.on_event`):

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _APP_STATE
    # --- startup ---
    if not _DB_PATH.exists() or not _BM25_PATH.exists():
        print(
            f"ERROR: knowledge index not found — run make knowledge-index first\n"
            f"  Expected: {_DB_PATH}",
            file=sys.stderr,
        )
        raise RuntimeError("knowledge index not found — run make knowledge-index first")
    # load model, open DB, load BM25, count docs/chunks, set index_version
    # print startup banner to stdout: port, chunk count, model name
    _APP_STATE = _AppState(...)
    yield
    # --- shutdown ---
    if _APP_STATE and _APP_STATE.conn:
        _APP_STATE.conn.close()
```

### 2.6 CORS middleware

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8765",
        "http://127.0.0.1",
        "http://127.0.0.1:8765",
        "null",  # file:// origins used by some agent tools
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
```

### 2.7 GET /api/health

Returns `_AppState` metadata. Response is a plain dict (no response model needed):

```json
{
  "status": "ok",
  "index_version": "<mtime of knowledge.db as ISO8601>",
  "documents": <int>,
  "chunks": <int>,
  "model": "<_MODEL_NAME>"
}
```

### 2.8 POST /api/search

Logic (mirrors `cmd_query()` at `knowledge_search.py:673–797` using imported primitives, not subprocess):

1. Validate request (Pydantic handles this).
2. Extract `mode = request.filters.get("mode", "hybrid")` and `section = request.filters.get("section")`.
3. Encode query with `_APP_STATE.model.encode(request.query)` → 384-dim vector.
4. Query `knowledge_vec` via sqlite-vec `knn_search` for top-K candidates (vector path).
5. If mode is `keyword` or `hybrid`: run BM25 scoring via `_APP_STATE.bm25.get_scores(_ks._tokenize(request.query))`.
6. Merge scores via `_ks._hybrid_score()` and `_ks._compute_boosts()`.
7. Apply `section` filter: if set, keep only rows where `section == request.filters["section"]`.
8. Sort by final score descending, take `request.top_k`.
9. Build `SearchResult` objects:
   - `doc_id`: from `knowledge_docs.doc_id`
   - `title`: derived from `doc_id` stem (rule at §2.3 above)
   - `heading`: from `knowledge_docs.heading`
   - `source_path`: from `knowledge_docs.path`
   - `section`: from `knowledge_docs.section`
   - `score`, `semantic_score`, `keyword_score`: from merged scoring
   - `excerpt`: `knowledge_docs.text[:200]`
   - `text`: `knowledge_docs.text` if `request.include_text` else `None`
10. Return `SearchResponse(query=..., top_k=request.top_k, results=...)` with `response_model_exclude_none=True` on the route.

Response route decorator:

```python
@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest, response: Response):
    ...
    return JSONResponse(content=response_obj.model_dump(exclude_none=True))
```

### 2.9 Startup banner

Print to stdout inside the lifespan startup block:

```
[search-server] Listening on http://localhost:8765
[search-server] Index: knowledge-index/knowledge.db (N chunks across M docs)
[search-server] Model: all-MiniLM-L6-v2
[search-server] Docs: http://localhost:8765/docs
```

### 2.10 Entry point

At the bottom of the file for direct execution:

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("tools.search_server:app", host="127.0.0.1", port=_PORT, reload=False)
```

**Files changed:** `tools/search_server.py` (new)

**Verify:**
```bash
# With knowledge-index/ present:
python3 -c "from tools import search_server" 2>&1
# Should import without error (model loading is deferred to lifespan)

# Without knowledge-index/:
python3 -c "
import asyncio, contextlib
# Only tests that lifespan raises — full test is in T-MISSING-01
"
```

**AC mapped:**
- "make search-server starts the server without error when knowledge-index/ exists"
- "curl POST returns valid JSON with 5 results"
- "curl GET /api/health returns {status: ok, ...}"
- "section filter returns only matching source_path"
- "Server prints startup message including port, chunk count, model name"
- "If knowledge-index/ does not exist, server exits with actionable error"
- "CORS rejects non-localhost origins"
- "include_text: true/false behavior"
- "FastAPI docs available at /docs" (auto-generated)

---

## Step 3 — Create `tools/search/Dockerfile`

**Purpose:** Containerized packaging for the search server. Enables `make search-server` (Docker path) without requiring the host Python environment to have `[knowledge]` deps installed.

**File to create:** `/home/vboxuser/Work/rpg-based-simulation/tools/search/Dockerfile`

Note: `tools/search/` directory must be created first (`mkdir -p tools/search/`).

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Python deps
RUN pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.30.0" \
    "pydantic>=2.0.0" \
    "sentence-transformers>=2.7.0" \
    "sqlite-vec>=0.1.1" \
    "rank-bm25>=0.2.2"

# Pre-download the embedding model (baked into image layer, avoids runtime download)
RUN python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application code (only the tools needed for the server)
COPY tools/knowledge_search.py tools/knowledge_search.py
COPY tools/search_server.py tools/search_server.py

EXPOSE 8765

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8765/api/health')" || exit 1

CMD ["uvicorn", "tools.search_server:app", "--host", "0.0.0.0", "--port", "8765"]
```

**Files changed:** `tools/search/Dockerfile` (new)

**Verify:** `docker build -f tools/search/Dockerfile -t rpg-search-server:local .` (manual, not CI).

**AC mapped:** Enables containerized `make search-server` path.

---

## Step 4 — Create `tools/search/docker-compose.yml`

**Purpose:** Defines the Docker Compose service for one-command `make search-server` startup.

**File to create:** `/home/vboxuser/Work/rpg-based-simulation/tools/search/docker-compose.yml`

```yaml
version: "3.9"

services:
  search-server:
    build:
      context: ../..
      dockerfile: tools/search/Dockerfile
    image: rpg-search-server:local
    container_name: rpg-search-server
    ports:
      - "127.0.0.1:8765:8765"
    volumes:
      - ../../knowledge-index:/app/knowledge-index:ro
    restart: unless-stopped
    environment:
      - PYTHONUNBUFFERED=1
    healthcheck:
      test: ["CMD", "python3", "-c",
             "import urllib.request; urllib.request.urlopen('http://localhost:8765/api/health')"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 10s
```

Key design decisions:
- `knowledge-index` volume is **read-only** (`:ro`). The container never writes to the index.
- Port binding is `127.0.0.1:8765:8765` — restricts to loopback only, not exposed on LAN.
- `restart: unless-stopped` — survives Docker daemon restarts but respects explicit `make search-server-stop`.

**Files changed:** `tools/search/docker-compose.yml` (new)

**Verify:** `docker compose -f tools/search/docker-compose.yml config` (validates YAML structure).

**AC mapped:** Enables `make search-server` Docker flow; `knowledge-index` mounted read-only.

---

## Step 5 — Add Makefile Targets

**Purpose:** Expose `search-server`, `search-server-stop`, `search-server-logs`, and `search-server-fallback` targets in the `# ── Knowledge Search` section.

**File changed:** `/home/vboxuser/Work/rpg-based-simulation/Makefile`

**Insertion point:** After line 166 (the `knowledge-index:` target block ends at line 166), before the `# ── Cleanup` comment at line 168.

**Insert the following block between lines 166 and 168:**

```makefile

search-server: ## Start local knowledge search server on :8765 (docker)
	docker compose -f tools/search/docker-compose.yml up -d --build
	@echo "[search-server] Server starting on http://localhost:8765 (check logs: make search-server-logs)"

search-server-stop: ## Stop local knowledge search server
	docker compose -f tools/search/docker-compose.yml down

search-server-logs: ## Tail logs from local knowledge search server
	docker compose -f tools/search/docker-compose.yml logs -f

search-server-fallback: ## FALLBACK ONLY — start search server directly via uvicorn (no Docker)
	@echo "[search-server] Fallback mode: uvicorn direct (requires pip install -e '.[knowledge]')"
	uvicorn tools.search_server:app --host 127.0.0.1 --port 8765 --reload
```

Note: `search-server-fallback` is labeled "FALLBACK ONLY" in both the help comment and the echo message to prevent it from being used as the primary path.

**Files changed:** `Makefile`

**Verify:**
```bash
make -n search-server          # dry-run shows docker compose command
make -n search-server-stop     # dry-run shows docker compose down
grep "search-server" Makefile  # confirms all 4 targets present
grep "8765" Makefile           # confirms port constant
```

**AC mapped:**
- "`make search-server` starts the server without error when `knowledge-index/` exists"

---

## Step 6 — Update CLAUDE.md Proactive Tool Use Table

**Purpose:** Register the search server as an agent proactive tool so future agents know to call it before answering project-specific architecture or mechanics questions.

**File changed:** `/home/vboxuser/Work/rpg-based-simulation/CLAUDE.md`

**Insertion point:** Inside the `### Always auto-invoke` table (lines 293–302). Append a new row at the bottom of the table body, before the empty line that closes the table.

**Row to add:**

```markdown
| Port 8765 reachable (`curl -s http://localhost:8765/api/health` returns `ok`) + user asks project-specific mechanics or architecture question | `POST http://localhost:8765/api/search` with the question as `query` before grep or file-search. Fallback when server is not running: `python3 tools/knowledge_search.py query "<q>" --top-k 5` |
```

**Scope guard:** Edit must stay within the `### Always auto-invoke` table. Do not add rows to the `### Require explicit user opt-in` section. Do not create a new section.

**Files changed:** `CLAUDE.md`

**Verify:**
```bash
grep -n "8765\|search_server\|localhost:8765" CLAUDE.md
# Must return at least one hit inside the ## Proactive Tool Use section
grep -n "Always auto-invoke" CLAUDE.md
# Then confirm the new row is between that line and the next blank line after the table
```

**AC mapped:**
- "Add tool-use entry to CLAUDE.md under Proactive Tool Use → Always auto-invoke"

---

## Step 7 — Create `tests/tools/test_search_server.py`

**Purpose:** FastAPI `TestClient` tests covering all ACs. Tests must run without a real `knowledge-index/` directory by patching `_APP_STATE` at the module level.

**File to create:** `/home/vboxuser/Work/rpg-based-simulation/tests/tools/test_search_server.py`

### 7.1 Stub strategy

The fixture `fake_client` must:
1. Import `search_server` module (using same `importlib` approach used in the module itself).
2. Build a deterministic `_AppState` object with:
   - `model`: a mock returning a fixed 384-dim zero vector on `.encode()`
   - `conn`: an in-memory SQLite DB with `knowledge_docs` table populated with ≥5 synthetic rows spanning `mechanics/`, `engine/`, `core/` sections
   - `bm25`: a real `BM25Okapi` instance built from the synthetic corpus tokens (or a mock returning fixed scores)
   - `bm25_ids`: list of chunk IDs matching the synthetic rows
   - `doc_count: 3`, `chunk_count: 5`
   - `index_version: "2026-06-12T00:00:00Z"`
3. Monkeypatch `search_server._APP_STATE` to this fake state.
4. Return `TestClient(search_server.app)`.

The fixture also patches the lifespan check so the app does not attempt to open real files at startup.

### 7.2 Test file structure

```
tests/tools/test_search_server.py
  imports + importlib load of search_server
  fixtures:
    - fake_client (module-scope)
    - missing_index_app (for T-MISSING-01)
  test groups:
    - Group 1: Health (T-HEALTH-01, T-HEALTH-02, T-HEALTH-03)
    - Group 2: Search normal flow (T-SEARCH-01 through T-SEARCH-07)
    - Group 3: Section filter (T-FILTER-01, T-FILTER-02, T-FILTER-03)
    - Group 4: Search mode (T-MODE-01, T-MODE-02, T-MODE-03)
    - Group 5: Input validation (T-VALIDATE-01, T-VALIDATE-02, T-VALIDATE-03)
    - Group 6: Missing index fast-fail (T-MISSING-01)
    - Group 7: CORS (T-CORS-01, T-CORS-02)
    - Group 8: Anti-drift guards (T-DRIFT-01 through T-DRIFT-05)
```

Full test list is specified in the test plan (see `staging_artifacts/TCK-20260612-LOCAL-CTX-HTTP-API/test_plan.md §2.2`).

### 7.3 Key implementation notes for tests

- **T-MISSING-01**: Use a fresh app instance with lifespan patched to point at a nonexistent path. Catch `RuntimeError` or `SystemExit` from the lifespan startup. Do NOT use the shared `fake_client` fixture.
- **T-DRIFT-01**: Use `is` identity check — `search_server._ks._hybrid_score is <imported from knowledge_search>`. Both should resolve to the same object since `_ks` is the loaded module.
- **T-CORS-02**: Send an `OPTIONS` request with `Origin: https://external-site.com`. Assert the response does NOT include `Access-Control-Allow-Origin: https://external-site.com`. Note: Starlette's CORSMiddleware returns the `Origin` value only if it matches an allowed origin; otherwise the header is absent.
- **T-SEARCH-04**: Assert `"text" not in result` (key absent) because `exclude_none=True` removes `None` values from JSON serialization.

**Files changed:** `tests/tools/test_search_server.py` (new)

**Verify:**
```bash
pytest tests/tools/test_search_server.py -v --tb=short
pytest tests/tools/ -v --tb=short  # regression: existing tests still pass
```

**AC mapped:** All ACs verified via test assertions (see test plan for full mapping).

---

## Acceptance Criteria Mapping

| AC | Step(s) |
|---|---|
| `make search-server` starts without error | Steps 2, 3, 4, 5 |
| `curl POST /api/search` returns 5 results with required fields | Step 2 |
| `curl GET /api/health` returns `{status: ok, ...}` with correct chunk count | Step 2 |
| `section` filter restricts results to matching `source_path` prefix | Step 2 |
| Server prints startup message (port, chunk count, model name) | Step 2 |
| Missing `knowledge-index/` causes immediate exit with actionable error | Step 2 |
| CORS rejects non-localhost origins | Step 2 |
| `include_text: true` includes full chunk text; `false` omits it | Step 2 |
| FastAPI docs available at `/docs` | Step 2 (automatic from FastAPI) |
| Tests cover all ACs without live DB | Step 7 |
| CLAUDE.md proactive tool entry present | Step 6 |
| Containerized start via docker-compose | Steps 3, 4, 5 |
| `make search-server-stop` and `search-server-logs` targets | Step 5 |
| Fallback target labeled and available | Step 5 |

---

## No Unresolved Questions

All open questions from the investigation have been resolved as implementation decisions in this plan:

| Former question | Resolution |
|---|---|
| Import strategy for `knowledge_search.py` | `importlib.util.spec_from_file_location` pattern (§2.1) |
| `title` derivation from `doc_id` | Strip `NN_` prefix, replace underscores, title-case (§2.3) |
| `include_text=False` field absence | `Optional[str] = None` + `exclude_none=True` on response (§2.3, §2.8) |
| Lifespan vs. `on_event` | `@asynccontextmanager` lifespan (§2.5) |
| Missing index behavior | `RuntimeError` in lifespan startup, print to stderr (§2.5) |
| CORS localhost variants | Four origins + `"null"` (§2.6) |
| Port binding scope | `127.0.0.1:8765:8765` in docker-compose (Step 4) |
| `make search-server` primary vs. fallback | Docker compose is primary; uvicorn direct is labeled fallback (Step 5) |
| Test stub strategy | Monkeypatch `_APP_STATE`, in-memory SQLite, mock model (§7.1) |
| `pyproject.toml` changes | None needed — confirmed in Step 1 |
