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
    monkeypatch.setenv(ss.CODE_ROOT_ENV, str(_TOOLS.parent))  # the stub server hashes this checkout's tools
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
        lexical: tuple = (None, [])

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
    assert loads == [1] and State.lexical == ("bm25", ["d"])


def test_a_reload_during_a_search_in_flight_never_mixes_generations(tmp_path):
    """The in-flight search keeps the generation it read at entry; the reload publishes a new one by a single swap and
    does not wait for it; the next search sees the new one. The interleaving is forced with Events, not timing."""
    db = tmp_path / "knowledge.db"
    db.write_bytes(b"1")
    in_search, release = threading.Event(), threading.Event()
    seen: dict[str, tuple] = {}
    loads = {"n": 0}

    class Ks:
        @staticmethod
        def _load_bm25(path: object) -> list:
            loads["n"] += 1
            return [f"bm25-gen{loads['n']}", [f"ids-gen{loads['n']}"]]

    class State:
        lexical = ("bm25-gen0", ["ids-gen0"])

    def search_fn(query: str, **kw: object) -> list:
        bm25, ids = State.lexical  # read once at entry, as search_mcp._search does
        if query == "slow":
            in_search.set()
            assert release.wait(5)
        seen[query] = (bm25, ids[0])
        return [query]

    class Mcp:
        _DB_PATH = db
        _BM25_PATH = tmp_path / "bm25.pkl"
        _ks = Ks
        _STATE = State
        _search = staticmethod(search_fn)

    search = ss._reloading(Mcp)
    slow = threading.Thread(target=search, args=("slow",))
    slow.start()
    assert in_search.wait(5)
    os.utime(db, (time.time() + 10, time.time() + 10))
    search("fast")  # reloads while "slow" is parked inside its search, and must not wait for it
    assert loads["n"] == 1 and seen["fast"] == ("bm25-gen1", "ids-gen1")
    release.set()
    slow.join(5)
    assert seen["slow"] == ("bm25-gen0", "ids-gen0")  # old generation, whole: never bm25-gen0 with ids-gen1
    assert isinstance(State.lexical, tuple)


def test_the_server_refuses_to_serve_a_database_other_than_the_one_it_searches(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "run"))
    class Mcp:
        _DB_PATH = tmp_path / "searched.db"

        @staticmethod
        def _ensure_loaded() -> bool:
            pytest.fail("must refuse before loading the model")

    monkeypatch.setattr(ss, "_load_search_mcp", lambda: Mcp)
    assert ss._main(["serve", "--db", str(tmp_path / "other.db")]) == 1
    assert "refusing to serve" in capsys.readouterr().err


def test_the_server_accepts_the_database_it_searches_under_any_spelling(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "run"))
    real = tmp_path / "real"
    real.mkdir()
    (tmp_path / "alias").symlink_to(real)

    class Mcp:
        _DB_PATH = real / "knowledge.db"

        @staticmethod
        def _ensure_loaded() -> bool:
            return False  # stop right after the identity check passed

    monkeypatch.setattr(ss, "_load_search_mcp", lambda: Mcp)
    assert ss._main(["serve", "--db", str(tmp_path / "alias" / "knowledge.db")]) == 1  # reached _ensure_loaded


# ── TCK-20261018-SEARCH-SHARED-SINGLE-SERVER-FROM-MAIN-CHECKOUT ──────────────

_SLOW_STUB = '''
import importlib.util, os, sys, time
from pathlib import Path
spec = importlib.util.spec_from_file_location("search_shared", {path!r})
ss = importlib.util.module_from_spec(spec); sys.modules["search_shared"] = ss; spec.loader.exec_module(ss)
db = Path(sys.argv[1])
with open({launches!r}, "a") as f:
    f.write("launch\\n")
directory = ss.state_dir(db)
assert ss._ensure_private_dir(directory)
if not ss._claim_single_instance(directory):
    sys.exit(0)
with open({launches!r}, "a") as f:
    f.write("won\\n")
ss._write_starting(directory, os.getpid())
time.sleep(float(os.environ["STUB_LOAD_SECONDS"]))   # the model load, longer than SPAWN_WAIT_SECONDS
def fake(query, top_k=8, section=None, mode="hybrid"):
    return [{{"doc_id": query}}]
sys.exit(ss.serve(fake, db, 30.0))
'''


def _git(cwd, *args):
    import subprocess
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t"}
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, env=env)


