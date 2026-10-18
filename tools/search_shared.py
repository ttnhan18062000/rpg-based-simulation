"""One shared embedding model for every session's `search_docs` (TCK-20261012-SEARCH-MCP-SHARED-MODEL, #520).

Each Claude session spawns its own `tools/search_mcp.py`, and each loads about 600 MB of model on its first query.
This module lets the first session start one local server that holds the model, and every later session ask it.

* The server answers with the very function the in-process path uses (`search_mcp._search`), so results are identical
  by construction. The client compares a code-version hash with the server's and falls back in-process on a mismatch.
* Any failure (no server, timeout, bad answer, unsafe state directory) returns `None`: the caller searches in-process,
  exactly as before. Search never depends on the server.
* State lives outside the repo, per user: `$XDG_RUNTIME_DIR/rpg-search/<key>/` (0700), `<key>` being the sha256 of the
  index database's resolved path (never its contents, so a rebuilt index reaches the same server). `server.json`
  (port, token, pid) is 0600 and written atomically; the client refuses a directory or file that is not owned by its
  uid or is group/other accessible.
* The server binds 127.0.0.1 on an OS-assigned port, requires the token, and exits after an idle period.

* One server per index, from the main checkout's code (TCK-20261018-SEARCH-SHARED-SINGLE-SERVER-FROM-MAIN-CHECKOUT):
  `code_tools_dir()` pins the server's argv and the client's code hash to the main checkout, so a worktree's own copy of
  `tools/search_*.py` neither spawns nor is refused. The server holds an exclusive flock on `server.lock` for its whole
  life (taken before it loads anything; a second `serve` exits 0, a killed one's lock vanishes with its pid) and writes a
  `starting` record while it loads, so a slow load is waited for or reported (`REASON_STARTING`), never answered by a
  second server or by a client loading its own model.

Kill switch: `RPG_SEARCH_SHARED=0` forces in-process search. Under pytest no server is ever spawned unless a test sets
`RPG_SEARCH_SHARED_ALLOW_TEST_SPAWN=1`.
"""
from __future__ import annotations

import contextlib
import fcntl
import functools
import hashlib
import hmac
import http.client
import importlib.util
import json
import os
import secrets
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

KILL_SWITCH = "RPG_SEARCH_SHARED"
ALLOW_TEST_SPAWN = "RPG_SEARCH_SHARED_ALLOW_TEST_SPAWN"
IDLE_ENV = "RPG_SEARCH_IDLE_SECONDS"
DEFAULT_IDLE_SECONDS = 1800
SPAWN_WAIT_SECONDS = 12.0
LOCK_WAIT_SECONDS = 15.0
START_GRACE_SECONDS = 180.0
CLAIM_WINDOW_SECONDS = 20.0
CODE_ROOT_ENV = "RPG_SEARCH_SHARED_CODE_ROOT"
REASON_STARTING = "server starting"
REASON_UNRESPONSIVE = "server not responding"
_SILENT_REASONS = frozenset({"shared search not used"})
CONNECT_TIMEOUT = 2.0
READ_TIMEOUT = 8.0
_TOOLS_DIR = Path(__file__).resolve().parent
_CODE_FILES = ("search_mcp.py", "search_shared.py", "knowledge_search.py", "hybrid_retrieval.py")
_TOKEN_HEADER = "X-Search-Token"


# ── Gate, code version, state directory ───────────────────────────────────────

def enabled() -> bool:
    """True unless the kill switch is set to 0."""
    return os.environ.get(KILL_SWITCH, "1") != "0"


def spawn_allowed() -> bool:
    """A test must opt in to starting a real detached server."""
    return "PYTEST_CURRENT_TEST" not in os.environ or os.environ.get(ALLOW_TEST_SPAWN) == "1"


def code_version(tools_dir: Path = _TOOLS_DIR) -> str:
    """Hash of the files that decide what a search returns; a server from older code must not answer."""
    digest = hashlib.sha256()
    for name in _CODE_FILES:
        path = tools_dir / name
        digest.update(name.encode())
        digest.update(path.read_bytes() if path.exists() else b"")
    return digest.hexdigest()[:16]


