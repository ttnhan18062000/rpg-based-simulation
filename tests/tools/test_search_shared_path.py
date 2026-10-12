"""TCK-20261012-SEARCH-MCP-SHARED-SERVER-AND-IDLE-UNLOAD: one ranking path for the MCP and the server, the proxy to the
shared server with silent in-process fallback, and the idle unload of the in-process model. No real model is loaded."""
from __future__ import annotations

import http.server
import importlib.util
import socket
import sqlite3
import sys
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_TOOLS = Path(__file__).parent.parent.parent / "tools"


def _load(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, _TOOLS / file)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def mcp():
    mod = _load("search_mcp_shared_test", "search_mcp.py")
    mod._server_check.update(at=None, usable=False)
    yield mod
    if mod._idle["timer"] is not None:
        mod._idle["timer"].cancel()


class _FakeScores(list):
    def max(self):
        return max(self) if self else 0.0


class _FakeBM25:
    def get_scores(self, tokens):
        return _FakeScores([0.0, 9.0])


def _make_db(path: Path) -> Path:
    con = sqlite3.connect(str(path))
    con.execute(
        "CREATE TABLE knowledge_docs (rowid INTEGER PRIMARY KEY, doc_id TEXT NOT NULL, path TEXT NOT NULL, "
        "text TEXT NOT NULL, source_type TEXT NOT NULL, heading TEXT NOT NULL DEFAULT '', section TEXT NOT NULL DEFAULT '')"
    )
    con.executemany(
        "INSERT INTO knowledge_docs VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(0, "doc-a", "docs/a.md", "alpha text", "doc_chunk", "A", "docs"),
         (1, "doc-rare", "docs/rare.md", "zzqfrobnicate_widget appears here", "doc_chunk", "Rare", "docs")],
    )
    con.commit()
    con.close()
    return path


def _ready(mod, db: Path, monkeypatch) -> None:
    monkeypatch.setattr(mod, "_DB_PATH", db)
    monkeypatch.setattr(
        mod._core._hr, "_dense_candidates",
        lambda conn, query_vec_bytes, dense_candidate_k: [(0, "doc-a", "docs/a.md", "A", "docs", "alpha text", "doc_chunk", 0.1)],
    )
    monkeypatch.setitem(sys.modules, "sqlite_vec", MagicMock())
    model = MagicMock()
    model.encode.return_value.tolist.return_value = [0.0] * 8
    mod._STATE.model, mod._STATE.bm25, mod._STATE.doc_ids, mod._STATE.ready = model, _FakeBM25(), ["doc-a", "doc-rare"], True


# ── AC1: the server and the MCP rank through the same function ────────────────

