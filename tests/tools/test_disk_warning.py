"""Mid-session low-disk line and the removable-worktrees section (TCK-20261014-DISK-HEADROOM-MIDSESSION-WARNING-AND-MERGED-WORKTREES)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REAL_ROOT = Path(__file__).resolve().parents[2]
if str(REAL_ROOT) not in sys.path:
    sys.path.insert(0, str(REAL_ROOT))

from tools.sessions import disk_headroom as dh  # noqa: E402
from tools.sessions import disk_warning as dw  # noqa: E402
from tools.sessions import prune_branches as pb  # noqa: E402

GB = dh.GB
ENV = {"SESSION_DISK_THRESHOLD_GB": "10"}


class Free:
    """A statvfs fake that counts its calls."""

    def __init__(self, gb):
        self.gb, self.calls = gb, 0

    def __call__(self):
        self.calls += 1
        return int(self.gb * GB)


def call(tmp_path, free, now, session="s1"):
    return dw.mid_session_line(session, tmp_path, now=now, free_fn=free, environ=ENV)


def test_no_warning_at_or_above_the_threshold(tmp_path):
    assert call(tmp_path, Free(10.0), 1000.0) is None
    assert call(tmp_path, Free(50), 5000.0) is None


def test_warning_below_the_threshold_names_free_space_and_both_commands(tmp_path):
    line = call(tmp_path, Free(6.5), 1000.0)
    assert "6.5 GB free" in line
    assert "disk_headroom.py" in line and "prune_branches --worktrees" in line


def test_second_statvfs_is_not_made_inside_the_check_window(tmp_path):
    free = Free(6)
    assert call(tmp_path, free, 1000.0)
    assert free.calls == 1
    assert call(tmp_path, free, 1000.0 + dw.CHECK_WINDOW_SECONDS - 1) is None
    assert free.calls == 1
    call(tmp_path, free, 1000.0 + dw.CHECK_WINDOW_SECONDS)
    assert free.calls == 2


def test_repeat_at_most_once_per_thirty_minutes_while_low(tmp_path):
    free = Free(6)
    assert call(tmp_path, free, 1000.0)
    assert call(tmp_path, free, 1000.0 + 700) is None
    assert call(tmp_path, free, 1000.0 + 1400) is None
    assert call(tmp_path, free, 1000.0 + dw.REPEAT_WINDOW_SECONDS + 700)


def test_dropping_below_two_gb_warns_at_once_even_inside_the_repeat_window(tmp_path):
    assert call(tmp_path, Free(6), 1000.0)
    line = call(tmp_path, Free(1.5), 1000.0 + dw.CHECK_WINDOW_SECONDS)
    assert line and "1.5 GB free" in line
    # but only once: still critical, inside the repeat window, no second line
    assert call(tmp_path, Free(1.0), 1000.0 + 2 * dw.CHECK_WINDOW_SECONDS) is None


def test_sessions_throttle_independently(tmp_path):
    free = Free(6)
    assert call(tmp_path, free, 1000.0, "a") and call(tmp_path, free, 1000.0, "b")
    assert call(tmp_path, free, 1100.0, "a") is None


def test_an_exception_from_statvfs_is_swallowed(tmp_path):
    def boom():
        raise OSError("statvfs failed")

    assert dw.mid_session_line("s", tmp_path, now=1.0, free_fn=boom, environ=ENV) is None


def test_unwritable_state_dir_still_warns_and_corrupt_state_is_ignored(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    assert dw.mid_session_line("s", blocker / "sub", now=1.0, free_fn=Free(3), environ=ENV)
    (tmp_path / (dw.STATE_PREFIX + "s")).write_text("not json")
    assert call(tmp_path, Free(3), 1.0, "s")


def test_stale_state_files_are_swept(tmp_path):
    old = tmp_path / (dw.STATE_PREFIX + "gone")
    old.write_text("{}")
    os.utime(old, (1.0, 1.0))
    call(tmp_path, Free(3), 1000.0 + dw.STALE_SECONDS + 10)
    assert not old.exists()


def test_session_id_cannot_escape_the_state_dir(tmp_path):
    call(tmp_path, Free(3), 1.0, "../../evil")
    assert [p.parent for p in tmp_path.rglob(dw.STATE_PREFIX + "*")] == [tmp_path]


def test_the_hook_prints_additional_context_and_still_writes_its_record(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    env = {**os.environ, "SESSION_DISK_THRESHOLD_GB": "100000"}  # any real disk is below this
    out = subprocess.run([sys.executable, str(REAL_ROOT / "tools/agent-monitoring/post_tool_hook.py")],
                         input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}, "session_id": "sess"}),
                         cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60)
    assert out.returncode == 0
    payload = json.loads(out.stdout)["hookSpecificOutput"]
    assert payload["hookEventName"] == "PostToolUse" and "disk-headroom" in payload["additionalContext"]
    assert list(tmp_path.rglob("*tools.jsonl")), "the monitoring record is still written"
    again = subprocess.run([sys.executable, str(REAL_ROOT / "tools/agent-monitoring/post_tool_hook.py")],
                           input=json.dumps({"tool_name": "Bash", "tool_input": {}, "session_id": "sess"}),
                           cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60)
    assert again.stdout.strip() == "", "throttled: no second line inside the window"


# ---- removable worktrees ---------------------------------------------------------------------------------------------

def _row(path, branch, removable, reason, size=0):
    return pb.WorktreeRow(path, branch, "sha", removable, reason, size)


def _report(*rows, gh_ok=True):
    return pb.WorktreeReport(tuple(rows), gh_ok=gh_ok)


def test_section_lists_merged_head_worktree_and_not_a_unique_commits_one(tmp_path):
    merged, unique = tmp_path / "merged", tmp_path / "unique"
    report = _report(_row(str(merged), "done", True, "tip equals the merged PR head", 3 * GB),
                     _row(str(unique), "wip", False, "unmerged: no merged PR with this tip"))
    r = dh.removable_worktrees(tmp_path, classify=lambda: report)
    assert [p for p, _, _ in r.removable] == [str(merged)]
    text = dh.render_removable(r)
    assert str(merged) in text and str(unique) not in text
    assert "3.0 GB" in text and "prune_branches --worktrees --execute --backup" in text


def test_detached_clean_worktree_is_listed_as_detached_check_and_dirty_one_is_not(tmp_path):
    clean, dirty = tmp_path / "clean", tmp_path / "dirty"
    clean.mkdir()
    dirty.mkdir()
    report = _report(_row(str(clean), "(detached)", False, pb.DETACHED_REASON),
                     _row(str(dirty), "(detached)", False, pb.DETACHED_REASON))
    r = dh.removable_worktrees(tmp_path, classify=lambda: report,
                               dirty=lambda p: ["f"] if p == dirty else [], size=lambda p: 2 * GB)
    assert [p for p, _ in r.detached] == [str(clean)]
    assert "detached, check" in dh.render_removable(r) and str(dirty) not in dh.render_removable(r)


def test_gh_unavailable_lists_nothing_as_removable(tmp_path):
    r = dh.removable_worktrees(tmp_path, classify=lambda: _report(_row("/x", "b", True, "r", GB), gh_ok=False))
    assert not r.gh_ok and r.removable == ()
    assert "gh unavailable" in dh.render_removable(r)


def test_a_failing_classifier_is_reported_not_raised(tmp_path):
    def boom():
        raise RuntimeError("no roster")

    r = dh.removable_worktrees(tmp_path, classify=boom)
    assert r.removable == () and "no roster" in r.error
    assert "unavailable" in dh.render_removable(r)


def test_json_report_carries_the_section(tmp_path):
    r = dh.RemovableWorktrees(True, (("/a", "b", 5),), (("/d", 7),))
    h = dh.Headroom(1, 2, ())
    data = json.loads(dh.to_json(h, r))
    assert data["removable_worktrees"]["removable_bytes"] == 5 and data["removable_worktrees"]["detached"][0]["path"] == "/d"
    assert "removable_worktrees" not in json.loads(dh.to_json(h))
