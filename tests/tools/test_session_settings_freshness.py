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