@pytest.fixture
def two_checkouts(tmp_path, monkeypatch):
    """A main checkout and a linked worktree, each with a tools/ holding search_shared.py (the worktree's differs)."""
    main = tmp_path / "main"
    (main / "tools").mkdir(parents=True)
    (main / "tools" / "search_shared.py").write_text("main\n")
    _git(main, "init", "-q", "-b", "main")
    _git(main, "add", "-A")
    _git(main, "commit", "-q", "-m", "init")
    wt = tmp_path / "wt"
    _git(main, "worktree", "add", "-q", "-b", "wt", str(wt))
    (wt / "tools" / "search_shared.py").write_text("an edit in the worktree\n")
    monkeypatch.delenv(ss.CODE_ROOT_ENV, raising=False)
    monkeypatch.setattr(ss, "_TOOLS_DIR", wt / "tools")
    ss._own_main_root.cache_clear()
    yield main, wt
    ss._own_main_root.cache_clear()


def test_code_root_is_the_main_checkout_from_a_worktree_never_the_cwd(two_checkouts, tmp_path, monkeypatch):
    main, wt = two_checkouts
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    main_index = main / "agent-working" / ".index" / "knowledge.db"
    assert ss.code_tools_dir(main_index) == main / "tools"
    assert ss.code_tools_dir(tmp_path / "somewhere" / "knowledge.db") == main / "tools"


def test_a_worktree_with_its_own_index_keeps_its_own_code(two_checkouts):
    main, wt = two_checkouts
    assert ss.code_tools_dir(wt / "agent-working" / ".index" / "knowledge.db") == wt / "tools"


def test_code_root_falls_back_to_the_own_dir_outside_git_and_the_override_wins(tmp_path, monkeypatch):
    plain = tmp_path / "plain" / "tools"
    plain.mkdir(parents=True)
    monkeypatch.delenv(ss.CODE_ROOT_ENV, raising=False)
    monkeypatch.setattr(ss, "_TOOLS_DIR", plain)
    ss._own_main_root.cache_clear()
    try:
        assert ss.code_tools_dir(tmp_path / "knowledge.db") == plain
        monkeypatch.setenv(ss.CODE_ROOT_ENV, str(tmp_path / "chosen"))
        assert ss.code_tools_dir(tmp_path / "knowledge.db") == tmp_path / "chosen" / "tools"
    finally:
        ss._own_main_root.cache_clear()


def test_the_server_argv_runs_the_main_checkouts_search_shared(two_checkouts):
    main, wt = two_checkouts
    argv = ss._server_argv(main / "knowledge.db")
    assert argv[1] == str(main / "tools" / "search_shared.py") and argv[2:] == ["serve", "--db", str(main / "knowledge.db")]


def test_clients_whose_own_tools_differ_still_attach_to_the_one_server(shared_env, tmp_path, monkeypatch):
    """Two worktree clients with edited tools/ and one main client hash the SAME code root, so none falls back."""
    other = tmp_path / "edited" / "tools"
    other.mkdir(parents=True)
    for name in ss._CODE_FILES:
        (other / name).write_text("an edit that changes this copy's own hash")
    answers = [ss.try_search_ex(shared_env, "a", 2, None, "hybrid")]
    monkeypatch.setattr(ss, "_TOOLS_DIR", other)  # a worktree client: its own copy differs, the code root is pinned
    answers += [ss.try_search_ex(shared_env, "b", 2, None, "hybrid"), ss.try_search_ex(shared_env, "c", 2, None, "hybrid")]
    assert [a[1] for a in answers] == [None, None, None] and answers[2][0] == _fake_search("c", 2)
    assert len({ss._read_state(ss.state_dir(shared_env))["pid"]}) == 1


def _slow_server(tmp_path, monkeypatch, load_seconds: float):
    launches = tmp_path / "launches.log"
    stub = tmp_path / "slow_stub.py"
    stub.write_text(_SLOW_STUB.format(path=str(_TOOLS / "search_shared.py"), launches=str(launches)))
    monkeypatch.setenv("STUB_LOAD_SECONDS", str(load_seconds))
    monkeypatch.setattr(ss, "_server_argv", lambda d: [sys.executable, str(stub), str(d)])
    monkeypatch.setattr(ss, "SPAWN_WAIT_SECONDS", 0.6)
    return launches


def _wait_ready_for_teardown(db):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline and ss._read_state(ss.state_dir(db)) is None:
        time.sleep(0.1)


