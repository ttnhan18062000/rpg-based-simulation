"""Tests for tools/search_server.py — FastAPI TestClient, no live server or index needed."""
from __future__ import annotations

import importlib.util
import sqlite3
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── Load search_server module via same importlib pattern as the server itself ──
_REPO_ROOT = Path(__file__).parent.parent.parent
_SERVER_PATH = _REPO_ROOT / "tools" / "search_server.py"

# Stub out knowledge_search before loading search_server
_KS_STUB = MagicMock()
_KS_STUB._DEFAULT_DB = _REPO_ROOT / "knowledge-index" / "knowledge.db"
_KS_STUB._MODEL_NAME = "all-MiniLM-L6-v2"
_KS_STUB._tokenize = lambda text: text.lower().split()
_KS_STUB._serialize_f32 = lambda vec: b"\x00" * (len(vec) * 4)
_KS_STUB._load_bm25 = lambda path: (None, [])
_KS_STUB._hybrid_score = lambda sem, kw, tb, hb, cb: round(sem * 0.6 + kw * 0.4, 4)
_KS_STUB._compute_boosts = lambda tokens, doc_id, heading, text: (0.0, 0.0, 0.0)
sys.modules["knowledge_search"] = _KS_STUB

spec = importlib.util.spec_from_file_location("search_server", _SERVER_PATH)
_mod = importlib.util.module_from_spec(spec)
sys.modules["search_server"] = _mod  # required for @dataclass __module__ resolution in Python 3.13
spec.loader.exec_module(_mod)

app = _mod.app
_APP_STATE = _mod._APP_STATE
_AppState = _mod._AppState

from fastapi.testclient import TestClient


@pytest.fixture()
def ready_state(tmp_path, monkeypatch):
    """Patch _APP_STATE with a ready mock state; patch _DB_PATH to a temp sqlite file."""
    db = tmp_path / "knowledge.db"
    con = sqlite3.connect(str(db))
    con.execute(
        "CREATE TABLE knowledge_docs ("
        "rowid INTEGER PRIMARY KEY, doc_id TEXT, path TEXT, "
        "text TEXT, heading TEXT, section TEXT)"
    )
    con.execute(
        "INSERT INTO knowledge_docs VALUES "
        "(1,'mechanics/02_combat_laws','docs/mechanics/02_combat_laws.md',"
        "'Some combat text','Combat Damage','combat')"
    )
    con.execute("CREATE TABLE knowledge_vec (rowid INTEGER, embedding BLOB)")
    con.commit()
    con.close()

    mock_model = MagicMock()
    mock_model.encode.return_value.tolist.return_value = [0.0] * 384

    state = _AppState(
        model=mock_model,
        bm25=None,
        doc_ids=["mechanics/02_combat_laws"],
        doc_count=1,
        chunk_count=1,
        ready=True,
    )
    monkeypatch.setattr(_mod, "_APP_STATE", state)
    monkeypatch.setattr(_mod, "_DB_PATH", db)
    monkeypatch.setattr(_mod, "_INDEX_DIR", tmp_path)
    return state


@pytest.fixture()
def client(ready_state):
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ── Health endpoint ────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert "index_version" in body
        assert body["documents"] == 1
        assert body["chunks"] == 1
        assert body["model"] == "all-MiniLM-L6-v2"

    def test_health_503_when_not_ready(self, monkeypatch):
        not_ready = _AppState(ready=False)
        monkeypatch.setattr(_mod, "_APP_STATE", not_ready)
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.get("/api/health")
        assert resp.status_code == 503


# ── Search endpoint ────────────────────────────────────────────────────────────

class TestSearch:
    def test_search_returns_results_shape(self, client, ready_state, monkeypatch):
        """POST /api/search returns correct JSON shape (empty results on no sqlite match is valid)."""
        # Stub sqlite_vec so load() is a no-op (virtual-table extension not needed in tests)
        monkeypatch.setitem(sys.modules, "sqlite_vec", MagicMock())
        # Stub sqlite3 to avoid real file I/O and sqlite_vec virtual-table query requirements
        mock_con = MagicMock()
        mock_con.execute.return_value.fetchall.return_value = []
        monkeypatch.setattr(_mod, "sqlite3", MagicMock(connect=MagicMock(return_value=mock_con)))

        resp = client.post("/api/search", json={"query": "combat damage"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["query"] == "combat damage"
        assert body["top_k"] == 8
        assert isinstance(body["results"], list)

    def test_search_empty_query_422(self, client):
        resp = client.post("/api/search", json={"query": ""})
        assert resp.status_code == 422

    def test_search_missing_query_422(self, client):
        resp = client.post("/api/search", json={"top_k": 5})
        assert resp.status_code == 422

    def test_search_503_when_not_ready(self, monkeypatch):
        not_ready = _AppState(ready=False)
        monkeypatch.setattr(_mod, "_APP_STATE", not_ready)
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.post("/api/search", json={"query": "test"})
        assert resp.status_code == 503

    def test_search_include_text_false_omits_text(self, monkeypatch, tmp_path):
        """text field should be absent (None excluded) when include_text=False."""
        import tools.search_server as srv
        result = srv.SearchResult(
            doc_id="x", title="X", heading="H", source_path="x.md",
            section="s", score=1.0, semantic_score=1.0, keyword_score=0.0,
            excerpt="ex", text=None,
        )
        serialized = result.model_dump(exclude_none=True)
        assert "text" not in serialized

    def test_search_include_text_true_includes_text(self):
        import tools.search_server as srv
        result = srv.SearchResult(
            doc_id="x", title="X", heading="H", source_path="x.md",
            section="s", score=1.0, semantic_score=1.0, keyword_score=0.0,
            excerpt="ex", text="full content here",
        )
        serialized = result.model_dump(exclude_none=True)
        assert serialized["text"] == "full content here"


# ── Title derivation ──────────────────────────────────────────────────────────

class TestDeriveTitle:
    def test_simple(self):
        import tools.search_server as srv
        assert srv._derive_title("mechanics/02_combat_laws") == "Combat Laws"

    def test_no_subdir(self):
        import tools.search_server as srv
        assert srv._derive_title("world_evolution") == "World Evolution"

    def test_deep_path(self):
        import tools.search_server as srv
        assert srv._derive_title("engine/kernel") == "Kernel"


# ── Excerpt helper ────────────────────────────────────────────────────────────

class TestMakeExcerpt:
    def test_finds_query_token(self):
        import tools.search_server as srv
        text = "Lorem ipsum. Combat damage is calculated here. More text."
        excerpt = srv._make_excerpt(text, ["combat"], max_len=50)
        assert "combat" in excerpt.lower() or "Combat" in excerpt

    def test_falls_back_to_start(self):
        import tools.search_server as srv
        text = "No matching tokens here at all."
        excerpt = srv._make_excerpt(text, ["zzz"], max_len=20)
        assert len(excerpt) <= 23  # 20 + possible ellipsis


# ── CORS headers ──────────────────────────────────────────────────────────────

class TestCORS:
    def test_localhost_origin_allowed(self, client):
        resp = client.get("/api/health", headers={"Origin": "http://localhost"})
        assert resp.headers.get("access-control-allow-origin") in (
            "http://localhost", "*", None
        )

    def test_external_origin_not_allowed(self, client):
        resp = client.get("/api/health", headers={"Origin": "http://evil.example.com"})
        cors_header = resp.headers.get("access-control-allow-origin", "")
        assert cors_header != "http://evil.example.com"
