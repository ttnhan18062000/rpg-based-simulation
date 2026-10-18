"""tools/sessions/settings_freshness.py and the launcher preflight (TCK-20261006-LIVE-SESSIONS-RUN-STALE-OR-NO-PROJECT-HOOKS).

Real git repositories; `origin/main` is simulated with `update-ref`, so nothing is fetched."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REAL_ROOT = Path(__file__).resolve().parents[2]
if str(REAL_ROOT) not in sys.path:
    sys.path.insert(0, str(REAL_ROOT))

from tools.sessions import launch as ln  # noqa: E402
from tools.sessions import settings_freshness as sf  # noqa: E402
from tools.sessions import state as st  # noqa: E402

_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t", "PATH": os.environ["PATH"], "HOME": os.environ.get("HOME", "/")}
GUARD = "python3 tools/sessions/guard.py"
SAMPLER = "python3 tools/agent-monitoring/manual_actions.py hook"


def git(cwd, *a):
    return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True, env=_ENV)


def _settings(*commands: str) -> str:
    hooks = {"PreToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": c} for c in commands]}]}
    return json.dumps({"permissions": {}, "hooks": hooks}, indent=2)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "main"
    (r / ".claude" / "agents").mkdir(parents=True)
    git(tmp_path, "init", "-q", "-b", "main", str(r))
    (r / ".claude" / "settings.json").write_text(_settings(GUARD, SAMPLER))
    (r / ".claude" / "agents" / "a.md").write_text("agent a\n")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "init")
    git(r, "update-ref", "refs/remotes/origin/main", "HEAD")
    return r


def test_a_fresh_detached_worktree_matches(repo, tmp_path):
    wt = tmp_path / "fresh"
    git(repo, "worktree", "add", "-q", "--detach", str(wt), "origin/main")
    report = sf.check(wt)
    assert report.status == sf.OK and report.problems == [] and sf.main([str(wt)]) == 0


def test_a_missing_hook_is_reported_by_name(repo):
    (repo / ".claude" / "settings.json").write_text(_settings(GUARD))
    report = sf.check(repo)
    assert report.status == sf.MISMATCH and report.missing_hooks == [f"PreToolUse: {SAMPLER}"]
    assert sf.main([str(repo)]) == 1


def test_a_differing_or_missing_agent_file_is_a_mismatch(repo):
    (repo / ".claude" / "agents" / "a.md").write_text("changed\n")
    assert any("a.md differs" in p for p in sf.check(repo).problems)
    (repo / ".claude" / "agents" / "a.md").unlink()
    assert any("a.md is missing" in p for p in sf.check(repo).problems)


def test_outside_the_repo_is_a_mismatch_naming_the_symptoms(tmp_path):
    report = sf.check(tmp_path)
    assert report.status == sf.MISMATCH and not report.inside_repo
    assert "not found" in report.problems[0] and "unresolved" in report.problems[0]


def test_a_missing_ref_is_unknown_not_a_mismatch(tmp_path):
    r = tmp_path / "norefs"
    git(tmp_path, "init", "-q", "-b", "main", str(r))
    report = sf.check(r)
    assert report.status == sf.UNKNOWN and sf.main([str(r)]) == 2


def test_the_ref_is_read_without_writing_or_fetching(repo):
    before = git(repo, "status", "--porcelain").stdout
    sf.check(repo)
    assert git(repo, "status", "--porcelain").stdout == before


# ---- the launcher preflight --------------------------------------------------------------------

def _dry_run(repo, tmp_path, monkeypatch, *extra):
    monkeypatch.setattr(st, "state_root", lambda *_: tmp_path / "sr")
    monkeypatch.setattr(os, "execvpe", lambda *a, **k: pytest.fail("must not exec in a dry run"))
    return ln.main(["agent-working-implementer", "--dry-run", "--worktree", str(repo), *extra], root=REAL_ROOT)


def test_dry_run_against_a_stale_worktree_prints_the_mismatch_and_no_exec_line(repo, tmp_path, monkeypatch, capsys):
    (repo / ".claude" / "settings.json").write_text(_settings(GUARD))
    assert _dry_run(repo, tmp_path, monkeypatch) == ln.EXIT_REFUSED
    out = capsys.readouterr().out
    assert "STALE OR OUTSIDE THE REPO" in out and "missing hook" in out and "DRY RUN" not in out


def test_allow_stale_launches_a_stale_worktree(repo, tmp_path, monkeypatch, capsys):
    (repo / ".claude" / "settings.json").write_text(_settings(GUARD))
    assert _dry_run(repo, tmp_path, monkeypatch, "--allow-stale") == 0
    out = capsys.readouterr().out
    assert "--allow-stale" in out and "DRY RUN" in out


def test_a_fresh_worktree_launches_with_no_preflight_noise(repo, tmp_path, monkeypatch, capsys):
    assert _dry_run(repo, tmp_path, monkeypatch) == 0
    assert "STALE" not in capsys.readouterr().out


def test_allow_stale_never_launches_from_outside_the_repo(tmp_path):
    outside = tmp_path / "plain"
    outside.mkdir()
    go, lines = ln.preflight(outside, allow_stale=True)
    assert go is False and "not inside a git repository" in "\n".join(lines)


def test_an_unverifiable_ref_only_warns(tmp_path):
    r = tmp_path / "norefs"
    git(tmp_path, "init", "-q", "-b", "main", str(r))
    go, lines = ln.preflight(r, allow_stale=False)
    assert go is True and "could not be verified" in lines[-1]


# ---- TCK-20261015-SESSION-CODE-FRESHNESS-AT-SESSION-START ---------------------------------------------------

def _code_repo(repo):
    (repo / "tools" / "sessions").mkdir(parents=True)
    (repo / "registries").mkdir()
    (repo / "tools" / "sessions" / "session_start_hook.py").write_text("v1\n")
    (repo / "registries" / "session_roles.yaml").write_text("roles: v1\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "session code v1")
    git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    return repo


def _advance_origin(repo, tmp_path, name="hook.py"):
    """Move origin/main ahead by one commit that changes session code, without moving `repo`'s branch."""
    other = tmp_path / "other"
    git(repo, "worktree", "add", "-q", "--detach", str(other), "origin/main")
    (other / "tools" / "sessions" / "session_start_hook.py").write_text("v2\n")
    git(other, "commit", "-aq", "-m", "session code v2")
    git(repo, "update-ref", "refs/remotes/origin/main", git(other, "rev-parse", "HEAD").stdout.strip())
    git(repo, "worktree", "remove", "--force", str(other))


