"""Run the Aseprite binary inside a bwrap sandbox: no network, read-only system, one job directory."""

from __future__ import annotations

import os
import signal
import subprocess
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


def kill_tree(proc: subprocess.Popen) -> None:
    """SIGKILL `proc` and every descendant, then reap `proc`.

    `subprocess.run(timeout=)` kills only the direct child. With `--unshare-all` bwrap forks an inner process that is the init of a new
    PID namespace; if the outer one dies before the inner one has armed `--die-with-parent`, the inner one is orphaned, outlives the job
    and holds a bind mount of the job directory (it ignores SIGTERM, being a namespace init). `--new-session` also puts it outside our
    process group, so a group kill cannot reach it. So: freeze the tree (SIGSTOP, repeated until no new child appears, so nothing can
    fork or exec in between), then SIGKILL all of it.
    """
    tree = {proc.pid}
    while True:
        _signal(tree, signal.SIGSTOP)
        grown = {child for pid in tree for child in _children(pid)} - tree
        if not grown:
            break
        tree |= grown
    _signal(tree, signal.SIGKILL)
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
            proc.communicate()  # drain the pipes of the killed tree
            raise AdapterError(f"aseprite timed out after {config.JOB_TIMEOUT_S}s") from exc
        except BaseException:
            kill_tree(proc)
            raise
        return subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)
