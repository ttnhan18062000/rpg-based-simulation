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

Kill switch: `RPG_SEARCH_SHARED=0` forces in-process search. Under pytest no server is ever spawned unless a test sets
`RPG_SEARCH_SHARED_ALLOW_TEST_SPAWN=1`.
"""
from __future__ import annotations

import contextlib
import fcntl
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
    return [sys.executable, str(_TOOLS_DIR / "search_shared.py"), "serve", "--db", str(db_path)]


def _spawn(directory: Path, db_path: Path) -> None:
    """Start the detached server; its stdout/stderr go to `server.log` in the private directory."""
    log_fd = os.open(directory / "server.log", os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        subprocess.Popen(  # noqa: S603 - fixed argv built from this file's own path
            _server_argv(db_path), stdin=subprocess.DEVNULL, stdout=log_fd, stderr=log_fd,
            start_new_session=True, close_fds=True,
        )
    finally:
        os.close(log_fd)


def _wait_ready(directory: Path, db_path: Path) -> dict | None:
    deadline = time.monotonic() + SPAWN_WAIT_SECONDS
    while time.monotonic() < deadline:
        state = _read_state(directory)
        if state is not None and _alive(state, db_path):
            return state
        time.sleep(0.1)
    return None


def _attach_or_spawn(directory: Path, db_path: Path) -> dict | None:
    """Under the lock: reuse a live server, else clear stale state and start one. None if it is not ready in time."""
    with _locked(directory) as got:
        if not got:
            return None
        state = _read_state(directory)
        if state is not None and _alive(state, db_path):
            return state
        with contextlib.suppress(OSError):
            (directory / "server.json").unlink()
        if not spawn_allowed():
            return None
        _spawn(directory, db_path)
        return _wait_ready(directory, db_path)


def _note(reason: str) -> None:
    print(f"[search_shared] in-process fallback: {reason}", file=sys.stderr)


def try_search(db_path: Path, query: str, top_k: int, section: str | None, mode: str) -> list | dict | None:
    """The shared server's answer, or None when the caller must search in-process."""
    if not enabled() or not query.strip() or not db_path.exists():
        return None
    directory = state_dir(db_path)
    if not _ensure_private_dir(directory):
        _note("state directory is not private to this user")
        return None
    state = _read_state(directory)
    if state is not None and state["code_version"] != code_version():
        _note("server was started from different code")
        return None
    body = {"query": query, "top_k": top_k, "section": section, "mode": mode}
    for attempt in (0, 1):
        if state is None or attempt == 1:
            state = _attach_or_spawn(directory, db_path)
        if state is None:
            _note("no server ready")
            return None
        if state["code_version"] != code_version():
            _note("server was started from different code")
            return None
        try:
            answer = _request(state, "POST", "/search", body)
        except (OSError, ValueError) as exc:
            state = None
            if attempt == 1:
                _note(f"request failed: {exc}")
                return None
            continue
        return answer
    return None


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


def _main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[0] != "serve" or argv[1] != "--db":
        print("usage: search_shared.py serve --db <knowledge.db>", file=sys.stderr)
        return 2
    mcp = _load_search_mcp()
    if not mcp._ensure_loaded():  # loads the model and BM25 before the port is announced
        print("[search_shared] index or model not available; not serving", file=sys.stderr)
        return 1
    mcp._STATE.model = _LockedModel(mcp._STATE.model)
    idle = float(os.environ.get(IDLE_ENV, DEFAULT_IDLE_SECONDS))
    return serve(_reloading(mcp), Path(argv[2]), idle)


def _reloading(mcp: object) -> Callable[..., list | dict]:
    """`mcp._search`, preceded by a BM25 reload when the index was rebuilt (the model does not depend on the index)."""
    lock = threading.Lock()
    seen = {"mtime": _mtime(mcp._DB_PATH)}

    def search(query: str, **kwargs: object) -> list | dict:
        current = _mtime(mcp._DB_PATH)
        with lock:
            if current != seen["mtime"]:
                mcp._STATE.bm25, mcp._STATE.doc_ids = mcp._ks._load_bm25(mcp._BM25_PATH)
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
