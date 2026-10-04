"""`sandbox.kill_tree` reaches every descendant, including one in its own session that ignores SIGTERM (what an orphaned bwrap
inner process is). Real processes, no Aseprite and no bwrap needed; runs in CI."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from visual_assets.drawing.backend import sandbox

# parent -> child (new session, SIGTERM ignored) -> grandchild; every one publishes its pid ATOMICALLY (write `<path>.tmp`, then `os.replace`), so a marker that
# exists is a marker with its full content: `open(path, 'w').write(...)` creates the file before it has content, and a test waiting on exists() could read "" under load
# (TCK-20261004-VISUAL-ASSETS-KILL-TREE-TEST-RACE)
MARK = """
def mark(path, value):
    import os
    with open(path + '.tmp', 'w') as handle:
        handle.write(str(value))
    os.replace(path + '.tmp', path)
"""
CHILD = MARK + """
import os, signal, sys, time
signal.signal(signal.SIGTERM, signal.SIG_IGN)
os.setsid()
pid = os.fork()
if pid == 0:
    mark(sys.argv[1] + '.grandchild', os.getpid())
    time.sleep(60)
else:
    mark(sys.argv[1] + '.child', os.getpid())
    time.sleep(60)
"""
PARENT = """
import subprocess, sys, time
subprocess.Popen([sys.executable, '-c', sys.argv[2], sys.argv[1]])
time.sleep(60)
"""
MARKERS = ("child", "grandchild")


def _alive(pid: int) -> bool:
    try:
        state = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0]
    except OSError:
        return False
    return state != "Z"


def _still_alive_after(pids: list[int], timeout_s: float = 10) -> list[int]:
    """The pids that are still alive after waiting up to `timeout_s` for SIGKILL to take effect (delivery is asynchronous)."""
    deadline = time.monotonic() + timeout_s
    alive = [p for p in pids if _alive(p)]
    while alive and time.monotonic() < deadline:
        time.sleep(0.02)
        alive = [p for p in pids if _alive(p)]
    return alive


def _descendants(pid: int) -> set[int]:
    found: set[int] = set()
    todo = [pid]
    while todo:
        for child in sandbox._children(todo.pop()):
            if child not in found:
                found.add(child)
                todo.append(child)
    return found


def _start_tree(marker: str, wait_s: float, child_script: str = CHILD) -> tuple[subprocess.Popen, list[int]]:
    """Start the parent -> child -> grandchild tree and wait until both markers are published. Returns (proc, every pid known).
    Raises AssertionError naming the missing marker(s) if they do not appear in `wait_s`; the tree is killed on ANY failure here, so a failed setup
    never leaves processes sleeping for 60 s."""
    proc = subprocess.Popen([sys.executable, "-c", PARENT, marker, child_script])
    try:
        deadline = time.monotonic() + wait_s
        while time.monotonic() < deadline and not all(Path(f"{marker}.{name}").exists() for name in MARKERS):
            time.sleep(0.02)
        missing = [name for name in MARKERS if not Path(f"{marker}.{name}").exists()]
        assert not missing, f"the {', '.join(missing)} pid marker(s) did not appear within {wait_s} s"
        pids = [proc.pid]
        for name in MARKERS:
            text = Path(f"{marker}.{name}").read_text()
            assert text.isdigit(), f"the {name} marker appeared before its content was complete ({text!r}): markers must be written atomically"
            pids.append(int(text))
        return proc, pids
    except BaseException:
        stray = _descendants(proc.pid)
        sandbox.kill_tree(proc)
        _START_FAILURE_PIDS[:] = [proc.pid, *stray]  # for the test of this very path
        raise


_START_FAILURE_PIDS: list[int] = []


def test_kill_tree_kills_a_sigterm_ignoring_descendant_in_its_own_session(tmp_path):
    proc, pids = _start_tree(str(tmp_path / "pid"), wait_s=10)
    try:
        assert all(_alive(p) for p in pids)

        sandbox.kill_tree(proc)

        survivors = _still_alive_after(pids)
        assert not survivors, f"a descendant survived kill_tree: {survivors}"
        assert proc.returncode is not None  # the direct child was reaped
    finally:
        sandbox.kill_tree(proc)  # harmless on a dead process; a failed assertion above must not leave a tree sleeping in CI


def test_a_setup_that_times_out_names_the_missing_marker_and_leaves_no_process(tmp_path):
    never_publishes_grandchild = CHILD.replace("mark(sys.argv[1] + '.grandchild', os.getpid())", "pass")
    with pytest.raises(AssertionError, match=r"the grandchild pid marker\(s\) did not appear within 0.5 s"):
        _start_tree(str(tmp_path / "pid"), wait_s=0.5, child_script=never_publishes_grandchild)
    leftovers = _still_alive_after(_START_FAILURE_PIDS)
    assert len(_START_FAILURE_PIDS) >= 3 and not leftovers, f"processes of the failed setup survived: {leftovers}"


def test_a_marker_that_is_not_written_atomically_is_reported_not_misread(tmp_path):
    """The race itself, made deterministic: a child that creates its marker, pauses, then writes. The test must fail clearly (never crash on int(''))."""
    racy = CHILD.replace("with open(path + '.tmp', 'w') as handle:\n        handle.write(str(value))\n    os.replace(path + '.tmp', path)",
                         "handle = open(path, 'w')\n    import time\n    time.sleep(3)\n    handle.write(str(value))\n    handle.close()")
    assert racy != CHILD
    with pytest.raises(AssertionError, match="appeared before its content was complete"):
        _start_tree(str(tmp_path / "pid"), wait_s=10, child_script=racy)
    assert not _still_alive_after(_START_FAILURE_PIDS)


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
