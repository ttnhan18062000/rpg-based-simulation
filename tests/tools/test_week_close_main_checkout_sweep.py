"""TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH: a week close run from a worktree pulls the main checkout's
`main.tools.jsonl` rows for the closed week into the canonical `tools.jsonl`. Read-only on the main checkout; full-row dedup;
only the week being closed. All fixtures live in tmp_path."""
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

from tools.agent_working_paths import AGENT_MONITORING

_TOOLS = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
sys.path.insert(0, str(_TOOLS))

import week_close as wc  # noqa: E402

WEEK, OTHER_WEEK = "2026-W39", "2026-W38"
AFTER = date(2026, 9, 28)


def _row(sid="s1", ts="2026-09-22T10:00:00Z", tool="Bash", **extra):
    return {"session_id": sid, "run_id": None, "ts": ts, "tool": tool, "input_summary": "x", **extra}


def _write(path, rows, compact=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    dump = (lambda r: json.dumps(r, separators=(",", ":"))) if compact else (lambda r: json.dumps(r, sort_keys=True))
    path.write_text("".join(dump(r) + "\n" for r in rows), encoding="utf-8")


def _setup(tmp_path):
    wt = tmp_path / "wt"
    main = tmp_path / "main"
    data = wt / AGENT_MONITORING / "data"
    (data / WEEK).mkdir(parents=True)
    return data, main / AGENT_MONITORING / "data"


def _lines(p):
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()]


def _close(data, main_root):
    return wc.close_week(WEEK, data, AFTER, main_checkout=main_root)


def test_rows_are_appended_once_in_ts_order_and_the_main_checkout_file_is_untouched(tmp_path):
    data, main_data = _setup(tmp_path)
    _write(data / WEEK / "tools.jsonl", [_row(ts="2026-09-22T09:00:00Z")])
    src = main_data / WEEK / "main.tools.jsonl"
    _write(src, [_row(ts="2026-09-23T10:00:00Z", tool="Edit"), _row(ts="2026-09-22T11:00:00Z", tool="Read")])
    before = (src.read_bytes(), src.stat().st_mtime_ns)

    result = _close(data, tmp_path / "main")

    assert result["main_checkout_tools"]["swept"] == 2
    assert [r["tool"] for r in _lines(data / WEEK / "tools.jsonl")] == ["Bash", "Read", "Edit"]
    assert (src.read_bytes(), src.stat().st_mtime_ns) == before  # never truncated, rewritten or touched


def test_second_close_adds_nothing(tmp_path):
    data, main_data = _setup(tmp_path)
    _write(main_data / WEEK / "main.tools.jsonl", [_row()])
    _close(data, tmp_path / "main")
    first = (data / WEEK / "tools.jsonl").read_bytes()
    again = _close(data, tmp_path / "main")
    assert again["main_checkout_tools"]["swept"] == 0 and again["main_checkout_tools"]["duplicates_dropped"] == 1
    assert (data / WEEK / "tools.jsonl").read_bytes() == first


def test_overlap_with_the_canonical_file_and_with_a_branch_shard_counts_once(tmp_path):
    data, main_data = _setup(tmp_path)
    shared = _row(ts="2026-09-22T12:00:00Z", tool="Grep")
    _write(data / WEEK / "tools.jsonl", [_row(ts="2026-09-22T09:00:00Z")], compact=False)
    _write(data / WEEK / "b1.tools.jsonl", [shared])  # a branch shard holding the same row, folded first
    _write(main_data / WEEK / "main.tools.jsonl", [_row(ts="2026-09-22T09:00:00Z"), shared, _row(ts="2026-09-22T13:00:00Z")])

    result = _close(data, tmp_path / "main")

    assert result["main_checkout_tools"]["swept"] == 1 and result["main_checkout_tools"]["duplicates_dropped"] == 2
    assert len(_lines(data / WEEK / "tools.jsonl")) == 3


def test_two_calls_sharing_a_timestamp_are_both_kept(tmp_path):
    data, main_data = _setup(tmp_path)
    _write(main_data / WEEK / "main.tools.jsonl", [_row(tool="Bash"), _row(tool="Read")])
    assert _close(data, tmp_path / "main")["main_checkout_tools"]["swept"] == 2


def test_only_the_week_being_closed_is_swept_and_a_branch_keyed_shard_is_ignored(tmp_path):
    data, main_data = _setup(tmp_path)
    _write(main_data / OTHER_WEEK / "main.tools.jsonl", [_row(ts="2026-09-15T10:00:00Z")])
    _write(main_data / WEEK / "some-branch.tools.jsonl", [_row()])
    result = _close(data, tmp_path / "main")
    assert result["main_checkout_tools"]["swept"] == 0
    assert not (data / WEEK / "tools.jsonl").exists()


def test_torn_and_blank_lines_are_skipped(tmp_path):
    data, main_data = _setup(tmp_path)
    src = main_data / WEEK / "main.tools.jsonl"
    src.parent.mkdir(parents=True)
    src.write_text(json.dumps(_row()) + "\n\n{\"session_id\": \"torn\n", encoding="utf-8")
    assert _close(data, tmp_path / "main")["main_checkout_tools"]["swept"] == 1


def test_no_main_checkout_or_no_file_is_a_skip_with_a_reason_not_an_error(tmp_path):
    data, main_data = _setup(tmp_path)
    r = wc.sweep_main_checkout_tools(WEEK, data / WEEK, None)
    assert r["swept"] == 0 and "no separate main checkout" in r["skipped"]
    r = wc.sweep_main_checkout_tools(WEEK, data / WEEK, tmp_path / "main")
    assert r["swept"] == 0 and "no main.tools.jsonl" in r["skipped"]


def test_cli_prints_one_line_with_the_swept_count(tmp_path, capsys, monkeypatch):
    data, main_data = _setup(tmp_path)
    _write(main_data / WEEK / "main.tools.jsonl", [_row()])
    monkeypatch.setattr(wc, "find_main_checkout", lambda d: tmp_path / "main")
    assert wc.main(["--week", WEEK, "--data-dir", str(data), "--today", AFTER.isoformat()]) == 0
    assert f"{WEEK} main-checkout tools rows: swept 1" in capsys.readouterr().out


def test_find_main_checkout_through_the_git_common_dir(tmp_path):
    main = tmp_path / "repo"
    main.mkdir()
    git = lambda *a, cwd=main: subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True)  # noqa: E731
    git("init", "-q", "-b", "main")
    git("-c", "user.email=a@b", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "i")
    wt = tmp_path / "wt1"
    git("worktree", "add", "-q", "-b", "side", str(wt))
    (wt / "data").mkdir()
    (main / "data").mkdir()
    assert wc.find_main_checkout(wt / "data") == main.resolve()
    assert wc.find_main_checkout(main / "data") is None  # the main checkout itself: its shard is folded as a normal shard
    assert wc.find_main_checkout(tmp_path / "outside" / "data") is None
