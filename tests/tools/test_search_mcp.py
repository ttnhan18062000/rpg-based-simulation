"""Tests for tools/search_mcp.py — MCP server, settings, and tool logic."""
from __future__ import annotations

import importlib.util
import json
import pickle
import sqlite3
import subprocess
import sys
import tomllib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from tools.agent_working_paths import KNOWLEDGE_INDEX

_REPO_ROOT = Path(__file__).parent.parent.parent
_MCP_PATH = _REPO_ROOT / "tools" / "search_mcp.py"

# Stub knowledge_search before loading search_mcp to avoid heavy deps at import time
_KS_STUB = MagicMock()
_KS_STUB._DEFAULT_DB = _REPO_ROOT / KNOWLEDGE_INDEX / "knowledge.db"
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
        """TCK-20260624-FIX-TOOLS-SERVER intentionally repointed the top-level `command` to
        `bash` running a portability wrapper (tools/start_search_mcp.sh), rather than invoking
        python3 directly — see test_start_search_mcp_wrapper_invokes_python3 below for the real
        interpreter hop."""
        data = json.loads((_REPO_ROOT / ".mcp.json").read_text())
        entry = data["mcpServers"]["knowledge-search"]
        assert entry["command"] == "bash"

    def test_args_point_to_search_mcp(self):
        """args[0] is the wrapper script, not search_mcp.py directly — the wrapper itself execs
        search_mcp.py with whichever python3 it finds (see test_start_search_mcp_wrapper_invokes_
        python3 below)."""
        data = json.loads((_REPO_ROOT / ".mcp.json").read_text())
        entry = data["mcpServers"]["knowledge-search"]
        assert len(entry["args"]) >= 1
        assert entry["args"][0] == "tools/start_search_mcp.sh"

    def test_start_search_mcp_wrapper_invokes_python3(self):
        """Proves the full .mcp.json -> wrapper -> real interpreter chain end-to-end, not just
        the first hop — derives the wrapper path from args[0] so it stays correct even if
        .mcp.json's args value is ever legitimately re-pointed elsewhere."""
        data = json.loads((_REPO_ROOT / ".mcp.json").read_text())
        entry = data["mcpServers"]["knowledge-search"]
        wrapper_path = _REPO_ROOT / entry["args"][0]
        assert wrapper_path.exists(), f"{wrapper_path} referenced by .mcp.json but does not exist"
        assert "python3" in wrapper_path.read_text()


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


# --- TCK-20261010-SEARCH-MCP-WORKTREE-VENV-RESOLUTION: a worktree with no index reads the main one ---


class TestResolveIndexDir:
    """A worktree with no knowledge index of its own queries the main checkout's."""

    def _make_index(self, root: Path) -> Path:
        index_dir = root / KNOWLEDGE_INDEX
        index_dir.mkdir(parents=True)
        (index_dir / "knowledge.db").write_bytes(b"")
        return index_dir

    def test_own_index_wins_when_present(self, tmp_path: Path) -> None:
        own = self._make_index(tmp_path / "worktree")
        self._make_index(tmp_path / "main")
        assert _mod._resolve_index_dir(own, tmp_path / "worktree", tmp_path / "main") == own

    def test_falls_back_to_main_checkout_index_when_own_missing(self, tmp_path: Path) -> None:
        own = tmp_path / "worktree" / KNOWLEDGE_INDEX
        main_index = self._make_index(tmp_path / "main")
        assert _mod._resolve_index_dir(own, tmp_path / "worktree", tmp_path / "main") == main_index

    def test_keeps_own_path_when_neither_index_exists(self, tmp_path: Path) -> None:
        own = tmp_path / "worktree" / KNOWLEDGE_INDEX
        assert _mod._resolve_index_dir(own, tmp_path / "worktree", tmp_path / "main") == own

    def test_keeps_own_path_when_main_root_unknown(self, tmp_path: Path) -> None:
        own = tmp_path / "worktree" / KNOWLEDGE_INDEX
        assert _mod._resolve_index_dir(own, tmp_path / "worktree", None) == own

    def test_main_checkout_root_from_a_worktree(self, tmp_path: Path) -> None:
        main = tmp_path / "main"
        main.mkdir()
        git = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "init.defaultBranch=main"]
        subprocess.run([*git, "init", "-q", str(main)], check=True)
        subprocess.run([*git, "-C", str(main), "commit", "-q", "--allow-empty", "-m", "x"], check=True)
        subprocess.run([*git, "-C", str(main), "worktree", "add", "-q", str(tmp_path / "wt")], check=True)
        assert _mod._main_checkout_root(tmp_path / "wt") == main.resolve()
        assert _mod._main_checkout_root(main) == main.resolve()

    def test_main_checkout_root_outside_git_is_none(self, tmp_path: Path) -> None:
        assert _mod._main_checkout_root(tmp_path) is None


