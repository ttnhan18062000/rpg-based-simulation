"""Tests for tools/sessions/state.py (TCK-20261004-SESSION-LAYER-M2A-ROLE-STATE-DIRECTORY-AND-LIVENESS).

Real git worktrees, real child processes and a real `kill -9` stand in for the harness: the liveness
claim is about /proc, so a stub would only prove our assumptions."""
from __future__ import annotations

import json
import multiprocessing
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.sessions import state as st  # noqa: E402

_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t", "PATH": os.environ["PATH"], "HOME": os.environ.get("HOME", "/")}


def _git(cwd, *a):
    subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, env=_ENV)


@pytest.fixture
def repo(tmp_path):
    main = tmp_path / "main"
    main.mkdir()
    _git(main, "init", "-q", "-b", "main")
    (main / "f").write_text("x")
    _git(main, "add", "-A")
    _git(main, "commit", "-q", "-m", "init")
    return main


def _binding(role="r-one", sid="s1", process=None, worktree="/w", **kw):
    return st.Binding(session_id=sid, role=role, source="startup", worktree=worktree, branch="b",
                      transcript_path="", process=process, manifest_digest="d", ts="2026-10-04T00:00:00Z", **kw)


@pytest.fixture
def child():
    p = subprocess.Popen(["sleep", "60"])
    yield p
    if p.poll() is None:
        p.kill()
    p.wait()


# ---- AC1: the state lives under the git common dir ---------------------------------------------

def test_two_worktrees_share_state_and_removing_one_leaves_it_intact(repo, tmp_path):
    wt = tmp_path / "wt"
    _git(repo, "worktree", "add", "-q", "-b", "other", str(wt))
    root_a, root_b = st.state_root(repo), st.state_root(wt)
    assert root_a == root_b
    st.record_start(root_a, _binding())
    assert st.read_instance(root_b, "r-one").holder.session_id == "s1"
    _git(repo, "worktree", "remove", "--force", str(wt))
    assert st.read_instance(root_a, "r-one") is not None
    assert (root_a / "r-one" / st.BINDINGS).is_file()


# ---- AC2: liveness, with a positive control ----------------------------------------------------

def test_live_child_reads_live_then_orphaned_after_kill_9_with_no_session_end(repo, child):
    proc = st.process_identity(child.pid)
    assert proc is not None and "sleep" in proc.cmdline
    root = st.state_root(repo)
    inst = st.record_start(root, _binding(process=proc))
    assert st.liveness(inst) == st.LIVE  # positive control: the instrument can say "live"
    os.kill(child.pid, signal.SIGKILL)
    child.wait()
    assert st.liveness(st.read_instance(root, "r-one")) == st.ORPHANED


def test_a_reused_pid_with_a_different_start_or_cmdline_is_orphaned(repo, child):
    real = st.process_identity(child.pid)
    root = st.state_root(repo)
    for forged in (st.ProcessId(real.pid, str(int(real.start) - 5), real.cmdline),
                   st.ProcessId(real.pid, real.start, "some other program")):
        assert st.liveness(st.record_start(root, _binding(process=forged))) == st.ORPHANED


def test_a_leftover_socket_file_alone_never_makes_an_instance_live(repo, tmp_path, child):
    real = st.process_identity(child.pid)
    (tmp_path / f"{real.pid}.sock").write_text("")  # what kill -9 leaves behind
    gone = st.ProcessId(2**22 + 12345, "1", "claude")  # a pid that does not exist
    assert st.process_identity(gone.pid) is None
    assert st.liveness(st.record_start(st.state_root(repo), _binding(process=gone))) == st.ORPHANED


def test_no_recorded_process_is_orphaned_not_live(repo):
    assert st.liveness(st.record_start(st.state_root(repo), _binding(process=None))) == st.ORPHANED


# ---- AC3: released is explicit and survives; live/orphaned is never on disk --------------------

def test_release_is_explicit_survives_rereading_and_liveness_is_never_written(repo, child):
    root = st.state_root(repo)
    st.record_start(root, _binding(process=st.process_identity(child.pid)))
    text = (root / "r-one" / st.INSTANCE).read_text()
    assert "live" not in json.loads(text) and "orphaned" not in text and '"state"' not in text
    assert st.liveness(st.read_instance(root, "r-one")) == st.LIVE
    st.release(root, "r-one")
    again = st.read_instance(root, "r-one")
    assert again.released and again.released_at and st.liveness(again) == st.RELEASED  # even though the pid is live
    st.record_start(root, _binding(sid="s2"))  # a new start clears the release
    assert not st.read_instance(root, "r-one").released


def test_release_without_an_instance_is_an_error(repo):
    with pytest.raises(st.StateError):
        st.release(st.state_root(repo), "nobody")


