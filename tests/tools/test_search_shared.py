"""Tests for tools/search_shared.py: the shared search-model server and its client
(TCK-20261012-SEARCH-MCP-SHARED-MODEL, #520).

Every server here lives in a tmp XDG_RUNTIME_DIR and is torn down by the `servers` fixture; the autouse kill switch in
tests/tools/conftest.py is switched off only where a test needs the shared path.
"""
from __future__ import annotations

import importlib.util
import json
import os
import signal
import socket
import stat
import sys
import threading
import time
from pathlib import Path

import pytest

_TOOLS = Path(__file__).resolve().parents[2] / "tools"
_spec = importlib.util.spec_from_file_location("search_shared_under_test", _TOOLS / "search_shared.py")
ss = importlib.util.module_from_spec(_spec)
sys.modules["search_shared_under_test"] = ss
_spec.loader.exec_module(ss)

QUERIES = ["damage formula", "goal interruption", "import linter contracts", "working log append helper", "ecology"]


def _fake_search(query: str, top_k: int = 8, section: str | None = None, mode: str = "hybrid") -> list[dict]:
    """Deterministic stand-in with floats, ordering and a section filter, so a JSON round trip must be lossless."""
    seed = sum(map(ord, query))
    rows = [{"doc_id": f"{query}#{i}", "score": round(1 / (i + 1 + seed % 7), 4), "section": section or "all"}
            for i in range(top_k)]
    return sorted(rows, key=lambda r: r["score"], reverse=True)


_STUB = '''
import importlib.util, sys
spec = importlib.util.spec_from_file_location("search_shared", {path!r})
ss = importlib.util.module_from_spec(spec); sys.modules["search_shared"] = spec.loader.exec_module(ss) or ss
def fake(query, top_k=8, section=None, mode="hybrid"):
    seed = sum(map(ord, query))
    rows = [{{"doc_id": f"{{query}}#{{i}}", "score": round(1 / (i + 1 + seed % 7), 4), "section": section or "all"}}
            for i in range(top_k)]
    return sorted(rows, key=lambda r: r["score"], reverse=True)
import os
sys.exit(ss.serve(fake, __import__("pathlib").Path(sys.argv[1]), float(os.environ.get("RPG_SEARCH_IDLE_SECONDS", "30"))))
'''


@pytest.fixture
def shared_env(tmp_path, monkeypatch):
    """A tmp runtime dir, a fake index file, the shared path switched on, and a stub server command."""
    runtime = tmp_path / "run"
    runtime.mkdir(mode=0o700)
    db = tmp_path / "knowledge.db"
    db.write_bytes(b"x")
    stub = tmp_path / "stub_server.py"
    stub.write_text(_STUB.format(path=str(_TOOLS / "search_shared.py")))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime))
    monkeypatch.setenv("RPG_SEARCH_SHARED", "1")
    monkeypatch.setenv("RPG_SEARCH_SHARED_ALLOW_TEST_SPAWN", "1")
    monkeypatch.setenv("RPG_SEARCH_IDLE_SECONDS", "30")
    monkeypatch.setattr(ss, "_server_argv", lambda d: [sys.executable, str(stub), str(d)])
    yield db
    state = ss._read_state(ss.state_dir(db))
    if state is not None and int(state["pid"]) != os.getpid():  # in-thread servers share the pytest pid
        try:
            os.kill(int(state["pid"]), signal.SIGTERM)
        except OSError:
            pass
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and ss._read_state(ss.state_dir(db)) is not None:
            time.sleep(0.05)


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


# ── gate, key, version ───────────────────────────────────────────────────────

def test_kill_switch_forces_in_process_and_touches_nothing(tmp_path, monkeypatch):
    db = tmp_path / "knowledge.db"
    db.write_bytes(b"x")
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "run"))
    monkeypatch.setenv("RPG_SEARCH_SHARED", "0")
    assert ss.try_search(db, "q", 5, None, "hybrid") is None
    assert not (tmp_path / "run").exists()


def test_no_server_is_spawned_under_pytest_without_opt_in(shared_env, monkeypatch):
    monkeypatch.delenv("RPG_SEARCH_SHARED_ALLOW_TEST_SPAWN")
    assert ss.try_search(shared_env, "q", 5, None, "hybrid") is None
    assert ss._read_state(ss.state_dir(shared_env)) is None