def test_clients_racing_a_slow_start_end_with_one_server_and_none_loads_a_model(shared_env, tmp_path, monkeypatch):
    launches = _slow_server(tmp_path, monkeypatch, load_seconds=2.0)
    results: list = []
    barrier = threading.Barrier(3)

    def client(i: int) -> None:
        barrier.wait()
        results.append(ss.try_search_ex(shared_env, f"q{i}", 2, None, "hybrid"))

    threads = [threading.Thread(target=client, args=(i,)) for i in range(3)]
    [t.start() for t in threads]
    [t.join(30) for t in threads]
    assert sorted(r[1] for r in results) == [ss.REASON_STARTING] * 3 and all(r[0] is None for r in results)
    _wait_ready_for_teardown(shared_env)
    lines = launches.read_text().split()
    assert lines.count("won") == 1 and lines.count("launch") == 1  # not even a losing second launch
    assert ss.try_search_ex(shared_env, "later", 2, None, "hybrid") == ([{"doc_id": "later"}], None)


def test_a_second_server_on_the_same_state_dir_exits_zero_without_loading(shared_env, monkeypatch):
    directory = ss.state_dir(shared_env)
    assert ss._ensure_private_dir(directory) and ss._claim_single_instance(directory)
    try:
        monkeypatch.setattr(ss, "_load_search_mcp", lambda: pytest.fail("a losing server must not load anything"))
        assert ss._main(["serve", "--db", str(shared_env)]) == 0
        assert ss._server_lock_held(directory)  # the holder's lock is untouched
    finally:
        ss._release_single_instance()
    assert not ss._server_lock_held(directory)


def test_a_killed_holders_lock_vanishes_with_its_pid(shared_env):
    import subprocess
    directory = ss.state_dir(shared_env)
    assert ss._ensure_private_dir(directory)
    code = ("import importlib.util,sys,time;from pathlib import Path;"
            f"s=importlib.util.spec_from_file_location('ss',{str(_TOOLS / 'search_shared.py')!r});m=importlib.util.module_from_spec(s);"
            "sys.modules['ss']=m;s.loader.exec_module(m);"
            f"assert m._claim_single_instance(Path({str(directory)!r}));print('held',flush=True);time.sleep(60)")
    child = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
    try:
        assert child.stdout.readline().strip() == "held"
        assert ss._server_lock_held(directory) and not ss._claim_single_instance(directory)
        child.kill()
        child.wait(10)
        assert not ss._server_lock_held(directory)
        assert ss._claim_single_instance(directory)  # the successor takes it with no manual cleanup
    finally:
        ss._release_single_instance()
        if child.poll() is None:
            child.kill()


def test_a_starting_record_with_a_dead_pid_is_stale_and_cleared_then_respawned(shared_env, monkeypatch):
    import subprocess
    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait()
    directory = ss.state_dir(shared_env)
    assert ss._ensure_private_dir(directory)
    ss._write_starting(directory, dead.pid)
    spawned: list = []
    monkeypatch.setattr(ss, "_spawn", lambda d, db: spawned.append(1) or os.getpid())
    monkeypatch.setattr(ss, "SPAWN_WAIT_SECONDS", 0.2)
    state, why = ss._attach_or_spawn(directory, shared_env)
    assert spawned == [1] and state is None and why == ss.REASON_STARTING


def test_a_live_young_starting_record_is_never_unlinked_or_respawned(shared_env, monkeypatch):
    directory = ss.state_dir(shared_env)
    assert ss._ensure_private_dir(directory)
    ss._write_starting(directory, os.getpid())
    monkeypatch.setattr(ss, "_spawn", lambda *a: pytest.fail("must not spawn over a starting server"))
    monkeypatch.setattr(ss, "SPAWN_WAIT_SECONDS", 0.2)
    assert ss._attach_or_spawn(directory, shared_env) == (None, ss.REASON_STARTING)
    assert ss._read_starting(directory)["pid"] == os.getpid()


def test_a_server_that_holds_the_lock_but_is_past_the_start_grace_is_reported_unresponsive(shared_env, monkeypatch):
    directory = ss.state_dir(shared_env)
    assert ss._ensure_private_dir(directory) and ss._claim_single_instance(directory)
    try:
        ss._write_state(directory, {"state": "starting", "pid": os.getpid(), "started": time.time() - ss.START_GRACE_SECONDS - 5})
        monkeypatch.setattr(ss, "_spawn", lambda *a: pytest.fail("a hung server still holds the lock: no second server"))
        monkeypatch.setattr(ss, "SPAWN_WAIT_SECONDS", 0.2)
        assert ss._attach_or_spawn(directory, shared_env) == (None, ss.REASON_UNRESPONSIVE)
    finally:
        ss._release_single_instance()