def main_checkout_root(start: Path) -> Path | None:
    """The main checkout's root, from any worktree of it (or from the main checkout itself); None outside git."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True, text=True, timeout=5, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    common_dir = proc.stdout.strip()
    return Path(common_dir).parent if proc.returncode == 0 and common_dir else None


@functools.lru_cache(maxsize=1)
def _own_main_root() -> Path | None:
    return main_checkout_root(_TOOLS_DIR)


def code_tools_dir(db_path: Path) -> Path:
    """The `tools/` directory whose code serves `db_path` and whose hash a client compares.

    The main checkout's, resolved from this module's own path (never the cwd), so the first client to spawn does not
    decide which checkout's code serves everyone, and a worktree editing `tools/search_*.py` neither spawns nor is
    served by its own copy (TCK-20261018-SEARCH-SHARED-SINGLE-SERVER-FROM-MAIN-CHECKOUT). Exceptions: the test/dev
    override `RPG_SEARCH_SHARED_CODE_ROOT`; no resolvable main checkout; and a worktree that built its own index, whose
    server must run that checkout's code because a server refuses a database its code does not search."""
    override = os.environ.get(CODE_ROOT_ENV)
    if override:
        return Path(override) / "tools"
    main = _own_main_root()
    if main is None or not (main / "tools" / "search_shared.py").is_file():
        return _TOOLS_DIR
    own_root = _TOOLS_DIR.parent.resolve()
    if own_root != main.resolve() and db_path.resolve().is_relative_to(own_root):
        return _TOOLS_DIR
    return main / "tools"


def state_dir(db_path: Path) -> Path:
    """Per-user directory for this index, keyed by the database's resolved path."""
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    base = Path(runtime) if runtime else Path(tempfile.gettempdir()) / f"rpg-search-{os.getuid()}"
    key = hashlib.sha256(str(db_path.resolve()).encode()).hexdigest()[:12]
    return base / "rpg-search" / key


def _owned_and_private(path: Path, *, directory: bool) -> bool:
    try:
        info = path.stat()
    except OSError:
        return False
    kind_ok = stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)
    return kind_ok and info.st_uid == os.getuid() and (info.st_mode & 0o077) == 0


def _ensure_private_dir(path: Path) -> bool:
    """Create `path` (and parents) as 0700 and verify ownership; False if it cannot be made safe."""
    try:
        path.parent.parent.mkdir(parents=True, exist_ok=True)
        path.parent.mkdir(mode=0o700, exist_ok=True)
        path.mkdir(mode=0o700, exist_ok=True)
    except OSError:
        return False
    return all(_owned_and_private(p, directory=True) for p in (path, path.parent))


def _read_state(directory: Path) -> dict | None:
    """The server record, or None if absent, unreadable or not a private file owned by this uid."""
    path = directory / "server.json"
    if not _owned_and_private(path, directory=False):
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    needed = {"pid", "port", "token", "db", "code_version"}
    return data if isinstance(data, dict) and needed <= data.keys() else None


def _write_state(directory: Path, record: dict) -> None:
    """Atomic 0600 write: temp file in the same directory, then os.replace."""
    tmp = directory / f"server.json.{os.getpid()}.tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(record, handle)
    os.replace(tmp, directory / "server.json")


def _read_starting(directory: Path) -> dict | None:
    """The record a spawning client or a loading server leaves before the port exists, or None."""
    path = directory / "server.json"
    if not _owned_and_private(path, directory=False):
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if data.get("state") == "starting" and int(data["pid"]) > 0 and float(data["started"]) > 0 else None
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return None


def _write_starting(directory: Path, pid: int) -> None:
    _write_state(directory, {"state": "starting", "pid": pid, "started": time.time()})


def _pid_alive(pid: int) -> bool:
    """A live process that is not a zombie (a dead child no one has reaped still answers kill 0)."""
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    try:
        fields = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").rsplit(")", 1)[1].split()
        return fields[0] != "Z"
    except (OSError, IndexError):
        return True


# ── Client ────────────────────────────────────────────────────────────────────

def _request(state: dict, method: str, path: str, body: dict | None = None,
             read_timeout: float = READ_TIMEOUT) -> dict | list:
    """One authenticated request to 127.0.0.1; raises OSError/ValueError on any failure."""
    conn = http.client.HTTPConnection("127.0.0.1", int(state["port"]), timeout=CONNECT_TIMEOUT)
    try:
        conn.connect()
        if conn.sock is not None:
            conn.sock.settimeout(read_timeout)
        payload = json.dumps(body).encode() if body is not None else None
        headers = {_TOKEN_HEADER: str(state["token"]), "Content-Type": "application/json"}
        conn.request(method, path, body=payload, headers=headers)
        response = conn.getresponse()
        data = response.read()
        if response.status != 200:
            raise OSError(f"shared search server answered {response.status}")
        return json.loads(data)
    except http.client.HTTPException as exc:
        raise OSError(str(exc)) from exc
    finally:
        conn.close()


