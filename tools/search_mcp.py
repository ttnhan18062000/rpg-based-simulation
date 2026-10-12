"""MCP server for agent-native context search — exposes search_docs and search_health tools.

Transport: stdio (Claude Code spawns this as a subprocess).
Requires: pip install mcp  (see pyproject.toml [search-mcp] optional deps)

Usage (Claude Code registers via .claude/settings.json):
    python3 tools/search_mcp.py

Smoke-test mode (no MCP client needed):
    echo '{"query": "damage formula", "top_k": 3}' | python3 tools/search_mcp.py --test
"""
from __future__ import annotations

import gc
import importlib.util
import json
import os
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

# Use locally cached HuggingFace models — avoids SSL cert failures on networks
# where the system Python cert bundle doesn't trust the HF CDN issuer.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# ── Import knowledge_search from sibling file ─────────────────────────────────
_TOOLS_DIR = Path(__file__).parent
_KS_PATH = _TOOLS_DIR / "knowledge_search.py"

if "knowledge_search" not in sys.modules:
    spec = importlib.util.spec_from_file_location("knowledge_search", _KS_PATH)
    _ks = importlib.util.module_from_spec(spec)
    sys.modules["knowledge_search"] = _ks
    spec.loader.exec_module(_ks)
_ks = sys.modules["knowledge_search"]

_HR_PATH = _TOOLS_DIR / "hybrid_retrieval.py"

if "hybrid_retrieval" not in sys.modules:
    spec = importlib.util.spec_from_file_location("hybrid_retrieval", _HR_PATH)
    _hr = importlib.util.module_from_spec(spec)
    sys.modules["hybrid_retrieval"] = _hr
    spec.loader.exec_module(_hr)
_hr = sys.modules["hybrid_retrieval"]



if "search_core" not in sys.modules:
    spec = importlib.util.spec_from_file_location("search_core", _TOOLS_DIR / "search_core.py")
    _core_mod = importlib.util.module_from_spec(spec)
    sys.modules["search_core"] = _core_mod
    spec.loader.exec_module(_core_mod)
_core = sys.modules["search_core"]

# The ranking, the worktree index fallback and the title rule live in search_core, shared with search_server.py.
_main_checkout_root = _core.main_checkout_root
_resolve_index_dir = _core.resolve_index_dir
_derive_title = _core.derive_title


_INDEX_DIR = _resolve_index_dir(
    _ks._DEFAULT_DB.parent, _TOOLS_DIR.resolve().parent, _main_checkout_root(_TOOLS_DIR)
)
_DB_PATH = _INDEX_DIR / _ks._DEFAULT_DB.name
_BM25_PATH = _INDEX_DIR / "bm25.pkl"
_MODEL_NAME: str = _ks._MODEL_NAME


# ── Lazy-loaded state (model loaded on first in-process search_docs call, released when idle) ──
@dataclass
class _State:
    model: object = None
    bm25: object = None
    doc_ids: list = field(default_factory=list)
    ready: bool = False

_STATE = _State()

# Guards _STATE: a search holds it while it uses the model, so the idle timer never unloads mid-query.
_LOCK = threading.RLock()

# TCK-20261012-SEARCH-MCP-SHARED-SERVER-AND-IDLE-UNLOAD: seconds without a query before the in-process model is
# released; 0 never unloads. A daemon Timer reset on every query does the unloading, because checking the idle
# time only when the next query arrives would never free memory while no query comes.
IDLE_UNLOAD_ENV = "SEARCH_MCP_IDLE_UNLOAD_S"
IDLE_UNLOAD_DEFAULT_S = 600.0
_CLOCK = time.monotonic          # injectable
_TIMER_FACTORY = threading.Timer  # injectable
_idle = {"timer": None, "last_used": 0.0}


def _idle_unload_seconds() -> float:
    raw = os.environ.get(IDLE_UNLOAD_ENV)
    if raw is None or not raw.strip():
        return IDLE_UNLOAD_DEFAULT_S
    try:
        return max(0.0, float(raw))
    except ValueError:
        return IDLE_UNLOAD_DEFAULT_S


def _release_memory() -> None:
    """Hand freed pages back to the OS. Dropping the references frees the weights (large blocks are mmap'd and unmapped at
    once), but glibc keeps freed small-block arenas, so `malloc_trim` is asked to return those too. Best effort."""
    gc.collect()
    try:
        import ctypes
        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except Exception:
        pass


def _unload() -> None:
    with _LOCK:
        _STATE.model = None
        _STATE.bm25 = None
        _STATE.doc_ids = []
        _STATE.ready = False
    _release_memory()


def _unload_if_idle() -> bool:
    """Timer callback: unload when no query arrived for the whole idle period (a query that raced the timer wins)."""
    idle = _idle_unload_seconds()
    with _LOCK:
        if not _STATE.ready or idle <= 0:
            return False
        if _CLOCK() - _idle["last_used"] < idle:
            _schedule_unload(idle - (_CLOCK() - _idle["last_used"]))
            return False
        _unload()
        return True