# --- TCK-20261012-SEARCH-MCP-SHARED-MODEL: _run_search asks the shared server first, else searches in-process ---


class TestSharedServerWiring:
    def test_a_shared_answer_is_used_and_the_local_search_is_not_run(self, monkeypatch):
        shared = [{"doc_id": "from-server"}]
        monkeypatch.setattr(_mod._ss, "try_search_ex", lambda *a, **k: (shared, None))
        monkeypatch.setattr(_mod, "_search", lambda *a, **k: pytest.fail("must not search in-process"))
        assert _mod._run_search("q") == shared

    def test_no_shared_answer_falls_back_to_the_in_process_search(self, monkeypatch):
        monkeypatch.setattr(_mod._ss, "try_search_ex", lambda *a, **k: (None, "no server ready"))
        monkeypatch.setattr(_mod, "_search", lambda *a, **k: [{"doc_id": "local"}])
        assert _mod._run_search("q") == [{"doc_id": "local"}]

    def test_the_request_carries_the_query_arguments_and_this_index(self, monkeypatch):
        seen: dict = {}

        def fake(db, query, top_k, section, mode):
            seen.update(db=db, query=query, top_k=top_k, section=section, mode=mode)
            return None, "no server ready"

        monkeypatch.setattr(_mod._ss, "try_search_ex", fake)
        monkeypatch.setattr(_mod, "_search", lambda *a, **k: [])
        _mod._run_search("damage", top_k=3, section="mechanics", mode="vector")
        assert seen == {"db": _mod._DB_PATH, "query": "damage", "top_k": 3, "section": "mechanics", "mode": "vector"}

    def test_the_server_runs_the_same_function_the_in_process_path_runs(self):
        """By construction: search_shared serves `search_mcp._search`, never a second search path."""
        text = (_REPO_ROOT / "tools" / "search_shared.py").read_text(encoding="utf-8")
        assert "return mcp._search(query, **kwargs)" in text and "serve(_reloading(mcp)" in text


class TestSearchReadsOneLexicalGeneration:
    """`_search` reads `_STATE.lexical` once, so a reload published between its reads cannot mix generations."""

    def test_a_swap_between_the_bm25_and_doc_id_reads_is_never_seen(self, tmp_path, monkeypatch):
        fake_db = tmp_path / "knowledge.db"
        fake_db.write_bytes(b"x")
        monkeypatch.setattr(_mod, "_DB_PATH", fake_db)
        monkeypatch.setitem(sys.modules, "sqlite_vec", MagicMock())
        monkeypatch.setattr(_mod, "sqlite3", MagicMock())
        model = MagicMock()
        model.encode.return_value.tolist.return_value = [0.0] * 8
        _mod._STATE.model = model
        _mod._STATE.lexical = ("bm25-gen1", ["ids-gen1"])
        _mod._STATE.ready = True

        def swapping_bm25(self):
            value = self.lexical[0]
            self.lexical = ("bm25-gen2", ["ids-gen2"])  # a reload lands right after the first read
            return value

        monkeypatch.setattr(_mod._State, "bm25", property(swapping_bm25), raising=True)
        captured: dict = {}

        def fake_fuse(**kwargs):
            captured.update(bm25=kwargs["bm25_obj"], ids=kwargs["bm25_doc_ids"])
            return []

        monkeypatch.setattr(_mod._hr, "hybrid_fuse_and_filter", fake_fuse)
        _mod._search("anything", top_k=3)
        assert (captured["bm25"], captured["ids"][0]) in {("bm25-gen1", "ids-gen1"), ("bm25-gen2", "ids-gen2")}
        assert captured["bm25"].split("-")[1] == captured["ids"][0].split("-")[1]


# --- TCK-20261018-SEARCH-SHARED-SINGLE-SERVER-FROM-MAIN-CHECKOUT: starting server, degraded answers, one log line per transition ---


