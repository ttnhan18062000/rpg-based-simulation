"""Tests for tools/search_mcp.py — MCP server, settings, and tool logic."""
from __future__ import annotations

import importlib.util
import json
import pickle
import sqlite3
import sys
import tomllib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
_MCP_PATH = _REPO_ROOT / "tools" / "search_mcp.py"

# Stub knowledge_search before loading search_mcp to avoid heavy deps at import time
_KS_STUB = MagicMock()
_KS_STUB._DEFAULT_DB = _REPO_ROOT / "knowledge-index" / "knowledge.db"
_KS_STUB._MODEL_NAME = "all-MiniLM-L6-v2"
_KS_STUB._tokenize = lambda text: text.lower().split()
_KS_STUB._serialize_f32 = lambda v: b""
_KS_STUB._load_bm25 = MagicMock(return_value=(None, []))
_KS_STUB._compute_boosts = MagicMock(return_value=(0.0, 0.0, 0.0))
_KS_STUB._hybrid_score = MagicMock(return_value=0.5)

sys.modules.setdefault("knowledge_search", _KS_STUB)
# sentence_transformers and sqlite_vec are lazy imports inside _ensure_loaded() —
# do NOT stub them at module level to avoid poisoning _check_deps() in other test files.


def _load_mcp_module():
    spec = importlib.util.spec_from_file_location("search_mcp_test", _MCP_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["search_mcp_test"] = mod
    spec.loader.exec_module(mod)
    return mod


_mod = _load_mcp_module()


# ── T-SETTINGS-01/02: .mcp.json registration ────────────────────────────────

class TestMcpJson:
    def test_mcp_json_exists(self):
        assert (_REPO_ROOT / ".mcp.json").exists(), ".mcp.json not found in project root"

    def test_has_knowledge_search_server(self):
        data = json.loads((_REPO_ROOT / ".mcp.json").read_text())
        assert "mcpServers" in data
        assert "knowledge-search" in data["mcpServers"]

    def test_command_is_python3(self):
        data = json.loads((_REPO_ROOT / ".mcp.json").read_text())
        entry = data["mcpServers"]["knowledge-search"]
        assert entry["command"] == "python3"

    def test_args_point_to_search_mcp(self):
        data = json.loads((_REPO_ROOT / ".mcp.json").read_text())
        entry = data["mcpServers"]["knowledge-search"]
        assert len(entry["args"]) >= 1
        assert entry["args"][0].endswith("search_mcp.py")


# ── Title derivation — nesting-agnosticism guard ──────────────────────────────

class TestDeriveTitle:
    def test_agnostic_to_nesting_depth(self):
        """_derive_title() splits on the LAST '/' only, so it produces the same title for a
        doc_id regardless of how many nesting levels precede the stem — confirms it needs no
        change for TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION's full-path doc_id fix."""
        old_scheme = "engine/measurement_baseline_contract"
        new_scheme = "engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract"
        assert _mod._derive_title(old_scheme) == _mod._derive_title(new_scheme)


# ── T-SEARCH-01: _run_search returns list with required keys ─────────────────

class TestRunSearch:
    def _make_ready_state(self, mod):
        mock_model = MagicMock()
        mock_model.encode.return_value.tolist.return_value = [0.0] * 384
        mod._STATE.model = mock_model
        mod._STATE.bm25 = None
        mod._STATE.doc_ids = []
        mod._STATE.ready = True

    def test_returns_list_when_index_present(self, tmp_path, monkeypatch):
        fake_db = tmp_path / "knowledge.db"
        fake_db.touch()
        monkeypatch.setattr(mod := _mod, "_DB_PATH", fake_db)
        self._make_ready_state(mod)
        mock_con = MagicMock()
        mock_con.execute.return_value.fetchall.return_value = []
        monkeypatch.setitem(sys.modules, "sqlite_vec", MagicMock())
        monkeypatch.setattr(mod, "sqlite3", MagicMock(connect=MagicMock(return_value=mock_con)))
        results = mod._run_search("damage formula", top_k=3)
        assert isinstance(results, list)

    def test_empty_query_returns_empty_list(self, tmp_path, monkeypatch):
        fake_db = tmp_path / "knowledge.db"
        fake_db.touch()
        monkeypatch.setattr(_mod, "_DB_PATH", fake_db)
        self._make_ready_state(_mod)
        results = _mod._run_search("   ")
        assert results == []

    def test_result_has_required_keys(self, tmp_path, monkeypatch):
        fake_db = tmp_path / "knowledge.db"
        fake_db.touch()
        monkeypatch.setattr(_mod, "_DB_PATH", fake_db)
        self._make_ready_state(_mod)
        fake_row = (1, "mechanics/02_combat_laws", "docs/mechanics/02_combat_laws.md",
                    "damage text", "Combat Damage", "mechanics", 0.2)
        mock_con = MagicMock()
        mock_con.execute.return_value.fetchall.return_value = [fake_row]
        monkeypatch.setitem(sys.modules, "sqlite_vec", MagicMock())
        monkeypatch.setattr(_mod, "sqlite3", MagicMock(connect=MagicMock(return_value=mock_con)))
        results = _mod._run_search("damage", top_k=1)
        if isinstance(results, list) and results:
            r = results[0]
            for key in ("doc_id", "title", "heading", "source_path", "section", "score", "excerpt"):
                assert key in r, f"missing key: {key}"


# ── T-SEARCH-02: Missing index returns error dict ────────────────────────────

class TestRunSearchMissingIndex:
    def test_returns_error_dict_when_db_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_mod, "_DB_PATH", tmp_path / "nonexistent.db")
        _mod._STATE.ready = False
        results = _mod._run_search("anything")
        assert isinstance(results, dict)
        assert "error" in results
        assert "index" in results["error"].lower() or "not found" in results["error"].lower()

    def test_error_dict_has_action_hint(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_mod, "_DB_PATH", tmp_path / "nonexistent.db")
        _mod._STATE.ready = False
        results = _mod._run_search("anything")
        assert "action" in results


