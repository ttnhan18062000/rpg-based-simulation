"""Tests for tools/agent-monitoring/migrate_monitoring_data.py
(TCK-20260903-MONITORING-DATA-MIGRATION).

Mirrors tests/tools/test_migrate_tools_shards.py's own structure: synthetic-fixture
unit tests, then integration tests against a copy of the real historical corpus (never
the real agent-monitoring/ directory directly), then architecture guards that only run
meaningfully once retirement (git rm + .gitattributes edit) has actually happened.
"""
import collections
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tools" / "agent-monitoring"))

import migrate_monitoring_data  # noqa: E402
from migrate_monitoring_data import (  # noqa: E402
    EVENTS_FIELD_PRIORITY,
    RUNS_FIELD_PRIORITY,
    UNKNOWN_WEEK_KEY,
    bucket_lines_by_week_multi_field,
    relocate_tools_shards,
    verify_migration,
    write_week_bucket,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_REAL_RUNS = _REPO_ROOT / "agent-monitoring" / "runs.jsonl"
_REAL_EVENTS = _REPO_ROOT / "agent-monitoring" / "events.jsonl"
_REAL_TOOLS_DIR = _REPO_ROOT / "agent-monitoring" / "tools"
_REAL_DATA_DIR = _REPO_ROOT / "agent-monitoring" / "data"


def _line(**fields) -> str:
    return json.dumps(fields, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Unit — bucketing (Steps 2/3)
# ---------------------------------------------------------------------------

def test_runs_bucket_by_start_ts_preserving_order():
    # All 4 timestamps fall in real ISO week 2026-W30 (2026-07-20 is a Monday); listed
    # out of chronological order on purpose to prove bucket order tracks file order.
    lines = [
        _line(run_id="a", start_ts="2026-07-20T10:00:00.000000Z"),
        _line(run_id="b", start_ts="2026-07-25T05:00:00.000000Z"),
        _line(run_id="c", start_ts="2026-07-22T23:59:59.000000Z"),
        _line(run_id="d", start_ts="2026-07-21T01:00:00.000000Z"),
    ]
    buckets = bucket_lines_by_week_multi_field(lines, RUNS_FIELD_PRIORITY)
    assert len(buckets) == 1
    (week_key, bucket_lines), = buckets.items()
    assert week_key == "2026-W30"
    assert bucket_lines == lines, "bucket order must match original file order, not start_ts order"


def test_events_bucket_by_ts_preserving_order():
    lines = [
        _line(run_id="a", ts="2026-07-20T10:00:00.000000Z"),
        _line(run_id="b", ts="2026-07-25T05:00:00.000000Z"),
        _line(run_id="c", ts="2026-07-22T23:59:59.000000Z"),
        _line(run_id="d", ts="2026-07-21T01:00:00.000000Z"),
    ]
    buckets = bucket_lines_by_week_multi_field(lines, EVENTS_FIELD_PRIORITY)
    assert len(buckets) == 1
    (week_key, bucket_lines), = buckets.items()
    assert week_key == "2026-W30"
    assert bucket_lines == lines, "bucket order must match original file order, not ts order"


def test_runs_and_events_fallback_field_priority_documented_and_correct():
    # runs half: missing start_ts, carries timestamp (TCK-20260618-AUDIT-D10-TESTS shape).
    runs_fallback_row = _line(
        run_id="TCK-20260618-AUDIT-D10-TESTS",
        timestamp="2026-06-18T00:00:00Z",
    )
    runs_buckets = bucket_lines_by_week_multi_field([runs_fallback_row], RUNS_FIELD_PRIORITY)
    assert list(runs_buckets.keys()) == ["2026-W25"]
    assert runs_buckets["2026-W25"] == [runs_fallback_row]

    # events half: explicit "ts": null routes to fallback field, not straight to unknown.
    events_fallback_row = _line(
        run_id="TCK-20260619-E53Ab-DECISION-PHASE",
        seq=10,
        ts=None,
        timestamp="2026-06-19T00:00:00Z",
    )
    events_buckets = bucket_lines_by_week_multi_field([events_fallback_row], EVENTS_FIELD_PRIORITY)
    assert list(events_buckets.keys()) == ["2026-W25"]
    assert events_buckets["2026-W25"] == [events_fallback_row]

    # events: "ts": null AND no other usable field -> unknown-week.
    events_null_no_fallback_row = _line(
        run_id="TCK-20260619-E53Ab-DECISION-PHASE", seq=10, ts=None,
    )
    buckets = bucket_lines_by_week_multi_field([events_null_no_fallback_row], EVENTS_FIELD_PRIORITY)
    assert list(buckets.keys()) == [UNKNOWN_WEEK_KEY]

    # events: pure event_type/details payload, no timestamp-like field at all.
    events_no_ts_field_row = _line(
        run_id="TCK-20260610-AUDIT-EVENT-SEQUENCE",
        event_type="implementation_complete",
        details={"foo": "bar"},
    )
    buckets = bucket_lines_by_week_multi_field([events_no_ts_field_row], EVENTS_FIELD_PRIORITY)
    assert list(buckets.keys()) == [UNKNOWN_WEEK_KEY]
    assert buckets[UNKNOWN_WEEK_KEY] == [events_no_ts_field_row]


# ---------------------------------------------------------------------------
# Unit — tools relocation, filename-only (Step 4)
# ---------------------------------------------------------------------------

def test_tools_shard_relocation_parses_week_from_filename_not_content(tmp_path, monkeypatch):
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()

    # Line's own ts deliberately disagrees with the shard filename's claimed week.
    disagreeing_line = _line(run_id="x", ts="2020-01-01T00:00:00Z")
    (tools_dir / "tools-2026-W24.jsonl").write_text(disagreeing_line + "\n")
    (tools_dir / "tools-unknown-week.jsonl").write_text(_line(run_id="y") + "\n")

    calls = {"bucket_multi_field": 0, "parse_ts": 0}
    monkeypatch.setattr(
        migrate_monitoring_data,
        "bucket_lines_by_week_multi_field",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not be called during relocation")),
    )

    buckets = relocate_tools_shards(tools_dir)

    assert buckets["2026-W24"] == [disagreeing_line]
    assert buckets["unknown-week"] == [_line(run_id="y")]
    assert buckets["unknown-week"] == buckets[UNKNOWN_WEEK_KEY]


# ---------------------------------------------------------------------------
# Unit/integration — per-week write logic, live merge, all 3 sources (Step 5)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("source", ["runs", "events", "tools"])
def test_case_b_merge_precedes_live_rows_for_all_three_sources(tmp_path, source):
    data_dir = tmp_path / "data"
    week_key = "2026-W99"
    target_path = data_dir / week_key / f"{source}.jsonl"
    target_path.parent.mkdir(parents=True)

    live_lines = [_line(seq=100, marker="live-a"), _line(seq=101, marker="live-b")]
    target_path.write_text("\n".join(live_lines) + "\n")

    historical_lines = [
        _line(seq=1, marker="hist-a"),
        _line(seq=2, marker="hist-b"),
        _line(seq=3, marker="hist-c"),
    ]

    ok, live_snapshot = write_week_bucket(week_key, historical_lines, source, data_dir)
    assert ok
    assert live_snapshot == live_lines

    final_lines = target_path.read_text().splitlines()
    assert final_lines == historical_lines + live_lines
    assert not target_path.with_name(target_path.name + ".pre-migration-backup").exists()


def test_migration_uses_one_write_lines_call_per_week_per_source(tmp_path, monkeypatch):
    calls = []

    def _spy_write_lines(target_path, lines):
        calls.append((target_path, list(lines)))
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "a") as f:
            for line in lines:
                f.write(line + "\n")
        return True

    monkeypatch.setattr(migrate_monitoring_data, "write_lines", _spy_write_lines)

    data_dir = tmp_path / "data"

    # One batch each for runs/2026-W36 and tools/2026-W36 in the same week — must be
    # two separate write_lines() calls to two separate target files, never combined.
    write_week_bucket("2026-W36", [_line(seq=1, marker="runs-a")], "runs", data_dir)
    write_week_bucket("2026-W36", [_line(seq=2, marker="tools-a")], "tools", data_dir)
    write_week_bucket("2026-W37", [_line(seq=3, marker="events-a")], "events", data_dir)

    assert len(calls) == 3, "write_lines() must be called exactly once per (week, source) pair"
    call_targets = {str(t) for t, _ in calls}
    assert str(data_dir / "2026-W36" / "runs.jsonl") in call_targets
    assert str(data_dir / "2026-W36" / "tools.jsonl") in call_targets
    assert str(data_dir / "2026-W37" / "events.jsonl") in call_targets


# ---------------------------------------------------------------------------
# Integration — full-corpus, against a copy of the real corpus
# ---------------------------------------------------------------------------

def _copy_real_corpus_into(tmp_path):
    """Copies whatever of the real runs.jsonl/events.jsonl/tools/ still exist (each
    source independently — post-retirement some or all may be gone, which is this
    ticket's own intended end state) plus any real agent-monitoring/data/*/ week
    folders, into tmp_path. Never touches the real agent-monitoring/ directory.

    Returns a dict of per-source availability so tests can skip a source's own checks
    once that source has already been retired, without failing the whole test.
    """
    repo_copy = tmp_path / "repo"
    (repo_copy / "agent-monitoring").mkdir(parents=True)
    data_dir = repo_copy / "agent-monitoring" / "data"

    available = {"runs": False, "events": False, "tools": False}

    if _REAL_RUNS.exists():
        (repo_copy / "agent-monitoring" / "runs.jsonl").write_text(_REAL_RUNS.read_text())
        available["runs"] = True
    if _REAL_EVENTS.exists():
        (repo_copy / "agent-monitoring" / "events.jsonl").write_text(_REAL_EVENTS.read_text())
        available["events"] = True
    if _REAL_TOOLS_DIR.is_dir():
        copy_tools_dir = repo_copy / "agent-monitoring" / "tools"
        copy_tools_dir.mkdir()
        for shard_path in sorted(_REAL_TOOLS_DIR.glob("tools-*.jsonl")):
            (copy_tools_dir / shard_path.name).write_text(shard_path.read_text())
        available["tools"] = True

    if _REAL_DATA_DIR.is_dir():
        for week_dir in sorted(_REAL_DATA_DIR.iterdir()):
            if not week_dir.is_dir():
                continue
            for source_file in week_dir.glob("*.jsonl"):
                dest = data_dir / week_dir.name / source_file.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(source_file.read_text())

    return repo_copy, data_dir, available


def _run_one_source(repo_copy, data_dir, source):
    if source == "tools":
        tools_dir = repo_copy / "agent-monitoring" / "tools"
        buckets = relocate_tools_shards(tools_dir)
        source_lines = []
        for week_key in sorted(buckets.keys()):
            source_lines.extend(buckets[week_key])
    else:
        source_path = repo_copy / "agent-monitoring" / f"{source}.jsonl"
        source_lines = source_path.read_text().splitlines()
        field_priority = RUNS_FIELD_PRIORITY if source == "runs" else EVENTS_FIELD_PRIORITY
        buckets = bucket_lines_by_week_multi_field(source_lines, field_priority)

    live_snapshots = {}
    for week_key in sorted(buckets.keys()):
        ok, live_snapshot = write_week_bucket(week_key, buckets[week_key], source, data_dir)
        assert ok
        if live_snapshot:
            live_snapshots[week_key] = live_snapshot

    report = verify_migration(source_lines, buckets, source, data_dir, live_snapshots)
    return source_lines, buckets, live_snapshots, report


def test_every_pre_cutover_line_lands_in_exactly_one_file_per_source_content_preserved(tmp_path):
    repo_copy, data_dir, available = _copy_real_corpus_into(tmp_path)
    if not any(available.values()):
        pytest.skip(
            "All 3 legacy sources have already been retired by this ticket's own migration "
            "run (intended end state, not a regression) -- nothing left to copy."
        )

    for source, is_available in available.items():
        if not is_available:
            continue
        source_lines, buckets, live_snapshots, report = _run_one_source(repo_copy, data_dir, source)
        assert report["verification_passed"], f"{source}: verification failed: {report}"

        original_counter = collections.Counter(source_lines)
        migrated_counter = collections.Counter()
        for week_key, expected_lines in buckets.items():
            target_path = data_dir / week_key / f"{source}.jsonl"
            all_lines = target_path.read_text().splitlines()
            live_snapshot = live_snapshots.get(week_key, [])
            migrated_only = (
                all_lines[: len(all_lines) - len(live_snapshot)] if live_snapshot else all_lines
            )
            migrated_counter.update(migrated_only)

        assert migrated_counter == original_counter, (
            f"{source}: every original line must land content-preserved in exactly one file, "
            "with no drop and no duplication (multiset equality)"
        )


def test_full_corpus_verification_reports_exact_counts_per_source(tmp_path):
    repo_copy, data_dir, available = _copy_real_corpus_into(tmp_path)
    if not any(available.values()):
        pytest.skip(
            "All 3 legacy sources have already been retired by this ticket's own migration "
            "run (intended end state, not a regression) -- nothing left to copy."
        )

    for source, is_available in available.items():
        if not is_available:
            continue
        source_lines, buckets, live_snapshots, report = _run_one_source(repo_copy, data_dir, source)

        assert report["original_total"] == len(source_lines)
        assert isinstance(report["migrated_total"], int)
        assert isinstance(report["explained_delta"], int)
        assert report["migrated_total"] == report["original_total"] + report["explained_delta"]
        assert report["reconciles_exactly"] is True
        assert report["content_preserved"] is True
        assert report["all_lines_parse"] is True
        if live_snapshots:
            assert report["explained_delta"] == sum(len(v) for v in live_snapshots.values())
            assert report["explained_delta"] > 0


def test_tools_relocation_is_route_only_not_re_bucketed(tmp_path):
    repo_copy, data_dir, available = _copy_real_corpus_into(tmp_path)
    if not available["tools"]:
        pytest.skip(
            "agent-monitoring/tools/ has already been retired by this ticket's own migration "
            "run -- nothing left to copy for this real-corpus integration test."
        )

    tools_dir = repo_copy / "agent-monitoring" / "tools"
    for shard_path in sorted(tools_dir.glob("tools-*.jsonl")):
        week_key = shard_path.stem[len("tools-"):]
        shard_lines = shard_path.read_text().splitlines()

        buckets = relocate_tools_shards(tools_dir)
        assert buckets[week_key] == shard_lines, (
            f"{shard_path.name}: every line must land in the shard's own filename-derived week "
            "regardless of that line's own ts content"
        )


# ---------------------------------------------------------------------------
# Architecture guards — run only after retirement (Steps 7/8)
# ---------------------------------------------------------------------------

def test_legacy_paths_removed_after_migration():
    assert not _REAL_RUNS.exists(), (
        "agent-monitoring/runs.jsonl must no longer exist in the working tree after this "
        "ticket's retirement step (git rm) -- full history recoverable via "
        "`git log --follow -- agent-monitoring/runs.jsonl`"
    )
    assert not _REAL_EVENTS.exists(), (
        "agent-monitoring/events.jsonl must no longer exist in the working tree after this "
        "ticket's retirement step (git rm) -- full history recoverable via "
        "`git log --follow -- agent-monitoring/events.jsonl`"
    )
    assert not _REAL_TOOLS_DIR.exists(), (
        "agent-monitoring/tools/ must no longer exist in the working tree after this ticket's "
        "retirement step (git rm -r) -- full history recoverable via "
        "`git log --follow -- agent-monitoring/tools/`"
    )


def test_gitattributes_no_longer_references_any_of_the_3_retired_paths():
    """Checks the unified glob via the shared _merge_union_glob_patterns() parser rather than an
    exact substring, since TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION added `text
    eol=lf` ahead of `merge=union` on this line, breaking a literal-suffix match."""
    from tests.integrity.test_no_duplicate_content_blocks import _merge_union_glob_patterns

    content = (_REPO_ROOT / ".gitattributes").read_text()
    assert "agent-monitoring/runs.jsonl merge=union" not in content
    assert "agent-monitoring/events.jsonl merge=union" not in content
    assert "agent-monitoring/tools/*.jsonl merge=union" not in content
    assert "agent-monitoring/data/*/*.jsonl" in _merge_union_glob_patterns()
