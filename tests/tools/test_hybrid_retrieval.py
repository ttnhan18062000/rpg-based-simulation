"""Tests for tools/hybrid_retrieval.py — RRF fusion, metadata filtering, and orchestration.

Built for TCK-20260729-HYBRID-RETRIEVAL-FUSION. None of these tests require
sentence-transformers/sqlite-vec/rank-bm25 to be installed: the dense channel's ANN query is
exercised through the module's own `_dense_candidates()` seam (monkeypatched in the
regression/orchestration tests below), and the lexical channel only needs a plain object with a
`get_scores()` method, not a real rank_bm25.BM25Okapi instance.
"""
from __future__ import annotations

import importlib.util
import inspect
import pickle
import sqlite3
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

_REPO_ROOT = Path(__file__).parent.parent.parent
_HR_PATH = _REPO_ROOT / "tools" / "hybrid_retrieval.py"
_KS_PATH = _REPO_ROOT / "tools" / "knowledge_search.py"
_EVAL_PATH = _REPO_ROOT / "tools" / "eval_search.py"


def _load_module(name: str, path: Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# Load hybrid_retrieval first and register it in sys.modules so knowledge_search.py's own
# `from hybrid_retrieval import hybrid_fuse_and_filter` (module top) reuses this exact object --
# required for monkeypatching `_hr._dense_candidates` to affect calls made from `_ks.cmd_query()`.
_hr = _load_module("hybrid_retrieval", _HR_PATH)
_ks = _load_module("knowledge_search", _KS_PATH)
_eval_search = _load_module("eval_search_for_naming_guard", _EVAL_PATH)


# ---------------------------------------------------------------------------
# Module-level fakes (pickled in some tests -- must stay at module scope)
# ---------------------------------------------------------------------------

class _FakeBM25Scores(list):
    def max(self):
        return max(self) if self else 0.0


class _FakeBM25:
    """Minimal get_scores()-only stand-in for rank_bm25.BM25Okapi -- picklable, no rank_bm25
    dependency required."""

    def __init__(self, scores):
        self._scores = scores

    def get_scores(self, tokens):
        return _FakeBM25Scores(self._scores)


class _FakeArray(list):
    def tolist(self):
        return list(self)


class _FakeEmbeddingModel:
    def __init__(self, *_a, **_kw):
        pass

    def encode(self, texts, **_kw):
        return _FakeArray([_FakeArray([0.0] * 8) for _ in texts])


def _make_docs_db(tmp_path: Path, rows: list[tuple]) -> sqlite3.Connection:
    """rows: list of (rowid, doc_id, path, heading, section, text, source_type)."""
    db_path = tmp_path / "knowledge.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE knowledge_docs (
            rowid       INTEGER PRIMARY KEY,
            doc_id      TEXT NOT NULL,
            path        TEXT NOT NULL,
            text        TEXT NOT NULL,
            source_type TEXT NOT NULL,
            heading     TEXT NOT NULL DEFAULT '',
            section     TEXT NOT NULL DEFAULT ''
        )
        """
    )
    for rowid, doc_id, path, heading, section, text, source_type in rows:
        conn.execute(
            "INSERT INTO knowledge_docs (rowid, doc_id, path, text, source_type, heading, section) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (rowid, doc_id, path, text, source_type, heading, section),
        )
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# AC2 — reciprocal_rank_fusion() itself
# ---------------------------------------------------------------------------

class TestReciprocalRankFusion:
    def test_rrf_score_matches_formula_for_known_ranks(self):
        ranked_lists = {
            "dense": ["a", "b", "c"],
            "lexical": ["c", "a"],
        }
        scores = _hr.reciprocal_rank_fusion(ranked_lists, k=60)
        assert scores["a"] == pytest.approx(1.0 / 61 + 1.0 / 62)
        assert scores["b"] == pytest.approx(1.0 / 62)
        assert scores["c"] == pytest.approx(1.0 / 63 + 1.0 / 61)

    def test_default_k_is_60(self):
        assert _hr.DEFAULT_RRF_K == 60

    def test_union_by_doc_id_includes_single_channel_hits(self):
        ranked_lists = {"dense": ["only-dense"], "lexical": ["only-lexical"]}
        scores = _hr.reciprocal_rank_fusion(ranked_lists)
        assert "only-dense" in scores
        assert "only-lexical" in scores
        assert len(scores) == 2

    def test_fusion_function_name_distinct_from_eval_search_reciprocal_rank(self):
        assert not hasattr(_hr, "_reciprocal_rank")
        assert _hr.reciprocal_rank_fusion is not _eval_search._reciprocal_rank

        fusion_params = list(inspect.signature(_hr.reciprocal_rank_fusion).parameters)
        mrr_params = list(inspect.signature(_eval_search._reciprocal_rank).parameters)
        assert fusion_params != mrr_params, (
            "reciprocal_rank_fusion (multi-list RRF) must not share a signature with "
            "eval_search._reciprocal_rank (single-list MRR@10 building block)"
        )


# ---------------------------------------------------------------------------
# AC3 — metadata resolution + pre-fusion filter
# ---------------------------------------------------------------------------

class TestResolveMetadata:
    def test_non_registry_backed_rows_get_sentinel_not_fabricated_value(self):
        registry_index = {
            "docs/mechanics/02_combat_laws.md": {"authority": "P0", "status": "authoritative"},
        }
        for source_type in ("ticket", "investigation", "working_log"):
            meta = _hr.resolve_metadata(
                "tickets/inprogress/TCK-20260101-EXAMPLE.md", source_type, registry_index
            )
            assert meta["authority"] == _hr.UNRATED
            assert meta["freshness"] == _hr.UNRATED
            assert meta["authority"] not in _hr.AUTHORITY_VALUES
            assert meta["freshness"] not in _hr.STATUS_VALUES

    def test_registry_backed_row_resolves_real_values(self):
        registry_index = {
            "docs/mechanics/02_combat_laws.md": {"authority": "P0", "status": "authoritative"},
        }
        meta = _hr.resolve_metadata("docs/mechanics/02_combat_laws.md", "doc_chunk", registry_index)
        assert meta == {"kind": "doc", "authority": "P0", "freshness": "authoritative"}

    def test_load_registry_index_keys_by_path(self, tmp_path):
        registry_path = tmp_path / "REGISTRY.yaml"
        registry_path.write_text(
            yaml.safe_dump([{"path": "docs/a.md", "authority": "P1", "status": "active"}])
        )
        index = _hr.load_registry_index(registry_path)
        assert index["docs/a.md"]["authority"] == "P1"


class TestFilterCandidates:
    def test_metadata_filter_excludes_before_fusion(self):
        ranked_lists = {"dense": ["a", "b"], "lexical": ["b", "c"]}
        metadata_by_id = {
            "a": {"authority": "P0", "freshness": "authoritative"},
            "b": {"authority": "P2", "freshness": "historical"},
            "c": {"authority": "P0", "freshness": "active"},
        }
        filtered = _hr.filter_candidates(
            ranked_lists, metadata_by_id, authority_in={"P0"}, freshness_in=None
        )
        assert filtered == {"dense": ["a"], "lexical": ["c"]}

        fused = _hr.reciprocal_rank_fusion(filtered)
        assert "b" not in fused, "excluded doc_id must never reach fusion's input"

    def test_no_filter_args_is_noop(self):
        ranked_lists = {"dense": ["a", "b"]}
        assert _hr.filter_candidates(ranked_lists, {}) == ranked_lists

    def test_preserves_relative_order_within_channel(self):
        ranked_lists = {"dense": ["a", "b", "c"]}
        metadata_by_id = {
            "a": {"authority": "P0"},
            "b": {"authority": "P2"},
            "c": {"authority": "P0"},
        }
        filtered = _hr.filter_candidates(ranked_lists, metadata_by_id, authority_in={"P0"})
        assert filtered["dense"] == ["a", "c"]


# ---------------------------------------------------------------------------
# AC1/AC2 — hybrid_fuse_and_filter() orchestration
# ---------------------------------------------------------------------------

class TestHybridFuseAndFilter:
    def test_lexical_only_match_outside_dense_cut_is_surfaced(self, tmp_path, monkeypatch):
        """The confirmed bug's direct regression test: a document with an exact rare token is
        semantically dissimilar and never appears in the dense channel's candidate list (the
        exact shape of the bug -- it would never enter `rows` at all today), but its high BM25
        score must still surface it in the fused result."""
        conn = _make_docs_db(
            tmp_path,
            [
                (0, "doc-a", "docs/a.md", "A", "docs", "alpha text", "doc_chunk"),
                (1, "doc-b", "docs/b.md", "B", "docs", "beta text", "doc_chunk"),
                (2, "doc-rare", "docs/rare.md", "Rare", "docs",
                 "zzqfrobnicate_widget appears here", "doc_chunk"),
            ],
        )

        monkeypatch.setattr(
            _hr, "_dense_candidates",
            lambda conn, query_vec_bytes, dense_candidate_k: [
                (0, "doc-a", "docs/a.md", "A", "docs", "alpha text", "doc_chunk", 0.1),
                (1, "doc-b", "docs/b.md", "B", "docs", "beta text", "doc_chunk", 0.2),
            ],
        )

        bm25_doc_ids = ["doc-a", "doc-b", "doc-rare"]
        bm25 = _FakeBM25([0.0, 0.0, 9.0])

        results = _hr.hybrid_fuse_and_filter(
            conn=conn,
            query_vec_bytes=b"",
            query_tokens=["zzqfrobnicate_widget"],
            bm25_obj=bm25,
            bm25_doc_ids=bm25_doc_ids,
            top_k=5,
        )
        conn.close()

        result_ids = [r.doc_id for r in results]
        assert "doc-rare" in result_ids, (
            "lexical-only exact match outside the dense candidate cut must be surfaced"
        )
        rare = next(r for r in results if r.doc_id == "doc-rare")
        assert rare.dense_rank is None
        assert rare.lexical_rank == 1
        assert rare.semantic_score is None

    def test_union_includes_both_channels_bounded_independently(self, tmp_path, monkeypatch):
        conn = _make_docs_db(
            tmp_path,
            [
                (0, "doc-dense", "docs/d.md", "D", "docs", "dense only", "doc_chunk"),
                (1, "doc-lex", "docs/l.md", "L", "docs", "lexical only", "doc_chunk"),
            ],
        )
        monkeypatch.setattr(
            _hr, "_dense_candidates",
            lambda conn, query_vec_bytes, dense_candidate_k: [
                (0, "doc-dense", "docs/d.md", "D", "docs", "dense only", "doc_chunk", 0.05),
            ],
        )
        results = _hr.hybrid_fuse_and_filter(
            conn=conn,
            query_vec_bytes=b"",
            query_tokens=["lexical"],
            bm25_obj=_FakeBM25([0.0, 5.0]),
            bm25_doc_ids=["doc-dense", "doc-lex"],
            top_k=5,
        )
        conn.close()
        result_ids = {r.doc_id for r in results}
        assert result_ids == {"doc-dense", "doc-lex"}

    def test_bm25_none_degrades_to_dense_only_without_crashing(self, tmp_path, monkeypatch):
        conn = _make_docs_db(
            tmp_path, [(0, "doc-a", "docs/a.md", "A", "docs", "alpha text", "doc_chunk")]
        )
        monkeypatch.setattr(
            _hr, "_dense_candidates",
            lambda conn, query_vec_bytes, dense_candidate_k: [
                (0, "doc-a", "docs/a.md", "A", "docs", "alpha text", "doc_chunk", 0.1),
            ],
        )
        results = _hr.hybrid_fuse_and_filter(
            conn=conn,
            query_vec_bytes=b"",
            query_tokens=["alpha"],
            bm25_obj=None,
            bm25_doc_ids=[],
            top_k=5,
        )
        conn.close()
        assert [r.doc_id for r in results] == ["doc-a"]
        assert results[0].keyword_score is None

    def test_authority_filter_excludes_candidate_from_fused_output(self, tmp_path, monkeypatch):
        conn = _make_docs_db(
            tmp_path,
            [
                (0, "docs/keep", "docs/keep.md", "Keep", "docs", "keep text", "doc_chunk"),
                (1, "docs/drop", "docs/drop.md", "Drop", "docs", "drop text", "doc_chunk"),
            ],
        )
        monkeypatch.setattr(
            _hr, "_dense_candidates",
            lambda conn, query_vec_bytes, dense_candidate_k: [
                (0, "docs/keep", "docs/keep.md", "Keep", "docs", "keep text", "doc_chunk", 0.1),
                (1, "docs/drop", "docs/drop.md", "Drop", "docs", "drop text", "doc_chunk", 0.2),
            ],
        )
        registry_index = {
            "docs/keep.md": {"authority": "P0", "status": "authoritative"},
            "docs/drop.md": {"authority": "P2", "status": "historical"},
        }
        results = _hr.hybrid_fuse_and_filter(
            conn=conn,
            query_vec_bytes=b"",
            query_tokens=[],
            bm25_obj=None,
            bm25_doc_ids=[],
            top_k=5,
            registry_index=registry_index,
            authority_in={"P0"},
        )
        conn.close()
        assert [r.doc_id for r in results] == ["docs/keep"]

    def test_candidate_k_policy_is_capped(self):
        assert _hr.candidate_k(1000) == _hr.DEFAULT_CANDIDATE_CAP
        assert _hr.candidate_k(5) == 5 * _hr.DEFAULT_CANDIDATE_MULTIPLIER


# ---------------------------------------------------------------------------
# AC4 — --mode vector/--mode keyword paths never call the fusion helper
# ---------------------------------------------------------------------------

class _FakeBM25Guard:
    def get_scores(self, tokens):
        return _FakeBM25Scores([0.0])


class TestModeRoutingGuard:
    def test_vector_and_keyword_modes_do_not_call_fusion_helper(self, tmp_path, monkeypatch):
        try:
            import numpy  # noqa: F401
        except ImportError:
            pytest.skip("numpy not installed")
        calls = []
        monkeypatch.setattr(_ks, "hybrid_fuse_and_filter", lambda **kw: calls.append(kw) or [])

        fake_db = tmp_path / "knowledge.db"
        fake_db.touch()

        fake_st_module = types.ModuleType("sentence_transformers")
        fake_st_module.SentenceTransformer = _FakeEmbeddingModel
        fake_vec_module = types.ModuleType("sqlite_vec")
        fake_vec_module.load = lambda conn: None
        monkeypatch.setitem(sys.modules, "sentence_transformers", fake_st_module)
        monkeypatch.setitem(sys.modules, "sqlite_vec", fake_vec_module)

        mock_con = MagicMock()
        mock_con.execute.return_value.fetchall.return_value = []
        monkeypatch.setattr(_ks, "sqlite3", MagicMock(connect=MagicMock(return_value=mock_con)))

        vector_args = types.SimpleNamespace(
            query="stamina", top_k=2, db_path=str(fake_db), mode="vector"
        )
        assert _ks.cmd_query(vector_args) == 0
        assert calls == [], f"vector mode called hybrid_fuse_and_filter: {calls}"

        bm25_path = fake_db.parent / "bm25.pkl"
        with open(bm25_path, "wb") as fh:
            pickle.dump((_FakeBM25Guard(), ["doc-a"]), fh)

        keyword_args = types.SimpleNamespace(
            query="stamina", top_k=2, db_path=str(fake_db), mode="keyword"
        )
        assert _ks.cmd_query(keyword_args) == 0
        assert calls == [], f"keyword mode called hybrid_fuse_and_filter: {calls}"
