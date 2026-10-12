"""Local FastAPI search server — wraps knowledge_search.py for HTTP access on :8765."""
from __future__ import annotations

import importlib.util
import sys
import sqlite3
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Import knowledge_search from sibling file ──────────────────────────────────
# Check sys.modules first so test stubs injected before import are respected.
_TOOLS_DIR = Path(__file__).parent
_KS_PATH = _TOOLS_DIR / "knowledge_search.py"
if "knowledge_search" not in sys.modules:
    spec = importlib.util.spec_from_file_location("knowledge_search", _KS_PATH)
    _ks = importlib.util.module_from_spec(spec)
    sys.modules["knowledge_search"] = _ks
    spec.loader.exec_module(_ks)
_ks = sys.modules["knowledge_search"]

# The one ranking path, shared with tools/search_mcp.py (TCK-20261012-SEARCH-MCP-SHARED-SERVER-AND-IDLE-UNLOAD).
if "search_core" not in sys.modules:
    _core_spec = importlib.util.spec_from_file_location("search_core", _TOOLS_DIR / "search_core.py")
    _core_mod = importlib.util.module_from_spec(_core_spec)
    sys.modules["search_core"] = _core_mod
    _core_spec.loader.exec_module(_core_mod)
_core = sys.modules["search_core"]

# agent-working/.index/knowledge-index/, or the main checkout's when this checkout has none (a worktree).
_INDEX_DIR = _core.resolve_index_dir(
    _ks._DEFAULT_DB.parent, _TOOLS_DIR.resolve().parent, _core.main_checkout_root(_TOOLS_DIR)
)
_DB_PATH = _INDEX_DIR / _ks._DEFAULT_DB.name
_BM25_PATH = _INDEX_DIR / "bm25.pkl"
_MODEL_NAME: str = _ks._MODEL_NAME

# ── App state ─────────────────────────────────────────────────────────────────
@dataclass
class _AppState:
    model: object = None
    bm25: object = None
    doc_ids: list = field(default_factory=list)
    doc_count: int = 0
    chunk_count: int = 0
    ready: bool = False

_APP_STATE = _AppState()

# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # If state is already ready (e.g. injected by a test fixture), skip startup.
    if _APP_STATE.ready:
        yield
        return

    if not _INDEX_DIR.exists() or not _DB_PATH.exists():
        print(
            f"[search-server] WARNING: knowledge-index not found at {_INDEX_DIR}. "
            "Run `make knowledge-index` first. "
            "Server starting in degraded mode — all endpoints return 503."
        )
        yield
        return

    import sentence_transformers
    _APP_STATE.model = sentence_transformers.SentenceTransformer(_MODEL_NAME)
    _APP_STATE.bm25, _APP_STATE.doc_ids = _ks._load_bm25(_BM25_PATH)

    con = sqlite3.connect(str(_DB_PATH))
    row = con.execute("SELECT COUNT(*) FROM knowledge_docs").fetchone()
    _APP_STATE.chunk_count = row[0] if row else 0
    row2 = con.execute("SELECT COUNT(DISTINCT path) FROM knowledge_docs").fetchone()
    _APP_STATE.doc_count = row2[0] if row2 else 0
    con.close()

    _APP_STATE.ready = True
    print(f"[search-server] Listening on http://localhost:8765")
    print(f"[search-server] Index: agent-working/.index/knowledge-index/knowledge.db ({_APP_STATE.chunk_count} chunks across {_APP_STATE.doc_count} docs)")
    print(f"[search-server] Model: {_MODEL_NAME}")
    print(f"[search-server] Docs: http://localhost:8765/docs")
    yield
    _APP_STATE.ready = False

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="Knowledge Search API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8765",
        "http://127.0.0.1",
        "http://127.0.0.1:8765",
        "null",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# ── Request / Response models ─────────────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str
    top_k: int = 8
    filters: dict = {}
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
    text: Optional[str] = None

class SearchResponse(BaseModel):
    query: str
    top_k: int
    results: list[SearchResult]
    # Same block `search_docs` returns for an index behind the corpus: {"changed", "new", "removed"} or {"unknown": true}.
    stale: Optional[dict] = None

# ── Helper ────────────────────────────────────────────────────────────────────
_derive_title = _core.derive_title

# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    if not _APP_STATE.ready:
        raise HTTPException(status_code=503, detail="Index not loaded")
    mtime = os.path.getmtime(str(_DB_PATH))
    index_version = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "status": "ok",
        "index_version": index_version,
        "documents": _APP_STATE.doc_count,
        "chunks": _APP_STATE.chunk_count,
        "model": _MODEL_NAME,
        # Identity of the index served, so a client can tell whether this is the index it would query itself.
        "index_fingerprint": _core.index_fingerprint(_DB_PATH),
        "index_path": str(_DB_PATH),
    }

@app.post("/api/search", response_model=SearchResponse)
def search(req: SearchRequest):
    if not _APP_STATE.ready:
        raise HTTPException(status_code=503, detail="Index not loaded")
    if not req.query.strip():
        raise HTTPException(status_code=422, detail="query must not be empty")

    results = _core.rank(
        req.query,
        top_k=req.top_k,
        section=req.filters.get("section"),
        include_text=req.include_text,
        model=_APP_STATE.model,
        bm25=_APP_STATE.bm25,
        doc_ids=_APP_STATE.doc_ids,
        db_path=_DB_PATH,
        connect=sqlite3.connect,
    )
    if isinstance(results, dict):
        raise HTTPException(status_code=500, detail=f"Search error: {results.get('error', 'unknown')}")
    stale = _ks.index_staleness(_DB_PATH)
    return SearchResponse(
        query=req.query,
        top_k=req.top_k,
        results=[SearchResult(**r) for r in results],
        stale=stale if isinstance(stale, dict) else None,
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)
