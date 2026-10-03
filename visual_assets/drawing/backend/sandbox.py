"""Run the Aseprite binary inside a bwrap sandbox: no network, read-only system, one job directory."""

from __future__ import annotations

import os
import signal
import subprocess
import time
from pathlib import Path

from visual_assets.drawing import config
from visual_assets.drawing.errors import AdapterError


def _children(pid: int) -> set[int]:
    """Direct children of `pid` (every thread's list), empty when the process is gone or /proc cannot say."""
    found: set[int] = set()
    try:
        for task in os.listdir(f"/proc/{pid}/task"):
            with open(f"/proc/{pid}/task/{task}/children") as handle:
                found.update(int(child) for child in handle.read().split())
    except (OSError, ValueError):
        pass
    return found


def _signal(pids, sig: int) -> None:
    for pid in pids:
        try:
            os.kill(pid, sig)
        except OSError:
            pass


def _state(pid: int) -> str | None:
    """The scheduler state letter of `pid` (`T`/`t` stopped, `Z` zombie), or None when it is gone."""
    try:
        with open(f"/proc/{pid}/stat") as handle:
            return handle.read().rsplit(")", 1)[1].split()[0]
    except (OSError, IndexError):
        return None


DRAIN_WAIT_S = 2.0  # how long to wait for the killed tree's pipes to close
STOP_WAIT_S = 1.0  # how long to wait for a SIGSTOP to take effect before giving up on being sure


def _wait_stopped(pids) -> bool:
    """Wait (bounded) until every pid is stopped, a zombie or gone. `os.kill` returns before the target has stopped, and a process that
    is still running may finish a fork after its children were read, so the children list is trusted only once this returns True."""
    deadline = time.monotonic() + STOP_WAIT_S
    pending = set(pids)
    while pending:
        pending = {pid for pid in pending if _state(pid) not in (None, "T", "t", "Z", "X")}
        if not pending:
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.001)
    return True


def kill_tree(proc: subprocess.Popen) -> None:
    """SIGKILL `proc` and every descendant, then reap `proc`.

    `subprocess.run(timeout=)` kills only the direct child. With `--unshare-all` bwrap forks an inner process that is the init of a new
    PID namespace; if the outer one dies before the inner one has armed `--die-with-parent`, the inner one is orphaned, outlives the job
    and holds a bind mount of the job directory (it ignores SIGTERM, being a namespace init). `--new-session` also puts it outside our
    process group, so a group kill cannot reach it. So: freeze the tree (SIGSTOP, then wait until every process really is stopped, then
    read the children, repeated until no new child appears, so nothing can fork or exec in between), then SIGKILL all of it. If a
    process will not stop in time, everything known is still killed and the children are read one last time.
    """
    tree = {proc.pid}
    sure = True
    try:
        while True:
            _signal(tree, signal.SIGSTOP)
            sure = _wait_stopped(tree)
            grown = {child for pid in tree for child in _children(pid)} - tree
            tree |= grown
            if not grown or not sure:
                break
    finally:
        # Always, even if something above raised (a test harness alarm, KeyboardInterrupt): a tree left stopped can never exit, and
        # `Popen.__exit__` would then wait on it forever.
        _signal(tree, signal.SIGKILL)
    if not sure:
        late = {child for pid in tree for child in _children(pid)} - tree
        _signal(late, signal.SIGKILL)
    proc.wait()


def bwrap(job: Path, argv: list[str]) -> subprocess.CompletedProcess:
    home = "/home/sandbox"
    cmd = [
        "bwrap",
        "--unshare-all",  # includes network
        "--die-with-parent",
        "--new-session",
        "--clearenv",
        "--setenv", "HOME", home,
        "--setenv", "PATH", "/usr/bin",
        "--ro-bind", "/usr", "/usr",
        "--symlink", "usr/lib", "/lib",
        "--symlink", "usr/lib64", "/lib64",
        "--symlink", "usr/bin", "/bin",
        "--ro-bind", "/etc/ld.so.cache", "/etc/ld.so.cache",
        "--proc", "/proc",
        "--dev", "/dev",
        "--tmpfs", "/tmp",
        "--tmpfs", home,
        "--ro-bind", str(config.LUA_PATH.parent), "/lua",
        "--bind", str(job), "/job",
        "--chdir", "/job",
        config.ASEPRITE, "-b", *argv,
    ]
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL) as proc:
        try:
            stdout, stderr = proc.communicate(timeout=config.JOB_TIMEOUT_S)
        except subprocess.TimeoutExpired as exc:
            kill_tree(proc)
            try:
                proc.communicate(timeout=DRAIN_WAIT_S)  # drain the pipes of the killed tree, but never wait on a survivor that holds them
            except subprocess.TimeoutExpired:
                pass
            raise AdapterError(f"aseprite timed out after {config.JOB_TIMEOUT_S}s") from exc
        except BaseException:
            kill_tree(proc)
            raise
        return subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)
