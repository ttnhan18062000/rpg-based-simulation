"""
tools/hybrid_retrieval.py — Reciprocal-rank fusion over the existing dense (embeddings) and
lexical (BM25) knowledge indexes, plus pre-fusion authority/freshness metadata filtering.

This is a fusion/filter layer over the *existing* knowledge_vec/knowledge_docs tables
(knowledge-index/knowledge.db) and bm25.pkl built by tools/knowledge_search.py's `build`
subcommand — it is not a new corpus source, is not wired into any .claude/workflows/*.js file or
existing pipeline/gate, and implements no lightweight re-ranker beyond fusion + metadata
filtering.

Built for TCK-20260729-HYBRID-RETRIEVAL-FUSION to fix a confirmed live bug: both
tools/knowledge_search.py::cmd_query()'s hybrid branch and tools/search_mcp.py::_run_search()
computed BM25 scores only for rows that already survived the dense-channel ANN's bounded
candidate cut, silently dropping high-BM25, low-semantic-similarity exact matches. This module
retrieves a bounded top-N independently from each channel, unions the results by doc_id, and
fuses them with the literal reciprocal-rank-fusion formula (score = sum of 1/(k+rank)) —
replacing the old linear-weighted `_hybrid_score()` formula for the hybrid path only.
`_hybrid_score()` itself is untouched and keeps serving `--mode vector`/`--mode keyword` (and
tools/search_server.py, out of this module's scope).
"""

from __future__ import annotations

import functools
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
from validate_frontmatter import AUTHORITY_VALUES, STATUS_VALUES  # noqa: E402

DEFAULT_RRF_K: int = 60
DEFAULT_CANDIDATE_MULTIPLIER: int = 4
DEFAULT_CANDIDATE_CAP: int = 50

UNRATED: str = "unrated"
# UNRATED must never collapse into either real enum -- it states "no registry-backed signal
# exists," not a real rating. Guarded here so the two enums drifting in validate_frontmatter.py
# can never silently swallow the sentinel.
assert UNRATED not in AUTHORITY_VALUES and UNRATED not in STATUS_VALUES

_SOURCE_TYPE_TO_KIND = {
    "doc_chunk": "doc",
    "ticket": "ticket",
    "investigation": "investigation",
    "working_log": "working_log",
}


# ---------------------------------------------------------------------------
# Step 1 — Reciprocal-rank fusion core
# ---------------------------------------------------------------------------

def reciprocal_rank_fusion(
    ranked_lists: dict[str, list[str]], k: int = DEFAULT_RRF_K
) -> dict[str, float]:
    """Fuse multiple named channels' ranked doc_id lists via literal RRF.

    Each channel's list is rank-1-indexed (list position 0 = rank 1, the best hit). A doc_id
    contributes 1/(k+rank) from each channel it appears in, and 0 from any channel it is absent
    from. Returns {doc_id: total_score} over the union of doc_ids across all channels.

    Distinct from tools/eval_search.py::_reciprocal_rank(), which computes the reciprocal rank
    of the first relevant hit in a single ranked list against one query's expected-set (an MRR@10
    building block) -- not RRF's fusion of multiple ranked lists for one query into one score per
    document. Never rename this to `_reciprocal_rank` or alias it to that function.
    """
    scores: dict[str, float] = {}
    for channel_ranked in ranked_lists.values():
        for rank, doc_id in enumerate(channel_ranked, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return scores


# ---------------------------------------------------------------------------
# Step 2 — Metadata resolution against docs/REGISTRY.yaml (query-time join)
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=1)
def _load_registry_index_cached(registry_path_str: str) -> dict[str, dict]:
    registry_path = Path(registry_path_str)
    if not registry_path.exists():
        return {}
    with open(registry_path, "r", encoding="utf-8") as fh:
        entries = yaml.safe_load(fh) or []
    return {entry["path"]: entry for entry in entries if "path" in entry}


def load_registry_index(registry_path: Path) -> dict[str, dict]:
    """Load and cache docs/REGISTRY.yaml, keyed by each entry's repo-relative `path` field.

    Cached via functools.lru_cache(maxsize=1) on the resolved path string -- a long-lived process
    (tools/search_mcp.py's MCP server, making many search_docs calls) re-parses the YAML at most
    once per process, not once per query.
    """
    return _load_registry_index_cached(str(registry_path.resolve()))