def _schedule_unload(delay: float) -> None:
    with _LOCK:
        if _idle["timer"] is not None:
            _idle["timer"].cancel()
        timer = _TIMER_FACTORY(delay, _unload_if_idle)
        timer.daemon = True
        _idle["timer"] = timer
        timer.start()


def _touch() -> None:
    """Record a query and (re)arm the idle timer."""
    idle = _idle_unload_seconds()
    with _LOCK:
        _idle["last_used"] = _CLOCK()
        if idle > 0 and _STATE.ready:
            _schedule_unload(idle)


def _ensure_loaded() -> bool:
    """Load model and BM25 index on first call. Returns True if ready."""
    with _LOCK:
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


# ── Shared search server (TCK-20261012-SEARCH-MCP-SHARED-SERVER-AND-IDLE-UNLOAD) ─────────────────────────────────────
# When tools/search_server.py is running on :8765 AND serves the same index file this session would query, forward to
# it: the model then lives once on the host instead of once per session. Any doubt falls back in-process, silently.
SERVER_URL_ENV = "SEARCH_SERVER_URL"
SERVER_URL_DEFAULT = "http://127.0.0.1:8765"
SHARED_OFF_ENV = "SEARCH_MCP_SHARED_SERVER"   # "off" disables the proxy
HEALTH_TIMEOUT_S = 0.5
SEARCH_TIMEOUT_S = 10.0
HEALTH_TTL_S = 15.0
_server_check = {"at": None, "usable": False}


def _server_url() -> str:
    return os.environ.get(SERVER_URL_ENV, SERVER_URL_DEFAULT).rstrip("/")


def _http_json(method: str, url: str, timeout: float, payload: dict | None = None) -> dict | None:
    """One JSON request; None on any failure (refused, timeout, non-200, bad body)."""
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - fixed http://127.0.0.1 default
            if resp.status != 200:
                return None
            body = json.loads(resp.read().decode())
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        return None
    return body if isinstance(body, dict) else None


def _shared_server_usable() -> bool:
    """True when the server answers `ok` and serves the same index file as this session. Cached for HEALTH_TTL_S."""
    if os.environ.get(SHARED_OFF_ENV, "").strip().lower() == "off":
        return False
    now = _CLOCK()
    at = _server_check["at"]
    if at is not None and now - at < HEALTH_TTL_S:
        return bool(_server_check["usable"])
    local = _core.index_fingerprint(_DB_PATH)
    health = _http_json("GET", f"{_server_url()}/api/health", HEALTH_TIMEOUT_S) if local else None
    usable = bool(health and health.get("status") == "ok" and health.get("index_fingerprint") == local)
    _server_check["at"], _server_check["usable"] = now, usable
    return usable


def _proxy_search(query: str, top_k: int, section: str | None) -> list[dict] | None:
    """Results from the shared server, or None to search in-process (also drops the cached health verdict)."""
    if not _shared_server_usable():
        return None
    body = _http_json(
        "POST", f"{_server_url()}/api/search", SEARCH_TIMEOUT_S,
        {"query": query, "top_k": top_k, "filters": {"section": section} if section else {}},
    )
    results = body.get("results") if body else None
    if not isinstance(results, list):
        _server_check["at"] = None
        return None
    return [{k: v for k, v in r.items() if k != "text"} for r in results if isinstance(r, dict)]


# ── Core search logic (shared by MCP tools and --test mode) ──────────────────

def _run_search(query: str, top_k: int = 8, section: str | None = None,
                mode: str = "hybrid", with_staleness: bool = False) -> list[dict] | dict:
    """Run hybrid search and return ranked results. Returns error dict if index missing.

    With `with_staleness` (what the `search_docs` tool passes), a stale index returns
    `{"results": [...], "stale": {"changed": n, "new": n, "removed": n}}` instead of the bare list, and an index whose
    manifest cannot be read gets `"stale": {"unknown": true}`; a current index still returns the bare list
    (TCK-20261006-KNOWLEDGE-INDEX-STALE-WARNING). The results are returned either way; the warning never blocks."""
    results = None
    if query.strip():
        results = _proxy_search(query, top_k, section)
    if results is None:
        results = _search(query, top_k=top_k, section=section, mode=mode)
    if not with_staleness or not isinstance(results, list):
        return results
    # Staleness is computed here, against this session's own corpus and index, on both paths.
    stale = _ks.index_staleness(_DB_PATH)
    return {"results": results, "stale": stale} if stale else results


def _search(query: str, top_k: int = 8, section: str | None = None,
            mode: str = "hybrid") -> list[dict] | dict:
    """The in-process path: loads the model on first use and rearms the idle unload timer."""
    with _LOCK:
        if not _ensure_loaded():
            return {"error": "index not found", "action": "run make knowledge-index"}
        results = _core.rank(
            query, top_k=top_k, section=section, model=_STATE.model, bm25=_STATE.bm25,
            doc_ids=_STATE.doc_ids, db_path=_DB_PATH, connect=sqlite3.connect,
        )
        _touch()
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
            # Which path search_docs takes now, and whether this process holds the model.
            "path": "shared-server" if _shared_server_usable() else "in-process",
            "model_loaded": bool(_STATE.ready),
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


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
        return _run_search(query, top_k=top_k, section=section or None, mode=mode, with_staleness=True)

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
