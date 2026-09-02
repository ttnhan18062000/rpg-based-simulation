"""Tests for tools/agent-monitoring/migrate_tools_shards.py
(TCK-20260902-MONITORING-SHARD-MIGRATION).

Unit tests use synthetic fixtures (deterministic, isolated). Integration tests that exercise
the full pipeline against the real historical corpus operate on a copy of it under tmp_path —
never against the real agent-monitoring/tools.jsonl or agent-monitoring/tools/ directly, so
running this test file never mutates the real repo or interferes with the one-time real
migration run performed separately for this ticket's Test Summary evidence.
"""
import collections
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tools" / "agent-monitoring"))

import migrate_tools_shards  # noqa: E402
from migrate_tools_shards import (  # noqa: E402
    UNKNOWN_WEEK_KEY,
    bucket_lines_by_week,
    verify_migration,
    write_week_bucket,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_REAL_SOURCE = _REPO_ROOT / "agent-monitoring" / "tools.jsonl"
_REAL_SHARD_DIR = _REPO_ROOT / "agent-monitoring" / "tools"


def _line(**fields) -> str:
    return json.dumps(fields, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Unit — bucketing (Step 1)
# ---------------------------------------------------------------------------

def test_within_week_bucket_preserves_original_append_order():
    # All 4 timestamps fall in real ISO week 2026-W30 (2026-07-20 is a Monday); listed
    # out of chronological order on purpose to prove bucket order tracks file order, not ts.
    lines = [
        _line(seq=1, ts="2026-07-20T10:00:00.000000Z"),
        _line(seq=2, ts="2026-07-25T05:00:00.000000Z"),
        _line(seq=3, ts="2026-07-22T23:59:59.000000Z"),
        _line(seq=4, ts="2026-07-21T01:00:00.000000Z"),
    ]
    buckets = bucket_lines_by_week(lines)
    assert len(buckets) == 1
    (week_key, bucket_lines), = buckets.items()
    assert bucket_lines == lines, "bucket order must match original file order, not ts order"


def test_malformed_and_off_schema_rows_route_without_erroring():
    run_summary_row = _line(
        run_id="TCK-20260628-SIMQ-E1-FOUNDATION",
        ts="2026-06-29T05:34:06Z",
        tools_used=["Bash"],
        files_written=20,
    )
    missing_tool_row = json.dumps(
        {
            "session_id": "abc",
            "run_id": "TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP",
            "seq": 4,
            "ts": "2026-07-16T12:06:04",
        },
        separators=(",", ":"),
    )
    buckets = bucket_lines_by_week([run_summary_row, missing_tool_row])
    all_lines = [line for bucket in buckets.values() for line in bucket]
    assert run_summary_row in all_lines
    assert missing_tool_row in all_lines
    assert "2026-W27" in buckets  # 2026-06-29 -> ISO week 27
    assert "2026-W29" in buckets  # 2026-07-16 -> ISO week 29


def test_missing_ts_row_routes_to_documented_fallback_bucket():
    ts_less_row = _line(tool="implement-epic", last_run="2026-06-28T04:10:00Z", result="DONE")
    buckets = bucket_lines_by_week([ts_less_row])
    assert list(buckets.keys()) == [UNKNOWN_WEEK_KEY]
    assert buckets[UNKNOWN_WEEK_KEY] == [ts_less_row]


def test_ts_format_variants_all_bucket_to_correct_week():
    standard_row = _line(seq=1, ts="2026-06-13T17:23:37.173746Z")
    bare_row = json.dumps(
        {"session_id": "x", "run_id": "y", "seq": 4, "ts": "2026-07-16T12:06:04"},
        separators=(",", ":"),
    )
    buckets = bucket_lines_by_week([standard_row, bare_row])
    assert set(buckets.keys()) == {"2026-W24", "2026-W29"}
    assert buckets["2026-W24"] == [standard_row]
    assert buckets["2026-W29"] == [bare_row]


# ---------------------------------------------------------------------------
# Unit/integration — per-week write logic, including live-shard merge (Step 2)
# ---------------------------------------------------------------------------

def test_current_week_shard_migrated_rows_precede_existing_live_rows(tmp_path):
    shard_dir = tmp_path / "tools"
    shard_dir.mkdir()
    week_key = "2026-W99"
    target_path = shard_dir / f"tools-{week_key}.jsonl"

    live_lines = [_line(seq=100, ts="2026-W99-live-a"), _line(seq=101, ts="2026-W99-live-b")]
    target_path.write_text("\n".join(live_lines) + "\n")

    historical_lines = [
        _line(seq=1, ts="2026-hist-a"),
        _line(seq=2, ts="2026-hist-b"),
        _line(seq=3, ts="2026-hist-c"),
    ]

    ok, live_snapshot = write_week_bucket(week_key, historical_lines, shard_dir)
    assert ok
    assert live_snapshot == live_lines

    final_lines = target_path.read_text().splitlines()
    assert final_lines == historical_lines + live_lines
    assert not target_path.with_name(target_path.name + ".pre-migration-backup").exists()


def test_write_week_bucket_case_a_direct_write_for_new_shard(tmp_path):
    shard_dir = tmp_path / "tools"
    week_key = "2026-W50"
    lines = [_line(seq=1, ts="a"), _line(seq=2, ts="b")]

    ok, live_snapshot = write_week_bucket(week_key, lines, shard_dir)
    assert ok
    assert live_snapshot == []
    target_path = shard_dir / f"tools-{week_key}.jsonl"
    assert target_path.read_text().splitlines() == lines


def test_migration_uses_write_lines_one_lock_per_week_batch(tmp_path, monkeypatch):
    calls = []

    def _spy_write_lines(target_path, lines):
        calls.append((target_path, list(lines)))
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "a") as f:
            for line in lines:
                f.write(line + "\n")
        return True

    monkeypatch.setattr(migrate_tools_shards, "write_lines", _spy_write_lines)

    shard_dir = tmp_path / "tools"
    shard_dir.mkdir()

    # Case B: pre-seed a live shard for one week.
    live_week_key = "2026-W60"
    live_target = shard_dir / f"tools-{live_week_key}.jsonl"
    live_lines = [_line(seq=9, ts="live")]
    live_target.write_text(live_lines[0] + "\n")

    buckets = {
        "2026-W59": [_line(seq=1, ts="a"), _line(seq=2, ts="b")],
        live_week_key: [_line(seq=3, ts="c")],
    }

    for week_key, lines in buckets.items():
        ok, _ = write_week_bucket(week_key, lines, shard_dir)
        assert ok

    assert len(calls) == 2, "write_lines() must be called exactly once per week bucket"
    call_targets = {str(target) for target, _ in calls}
    assert str(shard_dir / "tools-2026-W59.jsonl") in call_targets
    assert str(live_target) in call_targets

    live_call = [c for t, c in calls if str(t) == str(live_target)][0]
    assert live_call == buckets[live_week_key] + live_lines, (
        "the single write_lines() call for the live week must combine historical-then-live "
        "content, not two separate calls"
    )


# ---------------------------------------------------------------------------
# Integration — full-corpus verification (Step 3), against a copy of the real corpus
# ---------------------------------------------------------------------------

def _run_migration_against_copy(tmp_path):
    """Copies the real historical file (and, if present, the real currently-live shard) into
    tmp_path and runs the full bucket -> write -> verify pipeline there. Never touches the
    real agent-monitoring/ directory.

    Skips (does not fail) once agent-monitoring/tools.jsonl no longer exists: that absence is
    this ticket's own intended end state (TCK-20260902-MONITORING-SHARD-MIGRATION retires the
    file via `git rm` once its own real, one-time run's verification report — pasted into the
    ticket's Test Summary — already passed for real against the real corpus). These two tests
    exist to exercise the pipeline against real-world data shape while the source file was still
    present during implementation; after retirement there is no real corpus left to copy, so a
    real assertion failure here would misreport an expected, by-design condition as a
    regression. The synthetic-fixture unit tests above remain the durable regression guard for
    this script's own logic.
    """
    if not _REAL_SOURCE.exists():
        pytest.skip(
            "agent-monitoring/tools.jsonl has been retired by this ticket's own migration run "
            "(intended end state, not a regression) -- nothing left to copy for this real-corpus "
            "integration test."
        )
    source_lines = _REAL_SOURCE.read_text().splitlines()

    shard_dir = tmp_path / "tools"
    shard_dir.mkdir()

    buckets = bucket_lines_by_week(source_lines)

    # Simulate the real Case B condition by seeding whatever shard file(s) currently exist in
    # the real repo's live shard directory, found dynamically (never a hardcoded week string).
    if _REAL_SHARD_DIR.is_dir():
        for real_shard_path in sorted(_REAL_SHARD_DIR.glob("tools-*.jsonl")):
            week_key = real_shard_path.stem[len("tools-"):]
            if week_key in buckets:
                (shard_dir / real_shard_path.name).write_text(real_shard_path.read_text())

    live_snapshots = {}
    for week_key in sorted(buckets.keys()):
        ok, live_snapshot = write_week_bucket(week_key, buckets[week_key], shard_dir)
        assert ok
        if live_snapshot:
            live_snapshots[week_key] = live_snapshot

    report = verify_migration(source_lines, buckets, shard_dir, live_snapshots)
    return source_lines, buckets, shard_dir, live_snapshots, report


def test_every_pre_cutover_line_lands_in_exactly_one_shard_content_preserved(tmp_path):
    source_lines, buckets, shard_dir, live_snapshots, report = _run_migration_against_copy(tmp_path)

    assert report["verification_passed"]

    original_counter = collections.Counter(source_lines)
    migrated_counter = collections.Counter()
    for shard_path in shard_dir.glob("tools-*.jsonl"):
        week_key = shard_path.stem[len("tools-"):]
        all_lines = shard_path.read_text().splitlines()
        live_snapshot = live_snapshots.get(week_key, [])
        migrated_only = all_lines[: len(all_lines) - len(live_snapshot)] if live_snapshot else all_lines
        migrated_counter.update(migrated_only)

    assert migrated_counter == original_counter, (
        "every original line must land content-preserved in exactly one shard, with no drop "
        "and no duplication (multiset equality, preserving any genuine duplicate lines)"
    )


def test_full_corpus_verification_reports_exact_not_approximate_counts(tmp_path):
    source_lines, buckets, shard_dir, live_snapshots, report = _run_migration_against_copy(tmp_path)

    assert report["original_total"] == len(source_lines)
    assert isinstance(report["migrated_total"], int)
    assert isinstance(report["explained_delta"], int)
    assert report["migrated_total"] == report["original_total"] + report["explained_delta"]
    assert report["reconciles_exactly"] is True
    assert report["content_preserved"] is True
    assert report["all_lines_parse"] is True
    if live_snapshots:
        assert report["explained_delta"] == sum(len(v) for v in live_snapshots.values())
        assert report["explained_delta"] > 0, (
            "this real-corpus run is expected to have at least one live pre-existing shard "
            "(the in-progress current week) — a zero explained_delta here would mean this test "
            "silently stopped exercising the Case B merge path"
        )


# ---------------------------------------------------------------------------
# Architecture guards — real repo state (run these only after Step 5's retirement)
# ---------------------------------------------------------------------------

def test_tools_jsonl_removed_from_working_tree_after_migration():
    assert not _REAL_SOURCE.exists(), (
        "agent-monitoring/tools.jsonl must no longer exist in the working tree after this "
        "ticket's retirement step (git rm) — its full history remains recoverable via "
        "`git log --follow -- agent-monitoring/tools.jsonl`"
    )


def test_gitattributes_no_longer_references_retired_tools_jsonl_path():
    content = (_REPO_ROOT / ".gitattributes").read_text()
    assert "agent-monitoring/tools.jsonl merge=union" not in content
    assert "agent-monitoring/tools/*.jsonl merge=union" in content