def resolve_metadata(path: str, source_type: str, registry_index: dict[str, dict]) -> dict:
    """Resolve a knowledge_docs row's authority/freshness/kind against the loaded registry index.

    A `path` with no docs/REGISTRY.yaml entry (every `ticket`/`investigation`/`working_log` row
    not under tickets/done/, since REGISTRY only indexes docs/ and tickets/done/) resolves to the
    UNRATED sentinel for both authority and freshness, per context_packet_contract.md §3's
    non-registry-backed fallback rule -- never a fabricated P2/historical-looking default.
    """
    kind = _SOURCE_TYPE_TO_KIND.get(source_type, source_type)
    entry = registry_index.get(path)
    if entry is None:
        return {"kind": kind, "authority": UNRATED, "freshness": UNRATED}
    return {
        "kind": kind,
        "authority": entry.get("authority", UNRATED),
        "freshness": entry.get("status", UNRATED),
    }


# ---------------------------------------------------------------------------
# Step 3 — Pre-fusion metadata filter
# ---------------------------------------------------------------------------

def filter_candidates(
    ranked_lists: dict[str, list[str]],
    metadata_by_id: dict[str, dict],
    *,
    authority_in: set[str] | None = None,
    freshness_in: set[str] | None = None,
) -> dict[str, list[str]]:
    """Exclude non-matching doc_ids from each channel's ranked list before fusion.

    Filtering is opt-in: if both `authority_in` and `freshness_in` are None, `ranked_lists` is
    returned unchanged. Relative order within each surviving list is preserved (no renumbering
    trick). The returned filtered lists are what `reciprocal_rank_fusion()` sees -- a filtered-out
    doc_id never appears in fusion's input, satisfying "excluded from fusion entirely" rather than
    merely down-ranked post-hoc.
    """
    if authority_in is None and freshness_in is None:
        return ranked_lists

    def _keep(doc_id: str) -> bool:
        meta = metadata_by_id.get(doc_id, {})
        if authority_in is not None and meta.get("authority") not in authority_in:
            return False
        if freshness_in is not None and meta.get("freshness") not in freshness_in:
            return False
        return True

    return {
        channel: [doc_id for doc_id in ranked if _keep(doc_id)]
        for channel, ranked in ranked_lists.items()
    }


# ---------------------------------------------------------------------------
# Step 4 — Orchestration: bounded dense + lexical retrieval, union, filter, fuse
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HybridResult:
    """Designed, stable return shape -- TCK-20260729-CONTEXT-PACKET-ASSEMBLY has a hard,
    load-bearing dependency on this field set. Do not reshuffle field names without checking
    that ticket first.
    """

    doc_id: str
    path: str
    heading: str
    section: str
    text: str
    rrf_score: float
    dense_rank: int | None
    lexical_rank: int | None
    semantic_score: float | None
    keyword_score: float | None
    authority: str
    freshness: str
    kind: str


def candidate_k(top_k: int) -> int:
    """Single bounded-candidate-count policy shared by both dense and lexical channels,
    unifying knowledge_search.py's old bare `top_k*3` and search_mcp.py's old `min(top_k*4, 50)`
    into one explicit, already-capped formula.
    """
    return min(top_k * DEFAULT_CANDIDATE_MULTIPLIER, DEFAULT_CANDIDATE_CAP)


def _dense_candidates(
    conn: sqlite3.Connection, query_vec_bytes: bytes, dense_candidate_k: int
) -> list[tuple]:
    """Run the ANN query. Rows: (rowid, doc_id, path, heading, section, text, source_type,
    distance), distance-ascending. Same SQL shape as today's cmd_query/_run_search, parameterized
    on dense_candidate_k -- the sqlite-vec MATCH/`k = ?` syntax itself is unchanged.
    """
    return conn.execute(
        """
        SELECT d.rowid, d.doc_id, d.path, d.heading, d.section, d.text, d.source_type, v.distance
        FROM knowledge_vec v
        JOIN knowledge_docs d ON d.rowid = v.rowid
        WHERE v.embedding MATCH ?
          AND k = ?
        ORDER BY v.distance
        """,
        (query_vec_bytes, dense_candidate_k),
    ).fetchall()


def _fetch_row_by_doc_id(conn: sqlite3.Connection, doc_id: str) -> tuple | None:
    """Fetch a single knowledge_docs row by doc_id -- used for a lexical-only hit outside the
    dense channel's candidate cut, the exact case the confirmed bug drops today.
    """
    return conn.execute(
        "SELECT rowid, doc_id, path, heading, section, text, source_type "
        "FROM knowledge_docs WHERE doc_id = ?",
        (doc_id,),
    ).fetchone()


