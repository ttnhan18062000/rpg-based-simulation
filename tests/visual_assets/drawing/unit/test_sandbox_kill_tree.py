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


class _FakeProc:
    def __init__(self, pid: int):
        self.pid = pid
        self.returncode = None

    def wait(self):
        self.returncode = -9


def _fake_proc_fs(monkeypatch, *, tree: dict[int, set[int]], settle_after: int | None):
    """A fake /proc: `settle_after` state reads after a SIGSTOP the pid reads `T` (None: it never stops). Returns the event log."""
    log: list[tuple] = []
    reads: dict[int, int] = {}
    stopped: set[int] = set()

    def fake_signal(pids, sig):
        for pid in sorted(pids):
            log.append(("signal", pid, int(sig)))
            if sig == sandbox.signal.SIGSTOP:
                stopped.add(pid)
                reads[pid] = 0

    def fake_state(pid):
        if pid in stopped:
            reads[pid] += 1
            if settle_after is not None and reads[pid] > settle_after:
                return "T"
        return "S"

    def fake_children(pid):
        log.append(("children", pid, fake_state(pid) if pid in stopped else "S"))
        return set(tree.get(pid, set()))

    monkeypatch.setattr(sandbox, "_signal", fake_signal)
    monkeypatch.setattr(sandbox, "_state", fake_state)
    monkeypatch.setattr(sandbox, "_children", fake_children)
    return log


def test_children_are_read_only_after_every_process_has_really_stopped(monkeypatch):
    log = _fake_proc_fs(monkeypatch, tree={100: {101}, 101: {102}}, settle_after=3)
    sandbox.kill_tree(_FakeProc(100))
    reads = [event for event in log if event[0] == "children"]
    assert reads and all(state == "T" for _, _, state in reads), reads  # never trusted a list read from a running process
    killed = {pid for kind, pid, sig in log if kind == "signal" and sig == int(sandbox.signal.SIGKILL)}
    assert killed == {100, 101, 102}


def test_a_process_that_will_not_stop_is_still_killed_with_everything_known(monkeypatch):
    monkeypatch.setattr(sandbox, "STOP_WAIT_S", 0.05)
    log = _fake_proc_fs(monkeypatch, tree={100: {101}}, settle_after=None)
    sandbox.kill_tree(_FakeProc(100))
    killed = {pid for kind, pid, sig in log if kind == "signal" and sig == int(sandbox.signal.SIGKILL)}
    assert killed == {100, 101}
    assert [event for event in log if event[0] == "children"][-1][1] in {100, 101}  # one last look for late children after the kill


def test_an_interrupt_between_stop_and_kill_still_kills_the_tree(monkeypatch):
    """Found under CPU load: the test harness's SIGALRM time limit raised inside kill_tree after the tree was stopped; nothing was killed,
    the tree stayed stopped for good and `Popen.__exit__` waited on it forever (a hang, not a leak)."""
    log = _fake_proc_fs(monkeypatch, tree={100: {101}}, settle_after=0)

    def interrupted(pids):
        raise TimeoutError("alarm")

    monkeypatch.setattr(sandbox, "_wait_stopped", interrupted)
    try:
        sandbox.kill_tree(_FakeProc(100))
    except TimeoutError:
        pass
    else:  # pragma: no cover
        raise AssertionError("the interrupt must propagate")
    killed = {pid for kind, pid, sig in log if kind == "signal" and sig == int(sandbox.signal.SIGKILL)}
    assert 100 in killed