def test_server_and_mcp_return_the_same_ids_in_the_same_order(mcp, tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    db = _make_db(tmp_path / "knowledge.db")
    _ready(mcp, db, monkeypatch)
    server = _load("search_server_shared_test", "search_server.py")
    monkeypatch.setattr(server, "_DB_PATH", db)
    monkeypatch.setattr(server, "_INDEX_DIR", tmp_path)
    monkeypatch.setattr(server, "_APP_STATE", server._AppState(
        model=mcp._STATE.model, bm25=mcp._STATE.bm25, doc_ids=mcp._STATE.doc_ids, doc_count=2, chunk_count=2, ready=True))

    via_mcp = mcp._search("zzqfrobnicate_widget", top_k=5)
    with TestClient(server.app, raise_server_exceptions=False) as client:
        body = client.post("/api/search", json={"query": "zzqfrobnicate_widget", "top_k": 5}).json()

    assert [r["doc_id"] for r in via_mcp] == [r["doc_id"] for r in body["results"]] != []
    assert "doc-rare" in [r["doc_id"] for r in via_mcp]
    assert [r["score"] for r in via_mcp] == [r["score"] for r in body["results"]]


def test_server_search_response_may_carry_a_stale_block():
    server = _load("search_server_shared_test2", "search_server.py")
    resp = server.SearchResponse(query="q", top_k=1, results=[], stale={"changed": 1, "new": 0, "removed": 0})
    assert resp.model_dump()["stale"] == {"changed": 1, "new": 0, "removed": 0}
    assert server.SearchResponse(query="q", top_k=1, results=[]).stale is None


def test_server_health_exposes_the_index_fingerprint(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    db = _make_db(tmp_path / "knowledge.db")
    server = _load("search_server_shared_test3", "search_server.py")
    monkeypatch.setattr(server, "_DB_PATH", db)
    monkeypatch.setattr(server, "_INDEX_DIR", tmp_path)
    monkeypatch.setattr(server, "_APP_STATE", server._AppState(ready=True, doc_count=1, chunk_count=1))
    with TestClient(server.app, raise_server_exceptions=False) as client:
        body = client.get("/api/health").json()
    assert body["index_fingerprint"] == server._core.index_fingerprint(db) is not None


# ── Proxy: used only when the server serves the same index ────────────────────

def _fake_http(health, search):
    calls = []

    def fake(method, url, timeout, payload=None):
        calls.append((method, url))
        return health if url.endswith("/api/health") else search
    return fake, calls


def _proxy_setup(mcp, tmp_path, monkeypatch, *, health, search):
    db = _make_db(tmp_path / "knowledge.db")
    monkeypatch.setattr(mcp, "_DB_PATH", db)
    monkeypatch.setattr(mcp, "_search", MagicMock(return_value=[{"doc_id": "in-process"}]))
    monkeypatch.delenv(mcp.SHARED_OFF_ENV, raising=False)
    fake, calls = _fake_http(health(mcp._core.index_fingerprint(db)) if callable(health) else health, search)
    monkeypatch.setattr(mcp, "_http_json", fake)
    return calls


def test_proxy_is_used_when_the_server_serves_the_same_index(mcp, tmp_path, monkeypatch):
    calls = _proxy_setup(mcp, tmp_path, monkeypatch,
                         health=lambda fp: {"status": "ok", "index_fingerprint": fp},
                         search={"results": [{"doc_id": "from-server", "text": "dropped"}]})
    out = mcp._run_search("damage", top_k=3)
    assert out == [{"doc_id": "from-server"}]
    mcp._search.assert_not_called()
    assert ("POST", "http://127.0.0.1:8765/api/search") in calls


def test_health_verdict_is_cached(mcp, tmp_path, monkeypatch):
    calls = _proxy_setup(mcp, tmp_path, monkeypatch,
                         health=lambda fp: {"status": "ok", "index_fingerprint": fp}, search={"results": []})
    mcp._run_search("a")
    mcp._run_search("b")
    assert [c for c in calls if c[0] == "GET"] == [("GET", "http://127.0.0.1:8765/api/health")]


@pytest.mark.parametrize("health", [
    None,                                                       # refused / timeout / 503 -> _http_json gives None
    {"status": "ok", "index_fingerprint": "someone-elses:1"},    # a different index
    {"status": "degraded", "index_fingerprint": "x"},
])
def test_falls_back_in_process_when_the_server_is_unusable(mcp, tmp_path, monkeypatch, health):
    _proxy_setup(mcp, tmp_path, monkeypatch, health=health, search={"results": []})
    assert mcp._run_search("damage") == [{"doc_id": "in-process"}]


def test_falls_back_in_process_when_the_search_call_fails(mcp, tmp_path, monkeypatch):
    _proxy_setup(mcp, tmp_path, monkeypatch, health=lambda fp: {"status": "ok", "index_fingerprint": fp}, search=None)
    assert mcp._run_search("damage") == [{"doc_id": "in-process"}]
    assert mcp._server_check["at"] is None  # the next query re-checks the server


def test_proxy_can_be_switched_off(mcp, tmp_path, monkeypatch):
    calls = _proxy_setup(mcp, tmp_path, monkeypatch, health=lambda fp: {"status": "ok", "index_fingerprint": fp}, search={"results": []})
    monkeypatch.setenv(mcp.SHARED_OFF_ENV, "off")
    assert mcp._run_search("damage") == [{"doc_id": "in-process"}]
    assert calls == []


def test_staleness_is_computed_locally_on_the_proxy_path(mcp, tmp_path, monkeypatch):
    _proxy_setup(mcp, tmp_path, monkeypatch, health=lambda fp: {"status": "ok", "index_fingerprint": fp},
                 search={"results": [{"doc_id": "from-server"}], "stale": {"changed": 99, "new": 0, "removed": 0}})
    monkeypatch.setattr(mcp._ks, "index_staleness", lambda db: {"changed": 1, "new": 2, "removed": 3}, raising=False)
    out = mcp._run_search("damage", with_staleness=True)
    assert out == {"results": [{"doc_id": "from-server"}], "stale": {"changed": 1, "new": 2, "removed": 3}}


# ── The HTTP helper against a real socket: refused, 503, slow ─────────────────

class _Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path == "/slow":
            time.sleep(1.0)
        code = 503 if self.path == "/503" else 200
        body = b'{"status": "ok"}' if code == 200 else b'{"detail": "Index not loaded"}'
        try:
            self.send_response(code)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except OSError:  # the client timed out and left (the /slow case)
            pass


@pytest.fixture()
def live_server():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def test_http_json_ok_503_refused_and_timeout(mcp, live_server):
    assert mcp._http_json("GET", f"{live_server}/ok", 2.0) == {"status": "ok"}
    assert mcp._http_json("GET", f"{live_server}/503", 2.0) is None
    assert mcp._http_json("GET", f"{live_server}/slow", 0.2) is None
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    assert mcp._http_json("GET", f"http://127.0.0.1:{port}/x", 1.0) is None


# ── Idle unload ────────────────────────────────────────────────────────────────

class _FakeTimer:
    instances: list = []

    def __init__(self, delay, fn):
        self.delay, self.fn, self.daemon, self.started, self.cancelled = delay, fn, False, False, False
        _FakeTimer.instances.append(self)

    def start(self):
        self.started = True

    def cancel(self):
        self.cancelled = True


@pytest.fixture()
def clock(mcp, tmp_path, monkeypatch):
    _FakeTimer.instances = []
    now = {"t": 1000.0}
    monkeypatch.setattr(mcp, "_CLOCK", lambda: now["t"])
    monkeypatch.setattr(mcp, "_TIMER_FACTORY", _FakeTimer)
    monkeypatch.setenv(mcp.IDLE_UNLOAD_ENV, "600")
    monkeypatch.setattr(mcp, "_release_memory", MagicMock())
    _ready(mcp, _make_db(tmp_path / "knowledge.db"), monkeypatch)
    return now


def test_a_query_arms_a_daemon_timer_and_idle_expiry_unloads(mcp, clock):
    mcp._search("zzqfrobnicate_widget")
    timer = _FakeTimer.instances[-1]
    assert timer.started and timer.daemon and timer.delay == 600
    clock["t"] += 601
    timer.fn()
    assert mcp._STATE.ready is False and mcp._STATE.model is None and mcp._STATE.bm25 is None and mcp._STATE.doc_ids == []
    mcp._release_memory.assert_called_once()


def test_a_later_query_cancels_the_timer_and_a_raced_timer_rearms(mcp, clock):
    mcp._search("zzqfrobnicate_widget")
    first = _FakeTimer.instances[-1]
    clock["t"] += 300
    mcp._search("zzqfrobnicate_widget")
    assert first.cancelled and _FakeTimer.instances[-1] is not first
    clock["t"] += 400   # the first timer would have fired by now, but only 400s passed since the last query
    first.fn()
    assert mcp._STATE.ready is True
    assert _FakeTimer.instances[-1].delay == pytest.approx(200)


def test_zero_never_unloads(mcp, clock, monkeypatch):
    monkeypatch.setenv(mcp.IDLE_UNLOAD_ENV, "0")
    mcp._search("zzqfrobnicate_widget")
    assert _FakeTimer.instances == []
    assert mcp._unload_if_idle() is False and mcp._STATE.ready is True


def test_next_query_reloads_after_unload(mcp, clock, monkeypatch):
    fake_model = MagicMock()
    fake_model.encode.return_value.tolist.return_value = [0.0] * 8
    loader = MagicMock(return_value=fake_model)
    monkeypatch.setitem(sys.modules, "sentence_transformers", MagicMock(SentenceTransformer=loader))
    monkeypatch.setattr(mcp._ks, "_load_bm25", lambda path: (_FakeBM25(), ["doc-a", "doc-rare"]), raising=False)
    mcp._search("zzqfrobnicate_widget")
    clock["t"] += 601
    _FakeTimer.instances[-1].fn()
    assert mcp._STATE.ready is False
    out = mcp._search("zzqfrobnicate_widget")
    loader.assert_called_once()
    assert mcp._STATE.ready is True and "doc-rare" in [r["doc_id"] for r in out]


@pytest.mark.parametrize("raw,expected", [(None, 600.0), ("", 600.0), ("30", 30.0), ("0", 0.0), ("-5", 0.0), ("junk", 600.0)])
def test_idle_setting_parsing(mcp, monkeypatch, raw, expected):
    if raw is None:
        monkeypatch.delenv(mcp.IDLE_UNLOAD_ENV, raising=False)
    else:
        monkeypatch.setenv(mcp.IDLE_UNLOAD_ENV, raw)
    assert mcp._idle_unload_seconds() == expected


# ── search_health names the path and whether the model is loaded ──────────────

def test_health_reports_path_and_model_state(mcp, tmp_path, monkeypatch):
    db = _make_db(tmp_path / "knowledge.db")
    monkeypatch.setattr(mcp, "_DB_PATH", db)
    mcp._STATE.ready = False
    monkeypatch.setattr(mcp, "_shared_server_usable", lambda: False)
    health = mcp._run_health()
    assert health["path"] == "in-process" and health["model_loaded"] is False
    monkeypatch.setattr(mcp, "_shared_server_usable", lambda: True)
    assert mcp._run_health()["path"] == "shared-server"


# ── Reviewer fix: the fingerprint is the index the server LOADED, and covers bm25.pkl ──

def test_fingerprint_covers_bm25_pickle(tmp_path):
    core = _load("search_core_fp_test", "search_core.py")
    db = _make_db(tmp_path / "knowledge.db")
    without = core.index_fingerprint(db)
    (tmp_path / "bm25.pkl").write_bytes(b"one")
    with_bm25 = core.index_fingerprint(db)
    (tmp_path / "bm25.pkl").write_bytes(b"changed!")
    assert len({without, with_bm25, core.index_fingerprint(db)}) == 3
    assert core.index_fingerprint(tmp_path / "missing.db") is None


def test_health_keeps_reporting_the_loaded_index_after_the_files_change(mcp, tmp_path, monkeypatch):
    """After `make knowledge-index-update` the server still holds the old BM25, so it must not look current."""
    from fastapi.testclient import TestClient

    db = _make_db(tmp_path / "knowledge.db")
    (tmp_path / "bm25.pkl").write_bytes(b"old")
    server = _load("search_server_shared_test4", "search_server.py")
    loaded = server._core.index_fingerprint(db)
    monkeypatch.setattr(server, "_DB_PATH", db)
    monkeypatch.setattr(server, "_INDEX_DIR", tmp_path)
    monkeypatch.setattr(server, "_APP_STATE", server._AppState(ready=True, doc_count=1, chunk_count=1, index_fingerprint=loaded))

    (tmp_path / "bm25.pkl").write_bytes(b"rebuilt-by-knowledge-index-update")   # the index is rebuilt under the running server
    with TestClient(server.app, raise_server_exceptions=False) as client:
        reported = client.get("/api/health").json()["index_fingerprint"]
    assert reported == loaded != server._core.index_fingerprint(db)

    # a session that now resolves the rebuilt index does not match, so it searches in-process
    monkeypatch.setattr(mcp, "_DB_PATH", db)
    monkeypatch.setattr(mcp, "_http_json", lambda *a, **k: {"status": "ok", "index_fingerprint": reported})
    mcp._server_check.update(at=None, usable=False)
    assert mcp._shared_server_usable() is False