def hybrid_fuse_and_filter(
    *,
    conn: sqlite3.Connection,
    query_vec_bytes: bytes,
    query_tokens: list[str],
    bm25_obj,
    bm25_doc_ids: list[str],
    top_k: int,
    dense_candidate_k: int | None = None,
    lexical_candidate_k: int | None = None,
    registry_index: dict[str, dict] | None = None,
    authority_in: set[str] | None = None,
    freshness_in: set[str] | None = None,
    rrf_k: int = DEFAULT_RRF_K,
) -> list[HybridResult]:
    """Independently retrieve a bounded top-N from the dense and lexical channels, union by
    doc_id, apply the pre-fusion metadata filter, fuse via RRF, and return the top_k results.

    `bm25_obj` may be None (no lexical index loaded) -- the lexical channel then contributes
    nothing and fusion degrades to dense-only ranking, mirroring `_load_bm25()`'s own
    "never raises" fallback contract rather than crashing search_mcp.py's `_run_search()`, which
    calls this helper unconditionally regardless of whether BM25 loaded.
    """
    if dense_candidate_k is None:
        dense_candidate_k = candidate_k(top_k)
    if lexical_candidate_k is None:
        lexical_candidate_k = candidate_k(top_k)
    if registry_index is None:
        registry_index = {}

    row_by_id: dict[str, tuple] = {}
    dense_ranked: list[str] = []
    dense_distance_by_id: dict[str, float] = {}
    for rowid, doc_id, path, heading, section, text, source_type, distance in _dense_candidates(
        conn, query_vec_bytes, dense_candidate_k
    ):
        dense_ranked.append(doc_id)
        row_by_id[doc_id] = (path, heading, section, text, source_type)
        dense_distance_by_id[doc_id] = distance

    lexical_ranked: list[str] = []
    bm25_score_by_id: dict[str, float] = {}
    bm25_max = 1.0
    if bm25_obj is not None and bm25_doc_ids:
        bm25_scores = bm25_obj.get_scores(query_tokens)
        order = sorted(range(len(bm25_doc_ids)), key=lambda i: bm25_scores[i], reverse=True)
        lexical_ranked = [bm25_doc_ids[i] for i in order[:lexical_candidate_k]]
        bm25_score_by_id = {
            doc_id: float(bm25_scores[i]) for i, doc_id in enumerate(bm25_doc_ids)
        }
        raw_max = float(max(bm25_scores)) if len(bm25_scores) else 0.0
        bm25_max = raw_max if raw_max > 0 else 1.0

    for doc_id in lexical_ranked:
        if doc_id in row_by_id:
            continue
        row = _fetch_row_by_doc_id(conn, doc_id)
        if row is None:
            continue
        _, _, path, heading, section, text, source_type = row
        row_by_id[doc_id] = (path, heading, section, text, source_type)

    metadata_by_id = {
        doc_id: resolve_metadata(row[0], row[4], registry_index)
        for doc_id, row in row_by_id.items()
    }

    filtered = filter_candidates(
        {"dense": dense_ranked, "lexical": lexical_ranked},
        metadata_by_id,
        authority_in=authority_in,
        freshness_in=freshness_in,
    )

    fused_scores = reciprocal_rank_fusion(filtered, k=rrf_k)
    ordered_ids = sorted(fused_scores.keys(), key=lambda d: (-fused_scores[d], d))[:top_k]

    dense_rank_by_id = {doc_id: i + 1 for i, doc_id in enumerate(filtered["dense"])}
    lexical_rank_by_id = {doc_id: i + 1 for i, doc_id in enumerate(filtered["lexical"])}

    results: list[HybridResult] = []
    for doc_id in ordered_ids:
        path, heading, section, text, source_type = row_by_id[doc_id]
        meta = metadata_by_id[doc_id]
        distance = dense_distance_by_id.get(doc_id)
        semantic_score = (
            max(0.0, min(1.0, 1.0 - (distance / 2.0))) if distance is not None else None
        )
        raw_keyword = bm25_score_by_id.get(doc_id)
        keyword_score = (raw_keyword / bm25_max) if raw_keyword is not None else None
        results.append(
            HybridResult(
                doc_id=doc_id,
                path=path,
                heading=heading,
                section=section,
                text=text,
                rrf_score=fused_scores[doc_id],
                dense_rank=dense_rank_by_id.get(doc_id),
                lexical_rank=lexical_rank_by_id.get(doc_id),
                semantic_score=semantic_score,
                keyword_score=keyword_score,
                authority=meta["authority"],
                freshness=meta["freshness"],
                kind=meta["kind"],
            )
        )
    return results
