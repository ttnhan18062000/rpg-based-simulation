"""Tests for tools/agent-monitoring/monitoring_batch_identifier.py
(TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX).

Real throwaway git repos throughout, matching this project's own established pattern for proving
git-state claims (`test_delivery_pre_push_advisory.py`'s Check C,
`test_monitoring_consolidation.py`'s AC1) -- a synthetic mock of `.git`'s shape cannot prove the
resolver handles this repo's own real worktree-gitlink mode or a real detached HEAD correctly.
"""
import subprocess
import sys
from pathlib import Path

_MONITORING_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

import monitoring_batch_identifier as mbi  # noqa: E402


def _git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo)] + list(args), capture_output=True, text=True, check=True
    )


def _init_repo(repo):
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "README.md").write_text("base\n")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-q", "-m", "init")
    _git(repo, "branch", "-M", "main")


def test_resolves_branch_name_on_attached_head(tmp_path):
    repo = tmp_path / "repo"
    _init_repo(repo)
    _git(repo, "checkout", "-q", "-b", "my-feature-branch")

    assert mbi.resolve_batch_identifier(repo) == "my-feature-branch"


def test_resolves_via_worktree_gitlink(tmp_path):
    repo = tmp_path / "repo"
    _init_repo(repo)
    _git(repo, "branch", "wt-branch")
    worktree_dir = tmp_path / "wt"
    _git(repo, "worktree", "add", "-q", str(worktree_dir), "wt-branch")

    # The worktree's own .git is a gitlink FILE, not a directory -- confirms the resolver reads
    # the worktree-specific HEAD, not the main checkout's.
    assert (worktree_dir / ".git").is_file()
    assert mbi.resolve_batch_identifier(worktree_dir) == "wt-branch"
    # The main checkout is still on "main", proving these are genuinely independent HEADs.
    assert mbi.resolve_batch_identifier(repo) == "main"


def test_detached_head_without_sidecar_falls_back_to_labeled_identifier(tmp_path, capsys):
    repo = tmp_path / "repo"
    _init_repo(repo)
    sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _git(repo, "checkout", "-q", "--detach", sha)

    identifier = mbi.resolve_batch_identifier(repo)

    assert identifier.startswith("detached-")
    assert identifier != "detached-HEAD"
    assert not (repo / ".claude" / "current_batch").exists()
    captured = capsys.readouterr()
    assert "WARNING" in captured.err
    assert "detached" in captured.err.lower()


def test_detached_head_with_sidecar_self_heals(tmp_path):
    repo = tmp_path / "repo"
    _init_repo(repo)
    _git(repo, "checkout", "-q", "-b", "real-branch-name")

    # First resolution on the real branch writes the self-healing sidecar.
    first = mbi.resolve_batch_identifier(repo)
    assert first == "real-branch-name"
    sidecar_path = repo / ".claude" / "current_batch"
    assert sidecar_path.exists()
    assert sidecar_path.read_text(encoding="utf-8").strip() == "real-branch-name"

    # Now detach, in the SAME working dir, and bypass this test process's own in-memory cache by
    # resolving against a distinct Path object built from the same string (str-keyed cache) --
    # use a fresh subprocess-free reset instead: clear the module cache directly, which is exactly
    # what a brand-new process (the real-world case) would start with.
    mbi._cache.clear()
    sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _git(repo, "checkout", "-q", "--detach", sha)

    second = mbi.resolve_batch_identifier(repo)
    assert second == "real-branch-name"
    assert not second.startswith("detached-")


def test_slash_in_branch_name_sanitized(tmp_path):
    repo = tmp_path / "repo"
    _init_repo(repo)
    _git(repo, "checkout", "-q", "-b", "feature/foo")

    identifier = mbi.resolve_batch_identifier(repo)

    assert identifier == "feature-foo"
    assert "/" not in identifier


def test_sanitize_for_filename_replaces_slash():
    assert mbi.sanitize_for_filename("feature/foo") == "feature-foo"
    assert mbi.sanitize_for_filename("no-slash") == "no-slash"


def test_resolve_write_target_shape(tmp_path):
    repo = tmp_path / "repo"
    _init_repo(repo)
    _git(repo, "checkout", "-q", "-b", "my-branch")

    target = mbi.resolve_write_target("tools", cwd=repo)

    assert target.name.endswith("my-branch.tools.jsonl")
    assert target.parent.parent.name == "data"
    assert target.is_relative_to(repo)


def test_resolve_write_target_default_cwd_returns_relative_path(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    _init_repo(repo)
    _git(repo, "checkout", "-q", "-b", "relative-branch")
    monkeypatch.chdir(repo)
    mbi._cache.clear()

    target = mbi.resolve_write_target("runs")

    assert not target.is_absolute()
    assert str(target).startswith("agent-monitoring/data/")
    assert target.name.endswith("relative-branch.runs.jsonl")


def test_resolver_module_makes_no_subprocess_call():
    # Checks actual code usage, not prose -- the module's own docstring discusses *why* it
    # avoids subprocess calls, which would trip a bare substring check on the word itself.
    source = Path(mbi.__file__).read_text(encoding="utf-8")
    assert "import subprocess" not in source
    assert "subprocess.run(" not in source
    assert "subprocess.Popen(" not in source
    assert "Popen(" not in source
    assert "os.system(" not in source