def test_two_indexes_get_two_servers_and_neither_respawns_on_repeat_queries(shared_env, tmp_path, monkeypatch):
    other = tmp_path / "other" / "knowledge.db"
    other.parent.mkdir()
    other.write_bytes(b"y")
    spawns: list = []
    real = ss._spawn
    monkeypatch.setattr(ss, "_spawn", lambda d, db: spawns.append(db) or real(d, db))
    for _ in range(3):
        for db in (shared_env, other):
            assert ss.try_search_ex(db, "q", 2, None, "hybrid")[0] == _fake_search("q", 2)
    pids = {ss._read_state(ss.state_dir(db))["pid"] for db in (shared_env, other)}
    assert len(spawns) == 2 and len(pids) == 2
    try:
        os.kill(ss._read_state(ss.state_dir(other))["pid"], signal.SIGTERM)
    except OSError:
        pass


# ── a pull changes the code under a live server: replace it, never fall back fleet-wide ─────────

_VERSIONED_STUB = '''
import importlib.util, os, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("search_shared", {path!r})
ss = importlib.util.module_from_spec(spec); sys.modules["search_shared"] = ss; spec.loader.exec_module(ss)
orig = ss.code_version
ss.code_version = lambda tools_dir=None: orig(Path(os.environ["STUB_CODE_ROOT"]) / "tools")
db = Path(sys.argv[1])
with open({launches!r}, "a") as f:
    f.write("launch\\n")
directory = ss.state_dir(db)
assert ss._ensure_private_dir(directory)
if not ss._claim_single_instance(directory):
    sys.exit(0)
ss._write_starting(directory, os.getpid())
def fake(query, top_k=8, section=None, mode="hybrid"):
    return [{{"doc_id": query}}]
sys.exit(ss.serve(fake, db, 30.0))
'''


@pytest.fixture
def code_roots(shared_env, tmp_path, monkeypatch):
    """Two code roots with different hashes, a stub server that reports the hash of STUB_CODE_ROOT, a launch log."""
    roots = []
    for name in ("old", "new"):
        tools = tmp_path / name / "tools"
        tools.mkdir(parents=True)
        for f in ss._CODE_FILES:
            (tools / f).write_text(f"{name} {f}")
        roots.append(tmp_path / name)
    launches = tmp_path / "launches.log"
    stub = tmp_path / "versioned_stub.py"
    stub.write_text(_VERSIONED_STUB.format(path=str(_TOOLS / "search_shared.py"), launches=str(launches)))
    monkeypatch.setattr(ss, "_server_argv", lambda d: [sys.executable, str(stub), str(d)])

    def use(root):
        monkeypatch.setenv(ss.CODE_ROOT_ENV, str(root))
        monkeypatch.setenv("STUB_CODE_ROOT", str(root))

    use(roots[0])
    return roots, launches, use


def test_a_server_on_old_code_is_replaced_and_the_client_answers_lexical_only_meanwhile(shared_env, code_roots):
    (old, new), launches, use = code_roots
    first, why = ss.try_search_ex(shared_env, "a", 2, None, "hybrid")
    assert why is None and first == [{"doc_id": "a"}]
    old_pid = ss._read_state(ss.state_dir(shared_env))["pid"]
    use(new)  # main was pulled: clients now hash the new code
    answer, reason = ss.try_search_ex(shared_env, "b", 2, None, "hybrid")
    assert (answer, reason) == (None, ss.REASON_STARTING)  # the caller answers lexical-only: no model in the client
    _wait_ready_for_teardown(shared_env)
    state = ss._read_state(ss.state_dir(shared_env))
    assert state["pid"] != old_pid and not _alive(old_pid)
    assert launches.read_text().split() == ["launch", "launch"]  # exactly one new launch
    assert ss.try_search_ex(shared_env, "c", 2, None, "hybrid") == ([{"doc_id": "c"}], None)