# ── T-HEALTH-01: _run_health returns status dict ─────────────────────────────

class TestRunHealth:
    def test_unavailable_when_no_db(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_mod, "_DB_PATH", tmp_path / "nonexistent.db")
        result = _mod._run_health()
        assert result["status"] == "unavailable"
        assert "action" in result

    def test_ok_when_db_present(self, tmp_path, monkeypatch):
        import sqlite3 as _sqlite3
        fake_db = tmp_path / "knowledge.db"
        con = _sqlite3.connect(str(fake_db))
        con.execute("CREATE TABLE knowledge_docs (rowid INTEGER PRIMARY KEY, doc_id TEXT, path TEXT, text TEXT, heading TEXT, section TEXT)")
        con.commit()
        con.close()
        monkeypatch.setattr(_mod, "_DB_PATH", fake_db)
        result = _mod._run_health()
        assert result["status"] == "ok"
        assert "chunks" in result
        assert "model" in result
        assert "index_version" in result


# ── T-PYPROJECT-01: mcp in [search-mcp] optional deps ───────────────────────

class TestPyprojectDeps:
    def test_search_mcp_optional_group_exists(self):
        data = tomllib.loads((_REPO_ROOT / "pyproject.toml").read_text())
        groups = data.get("project", {}).get("optional-dependencies", {})
        assert "search-mcp" in groups, "pyproject.toml missing [project.optional-dependencies.search-mcp]"

    def test_mcp_dep_in_search_mcp_group(self):
        data = tomllib.loads((_REPO_ROOT / "pyproject.toml").read_text())
        deps = data["project"]["optional-dependencies"]["search-mcp"]
        assert any("mcp" in d for d in deps), f"mcp not found in search-mcp deps: {deps}"


# ── T-MAKEFILE-01: mcp-server-test target present ────────────────────────────

class TestMakefileTargets:
    def test_mcp_server_test_target_present(self):
        makefile = (_REPO_ROOT / "Makefile").read_text()
        assert "mcp-server-test:" in makefile

    def test_mcp_server_test_calls_search_mcp(self):
        makefile = (_REPO_ROOT / "Makefile").read_text()
        # find the block after the target
        idx = makefile.index("mcp-server-test:")
        block = makefile[idx: idx + 300]
        assert "search_mcp.py" in block
        assert "--test" in block


# ── AC1/Scope (TCK-20260729-HYBRID-RETRIEVAL-FUSION): _run_search() fusion wiring ────────────

class _FakeBM25ScoresRS(list):
    def max(self):
        return max(self) if self else 0.0


class _FakeBM25RunSearch:
    def get_scores(self, tokens):
        return _FakeBM25ScoresRS([0.0, 9.0])


class TestRunSearchFusionWiring:
    """Proves _run_search() -- the exact function `search_docs` (every agent's MCP tool)
    invokes -- routes through hybrid_retrieval.hybrid_fuse_and_filter and surfaces a
    lexical-only exact match outside the dense channel's candidate cut (AC1), the confirmed
    live bug this ticket fixes. Only the sqlite-vec-dependent ANN query itself
    (`_hr._dense_candidates`) is stubbed, so this runs without sqlite-vec installed.
    """

    def test_lexical_only_match_surfaced(self, tmp_path, monkeypatch):
        fake_db = tmp_path / "knowledge.db"
        con = sqlite3.connect(str(fake_db))
        con.execute(
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
        con.executemany(
            "INSERT INTO knowledge_docs (rowid, doc_id, path, text, source_type, heading, section) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (0, "doc-a", "docs/a.md", "alpha text", "doc_chunk", "A", "docs"),
                (1, "doc-rare", "docs/rare.md", "zzqfrobnicate_widget appears here",
                 "doc_chunk", "Rare", "docs"),
            ],
        )
        con.commit()
        con.close()

        monkeypatch.setattr(_mod, "_DB_PATH", fake_db)
        monkeypatch.setattr(
            _mod._hr, "_dense_candidates",
            lambda conn, query_vec_bytes, dense_candidate_k: [
                (0, "doc-a", "docs/a.md", "A", "docs", "alpha text", "doc_chunk", 0.1),
            ],
        )
        monkeypatch.setitem(sys.modules, "sqlite_vec", MagicMock())

        mock_model = MagicMock()
        mock_model.encode.return_value.tolist.return_value = [0.0] * 8
        _mod._STATE.model = mock_model
        _mod._STATE.bm25 = _FakeBM25RunSearch()
        _mod._STATE.doc_ids = ["doc-a", "doc-rare"]
        _mod._STATE.ready = True

        results = _mod._run_search("zzqfrobnicate_widget", top_k=5)

        assert isinstance(results, list)
        result_ids = [r["doc_id"] for r in results]
        assert "doc-rare" in result_ids, (
            f"lexical-only hit missing from _run_search results: {result_ids}"
        )
        for key in ("doc_id", "title", "heading", "source_path", "section",
                    "score", "semantic_score", "keyword_score", "excerpt"):
            assert key in results[0], f"missing key in _run_search result: {key}"