# ---- AC4: the writer lease ---------------------------------------------------------------------

def test_lease_retake_by_the_same_role_succeeds_and_another_role_is_refused(repo, child):
    root, wt = st.state_root(repo), repo
    live = st.process_identity(child.pid)
    st.take_lease(root, wt, "r-one", "s1", live)
    again = st.take_lease(root, wt, "r-one", "s2", None)  # /clear: new session id, same role
    assert again.session_id == "s2" and st.read_lease(root, wt).session_id == "s2"
    with pytest.raises(st.LeaseRefused) as exc:
        st.take_lease(root, wt, "r-two", "s3", live)
    assert exc.value.lease.role == "r-one"
    assert st.read_lease(root, wt).role == "r-one"  # not taken


def test_a_stale_lease_is_reported_with_holder_and_age_and_not_taken(repo):
    root = st.state_root(repo)
    st.take_lease(root, repo, "r-one", "s1", st.ProcessId(2**22 + 999, "1", "claude"))
    with pytest.raises(st.LeaseRefused) as exc:
        st.take_lease(root, repo, "r-two", "s9", None)
    assert exc.value.liveness == "stale" and exc.value.age_seconds >= 0
    assert "r-one" in str(exc.value) and "s1" in str(exc.value)
    assert st.read_lease(root, repo).role == "r-one"
    assert st.release_lease(root, repo) is True  # the explicit, user-driven path
    assert st.take_lease(root, repo, "r-two", "s9", None).role == "r-two"
    assert st.release_lease(root, tmp_nonexistent := repo / "nope") is False


def test_lease_key_is_the_physical_worktree_path(repo, tmp_path):
    wt = tmp_path / "wt2"
    _git(repo, "worktree", "add", "-q", "-b", "o2", str(wt))
    root = st.state_root(repo)
    st.take_lease(root, repo, "r-one", "s1", None)
    st.take_lease(root, wt, "r-two", "s2", None)  # a different physical worktree: its own writer
    assert st.read_lease(root, repo).role == "r-one" and st.read_lease(root, wt).role == "r-two"
    link = tmp_path / "link"
    link.symlink_to(wt)
    assert st.lease_path(root, link) == st.lease_path(root, wt)


# ---- AC5: concurrent appends -------------------------------------------------------------------

def _append_many(args):
    root, n, tag = args
    for i in range(n):
        st.append_binding(Path(root), _binding(sid=f"{tag}-{i}"))


def test_parallel_appends_yield_exactly_n_valid_json_lines(repo):
    root = st.state_root(repo)
    with multiprocessing.get_context("fork").Pool(6) as pool:
        pool.map(_append_many, [(str(root), 40, f"p{k}") for k in range(6)])
    lines = (root / "r-one" / st.BINDINGS).read_text().splitlines()
    assert len(lines) == 240
    assert len({json.loads(x)["session_id"] for x in lines}) == 240
    assert len(st.read_bindings(root, "r-one")) == 240


# ---- AC6: typed loader, nothing outside the role-state dir -------------------------------------

def test_malformed_files_raise_state_error_with_the_path(repo):
    root = st.state_root(repo)
    st.record_start(root, _binding())
    (root / "r-one" / st.INSTANCE).write_text("{not json")
    with pytest.raises(st.StateError, match="instance.json"):
        st.read_instance(root, "r-one")
    (root / "r-one" / st.BINDINGS).write_text('{"session_id": "x"}\n')
    with pytest.raises(st.StateError, match="bindings.jsonl:1"):
        st.read_bindings(root, "r-one")


@pytest.mark.parametrize("bad", ["", "../escape", "Upper", "a/b", "-x"])
def test_unusable_role_ids_are_refused(repo, bad):
    with pytest.raises(st.StateError):
        st.role_dir(st.state_root(repo), bad)


def test_writes_stay_inside_the_state_root(repo):
    root = st.state_root(repo)
    before = {p for p in root.parent.rglob("*") if not str(p).startswith(str(root))}
    st.record_start(root, _binding())
    st.take_lease(root, repo, "r-one", "s1", None)
    st.release(root, "r-one")
    after = {p for p in root.parent.rglob("*") if not str(p).startswith(str(root))}
    assert before == after


def test_cli_show_and_release(repo, capsys, monkeypatch):
    monkeypatch.chdir(repo)
    assert st.main(["show", "r-one"]) == 0 and "no instance recorded" in capsys.readouterr().out
    st.record_start(st.state_root(repo), _binding())
    assert st.main(["show", "r-one"]) == 0 and "orphaned" in capsys.readouterr().out
    assert st.main(["release", "r-one"]) == 0
    st.main(["show", "r-one"])
    assert "released" in capsys.readouterr().out
    assert st.main(["release", "ghost"]) == 1
