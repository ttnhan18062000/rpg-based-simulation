"""Local FastAPI search server — wraps knowledge_search.py for HTTP access on :8765."""
from __future__ import annotations

import importlib.util
import re
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

_INDEX_DIR = _ks._DEFAULT_DB.parent  # knowledge-index/
_DB_PATH = _ks._DEFAULT_DB            # knowledge-index/knowledge.db
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
    print(f"[search-server] Index: knowledge-index/knowledge.db ({_APP_STATE.chunk_count} chunks across {_APP_STATE.doc_count} docs)")
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

# ── Helper ────────────────────────────────────────────────────────────────────
def _derive_title(doc_id: str) -> str:
    """Derive display title from doc_id stem, stripping leading NN_ numbering prefix."""
    stem = doc_id.split("/")[-1]
    stem = re.sub(r"^\d+_", "", stem)
    return stem.replace("_", " ").title()

def _make_excerpt(text: str, query_tokens: list[str], max_len: int = 200) -> str:
    lower = text.lower()
    best_pos = 0
    for tok in query_tokens:
        pos = lower.find(tok)
        if pos != -1:
            best_pos = max(0, pos - 40)
            break
    snippet = text[best_pos : best_pos + max_len]
    if best_pos > 0:
        snippet = "…" + snippet
    if best_pos + max_len < len(text):
        snippet = snippet + "…"
    return snippet

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
    }

@app.post("/api/search", response_model=SearchResponse)
def search(req: SearchRequest):
    if not _APP_STATE.ready:
        raise HTTPException(status_code=503, detail="Index not loaded")
    if not req.query.strip():
        raise HTTPException(status_code=422, detail="query must not be empty")

    query_tokens = _ks._tokenize(req.query)
    q_vec = _APP_STATE.model.encode(req.query).tolist()
    q_bytes = _ks._serialize_f32(q_vec)

    con = None
    rows = []
    try:
        import sqlite_vec
        con = sqlite3.connect(str(_DB_PATH))
        con.enable_load_extension(True)
        sqlite_vec.load(con)
        con.enable_load_extension(False)

        sql = """
            SELECT kd.rowid, kd.doc_id, kd.path, kd.text, kd.heading, kd.section,
                   distance
            FROM knowledge_vec kv
            JOIN knowledge_docs kd ON kd.rowid = kv.rowid
            WHERE kv.embedding MATCH ?
              AND k = ?
            ORDER BY distance
        """
        rows = con.execute(sql, (q_bytes, min(req.top_k * 4, 50))).fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {e}")
    finally:
        try:
            if con is not None:
                con.close()
        except Exception:
            pass

    # Apply filters
    section_filter = req.filters.get("section")
    if section_filter:
        rows = [r for r in rows if r[5] == section_filter]

    results = []
    for row in rows[:req.top_k]:
        rowid, doc_id, path, text, heading, section, distance = row
        sem_score = max(0.0, 1.0 - float(distance))
        kw_score = 0.0
        if _APP_STATE.bm25 is not None and query_tokens:
            scores = _APP_STATE.bm25.get_scores(query_tokens)
            try:
                idx = _APP_STATE.doc_ids.index(doc_id)
                kw_score = float(scores[idx]) / 10.0
            except ValueError:
                kw_score = 0.0
        title_boost, heading_boost, code_boost = _ks._compute_boosts(query_tokens, doc_id, heading, text)
        combined = _ks._hybrid_score(sem_score, kw_score, title_boost, heading_boost, code_boost)
        excerpt = _make_excerpt(text, query_tokens)
        results.append(SearchResult(
            doc_id=doc_id,
            title=_derive_title(doc_id),
            heading=heading or "",
            source_path=path,
            section=section or "",
            score=round(combined, 4),
            semantic_score=round(sem_score, 4),
            keyword_score=round(kw_score, 4),
            excerpt=excerpt,
            text=text if req.include_text else None,
        ))

    results.sort(key=lambda r: r.score, reverse=True)
    return SearchResponse(
        query=req.query,
        top_k=req.top_k,
        results=results,
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)