def test_clients_racing_after_a_pull_cause_exactly_one_new_launch(shared_env, code_roots):
    (old, new), launches, use = code_roots
    assert ss.try_search_ex(shared_env, "a", 2, None, "hybrid")[1] is None
    use(new)
    results: list = []
    barrier = threading.Barrier(3)

    def client(i: int) -> None:
        barrier.wait()
        results.append(ss.try_search_ex(shared_env, f"q{i}", 2, None, "hybrid"))

    threads = [threading.Thread(target=client, args=(i,)) for i in range(3)]
    [t.start() for t in threads]
    [t.join(30) for t in threads]
    assert all(r[0] is None and r[1] == ss.REASON_STARTING for r in results)
    _wait_ready_for_teardown(shared_env)
    assert launches.read_text().split() == ["launch", "launch"]


def test_a_stuck_old_server_that_keeps_its_lock_is_never_raced_by_a_second_spawn(shared_env, code_roots, monkeypatch):
    (old, new), launches, use = code_roots
    assert ss.try_search_ex(shared_env, "a", 2, None, "hybrid")[1] is None
    use(new)
    monkeypatch.setattr(ss, "RETIRE_WAIT_SECONDS", 0.3)
    monkeypatch.setattr(ss.os, "kill", lambda pid, sig: None)  # the old server ignores the signal and keeps its lock
    assert ss.try_search_ex(shared_env, "b", 2, None, "hybrid") == (None, ss.REASON_STARTING)
    assert launches.read_text().split() == ["launch"]


def _watch_sigterm(monkeypatch):
    sent: list = []
    real = os.kill
    monkeypatch.setattr(ss.os, "kill", lambda pid, sig: sent.append((pid, sig)) if sig == signal.SIGTERM else real(pid, sig))
    return sent


def test_a_client_whose_own_worktree_tools_are_older_never_terminates_a_matching_server(shared_env, code_roots, tmp_path, monkeypatch):
    (old, new), launches, use = code_roots
    assert ss.try_search_ex(shared_env, "a", 2, None, "hybrid")[1] is None
    pid = ss._read_state(ss.state_dir(shared_env))["pid"]
    older = tmp_path / "older_commit" / "tools"
    older.mkdir(parents=True)
    for f in ss._CODE_FILES:
        (older / f).write_text("an older commit's copy")
    monkeypatch.setattr(ss, "_TOOLS_DIR", older)  # this worktree's own copy differs; the code root is still the main checkout's
    sent = _watch_sigterm(monkeypatch)
    answer, reason = ss.try_search_ex(shared_env, "b", 2, None, "hybrid")
    assert (answer, reason) == ([{"doc_id": "b"}], None)  # attached: nothing for the caller to load
    assert sent == [] and ss._read_state(ss.state_dir(shared_env))["pid"] == pid
    assert launches.read_text().split() == ["launch"]


def test_an_own_index_worktree_client_never_touches_the_main_index_server(two_checkouts, shared_env, code_roots, monkeypatch):
    main, wt = two_checkouts
    (old, new), launches, use = code_roots
    assert ss.try_search_ex(shared_env, "a", 2, None, "hybrid")[1] is None
    main_pid = ss._read_state(ss.state_dir(shared_env))["pid"]
    own_db = wt / "agent-working" / ".index" / "knowledge.db"
    own_db.parent.mkdir(parents=True)
    own_db.write_bytes(b"z")
    monkeypatch.delenv(ss.CODE_ROOT_ENV)  # a plain worktree client: its own index means its own code root
    assert ss.code_tools_dir(own_db) == wt / "tools" and ss.state_dir(own_db) != ss.state_dir(shared_env)
    spawned: list = []
    monkeypatch.setattr(ss, "_spawn", lambda d, db: spawned.append((d, db)) or os.getpid())
    monkeypatch.setattr(ss, "SPAWN_WAIT_SECONDS", 0.2)
    sent = _watch_sigterm(monkeypatch)
    ss.try_search_ex(own_db, "b", 2, None, "hybrid")
    assert [db for _, db in spawned] == [own_db] and sent == []
    assert ss._read_state(ss.state_dir(shared_env))["pid"] == main_pid and _alive(main_pid)


def test_a_live_pid_whose_start_time_differs_is_never_signalled(shared_env, code_roots, monkeypatch):
    (old, new), launches, use = code_roots
    assert ss.try_search_ex(shared_env, "a", 2, None, "hybrid")[1] is None
    directory = ss.state_dir(shared_env)
    record = ss._read_state(directory)
    assert record["starttime"] == ss._proc_starttime(record["pid"])  # the server recorded its own identity
    ss._write_state(directory, {**record, "starttime": "1"})  # the pid is live but is not the process that wrote this
    use(new)
    sent = _watch_sigterm(monkeypatch)
    monkeypatch.setattr(ss, "RETIRE_WAIT_SECONDS", 0.3)
    assert ss.try_search_ex(shared_env, "b", 2, None, "hybrid") == (None, ss.REASON_STARTING)
    assert sent == [] and _alive(record["pid"]) and launches.read_text().split() == ["launch"]


