"""tools/sessions/disk_headroom.py and its launcher / SessionStart wiring (TCK-20261008-SESSION-DISK-HEADROOM-GUARD)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REAL_ROOT = Path(__file__).resolve().parents[2]
if str(REAL_ROOT) not in sys.path:
    sys.path.insert(0, str(REAL_ROOT))

from tools.sessions import disk_headroom as dh  # noqa: E402
from tools.sessions import launch as ln  # noqa: E402
from tools.sessions import session_start_hook as hook  # noqa: E402
from tools.sessions import state as st  # noqa: E402

GB = dh.GB
_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t", "PATH": os.environ["PATH"], "HOME": os.environ.get("HOME", "/")}


def _git(cwd, *a):
    subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, env=_ENV)


@pytest.fixture
def world(tmp_path):
    main = tmp_path / "main"
    main.mkdir()
    _git(main, "init", "-q", "-b", "main")
    (main / "f").write_text("x")
    _git(main, "add", "-A")
    _git(main, "commit", "-q", "-m", "i")
    other = tmp_path / "other"
    _git(main, "worktree", "add", "-q", "-b", "topic", str(other))
    (main / "data" / "runs" / "r1").mkdir(parents=True)
    (main / "data" / "runs" / "r1" / "blob").write_bytes(b"a" * 40960)
    (other / "reports" / "release_proof").mkdir(parents=True)
    (other / "reports" / "release_proof" / "blob").write_bytes(b"b" * 81920)
    return main, other


def _du(path: Path) -> int:
    out = subprocess.run(["du", "-s", "--block-size=1", str(path)], capture_output=True, text=True, check=True)
    return int(out.stdout.split()[0])


def test_free_space_matches_statvfs_and_df(tmp_path):
    st_ = os.statvfs(tmp_path)
    assert abs(dh.free_bytes(tmp_path) - st_.f_bavail * st_.f_frsize) < 64 * 1024 * 1024
    df = subprocess.run(["df", "--output=avail", "--block-size=1", str(tmp_path)], capture_output=True, text=True, check=True)
    assert abs(dh.free_bytes(tmp_path) - int(df.stdout.split()[-1])) < 64 * 1024 * 1024


def test_run_data_and_totals_match_du_on_a_fixture(world):
    main, other = world
    h = dh.measure(main)
    by_path = {w.path: w for w in h.worktrees}
    assert set(by_path) == {str(main), str(other)}
    assert by_path[str(main)].run_data_bytes == _du(main / "data" / "runs")
    assert by_path[str(other)].run_data_bytes == _du(other / "reports" / "release_proof")
    assert by_path[str(other)].run_data_bytes > by_path[str(main)].run_data_bytes
    assert h.worktrees[0].path == str(other)  # largest run-data holder first
    assert by_path[str(main)].total_bytes >= by_path[str(main)].run_data_bytes
    assert h.total_worktree_bytes == sum(w.total_bytes for w in h.worktrees)


def test_json_output_has_a_stable_shape(world):
    main, _ = world
    doc = json.loads(dh.to_json(dh.measure(main)))
    assert list(doc) == sorted(doc) == ["free_bytes", "total_bytes", "total_run_data_bytes", "total_worktree_bytes", "worktrees"]
    assert sorted(doc["worktrees"][0]) == ["branch", "path", "run_data_bytes", "total_bytes"]
    assert all(isinstance(doc[k], int) for k in doc if k != "worktrees")


def test_cli_prints_text_and_json_and_exits_zero(world, capsys):
    main, _ = world
    assert dh.main(["--root", str(main)]) == 0
    assert "worktrees: 2" in capsys.readouterr().out
    assert dh.main(["--root", str(main), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["worktrees"]


def test_warning_line_only_below_the_threshold_and_names_the_largest_holders(world):
    main, other = world
    h = dh.measure(main)
    low = dh.Headroom(5 * GB, 50 * GB, h.worktrees)
    line = dh.warning_line(low, 10 * GB)
    assert line and "5.0 GB free" in line and "other" in line
    assert dh.warning_line(dh.Headroom(11 * GB, 50 * GB, h.worktrees), 10 * GB) is None
    assert dh.low_space_line(10 * GB, 10 * GB) is None  # at the threshold is silent


def test_threshold_default_override_and_bad_env():
    assert dh.threshold_bytes(environ={}) == 10 * GB
    assert dh.threshold_bytes(environ={dh.THRESHOLD_ENV: "3"}) == 3 * GB
    assert dh.threshold_bytes(environ={dh.THRESHOLD_ENV: "junk"}) == 10 * GB
    assert dh.threshold_bytes(2.5, environ={}) == int(2.5 * GB)


def test_launcher_warns_below_and_is_silent_above_without_walking(monkeypatch):
    walks = []
    monkeypatch.setattr(dh, "measure", lambda root: walks.append(root) or dh.Headroom(1 * GB, 50 * GB, ()))
    monkeypatch.setattr(dh, "free_bytes", lambda root=None: 50 * GB)
    assert ln.disk_warning(REAL_ROOT) == [] and walks == []  # healthy disk: no tree walk at all
    monkeypatch.setattr(dh, "free_bytes", lambda root=None: 1 * GB)
    lines = ln.disk_warning(REAL_ROOT)
    assert len(lines) == 1 and "1.0 GB free" in lines[0] and walks == [REAL_ROOT]


def test_launcher_warning_never_raises(monkeypatch):
    monkeypatch.setattr(dh, "free_bytes", lambda root=None: (_ for _ in ()).throw(OSError("boom")))
    assert ln.disk_warning(REAL_ROOT) == []


def test_launcher_exit_code_is_the_same_with_and_without_the_warning(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(st, "state_root", lambda *_: tmp_path / "sr")
    monkeypatch.setattr(os, "execvpe", lambda *a, **k: pytest.fail("must not exec in a dry run"))
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    (repo / "f").write_text("x")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "i")
    codes = []
    for free in (50 * GB, 1 * GB):
        monkeypatch.setattr(dh, "free_bytes", lambda root=None, f=free: f)
        monkeypatch.setattr(dh, "measure", lambda root: dh.Headroom(1 * GB, 50 * GB, ()))
        codes.append(ln.main(["agent-working-implementer", "--dry-run", "--worktree", str(repo)], root=REAL_ROOT))
        out = capsys.readouterr().out
        assert ("disk-headroom:" in out) == (free < 10 * GB)
    assert codes[0] == codes[1]


def test_session_start_line_appears_only_below_the_threshold(monkeypatch):
    monkeypatch.setattr(dh, "free_bytes", lambda root=None: 50 * GB)
    assert hook._disk_line(REAL_ROOT) == ""
    monkeypatch.setattr(dh, "free_bytes", lambda root=None: 2 * GB)
    assert "2.0 GB free" in hook._disk_line(REAL_ROOT)


def test_session_start_line_failure_yields_no_line(monkeypatch):
    monkeypatch.setattr(dh, "free_bytes", lambda root=None: (_ for _ in ()).throw(RuntimeError("boom")))
    assert hook._disk_line(REAL_ROOT) == ""