def test_a_current_worktree_has_no_stale_session_code_and_no_line(repo):
    _code_repo(repo)
    assert sf.stale_session_code(repo) == []
    assert sf.session_code_line(repo) == ""


def test_a_worktree_behind_origin_names_the_stale_files_in_one_line(repo, tmp_path):
    _code_repo(repo)
    _advance_origin(repo, tmp_path)
    assert sf.stale_session_code(repo) == ["tools/sessions/session_start_hook.py"]
    line = sf.session_code_line(repo)
    assert line.count("\n") == 0 and "STALE SESSION CODE" in line
    assert "tools/sessions/session_start_hook.py" in line and "Sync this worktree" in line


def test_a_branch_that_edits_session_code_itself_is_not_called_stale(repo):
    _code_repo(repo)
    (repo / "tools" / "sessions" / "session_start_hook.py").write_text("my own edit\n")
    git(repo, "commit", "-aq", "-m", "my edit")  # ahead of origin/main, never behind
    assert sf.stale_session_code(repo) == []


def test_no_origin_ref_or_no_repo_says_it_could_not_verify(repo, tmp_path):
    git(repo, "update-ref", "-d", "refs/remotes/origin/main")
    assert sf.stale_session_code(repo) is None
    assert "could not verify" in sf.session_code_line(repo)
    assert sf.stale_session_code(tmp_path / "nowhere") is None


def test_a_crash_in_the_check_fails_open_and_says_so(repo, monkeypatch):
    monkeypatch.setattr(sf, "stale_session_code", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    assert "check failed (RuntimeError); not verified" in sf.session_code_line(repo)


def test_the_check_is_offline_and_fast(repo, tmp_path):
    import time
    _code_repo(repo)
    _advance_origin(repo, tmp_path)
    calls = []
    real = sf._git
    sf._git = lambda args, cwd, binary=False: (calls.append(args[0]), real(args, cwd, binary))[1]
    try:
        t0 = time.perf_counter()
        sf.session_code_line(repo)
        elapsed = time.perf_counter() - t0
    finally:
        sf._git = real
    assert not {"fetch", "pull", "ls-remote", "clone"} & set(calls) and len(calls) == 3
    assert elapsed < 2.0
