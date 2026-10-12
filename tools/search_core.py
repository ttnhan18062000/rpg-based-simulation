"""The one ranking path behind `search_docs` (tools/search_mcp.py) and `/api/search` (tools/search_server.py).

TCK-20261012-SEARCH-MCP-SHARED-SERVER-AND-IDLE-UNLOAD: the MCP and the HTTP server used to rank differently
(RRF fusion with the authority/freshness filter versus a vector top-k plus `_hybrid_score`), so a session that
forwarded to the server would have silently changed its results. Both now call `rank()`.

Pure of any global state: the caller passes the model, the BM25 object and the db path, so each process keeps
its own lifecycle (the MCP loads lazily and unloads when idle; the server loads at startup).
"""
from __future__ import annotations

import importlib.util
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

_TOOLS_DIR = Path(__file__).parent


def _sibling(name: str):
    """A sibling tool module, reusing one already in `sys.modules` (test stubs are respected)."""
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, _TOOLS_DIR / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


_ks = _sibling("knowledge_search")
_hr = _sibling("hybrid_retrieval")


def main_checkout_root(start: Path) -> Path | None:
    """The main checkout's root, from any worktree of it (or from the main checkout itself)."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True, text=True, timeout=5, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    common_dir = proc.stdout.strip()
    return Path(common_dir).parent if proc.returncode == 0 and common_dir else None


def resolve_index_dir(own_index_dir: Path, own_root: Path, main_root: Path | None) -> Path:
    """This checkout's own knowledge index, or the main checkout's when this one has none.

    The index is generated and gitignored, so a fresh git worktree has none and every
    search_docs call there answered "index not found"
    (TCK-20261010-SEARCH-MCP-WORKTREE-VENV-RESOLUTION). Querying reads the main checkout's index
    instead; building one (`make knowledge-index`) still writes only to the checkout it runs in.
    """
    db_name = _ks._DEFAULT_DB.name
    if (own_index_dir / db_name).exists() or main_root is None:
        return own_index_dir
    try:
        main_index_dir = main_root / own_index_dir.relative_to(own_root)
    except ValueError:
        return own_index_dir
    return main_index_dir if (main_index_dir / db_name).exists() else own_index_dir


def index_fingerprint(db_path: Path) -> str | None:
    """Identity of the index file: size and mtime in ns. The same file reached through a bind mount, a symlink or another
    checkout's path gives the same value, so it is compared instead of a path (a container's path differs from the host's)."""
    try:
        st = os.stat(db_path)
    except OSError:
        return None
    return f"{st.st_size}:{st.st_mtime_ns}"


def derive_title(doc_id: str) -> str:
    """Display title from the doc_id stem, stripping a leading NN_ numbering prefix."""
    stem = doc_id.split("/")[-1]
    stem = re.sub(r"^\d+_", "", stem)
    return stem.replace("_", " ").title()


def rank(query: str, *, top_k: int = 8, section: str | None = None, include_text: bool = False,
         model: Any, bm25: Any, doc_ids: list, db_path: Path,
         connect: Callable[[str], Any] | None = None) -> list[dict] | dict:
    """Ranked chunks for `query`, or `{"error": ...}` when the query cannot be embedded.

    Embeds the query, fuses the dense and lexical channels with RRF and applies the authority/freshness filter
    (`hybrid_retrieval.hybrid_fuse_and_filter`), then narrows by exact `section` (orthogonal to that filter, so it
    stays a post-fusion step). `connect` defaults to `sqlite3.connect`; callers whose tests patch their own `sqlite3`
    pass theirs.
    """
    if not query.strip():
        return []
    query_tokens = _ks._tokenize(query)
    try:
        q_bytes = _ks._serialize_f32(model.encode(query).tolist())
    except Exception as exc:
        return {"error": f"embed failed: {exc}"}

    hybrid_results = []
    con = None
    try:
        import sqlite_vec
        con = (connect or sqlite3.connect)(str(db_path))
        con.enable_load_extension(True)
        sqlite_vec.load(con)
        con.enable_load_extension(False)
        hybrid_results = _hr.hybrid_fuse_and_filter(
            conn=con,
            query_vec_bytes=q_bytes,
            query_tokens=query_tokens,
            bm25_obj=bm25,
            bm25_doc_ids=doc_ids,
            top_k=top_k,
        )
    except Exception:
        hybrid_results = []
    finally:
        if con is not None:
            try:
                con.close()
            except Exception:
                pass

    if section:
        hybrid_results = [r for r in hybrid_results if r.section == section]

    results = []
    for r in hybrid_results[:top_k]:
        item = {
            "doc_id": r.doc_id,
            "title": derive_title(r.doc_id),
            "heading": r.heading or "",
            "source_path": r.path,
            "section": r.section or "",
            "score": round(r.rrf_score, 4),
            "semantic_score": round(r.semantic_score or 0.0, 4),
            "keyword_score": round(r.keyword_score or 0.0, 4),
            "excerpt": r.text[:200].replace("\n", " "),
        }
        if include_text:
            item["text"] = r.text
        results.append(item)

    results.sort(key=lambda r: r["score"], reverse=True)
    return results