class TestSingleServerFallbacks:
    @pytest.fixture(autouse=True)
    def _fresh_mode(self, monkeypatch):
        monkeypatch.setitem(_mod._LAST_MODE, "mode", None)

    @pytest.fixture
    def loads(self, monkeypatch):
        """A fake embedder: counts every model load the in-process path attempts. Never the real model."""
        count = {"n": 0}

        def ensure() -> bool:
            count["n"] += 1
            return False  # `_search` then answers "index not found" without any model

        monkeypatch.setattr(_mod, "_ensure_loaded", ensure)
        return count

    def test_a_starting_server_gets_a_lexical_only_degraded_answer_and_no_model_load(self, monkeypatch, loads):
        monkeypatch.setattr(_mod._ss, "try_search_ex", lambda *a, **k: (None, _mod._ss.REASON_STARTING))
        monkeypatch.setattr(_mod, "_search_lexical", lambda q, **k: [{"doc_id": "kw"}])
        out = _mod._search_shared_or_local("q")
        assert out == {"results": [{"doc_id": "kw"}], "degraded": "lexical_only_server_starting"}
        assert loads["n"] == 0

    @pytest.mark.parametrize("reason", ["server not responding", "server was started from different code",
                                        "request failed: boom", "state directory is not private to this user"])
    def test_any_other_reason_searches_in_process_loading_the_model_once(self, monkeypatch, loads, reason):
        monkeypatch.setattr(_mod._ss, "try_search_ex", lambda *a, **k: (None, reason))
        _mod._search_shared_or_local("q")
        assert loads["n"] == 1

    def test_without_a_usable_lexical_index_a_starting_server_falls_back_in_process(self, monkeypatch, loads):
        monkeypatch.setattr(_mod._ss, "try_search_ex", lambda *a, **k: (None, _mod._ss.REASON_STARTING))
        monkeypatch.setattr(_mod, "_search_lexical", lambda q, **k: {"error": "lexical index not available"})
        _mod._search_shared_or_local("q")
        assert loads["n"] == 1

    def test_one_stderr_line_per_move_between_shared_lexical_and_in_process(self, monkeypatch, loads, capsys):
        script = iter([([1], None), ([2], None), (None, _mod._ss.REASON_STARTING), (None, _mod._ss.REASON_STARTING),
                       (None, "request failed: x"), (None, "request failed: x"), ([3], None)])
        monkeypatch.setattr(_mod._ss, "try_search_ex", lambda *a, **k: next(script))
        monkeypatch.setattr(_mod, "_search_lexical", lambda q, **k: [])
        for _ in range(7):
            _mod._search_shared_or_local("q")
        lines = capsys.readouterr().err.strip().splitlines()
        assert len(lines) == 4  # shared, lexical-only, in-process, shared again: never one per query
        assert lines[0].endswith("using shared server") and "lexical-only" in lines[1]
        assert "in-process fallback: request failed: x" in lines[2] and lines[3].endswith("using shared server")

    def test_the_degraded_answer_still_carries_the_staleness_warning(self, monkeypatch):
        monkeypatch.setattr(_mod._ss, "try_search_ex", lambda *a, **k: (None, _mod._ss.REASON_STARTING))
        monkeypatch.setattr(_mod, "_search_lexical", lambda q, **k: [{"doc_id": "kw"}])
        monkeypatch.setattr(_mod._ks, "index_staleness", lambda db: {"changed": 2, "new": 0, "removed": 0})
        out = _mod._run_search("q", with_staleness=True)
        assert out["degraded"] == "lexical_only_server_starting" and out["stale"]["changed"] == 2

    def test_search_lexical_ranks_by_bm25_alone_without_the_model(self, tmp_path, monkeypatch):
        db = tmp_path / "knowledge.db"
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE knowledge_docs (doc_id TEXT, path TEXT, heading TEXT, section TEXT, text TEXT, source_type TEXT)")
        con.executemany("INSERT INTO knowledge_docs VALUES (?,?,?,?,?,?)", [
            ("a", "docs/a.md", "A", "mechanics", "damage formula text", "doc"),
            ("b", "docs/b.md", "B", "engine", "kernel loop", "doc"),
            ("c", "docs/c.md", "C", "mechanics", "unrelated", "doc")])
        con.commit()
        con.close()

        class Bm25:
            @staticmethod
            def get_scores(tokens):
                return [2.0, 1.0, 0.0]

        monkeypatch.setattr(_mod, "_DB_PATH", db)
        monkeypatch.setattr(_mod._STATE, "lexical", (Bm25, ["a", "b", "c"]))
        monkeypatch.setattr(_mod, "_ensure_loaded", lambda: pytest.fail("the lexical path must not load the model"))
        out = _mod._search_lexical("damage", top_k=5)
        assert [r["doc_id"] for r in out] == ["a", "b"]  # zero-score "c" is not a hit
        assert out[0]["semantic_score"] == 0.0 and out[0]["score"] == 1.0 and out[0]["source_path"] == "docs/a.md"
        assert [r["doc_id"] for r in _mod._search_lexical("damage", top_k=5, section="engine")] == ["b"]