# ── TCK-20261018-SEARCH-SHARED-SERVER-CWD-AND-TEST-RUNTIME-ISOLATION ─────────

def test_the_spawn_runs_the_server_in_the_main_checkout_not_the_spawning_cwd(shared_env, two_checkouts, monkeypatch, tmp_path):
    main, wt = two_checkouts
    seen: dict = {}

    class FakePopen:
        pid = 4242

        def __init__(self, argv, **kwargs):
            seen.update(kwargs)

    ss._own_main_root()  # resolve (one git call) before Popen is faked
    monkeypatch.setattr(ss.subprocess, "Popen", FakePopen)
    monkeypatch.chdir(tmp_path)  # the spawning client's cwd is somewhere else entirely
    directory = ss.state_dir(shared_env)
    assert ss._ensure_private_dir(directory)
    assert ss._spawn(directory, shared_env) == 4242
    assert Path(seen["cwd"]).resolve() == main.resolve()


def test_the_spawn_cwd_falls_back_to_the_code_roots_parent_outside_git(tmp_path, monkeypatch):
    tools = tmp_path / "plain" / "tools"
    tools.mkdir(parents=True)
    monkeypatch.delenv(ss.CODE_ROOT_ENV, raising=False)
    monkeypatch.setattr(ss, "_TOOLS_DIR", tools)
    ss._own_main_root.cache_clear()
    try:
        assert ss._server_cwd(tmp_path / "knowledge.db") == tools.parent
    finally:
        ss._own_main_root.cache_clear()


def test_every_tools_test_runs_in_a_tmp_runtime_dir_not_the_real_one(tmp_path):
    real = Path(os.environ[ss.TEST_REAL_BASE_ENV])
    runtime = Path(os.environ["XDG_RUNTIME_DIR"]).resolve()
    assert runtime != real and runtime.is_dir() and runtime != tmp_path.resolve()
    assert runtime.is_relative_to(tmp_path.resolve().parent)  # under the pytest basetemp, beside the test's own tmp_path


def test_state_dir_refuses_the_real_runtime_dir_under_pytest(tmp_path, monkeypatch):
    """The guard is deterministic: it compares the base path with the one captured at conftest import, and never looks
    at what live sessions have written there."""
    db = tmp_path / "knowledge.db"
    real = os.environ[ss.TEST_REAL_BASE_ENV]
    monkeypatch.setenv("XDG_RUNTIME_DIR", real)
    with pytest.raises(RuntimeError, match="real runtime dir"):
        ss.state_dir(db)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "ok"))
    assert ss.state_dir(db).parent == tmp_path / "ok" / "rpg-search"
    monkeypatch.delenv("XDG_RUNTIME_DIR")  # the tempdir fallback is guarded too when it is the captured base
    monkeypatch.setenv(ss.TEST_REAL_BASE_ENV, str(Path(ss.tempfile.gettempdir()) / f"rpg-search-{os.getuid()}"))
    with pytest.raises(RuntimeError):
        ss.state_dir(db)


def test_the_server_main_creates_its_lock_only_inside_the_tmp_runtime_dir(tmp_path, monkeypatch):
    """The two tests that call `_main` created `server.lock`-only dirs in the real runtime dir (batch 1, before they set
    their own XDG_RUNTIME_DIR). With the autouse tmp dir, the same call lands in tmp."""
    class Mcp:
        _DB_PATH = tmp_path / "other.db"

        @staticmethod
        def _ensure_loaded() -> bool:
            return False

    monkeypatch.setattr(ss, "_load_search_mcp", lambda: Mcp)
    assert ss._main(["serve", "--db", str(tmp_path / "knowledge.db")]) == 1
    assert (ss.state_dir(tmp_path / "knowledge.db") / "server.lock").exists()
    assert ss.state_dir(tmp_path / "knowledge.db").is_relative_to(Path(os.environ["XDG_RUNTIME_DIR"]))
    assert not ss.state_dir(tmp_path / "knowledge.db").is_relative_to(Path(os.environ[ss.TEST_REAL_BASE_ENV]))
