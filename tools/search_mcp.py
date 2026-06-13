"""MCP server for agent-native context search — exposes search_docs and search_health tools.

Transport: stdio (Claude Code spawns this as a subprocess).
Requires: pip install mcp  (see pyproject.toml [search-mcp] optional deps)

Usage (Claude Code registers via .claude/settings.json):
    python3 tools/search_mcp.py

Smoke-test mode (no MCP client needed):
    echo '{"query": "damage formula", "top_k": 3}' | python3 tools/search_mcp.py --test
"""
from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ── Import knowledge_search from sibling file ─────────────────────────────────
_TOOLS_DIR = Path(__file__).parent
_KS_PATH = _TOOLS_DIR / "knowledge_search.py"

if "knowledge_search" not in sys.modules:
    spec = importlib.util.spec_from_file_location("knowledge_search", _KS_PATH)
    _ks = importlib.util.module_from_spec(spec)
    sys.modules["knowledge_search"] = _ks
    spec.loader.exec_module(_ks)
_ks = sys.modules["knowledge_search"]

_INDEX_DIR = _ks._DEFAULT_DB.parent
_DB_PATH = _ks._DEFAULT_DB
_BM25_PATH = _INDEX_DIR / "bm25.pkl"
_MODEL_NAME: str = _ks._MODEL_NAME


# ── Lazy-loaded state (model loaded on first search_docs call) ────────────────
@dataclass
class _State:
    model: object = None
    bm25: object = None
    doc_ids: list = field(default_factory=list)
    ready: bool = False

_STATE = _State()


def _ensure_loaded() -> bool:
    """Load model and BM25 index on first call. Returns True if ready."""
    if _STATE.ready:
        return True
    if not _DB_PATH.exists():
        return False
    try:
        from sentence_transformers import SentenceTransformer
        _STATE.model = SentenceTransformer(_MODEL_NAME)
        _STATE.bm25, _STATE.doc_ids = _ks._load_bm25(_BM25_PATH)
        _STATE.ready = True
        return True
    except Exception:
        return False


# ── Core search logic (shared by MCP tools and --test mode) ──────────────────

