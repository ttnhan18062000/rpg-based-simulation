"""Tests for tools/agent-monitoring/arch_verify_read_check.py
(TCK-20261002-ARCH-VERIFY-TEST-QUALITY-FINDINGS, follow-up serving the same evidence purpose).

Fixture shards in tmp_path; the git diff is injected, so nothing here touches the real repo."""
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

_TOOLS = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
sys.path.insert(0, str(_TOOLS))

import arch_verify_read_check as m  # noqa: E402

TID = "TCK-20261002-X"
ROOT = "/home/u/work/rpg/.claude/worktrees/some-fairly-long-worktree-name-here"


def _write(tmp_path, tools, events=()):
    week = tmp_path / "2026-W40"
    week.mkdir()
    (week / "br.tools.jsonl").write_text("\n".join(json.dumps(r) for r in tools) + "\n")
    (week / "br.events.jsonl").write_text("\n".join(json.dumps(r) for r in events) + "\n")
    return tmp_path


def _read(path, run_id=TID, phase=m.PHASE, agent=m.PRODUCTION_AGENT, ts="2026-10-02T10:00:05Z", tool="Read"):
    return {"run_id": run_id, "seq": 5, "phase": phase, "agent": agent, "ts": ts, "tool": tool, "input_summary": path}


def _events():
    return [
        {"run_id": TID, "seq": 4, "phase": "Implement", "agent": "implementer", "ts": "2026-10-02T09:00:00Z"},
        {"run_id": TID, "seq": 5, "phase": m.PHASE, "agent": m.PRODUCTION_AGENT, "ts": "2026-10-02T10:00:00Z"},
        {"run_id": TID, "seq": 6, "phase": "Test", "agent": "test-scoper", "ts": "2026-10-02T11:00:00Z"},
    ]


def test_exact_read_is_read_and_an_unread_changed_test_is_not_read(tmp_path):
    root = _write(tmp_path, [_read(f"{ROOT}/tests/a/test_one.py")], _events())
    res = m.check(TID, ["tests/a/test_one.py", "tests/a/test_two.py"], root)
    assert res["files"] == {"tests/a/test_one.py": "READ", "tests/a/test_two.py": "NOT-READ"}
    assert res["attributed_read_rows"] == 1


def test_a_path_cut_at_120_chars_is_only_possibly_read_never_asserted_read(tmp_path):
    long_root = "/" + "d" * 100
    cut = (f"{long_root}/tests/tools/test_something_quite_long_indeed.py")[: m.CUT]
    assert len(cut) == m.CUT
    root = _write(tmp_path, [_read(cut)], _events())
    res = m.check(TID, ["tests/tools/test_something_quite_long_indeed.py", "tests/other/test_x.py"], root)
    assert res["files"]["tests/tools/test_something_quite_long_indeed.py"] == "POSSIBLY-READ"
    assert res["files"]["tests/other/test_x.py"] == "NOT-READ"
    assert res["attributed_rows_cut_at_120"] == 1


def test_a_cut_that_ends_before_reaching_tests_matches_nothing(tmp_path):
    cut = ("/" + "d" * 118)[: m.CUT]
    root = _write(tmp_path, [_read(cut + "x")], _events())  # 120 chars, no tests/ tail
    assert m.check(TID, ["tests/a.py"], root)["files"] == {"tests/a.py": "NOT-READ"}


def test_no_attributed_rows_means_unattributed_not_not_read_and_counts_window_candidates(tmp_path):
    tools = [
        _read(f"{ROOT}/tests/a/test_one.py", run_id=None, phase=None, agent=None, ts="2026-10-02T10:30:00Z"),  # in window
        _read(f"{ROOT}/tests/a/test_one.py", run_id=None, phase=None, agent=None, ts="2026-10-02T12:00:00Z"),  # after window
        _read(f"{ROOT}/tests/a/test_one.py", run_id=None, phase=None, agent=None, ts="2026-10-02T09:30:00Z"),  # before window
    ]
    root = _write(tmp_path, tools, _events())
    res = m.check(TID, ["tests/a/test_one.py"], root)
    assert res["files"] == {"tests/a/test_one.py": "UNATTRIBUTED"}
    assert res["unattributed_read_rows_in_window"] == 1
    text = m.render(res)
    assert "Not read' cannot be said" in text and "UNATTRIBUTED" in text


