"""Tests for tools/delivery/pre_push_advisory_hook.py (TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY).

One section per Acceptance Criterion, per staging_artifacts/TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY/
test_plan.md. Checks A/B use a FakeRunner; Check C (AC6) uses a real throwaway git repo, since a
faked-output fixture cannot prove the ancestor-vs-content distinction is real.
"""
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.delivery import pre_push_advisory_hook as hook


def _write_ticket(root: Path, ticket_id: str) -> Path:
    path = root / f"{ticket_id}.md"
    path.write_text(f"---\nticket_id: {ticket_id}\n---\n# {ticket_id}\n", encoding="utf-8")
    return path


class FakeRunner:
    def __init__(self, rules):
        self.rules = rules
        self.calls = []

    def __call__(self, cmd, timeout=30):
        self.calls.append(cmd)
        for predicate, result in self.rules:
            if predicate(cmd):
                return result
        raise AssertionError(f"no rule matched {cmd!r}")


def ok(stdout=""):
    return hook.CommandResult(0, stdout, "")


def fail():
    return hook.CommandResult(1, "", "error")


def _log_rule(lines):
    return (lambda cmd: cmd[:2] == ["git", "log"], ok("\n".join(lines) + ("\n" if lines else "")))


def _status_rule(lines):
    return (lambda cmd: cmd[:2] == ["git", "status"], ok("\n".join(lines) + ("\n" if lines else "")))


def _revlist_rule(count):
    return (lambda cmd: cmd[:2] == ["git", "rev-list"], ok(str(count) + "\n"))


def _ancestor_rule(is_ancestor):
    return (lambda cmd: cmd[:2] == ["git", "merge-base"], ok() if is_ancestor else fail())


def _diff_rule(matcher_extra, content):
    def predicate(cmd):
        return cmd[:2] == ["git", "diff"] and matcher_extra(cmd)
    return (predicate, ok(content))


# ---------------------------------------------------------------------------
# Matcher (Assumption 1's measured corpus shapes)
# ---------------------------------------------------------------------------

def test_matcher_regex_against_measured_corpus_shapes():
    real_shapes = [
        "git push",
        "git push origin main",
        "git push origin feature-branch",
        "cd /repo\ngit push origin main",
        "git status\ngit push",
        "git add -A && git commit -m x && git push origin main",
        "git commit -m x; git push",
    ]
    for shape in real_shapes:
        assert hook.is_git_push_command(shape), f"expected match: {shape!r}"

    false_positive = 'grep -n "git commit\\|git add\\|git push\\|git checkout" file.py'
    assert not hook.is_git_push_command(false_positive)


# ---------------------------------------------------------------------------
# AC1 — all-clear
# ---------------------------------------------------------------------------

def test_all_clear_yields_no_findings(tmp_path):
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    _write_ticket(tickets_root, "TCK-20260924-EXAMPLE")
    runner = FakeRunner([
        _log_rule(["abc1234\tTCK-20260924-EXAMPLE: do the thing"]),
        _status_rule([]),
        _revlist_rule(0),
    ])
    findings = hook.run_all_checks(run_command=runner, tickets_root=tickets_root)
    assert findings == []


# ---------------------------------------------------------------------------
# AC2 / AC3 — commit subject checks
# ---------------------------------------------------------------------------

def test_commit_with_no_ticket_id_is_reported(tmp_path):
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    runner = FakeRunner([_log_rule(["abc1234\tjust a fix, no ticket"])])
    findings = hook.check_commit_subjects(run_command=runner, tickets_root=tickets_root)
    assert len(findings) == 1
    assert "abc1234" in findings[0]
    assert "no ticket ID" in findings[0]


def test_commit_with_ticket_id_but_no_file_is_a_distinct_finding(tmp_path):
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    runner = FakeRunner([_log_rule(["def5678\tTCK-20260924-GHOST: does not exist"])])
    findings = hook.check_commit_subjects(run_command=runner, tickets_root=tickets_root)
    assert len(findings) == 1
    assert "TCK-20260924-GHOST" in findings[0]
    assert "no ticket file exists" in findings[0]
    assert "no ticket ID" not in findings[0]


def test_ticket_moved_to_done_mid_branch_not_reported_missing(tmp_path):
    tickets_root = tmp_path / "tickets"
    done_dir = tickets_root / "done"
    done_dir.mkdir(parents=True)
    _write_ticket(done_dir, "TCK-20260924-MOVED")
    runner = FakeRunner([_log_rule(["aaa1111\tTCK-20260924-MOVED: closed mid-branch"])])
    findings = hook.check_commit_subjects(run_command=runner, tickets_root=tickets_root)
    assert findings == []


# ---------------------------------------------------------------------------
# AC5 — monitoring shard staged
# ---------------------------------------------------------------------------

def test_dirty_shard_is_reported():
    runner = FakeRunner([_status_rule([" M agent-monitoring/data/2026-W39/tools.jsonl"])])
    findings = hook.check_monitoring_shard_staged(run_command=runner)
    assert len(findings) == 1
    assert "tools.jsonl" in findings[0]


def test_clean_shard_yields_no_finding():
    runner = FakeRunner([_status_rule([])])
    findings = hook.check_monitoring_shard_staged(run_command=runner)
    assert findings == []


# ---------------------------------------------------------------------------
# AC6 — squash-merged-and-finished (real throwaway git repo)
# ---------------------------------------------------------------------------

