"""`sandbox.kill_tree` reaches every descendant, including one in its own session that ignores SIGTERM (what an orphaned bwrap
inner process is). Real processes, no Aseprite and no bwrap needed; runs in CI."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

from visual_assets.drawing.backend import sandbox

# parent -> child (new session, SIGTERM ignored) -> grandchild; every one writes its pid and sleeps
CHILD = """
import os, signal, sys, time
signal.signal(signal.SIGTERM, signal.SIG_IGN)
os.setsid()
pid = os.fork()
if pid == 0:
    open(sys.argv[1] + '.grandchild', 'w').write(str(os.getpid()))
    time.sleep(60)
else:
    open(sys.argv[1] + '.child', 'w').write(str(os.getpid()))
    time.sleep(60)
"""
PARENT = """
import subprocess, sys, time
subprocess.Popen([sys.executable, '-c', sys.argv[2], sys.argv[1]])
time.sleep(60)
"""


def _alive(pid: int) -> bool:
    try:
        state = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0]
    except OSError:
        return False
    return state != "Z"


def test_kill_tree_kills_a_sigterm_ignoring_descendant_in_its_own_session(tmp_path):
    marker = str(tmp_path / "pid")
    proc = subprocess.Popen([sys.executable, "-c", PARENT, marker, CHILD])
    deadline = time.monotonic() + 10
    while not (Path(marker + ".child").exists() and Path(marker + ".grandchild").exists()) and time.monotonic() < deadline:
        time.sleep(0.02)
    pids = [proc.pid, int(Path(marker + ".child").read_text()), int(Path(marker + ".grandchild").read_text())]
    assert all(_alive(p) for p in pids)

    sandbox.kill_tree(proc)

    deadline = time.monotonic() + 10
    while any(_alive(p) for p in pids) and time.monotonic() < deadline:
        time.sleep(0.02)
    assert not [p for p in pids if _alive(p)], "a descendant survived kill_tree"
    assert proc.returncode is not None  # the direct child was reaped


def test_kill_tree_on_an_already_dead_process_is_harmless():
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait()
    sandbox.kill_tree(proc)
    assert proc.returncode == 0


def test_children_of_a_gone_process_is_empty():
    assert sandbox._children(2**22 + os.getpid()) == set()