def _alive(state: dict, db_path: Path) -> bool:
    """A recorded server counts only if its pid lives AND /health, with the token, names this index and code."""
    try:
        os.kill(int(state["pid"]), 0)
        health = _request(state, "GET", "/health", read_timeout=CONNECT_TIMEOUT)
    except (OSError, ValueError):
        return False
    return isinstance(health, dict) and health.get("db") == str(db_path.resolve()) and \
        health.get("code_version") == state["code_version"]


@contextlib.contextmanager
def _locked(directory: Path) -> Iterator[bool]:
    """Exclusive flock on `<dir>/lock`, waiting up to LOCK_WAIT_SECONDS. Yields False if it was not obtained."""
    fd = os.open(directory / "lock", os.O_RDWR | os.O_CREAT, 0o600)
    got = False
    deadline = time.monotonic() + LOCK_WAIT_SECONDS
    try:
        while not got:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                got = True
            except OSError:
                if time.monotonic() >= deadline:
                    break
                time.sleep(0.05)
        yield got
    finally:
        if got:
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _server_argv(db_path: Path) -> list[str]:
    return [sys.executable, str(code_tools_dir(db_path) / "search_shared.py"), "serve", "--db", str(db_path)]


def _spawn(directory: Path, db_path: Path) -> int:
    """Start the detached server and return its pid; its stdout/stderr go to `server.log` in the private directory."""
    log_fd = os.open(directory / "server.log", os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        return subprocess.Popen(  # noqa: S603 - fixed argv built from the code root's own path
            _server_argv(db_path), stdin=subprocess.DEVNULL, stdout=log_fd, stderr=log_fd,
            start_new_session=True, close_fds=True,
        ).pid
    finally:
        os.close(log_fd)


def _wait_ready(directory: Path, db_path: Path) -> dict | None:
    """Poll for a ready, healthy server until SPAWN_WAIT_SECONDS; stop early once the starting process is gone."""
    deadline = time.monotonic() + SPAWN_WAIT_SECONDS
    while time.monotonic() < deadline:
        state = _read_state(directory)
        if state is not None and _alive(state, db_path):
            return state
        starting = _read_starting(directory)
        if state is None and starting is not None and not _pid_alive(int(starting["pid"])):
            return None
        time.sleep(0.1)
    return None


def _starting_reason(directory: Path) -> str:
    """Why no ready server: still within its start grace, or wedged / gone."""
    starting = _read_starting(directory)
    if starting is not None and _pid_alive(int(starting["pid"])) \
            and time.time() - float(starting["started"]) < START_GRACE_SECONDS:
        return REASON_STARTING
    return REASON_UNRESPONSIVE


def _server_lock_held(directory: Path) -> bool:
    """True while some process holds `server.lock`, i.e. a server process lives (loading or serving)."""
    fd = os.open(directory / "server.lock", os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return True
    else:
        fcntl.flock(fd, fcntl.LOCK_UN)
        return False
    finally:
        os.close(fd)


def _server_present(directory: Path, state: dict | None) -> bool:
    """A server process exists for this directory even though it does not answer yet (or any more).

    The server's own flock is the proof, so a pid the kernel reused for something else never counts. The one gap is a
    child a client just spawned that has not taken the lock yet: its `starting` record counts for CLAIM_WINDOW_SECONDS."""
    if _server_lock_held(directory):
        return True
    starting = _read_starting(directory) if state is None else None
    return starting is not None and _pid_alive(int(starting["pid"])) \
        and time.time() - float(starting["started"]) < CLAIM_WINDOW_SECONDS


def _attach_or_spawn(directory: Path, db_path: Path) -> tuple[dict | None, str | None]:
    """(ready server, None) or (None, reason).

    Under the client lock: reuse a live server; never touch or respawn over a server that is starting or hung (its pid
    lives and it holds `server.lock`); clear a record whose pid is dead and start one, leaving a `starting` record with
    the child's pid so the next client sees it. The wait for readiness happens outside the lock."""
    with _locked(directory) as got:
        if not got:
            return None, REASON_UNRESPONSIVE
        state = _read_state(directory)
        if state is not None and _alive(state, db_path):
            return state, None
        if _server_present(directory, state):
            pass  # starting, or alive but not answering: wait / report, never a second server
        else:
            with contextlib.suppress(OSError):
                (directory / "server.json").unlink()
            if not spawn_allowed():
                return None, REASON_UNRESPONSIVE
            _write_starting(directory, _spawn(directory, db_path))
    state = _wait_ready(directory, db_path)
    return (state, None) if state is not None else (None, _starting_reason(directory))


def _note(reason: str) -> None:
    print(f"[search_shared] in-process fallback: {reason}", file=sys.stderr)


def try_search_ex(db_path: Path, query: str, top_k: int, section: str | None,
                  mode: str) -> tuple[list | dict | None, str | None]:
    """(the shared server's answer, None), or (None, why) when the caller must search in-process.

    Prints nothing: the caller logs its mode transitions once (`search_mcp`). `REASON_STARTING` means a server is
    loading its model right now, so the caller may answer without loading one itself."""
    if not enabled() or not query.strip() or not db_path.exists():
        return None, "shared search not used"
    directory = state_dir(db_path)
    if not _ensure_private_dir(directory):
        return None, "state directory is not private to this user"
    want = code_version(code_tools_dir(db_path))
    state = _read_state(directory)
    if state is not None and state["code_version"] != want:
        return None, "server was started from different code"
    body = {"query": query, "top_k": top_k, "section": section, "mode": mode}
    for attempt in (0, 1):
        if state is None or attempt == 1:
            state, why = _attach_or_spawn(directory, db_path)
            if state is None:
                return None, why or "no server ready"
        if state["code_version"] != want:
            return None, "server was started from different code"
        try:
            return _request(state, "POST", "/search", body), None
        except (OSError, ValueError) as exc:
            state = None
            if attempt == 1:
                return None, f"request failed: {exc}"
    return None, "no server ready"


def try_search(db_path: Path, query: str, top_k: int, section: str | None, mode: str) -> list | dict | None:
    """The shared server's answer, or None when the caller must search in-process (the reason goes to stderr)."""
    answer, reason = try_search_ex(db_path, query, top_k, section, mode)
    if answer is None and reason and reason not in _SILENT_REASONS:
        _note(reason)
    return answer


# ── Server ────────────────────────────────────────────────────────────────────

class _SharedServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, search_fn: Callable[..., list | dict], db_path: Path, token: str) -> None:
        super().__init__(("127.0.0.1", 0), _Handler)
        self.search_fn = search_fn
        self.db_path = db_path
        self.token = token
        self.version = code_version()
        self.last_request = time.monotonic()


class _Handler(BaseHTTPRequestHandler):
    server: _SharedServer

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002 - signature fixed by BaseHTTPRequestHandler
        return

    def _authorized(self) -> bool:
        sent = self.headers.get(_TOKEN_HEADER, "")
        return hmac.compare_digest(sent.encode(), self.server.token.encode())

    def _reply(self, status: int, payload: object) -> None:
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802 - name fixed by BaseHTTPRequestHandler
        if not self._authorized():
            return self._reply(401, {"error": "unauthorized"})
        if self.path != "/health":
            return self._reply(404, {"error": "not found"})
        self.server.last_request = time.monotonic()
        return self._reply(200, {"status": "ok", "pid": os.getpid(), "db": str(self.server.db_path.resolve()),
                                 "code_version": self.server.version})

    def do_POST(self) -> None:  # noqa: N802 - name fixed by BaseHTTPRequestHandler
        if not self._authorized():
            return self._reply(401, {"error": "unauthorized"})
        if self.path != "/search":
            return self._reply(404, {"error": "not found"})
        self.server.last_request = time.monotonic()
        try:
            req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            result = self.server.search_fn(
                str(req["query"]), top_k=int(req.get("top_k", 8)), section=req.get("section") or None,
                mode=str(req.get("mode", "hybrid")),
            )
        except (ValueError, KeyError, TypeError) as exc:
            return self._reply(400, {"error": f"bad request: {exc}"})
        return self._reply(200, result)


def _idle_watch(server: _SharedServer, idle_seconds: float) -> None:
    while True:
        time.sleep(min(1.0, max(idle_seconds / 4, 0.05)))
        if time.monotonic() - server.last_request >= idle_seconds:
            server.shutdown()
            return


def serve(search_fn: Callable[..., list | dict], db_path: Path, idle_seconds: float,
          on_ready: Callable[[], None] | None = None) -> int:
    """Run the shared server until idle or signalled. `search_fn` must be the in-process search function."""
    directory = state_dir(db_path)
    if not _ensure_private_dir(directory):
        print("[search_shared] state directory is not private to this user", file=sys.stderr)
        return 1
    server = _SharedServer(search_fn, db_path, secrets.token_hex(32))
    record = {"pid": os.getpid(), "port": server.server_address[1], "token": server.token,
              "db": str(db_path.resolve()), "code_version": server.version, "started": time.time()}
    _write_state(directory, record)
    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGTERM, lambda *_: threading.Thread(target=server.shutdown, daemon=True).start())
    threading.Thread(target=_idle_watch, args=(server, idle_seconds), daemon=True).start()
    if on_ready is not None:
        on_ready()
    try:
        server.serve_forever()
    finally:
        current = _read_state(directory)
        if current is not None and current.get("pid") == os.getpid():
            with contextlib.suppress(OSError):
                (directory / "server.json").unlink()
        server.server_close()
    return 0