def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo)] + list(args), capture_output=True, text=True, check=True)


def _init_repo(repo):
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "f.txt").write_text("a\n")
    _git(repo, "add", "f.txt")
    _git(repo, "commit", "-q", "-m", "init")
    _git(repo, "branch", "-M", "main")


def test_squash_merged_finished_shape_detected(tmp_path):
    repo = tmp_path / "repo"
    _init_repo(repo)

    _git(repo, "checkout", "-q", "-b", "feature")
    (repo / "f.txt").write_text("a\nb\n")
    _git(repo, "add", "f.txt")
    _git(repo, "commit", "-q", "-m", "feature work")

    # Simulate the GitHub squash-merge: apply feature's content to main as ONE new commit, whose
    # parent is main's own prior tip -- feature's own commit is never an ancestor of this.
    _git(repo, "checkout", "-q", "main")
    _git(repo, "checkout", "-q", "feature", "--", "f.txt")
    _git(repo, "commit", "-q", "-m", "feature work (squashed) (#1)")

    # Simulate origin/main by making main itself the "remote" ref this hook compares against.
    _git(repo, "update-ref", "refs/remotes/origin/main", "main")

    # Back on feature (still based on the OLD content), no-op commit -- content already in main,
    # but feature's own commits are not ancestors of main.
    _git(repo, "checkout", "-q", "feature")
    (repo / "g.txt").write_text("noop\n")
    _git(repo, "add", "g.txt")
    _git(repo, "commit", "-q", "-m", "trailing no-op commit")
    _git(repo, "rm", "-q", "g.txt")
    _git(repo, "commit", "-q", "-m", "revert the no-op, back to squashed content")

    def real_run(cmd, timeout=30):
        result = subprocess.run(["git", "-C", str(repo)] + cmd[1:], capture_output=True, text=True)
        return hook.CommandResult(result.returncode, result.stdout, result.stderr)

    findings = hook.check_squash_merged_finished(run_command=real_run, base_ref="origin/main")
    assert len(findings) == 1
    assert "squash-merged and finished" in findings[0]
    assert "fresh branch" in findings[0]


def test_branch_merely_behind_main_is_not_flagged(tmp_path):
    repo = tmp_path / "repo"
    _init_repo(repo)
    _git(repo, "checkout", "-q", "-b", "feature")
    (repo / "f.txt").write_text("a\nb\n")
    _git(repo, "add", "f.txt")
    _git(repo, "commit", "-q", "-m", "real new work")
    _git(repo, "update-ref", "refs/remotes/origin/main", "main")

    def real_run(cmd, timeout=30):
        result = subprocess.run(["git", "-C", str(repo)] + cmd[1:], capture_output=True, text=True)
        return hook.CommandResult(result.returncode, result.stdout, result.stderr)

    findings = hook.check_squash_merged_finished(run_command=real_run, base_ref="origin/main")
    assert findings == []


# ---------------------------------------------------------------------------
# AC7 / AC8 — exit code and malformed input
# ---------------------------------------------------------------------------

def test_exit_code_zero_for_every_check_combination(tmp_path, monkeypatch):
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    runner = FakeRunner([
        _log_rule(["abc1234\tno ticket here"]),
        _status_rule([" M agent-monitoring/data/2026-W39/tools.jsonl"]),
        _revlist_rule(0),
    ])
    findings = hook.run_all_checks(run_command=runner, tickets_root=tickets_root)
    assert len(findings) == 2  # commit + shard findings, no squash-finished finding (ahead=0)

    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"tool_input": {"command": "git push"}})))
    monkeypatch.setattr(hook, "run_all_checks", lambda: findings)
    exit_code = hook.main()
    assert exit_code == 0


def test_malformed_json_stdin_no_traceback(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
    exit_code = hook.main()
    assert exit_code == 0
    assert capsys.readouterr().out == ""


def test_empty_stdin_no_traceback(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    exit_code = hook.main()
    assert exit_code == 0


def test_non_push_command_never_runs_checks(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"tool_input": {"command": "ls -la"}})))
    called = []
    monkeypatch.setattr(hook, "run_all_checks", lambda: called.append(True))
    exit_code = hook.main()
    assert exit_code == 0
    assert called == []


# ---------------------------------------------------------------------------
# Regression-prone paths
# ---------------------------------------------------------------------------

def test_detached_head_git_failure_degrades_to_no_finding():
    runner = FakeRunner([
        (lambda cmd: True, fail()),
    ])
    assert hook.check_commit_subjects(run_command=runner) == []
    assert hook.check_monitoring_shard_staged(run_command=runner) == []
    assert hook.check_squash_merged_finished(run_command=runner) == []


def test_settings_json_new_hook_appended_at_end_not_inserted():
    settings = json.loads(Path(".claude/settings.json").read_text(encoding="utf-8"))
    pre_tool_use = settings["hooks"]["PreToolUse"]
    assert len(pre_tool_use) == 7
    last = pre_tool_use[-1]
    assert last["matcher"] == "Bash"
    commands = [h["command"] for h in last["hooks"]]
    assert any("pre_push_advisory_hook.py" in c for c in commands)


def test_settings_json_hooks_wiring_count_bumped():
    text = Path("tests/tools/test_settings_json_hooks_wiring.py").read_text(encoding="utf-8")
    assert 'len(settings["hooks"]["PreToolUse"]) == 7' in text
    assert 'len(settings["hooks"]["PreToolUse"]) == 6' not in text