def test_shadow_reviewer_other_phases_other_tools_and_other_runs_are_ignored(tmp_path):
    tools = [
        _read(f"{ROOT}/tests/a/test_one.py", agent="architecture-reviewer-shadow"),
        _read(f"{ROOT}/tests/a/test_one.py", phase="Implement"),
        _read(f"{ROOT}/tests/a/test_one.py", tool="Bash"),
        _read(f"{ROOT}/tests/a/test_one.py", run_id="TCK-OTHER"),
    ]
    root = _write(tmp_path, tools, _events())
    res = m.check(TID, ["tests/a/test_one.py"], root)
    assert res["attributed_read_rows"] == 0 and res["files"]["tests/a/test_one.py"] == "UNATTRIBUTED"


def test_changed_test_files_keeps_only_tests_paths_and_uses_a_three_dot_diff():
    seen = {}

    def fake(cmd, **kw):
        seen["cmd"] = cmd
        return SimpleNamespace(returncode=0, stdout="tests/b.py\ntools/x.py\ntests/a.py\ndocs/y.md\n", stderr="")

    assert m.changed_test_files("origin/main", run=fake) == ["tests/a.py", "tests/b.py"]
    assert seen["cmd"][-1] == "origin/main...HEAD"
    assert "--diff-filter=d" in seen["cmd"]


def test_changed_test_files_raises_on_a_failed_diff():
    bad = lambda cmd, **kw: SimpleNamespace(returncode=128, stdout="", stderr="bad ref")
    try:
        m.changed_test_files("nope", run=bad)
    except RuntimeError as e:
        assert "bad ref" in str(e)
    else:
        raise AssertionError("expected RuntimeError")


def test_cli_is_report_only_and_prints_each_class(tmp_path):
    root = _write(tmp_path, [_read(f"{ROOT}/tests/a/test_one.py")], _events())
    out = subprocess.run(
        [sys.executable, str(_TOOLS / "arch_verify_read_check.py"), "--ticket-id", TID, "--data-root", str(root), "--base-ref", "HEAD", "--json"],
        capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent,
    )
    assert out.returncode == 0, out.stderr
    assert json.loads(out.stdout)["ticket_id"] == TID


def test_docstring_states_the_limits():
    doc = m.__doc__
    for needle in ("Bash row", "writeSidecar", "cut to 120", "UNATTRIBUTED", "NOT-READ", "shadow", "shared across concurrent sessions"):
        assert needle in doc, needle


def test_a_deleted_test_file_is_not_listed_but_an_added_and_a_renamed_one_are(tmp_path):
    """Real git: a deleted test file cannot be read, so it must not become a false NOT-READ."""
    def git(*a):
        subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True,
                       env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                            "GIT_COMMITTER_EMAIL": "t@t", "PATH": "/usr/bin:/bin"})
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "keep.py").write_text("keep\n" * 20)
    (tmp_path / "tests" / "gone.py").write_text("gone\n" * 20)
    (tmp_path / "tests" / "old_name.py").write_text("rename me\n" * 20)
    git("init", "-q", "-b", "main"); git("add", "-A"); git("commit", "-q", "-m", "base")
    git("checkout", "-q", "-b", "work")
    (tmp_path / "tests" / "gone.py").unlink()
    git("mv", "tests/old_name.py", "tests/new_name.py")
    (tmp_path / "tests" / "added.py").write_text("added\n")
    git("add", "-A"); git("commit", "-q", "-m", "change")
    out = m.changed_test_files("main", run=lambda cmd, **kw: subprocess.run(cmd, cwd=tmp_path, **kw))
    assert out == ["tests/added.py", "tests/new_name.py"]