class _LockedModel:
    """Serialises `encode()`: one SentenceTransformer is shared by every request thread."""

    def __init__(self, model: object) -> None:
        self._model = model
        self._lock = threading.Lock()

    def encode(self, *args: object, **kwargs: object) -> object:
        with self._lock:
            return self._model.encode(*args, **kwargs)  # type: ignore[attr-defined]


def _load_search_mcp() -> object:
    spec = importlib.util.spec_from_file_location("search_mcp", _TOOLS_DIR / "search_mcp.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["search_mcp"] = module
    spec.loader.exec_module(module)
    return module


_SERVER_LOCK_FD: int | None = None


def _claim_single_instance(directory: Path) -> bool:
    """Take the exclusive, non-blocking flock on `<dir>/server.lock` and keep it for the process's life.

    The kernel drops it when the pid dies, so a killed server never blocks its successor. False: another server holds it."""
    global _SERVER_LOCK_FD
    fd = os.open(directory / "server.lock", os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        return False
    _SERVER_LOCK_FD = fd
    return True


def _release_single_instance() -> None:
    global _SERVER_LOCK_FD
    if _SERVER_LOCK_FD is not None:
        os.close(_SERVER_LOCK_FD)
        _SERVER_LOCK_FD = None


def _clear_own_starting(directory: Path) -> None:
    starting = _read_starting(directory)
    if starting is not None and int(starting["pid"]) == os.getpid():
        with contextlib.suppress(OSError):
            (directory / "server.json").unlink()


def _main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[0] != "serve" or argv[1] != "--db":
        print("usage: search_shared.py serve --db <knowledge.db>", file=sys.stderr)
        return 2
    db_path = Path(argv[2])
    directory = state_dir(db_path)
    if not _ensure_private_dir(directory):
        print("[search_shared] state directory is not private to this user", file=sys.stderr)
        return 1
    if not _claim_single_instance(directory):  # before importing search_mcp or loading anything
        print(f"[search_shared] another server already serves {db_path}; exiting without loading", file=sys.stderr)
        return 0
    try:
        _write_starting(directory, os.getpid())
        mcp = _load_search_mcp()
        if db_path.resolve() != Path(mcp._DB_PATH).resolve():
            print(f"[search_shared] refusing to serve {argv[2]}: this code searches {mcp._DB_PATH}", file=sys.stderr)
            return 1
        if not mcp._ensure_loaded():  # loads the model and BM25 before the port is announced
            print("[search_shared] index or model not available; not serving", file=sys.stderr)
            return 1
        mcp._STATE.model = _LockedModel(mcp._STATE.model)
        idle = float(os.environ.get(IDLE_ENV, DEFAULT_IDLE_SECONDS))
        return serve(_reloading(mcp), db_path, idle)
    finally:
        _clear_own_starting(directory)
        _release_single_instance()


def _reloading(mcp: object) -> Callable[..., list | dict]:
    """`mcp._search`, preceded by a BM25 reload when the index was rebuilt (the model does not depend on the index).

    The new generation is built completely and published with ONE reference swap (`_STATE.lexical`); a search reads
    that reference once at entry, so a reload never mixes generations and never blocks a search in flight."""
    lock = threading.Lock()
    seen = {"mtime": _mtime(mcp._DB_PATH)}

    def search(query: str, **kwargs: object) -> list | dict:
        current = _mtime(mcp._DB_PATH)
        if current != seen["mtime"]:
            with lock:
                if current != seen["mtime"]:
                    mcp._STATE.lexical = tuple(mcp._ks._load_bm25(mcp._BM25_PATH))
                    seen["mtime"] = current
        return mcp._search(query, **kwargs)

    return search


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
