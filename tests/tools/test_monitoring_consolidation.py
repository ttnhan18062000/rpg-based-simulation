"""Tests for tools/agent-monitoring/monitoring_consolidation.py
(TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE).

One section per Acceptance Criterion, per staging_artifacts/TCK-20260924-MONITORING-SHARD-
SQUASH-MERGE-CONFLICT-AVOIDANCE/test_plan.md. AC1 uses a real throwaway git repo, since a
faked-output fixture cannot prove two disjoint file paths are genuinely conflict-free under a real
squash-merge -- the exact standard `test_delivery_pre_push_advisory.py`'s own Check C test set.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

_MONITORING_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

import monitoring_consolidation as mc  # noqa: E402
import writer  # noqa: E402


def _write_jsonl(path: Path, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def _read_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# AC1 — real throwaway git repo: two per-ticket files can never conflict, even under a
# simulated GitHub squash-merge.
# ---------------------------------------------------------------------------

def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo)] + list(args), capture_output=True, text=True, check=True)


def _init_repo(repo):
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "README.md").write_text("base\n")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-q", "-m", "init")
    _git(repo, "branch", "-M", "main")


def test_two_per_ticket_files_never_conflict_under_sequential_squash_merges(tmp_path):
    repo = tmp_path / "repo"
    _init_repo(repo)
    week_dir = repo / "agent-monitoring" / "data" / "2026-W01"
    week_dir.mkdir(parents=True)

    # Branch A adds its own per-ticket file.
    _git(repo, "checkout", "-q", "-b", "ticket-a")
    (week_dir / "TCK-A.tools.jsonl").write_text('{"run_id": "TCK-A"}\n')
    _git(repo, "add", "agent-monitoring")
    _git(repo, "commit", "-q", "-m", "TCK-A: add shard")

    # Squash-merge branch A into main (a new commit whose parent is main's own prior tip).
    _git(repo, "checkout", "-q", "main")
    _git(repo, "checkout", "-q", "ticket-a", "--", "agent-monitoring")
    _git(repo, "add", "agent-monitoring")
    _git(repo, "commit", "-q", "-m", "TCK-A: add shard (squashed) (#1)")

    # Branch B, diverged from the ORIGINAL base (before A's squash landed), adds a DIFFERENT
    # per-ticket file.
    _git(repo, "checkout", "-q", "-b", "ticket-b", "main~1")
    week_dir_b = repo / "agent-monitoring" / "data" / "2026-W01"
    week_dir_b.mkdir(parents=True)
    (week_dir_b / "TCK-B.tools.jsonl").write_text('{"run_id": "TCK-B"}\n')
    _git(repo, "add", "agent-monitoring")
    _git(repo, "commit", "-q", "-m", "TCK-B: add shard")

    # Squash-merge branch B onto the NEW main tip (post-A) -- this is exactly the sequential-
    # squash-merge shape that produces a real conflict for a SHARED file. Since A and B touch
    # disjoint file paths, `git merge` must succeed with zero conflicts.
    _git(repo, "checkout", "-q", "main")
    merge = subprocess.run(
        ["git", "-C", str(repo), "merge", "--no-ff", "-m", "merge ticket-b", "ticket-b"],
        capture_output=True, text=True,
    )
    assert merge.returncode == 0, f"expected a clean merge, got a conflict:\n{merge.stdout}\n{merge.stderr}"
    assert (week_dir / "TCK-A.tools.jsonl").exists()
    assert (week_dir / "TCK-B.tools.jsonl").exists()


# ---------------------------------------------------------------------------
# AC2 — round-trip equivalence
# ---------------------------------------------------------------------------

def test_consolidation_round_trip_matches_direct_append(tmp_path):
    week_dir = tmp_path / "2026-W01"
    week_dir.mkdir()
    row_a = {"run_id": "TCK-A", "seq": 1, "tool": "Bash"}
    row_b = {"run_id": "TCK-B", "seq": 1, "tool": "Read"}
    _write_jsonl(week_dir / "TCK-A.tools.jsonl", [row_a])
    _write_jsonl(week_dir / "TCK-B.tools.jsonl", [row_b])

    count = mc.consolidate_jsonl_kind(week_dir, "tools")
    assert count == 2

    consolidated = _read_jsonl(week_dir / "tools.jsonl")
    assert row_a in consolidated
    assert row_b in consolidated
    assert len(consolidated) == 2
    # Per-ticket files are deleted only after a successful fold.
    assert not (week_dir / "TCK-A.tools.jsonl").exists()
    assert not (week_dir / "TCK-B.tools.jsonl").exists()


def test_consolidation_folds_mixed_old_per_ticket_and_new_per_pr_shaped_files(tmp_path):
    # TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX: real historical per-ticket-shaped files
    # (written before this fix) will coexist with new per-PR/branch-shaped ones until the next
    # retro consolidation run -- confirms consolidate_jsonl_kind()'s glob is genuinely
    # identifier-shape-agnostic, not just tested against one shape.
    week_dir = tmp_path / "2026-W01"
    week_dir.mkdir()
    old_shape_row = {"run_id": "TCK-OLD-TICKET-SHAPED", "seq": 1, "tool": "Bash"}
    new_shape_row = {"run_id": "TCK-SOME-TICKET", "seq": 1, "tool": "Read"}
    _write_jsonl(week_dir / "TCK-OLD-TICKET-SHAPED.tools.jsonl", [old_shape_row])
    _write_jsonl(week_dir / "some-branch-name.tools.jsonl", [new_shape_row])

    count = mc.consolidate_jsonl_kind(week_dir, "tools")
    assert count == 2

    consolidated = _read_jsonl(week_dir / "tools.jsonl")
    assert old_shape_row in consolidated
    assert new_shape_row in consolidated
    assert len(consolidated) == 2
    assert not (week_dir / "TCK-OLD-TICKET-SHAPED.tools.jsonl").exists()
    assert not (week_dir / "some-branch-name.tools.jsonl").exists()


def test_consolidation_merges_with_pre_existing_canonical_content(tmp_path):
    week_dir = tmp_path / "2026-W01"
    week_dir.mkdir()
    existing = {"run_id": "TCK-OLD", "seq": 1, "tool": "Bash"}
    _write_jsonl(week_dir / "runs.jsonl", [existing])
    new_row = {"run_id": "TCK-NEW", "seq": 1, "tool": "Bash"}
    _write_jsonl(week_dir / "TCK-NEW.runs.jsonl", [new_row])

    mc.consolidate_jsonl_kind(week_dir, "runs")

    consolidated = _read_jsonl(week_dir / "runs.jsonl")
    assert existing in consolidated
    assert new_row in consolidated


# ---------------------------------------------------------------------------
# AC4 — idempotency
# ---------------------------------------------------------------------------

def test_consolidation_is_idempotent(tmp_path):
    week_dir = tmp_path / "2026-W01"
    week_dir.mkdir()
    _write_jsonl(week_dir / "TCK-A.events.jsonl", [{"run_id": "TCK-A", "seq": 1}])

    first_count = mc.consolidate_jsonl_kind(week_dir, "events")
    assert first_count == 1
    after_first = _read_jsonl(week_dir / "events.jsonl")

    second_count = mc.consolidate_jsonl_kind(week_dir, "events")
    assert second_count == 0
    after_second = _read_jsonl(week_dir / "events.jsonl")
    assert after_first == after_second


def test_consolidate_week_and_consolidate_all(tmp_path):
    data_dir = tmp_path / "data"
    week_dir = data_dir / "2026-W01"
    week_dir.mkdir(parents=True)
    _write_jsonl(week_dir / "TCK-A.runs.jsonl", [{"run_id": "TCK-A"}])
    _write_jsonl(week_dir / "TCK-A.events.jsonl", [{"run_id": "TCK-A", "seq": 1}])
    _write_jsonl(week_dir / "TCK-A.tools.jsonl", [{"run_id": "TCK-A", "seq": 1, "tool": "Bash"}])

    result = mc.consolidate_all(data_dir)
    assert result == {"2026-W01": {"runs": 1, "events": 1, "tools": 1}}
    assert (week_dir / "runs.jsonl").exists()
    assert (week_dir / "events.jsonl").exists()
    assert (week_dir / "tools.jsonl").exists()


# ---------------------------------------------------------------------------
# TCK-20260928-WORKING-LOG-CONSOLIDATION-CROSS-CHECKOUT-ROW-LOSS — foreign-cwd regression
# ---------------------------------------------------------------------------

_CSV_HEADER = "timestamp,ticket_id,title,status,summary,artifacts_path\n"


def test_consolidate_all_derives_csv_path_from_data_dir_not_foreign_cwd(tmp_path, monkeypatch):
    """Pre-fix, `consolidate_all()` passed no `csv_path` to `consolidate_pending_rows()`, which
    defaulted to a cwd-relative `tickets/working_log.csv` -- so a run with cwd pointed at a
    *different* checkout (the exact shape that lost 3 real rows off `origin/main`) wrote the
    pending row into that foreign checkout's CSV instead of the CSV next to `data_dir` (the
    checkout that actually owns the pending shard). Must fail on the pre-fix code: pre-fix, the
    row lands in `foreign_csv` and `owning_csv` is left with only its header."""
    owning = tmp_path / "owning-checkout"
    week_dir = owning / "agent-monitoring" / "data" / "2026-W01"
    week_dir.mkdir(parents=True)
    (owning / "tickets").mkdir(parents=True)
    owning_csv = owning / "tickets" / "working_log.csv"
    owning_csv.write_text(_CSV_HEADER, encoding="utf-8")
    _write_jsonl(week_dir / "TCK-A.working_log.jsonl", [{
        "timestamp": "2026-09-28T00:00:00Z", "ticket_id": "TCK-FOREIGN-CWD",
        "title": "t", "status": "DONE", "summary": "s", "artifacts_path": "none",
    }])

    foreign_cwd = tmp_path / "foreign-checkout"
    (foreign_cwd / "tickets").mkdir(parents=True)
    foreign_csv = foreign_cwd / "tickets" / "working_log.csv"
    foreign_csv.write_text(_CSV_HEADER, encoding="utf-8")
    monkeypatch.chdir(foreign_cwd)

    result = mc.consolidate_all(owning / "agent-monitoring" / "data")

    assert result["working_log"] == {"consolidated_rows": 1, "shard_files": 1}
    assert "TCK-FOREIGN-CWD" in owning_csv.read_text(encoding="utf-8")
    assert foreign_csv.read_text(encoding="utf-8") == _CSV_HEADER  # untouched


def test_consolidate_pending_rows_default_path_resolves_against_module_not_foreign_cwd(tmp_path, monkeypatch):
    """`working_log_writer.consolidate_pending_rows()`'s own defaults (`_WORKING_LOG_PATH`,
    `_DEFAULT_DATA_ROOT`) must resolve against the module's own checkout (`_REPO_ROOT`, anchored
    to `Path(__file__)`), not cwd, mirroring `monitoring_consolidation.DEFAULT_DATA_DIR`'s own
    anchoring. Must fail on the pre-fix code: pre-fix, `data_root`/`csv_path` were cwd-relative, so
    `data_root.exists()` (checked against the *foreign* cwd) is False and nothing is consolidated
    at all -- {"consolidated_rows": 0, "shard_files": 0}, not the 1/1 this test asserts."""
    from tools import working_log_writer as wlw

    owning = tmp_path / "owning-checkout"
    week_dir = owning / "agent-monitoring" / "data" / "2026-W01"
    week_dir.mkdir(parents=True)
    owning_csv = owning / "tickets" / "working_log.csv"
    owning_csv.parent.mkdir(parents=True)
    owning_csv.write_text(_CSV_HEADER, encoding="utf-8")
    _write_jsonl(week_dir / "TCK-B.working_log.jsonl", [{
        "timestamp": "2026-09-28T00:00:01Z", "ticket_id": "TCK-FOREIGN-CWD-2",
        "title": "t", "status": "DONE", "summary": "s", "artifacts_path": "none",
    }])

    foreign_cwd = tmp_path / "foreign-checkout"
    (foreign_cwd / "tickets").mkdir(parents=True)
    foreign_csv = foreign_cwd / "tickets" / "working_log.csv"
    foreign_csv.write_text(_CSV_HEADER, encoding="utf-8")

    monkeypatch.setattr(wlw, "_REPO_ROOT", owning)
    monkeypatch.chdir(foreign_cwd)

    result = wlw.consolidate_pending_rows()  # no args -- exercises the module's own defaults

    assert result == {"consolidated_rows": 1, "shard_files": 1}
    assert "TCK-FOREIGN-CWD-2" in owning_csv.read_text(encoding="utf-8")
    assert foreign_csv.read_text(encoding="utf-8") == _CSV_HEADER  # untouched


def test_consolidation_leaves_per_ticket_file_in_place_on_failed_canonical_write(tmp_path, monkeypatch):
    week_dir = tmp_path / "2026-W01"
    week_dir.mkdir()
    _write_jsonl(week_dir / "TCK-A.tools.jsonl", [{"run_id": "TCK-A"}])

    monkeypatch.setattr(mc, "write_lines", lambda *a, **kw: False)
    count = mc.consolidate_jsonl_kind(week_dir, "tools")

    assert count == 0
    assert (week_dir / "TCK-A.tools.jsonl").exists()  # not deleted -- safe to retry


# ---------------------------------------------------------------------------
# AC5 — done-checker / compute_tool_stats unaffected; writer.py untouched
# ---------------------------------------------------------------------------

def test_writer_py_source_unchanged():
    # This ticket's entire mechanism rests on writer.py already being path-agnostic -- a future
    # session must not "helpfully" hardcode a path back into it.
    source = Path(writer.__file__).read_text(encoding="utf-8")
    assert "def write_line(target_path: Path, line: str) -> bool:" in source
    assert "def write_lines(target_path: Path, lines: list[str]) -> bool:" in source


def test_working_log_writer_untouched_by_this_ticket():
    # Disclosed scope reduction (investigation.md): tickets/working_log.csv's write path is not
    # changed by this ticket. Confirm append_working_log_row's signature is exactly as before.
    from tools import working_log_writer
    source = Path(working_log_writer.__file__).read_text(encoding="utf-8")
    assert "def append_working_log_row(" in source
    assert "def write_pending_working_log_row(" not in source


def test_done_checker_static_suite_still_passes():
    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tests/tools/test_done_checker_static.py", "-q"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


# ---------------------------------------------------------------------------
# Regression-prone paths
# ---------------------------------------------------------------------------

def test_no_per_ticket_files_is_a_no_op(tmp_path):
    week_dir = tmp_path / "2026-W01"
    week_dir.mkdir()
    _write_jsonl(week_dir / "runs.jsonl", [{"run_id": "TCK-EXISTING"}])
    result = mc.consolidate_week(week_dir)
    assert result == {"runs": 0, "events": 0, "tools": 0}
    assert _read_jsonl(week_dir / "runs.jsonl") == [{"run_id": "TCK-EXISTING"}]


def test_consolidate_all_skips_weeks_with_nothing_to_do(tmp_path):
    data_dir = tmp_path / "data"
    (data_dir / "2026-W01").mkdir(parents=True)
    _write_jsonl(data_dir / "2026-W01" / "runs.jsonl", [{"run_id": "TCK-X"}])
    result = mc.consolidate_all(data_dir)
    assert result == {}


def test_missing_data_dir_returns_empty(tmp_path):
    assert mc.consolidate_all(tmp_path / "does-not-exist") == {}


def test_cli_exit_code_zero_and_reports_json(tmp_path, capsys, monkeypatch):
    week_dir = tmp_path / "2026-W01"
    week_dir.mkdir(parents=True)
    _write_jsonl(week_dir / "TCK-A.tools.jsonl", [{"run_id": "TCK-A"}])
    exit_code = mc.main(["--data-dir", str(tmp_path), "--json"])
    assert exit_code == 0
    out = json.loads(capsys.readouterr().out)
    assert out == {"2026-W01": {"runs": 0, "events": 0, "tools": 1}}