def test_state_dir_key_is_the_resolved_path_not_the_contents(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    db = tmp_path / "a" / "knowledge.db"
    db.parent.mkdir()
    db.write_bytes(b"one")
    link = tmp_path / "link"
    link.symlink_to(db.parent)
    first = ss.state_dir(db)
    db.write_bytes(b"completely different content after a rebuild")
    assert ss.state_dir(db) == first == ss.state_dir(link / "knowledge.db")
    assert first.parent == tmp_path / "rpg-search"


def test_code_version_follows_the_result_deciding_files(tmp_path):
    for name in ss._CODE_FILES:
        (tmp_path / name).write_text("v1")
    before = ss.code_version(tmp_path)
    (tmp_path / "hybrid_retrieval.py").write_text("v2")
    assert ss.code_version(tmp_path) != before


# ── safety of the state directory and file ───────────────────────────────────

def test_client_refuses_a_group_or_other_accessible_state_dir(shared_env):
    directory = ss.state_dir(shared_env)
    assert ss._ensure_private_dir(directory)
    directory.chmod(0o755)
    assert ss.try_search(shared_env, "q", 5, None, "hybrid") is None
    assert not (directory / "server.json").exists()


def test_client_refuses_a_state_file_that_is_not_private(shared_env):
    directory = ss.state_dir(shared_env)
    assert ss._ensure_private_dir(directory)
    record = {"pid": os.getpid(), "port": 1, "token": "t", "db": str(shared_env), "code_version": ss.code_version()}
    path = directory / "server.json"
    path.write_text(json.dumps(record))
    path.chmod(0o644)
    assert ss._read_state(directory) is None
    path.chmod(0o600)
    assert ss._read_state(directory) == record


def test_state_file_is_written_atomically_with_mode_0600(tmp_path):
    ss._write_state(tmp_path, {"pid": 1})
    assert stat.S_IMODE((tmp_path / "server.json").stat().st_mode) == 0o600
    assert not list(tmp_path.glob("*.tmp"))


# ── lifecycle: spawn, attach, races, stale state, foreign port ───────────────

def test_first_call_spawns_a_server_and_answers_like_in_process(shared_env):
    for query in QUERIES:
        assert ss.try_search(shared_env, query, 5, None, "hybrid") == _fake_search(query, 5)
    assert ss.try_search(shared_env, "damage formula", 3, "mechanics", "hybrid") == _fake_search(
        "damage formula", 3, "mechanics")


def test_later_calls_attach_to_the_same_server(shared_env):
    ss.try_search(shared_env, "a", 2, None, "hybrid")
    pid = ss._read_state(ss.state_dir(shared_env))["pid"]
    ss.try_search(shared_env, "b", 2, None, "hybrid")
    assert ss._read_state(ss.state_dir(shared_env))["pid"] == pid


def test_two_sessions_starting_at_once_get_one_server(shared_env):
    answers: list = []

    def call() -> None:
        answers.append(ss.try_search(shared_env, "race", 3, None, "hybrid"))

    threads = [threading.Thread(target=call) for _ in range(6)]
    [t.start() for t in threads]
    [t.join(30) for t in threads]
    assert answers == [_fake_search("race", 3)] * 6
    pid = ss._read_state(ss.state_dir(shared_env))["pid"]
    assert _alive(pid)


def test_a_stale_state_file_is_replaced(shared_env):
    directory = ss.state_dir(shared_env)
    assert ss._ensure_private_dir(directory)
    ss._write_state(directory, {"pid": 2_000_000, "port": 1, "token": "stale", "db": str(shared_env),
                                "code_version": ss.code_version()})
    assert ss.try_search(shared_env, "q", 2, None, "hybrid") == _fake_search("q", 2)
    assert ss._read_state(directory)["pid"] != 2_000_000


def test_a_foreign_process_on_the_recorded_port_is_not_trusted(shared_env, monkeypatch):
    monkeypatch.setattr(ss, "READ_TIMEOUT", 1.0)  # the foreign listener accepts and never answers
    monkeypatch.setattr(ss, "CONNECT_TIMEOUT", 1.0)
    directory = ss.state_dir(shared_env)
    assert ss._ensure_private_dir(directory)
    foreign = socket.socket()
    foreign.bind(("127.0.0.1", 0))
    foreign.listen(1)
    try:
        ss._write_state(directory, {"pid": os.getpid(), "port": foreign.getsockname()[1], "token": "x",
                                    "db": str(shared_env), "code_version": ss.code_version()})
        assert ss.try_search(shared_env, "q", 2, None, "hybrid") == _fake_search("q", 2)
        assert ss._read_state(directory)["port"] != foreign.getsockname()[1]
    finally:
        foreign.close()


def test_a_server_from_different_code_is_never_used(shared_env, monkeypatch):
    directory = ss.state_dir(shared_env)
    assert ss._ensure_private_dir(directory)
    ss._write_state(directory, {"pid": os.getpid(), "port": 1, "token": "x", "db": str(shared_env),
                                "code_version": "an-older-version"})
    monkeypatch.setattr(ss, "_spawn", lambda *a: pytest.fail("must not spawn over a live mismatched server"))
    assert ss.try_search(shared_env, "q", 2, None, "hybrid") is None


def test_a_dead_server_falls_back_and_the_next_call_respawns(shared_env):
    ss.try_search(shared_env, "a", 2, None, "hybrid")
    pid = ss._read_state(ss.state_dir(shared_env))["pid"]
    os.kill(pid, signal.SIGKILL)
    deadline = time.monotonic() + 5
    while _alive(pid) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert ss.try_search(shared_env, "b", 2, None, "hybrid") == _fake_search("b", 2)
    assert ss._read_state(ss.state_dir(shared_env))["pid"] != pid


def test_a_spawn_that_never_becomes_ready_falls_back(shared_env, monkeypatch):
    monkeypatch.setattr(ss, "SPAWN_WAIT_SECONDS", 0.3)
    monkeypatch.setattr(ss, "_server_argv", lambda d: [sys.executable, "-c", "import time; time.sleep(1)"])
    assert ss.try_search(shared_env, "q", 2, None, "hybrid") is None


# ── the server itself: auth, concurrency, idle exit, reload ──────────────────

def _serve_in_thread(db: Path, search_fn, idle: float = 30.0):
    ready = threading.Event()
    result: dict = {}
    thread = threading.Thread(target=lambda: result.update(code=ss.serve(search_fn, db, idle, ready.set)), daemon=True)
    thread.start()
    assert ready.wait(10)
    return thread, result


def test_requests_without_the_token_are_refused(shared_env):
    _serve_in_thread(shared_env, _fake_search)
    state = ss._read_state(ss.state_dir(shared_env))
    with pytest.raises(OSError):
        ss._request({**state, "token": "wrong"}, "GET", "/health")
    assert ss._request(state, "GET", "/health")["status"] == "ok"


def test_two_parallel_queries_equal_the_same_two_run_one_after_the_other(shared_env):
    gate = threading.Barrier(2)

    def slow(query: str, **kw: object) -> list[dict]:
        time.sleep(0.05)
        return _fake_search(query, **kw)

    _serve_in_thread(shared_env, slow)
    state = ss._read_state(ss.state_dir(shared_env))
    body = lambda q: {"query": q, "top_k": 4, "section": None, "mode": "hybrid"}  # noqa: E731
    sequential = [ss._request(state, "POST", "/search", body(q)) for q in QUERIES[:2]]
    parallel: dict = {}

    def run(q: str) -> None:
        gate.wait()
        parallel[q] = ss._request(state, "POST", "/search", body(q))

    threads = [threading.Thread(target=run, args=(q,)) for q in QUERIES[:2]]
    [t.start() for t in threads]
    [t.join(10) for t in threads]
    assert [parallel[q] for q in QUERIES[:2]] == sequential


def test_encode_calls_never_overlap_behind_the_model_lock():
    class Probe:
        active = peak = 0

        def encode(self, *a: object, **k: object) -> int:
            Probe.active += 1
            Probe.peak = max(Probe.peak, Probe.active)
            time.sleep(0.02)
            Probe.active -= 1
            return 1

    locked = ss._LockedModel(Probe())
    threads = [threading.Thread(target=locked.encode, args=("q",)) for _ in range(8)]
    [t.start() for t in threads]
    [t.join(10) for t in threads]
    assert Probe.peak == 1


def test_the_server_exits_when_idle_and_removes_its_state(shared_env):
    thread, result = _serve_in_thread(shared_env, _fake_search, idle=0.4)
    thread.join(10)
    assert result["code"] == 0 and not thread.is_alive()
    assert ss._read_state(ss.state_dir(shared_env)) is None


def test_the_server_reloads_bm25_when_the_index_is_rebuilt(tmp_path):
    db = tmp_path / "knowledge.db"
    db.write_bytes(b"1")
    loads: list[int] = []

    class Ks:
        @staticmethod
        def _load_bm25(path: object) -> tuple[str, list[str]]:
            loads.append(1)
            return "bm25", ["d"]

    class State:
        bm25 = None
        doc_ids: list = []

    class Mcp:
        _DB_PATH = db
        _BM25_PATH = tmp_path / "bm25.pkl"
        _ks = Ks
        _STATE = State
        _search = staticmethod(lambda q, **k: [q])

    search = ss._reloading(Mcp)
    search("a")
    assert loads == []
    os.utime(db, (time.time() + 10, time.time() + 10))
    search("b")
    search("c")
    assert loads == [1] and State.bm25 == "bm25"