def _run_search(query: str, top_k: int = 8, section: str | None = None,
                mode: str = "hybrid") -> list[dict] | dict:
    """Run hybrid search and return ranked results. Returns error dict if index missing."""
    if not _ensure_loaded():
        return {"error": "index not found", "action": "run make knowledge-index"}

    if not query.strip():
        return []

    query_tokens = _ks._tokenize(query)
    try:
        q_vec = _STATE.model.encode(query).tolist()
        q_bytes = _ks._serialize_f32(q_vec)
    except Exception as exc:
        return {"error": f"embed failed: {exc}"}

    rows = []
    con = None
    try:
        import sqlite_vec
        con = sqlite3.connect(str(_DB_PATH))
        con.enable_load_extension(True)
        sqlite_vec.load(con)
        con.enable_load_extension(False)
        sql = """
            SELECT kd.rowid, kd.doc_id, kd.path, kd.text, kd.heading, kd.section, distance
            FROM knowledge_vec kv
            JOIN knowledge_docs kd ON kd.rowid = kv.rowid
            WHERE kv.embedding MATCH ?
              AND k = ?
            ORDER BY distance
        """
        rows = con.execute(sql, (q_bytes, min(top_k * 4, 50))).fetchall()
    except Exception:
        rows = []
    finally:
        if con is not None:
            try:
                con.close()
            except Exception:
                pass

    if section:
        rows = [r for r in rows if r[5] == section]

    results = []
    for row in rows[:top_k]:
        rowid, doc_id, path, text, heading, sec, distance = row
        sem_score = max(0.0, 1.0 - float(distance))
        kw_score = 0.0
        if _STATE.bm25 is not None and query_tokens:
            scores = _STATE.bm25.get_scores(query_tokens)
            try:
                idx = _STATE.doc_ids.index(doc_id)
                kw_score = float(scores[idx]) / 10.0
            except (ValueError, IndexError):
                kw_score = 0.0
        title_boost, heading_boost, code_boost = _ks._compute_boosts(query_tokens, doc_id, heading, text)
        combined = _ks._hybrid_score(sem_score, kw_score, title_boost, heading_boost, code_boost)
        excerpt = text[:200].replace("\n", " ")
        results.append({
            "doc_id": doc_id,
            "title": _derive_title(doc_id),
            "heading": heading or "",
            "source_path": path,
            "section": sec or "",
            "score": round(combined, 4),
            "semantic_score": round(sem_score, 4),
            "keyword_score": round(kw_score, 4),
            "excerpt": excerpt,
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results


def _run_health() -> dict:
    """Return index status."""
    if not _DB_PATH.exists():
        return {"status": "unavailable", "error": "index not found", "action": "run make knowledge-index"}
    try:
        mtime = os.path.getmtime(str(_DB_PATH))
        from datetime import datetime, timezone
        index_version = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con = sqlite3.connect(str(_DB_PATH))
        chunk_count = con.execute("SELECT COUNT(*) FROM knowledge_docs").fetchone()[0]
        con.close()
        return {
            "status": "ok",
            "index_version": index_version,
            "chunks": chunk_count,
            "model": _MODEL_NAME,
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def _derive_title(doc_id: str) -> str:
    import re
    stem = doc_id.split("/")[-1]
    stem = re.sub(r"^\d+_", "", stem)
    return stem.replace("_", " ").title()


# ── --test mode (smoke test without MCP client) ───────────────────────────────

def _run_test_mode() -> int:
    """Read JSON from stdin, run search, print results. Exit 0 on success."""
    raw = sys.stdin.read().strip()
    if not raw:
        print("ERROR: no input on stdin. Pipe JSON: echo '{\"query\": \"...\"}' | python3 tools/search_mcp.py --test",
              file=sys.stderr)
        return 1
    try:
        req = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
        return 1

    query = req.get("query", "")
    top_k = int(req.get("top_k", 8))
    section = req.get("section")
    mode = req.get("mode", "hybrid")

    if not query:
        print("ERROR: 'query' field required", file=sys.stderr)
        return 1

    results = _run_search(query, top_k=top_k, section=section, mode=mode)
    print(json.dumps(results, indent=2))

    if isinstance(results, dict) and "error" in results:
        return 1
    print(f"\n[search_mcp --test] {len(results)} result(s) for: {query!r}", file=sys.stderr)
    return 0


# ── MCP server (requires mcp package) ────────────────────────────────────────

def _run_mcp_server() -> int:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print(
            "ERROR: mcp package not installed.\n"
            "Run: pip install 'mcp>=1.0.0'\n"
            "Or add to pyproject.toml: pip install -e '.[search-mcp]'",
            file=sys.stderr,
        )
        return 1

    server = FastMCP("knowledge-search")

    @server.tool()
    def search_docs(
        query: str,
        top_k: int = 8,
        section: str = "",
        mode: str = "hybrid",
    ) -> list[dict] | dict:
        """
        Search project documentation, ticket history, and stored investigations
        by natural language or exact technical term.

        Returns ranked chunks with title, heading, source_path, section, score, and excerpt.
        Use this before answering any project-specific mechanics, architecture, or history question.

        Args:
            query: Natural-language or exact-term search query.
            top_k: Number of results to return (default 8).
            section: Filter to a section (e.g. "mechanics", "engine", "core", "strategy").
            mode: "hybrid" (default), "vector", or "keyword".
        """
        return _run_search(query, top_k=top_k, section=section or None, mode=mode)

    @server.tool()
    def search_health() -> dict:
        """
        Check whether the knowledge index is loaded and ready.
        Returns index version, chunk count, and model name.
        Call this if search_docs returns no results unexpectedly.
        """
        return _run_health()

    server.run()
    return 0


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--test" in sys.argv:
        sys.exit(_run_test_mode())
    sys.exit(_run_mcp_server())
