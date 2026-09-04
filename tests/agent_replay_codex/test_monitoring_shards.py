"""Direct unit coverage of tools/agent_replay_codex/monitoring_shards.py's own public API
(TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION).

Prior to this ticket, source_paths/read_source_bytes/hash_source (formerly the tools-only
tools_source_paths/read_tools_source_bytes/hash_tools_source) had no direct unit test — only
indirect coverage through each call site's own tests. This module closes that gap and exercises
the filesystem-based (not tree-snapshot-based — see test_tools_shard_resolution.py for those)
functions directly for all 3 monitoring sources, against both the real-repo per-week-folder shape
and the synthetic single-legacy-file scratch shape.
"""
from __future__ import annotations

import json

import pytest

from tools.agent_replay_codex.monitoring_shards import (
    hash_source,
    read_source_bytes,
    source_paths,
)

_SOURCES = ("runs.jsonl", "events.jsonl", "tools.jsonl")


@pytest.mark.parametrize("source", _SOURCES)
def test_source_paths_resolves_scratch_shape(tmp_path, source):
    monitoring_dir = tmp_path / "agent-monitoring"
    monitoring_dir.mkdir()
    single = monitoring_dir / source
    single.write_text('{"a": 1}\n', encoding="utf-8")

    assert source_paths(monitoring_dir, source) == [single]


@pytest.mark.parametrize("source", _SOURCES)
def test_source_paths_returns_empty_when_scratch_file_absent(tmp_path, source):
    monitoring_dir = tmp_path / "agent-monitoring"
    monitoring_dir.mkdir()

    assert source_paths(monitoring_dir, source) == []


@pytest.mark.parametrize("source", _SOURCES)
def test_source_paths_resolves_real_shape_sorted_including_unknown_week(tmp_path, source):
    monitoring_dir = tmp_path / "agent-monitoring"
    data_dir = monitoring_dir / "data"
    for week in ("2026-W02", "2026-W01", "unknown-week"):
        week_dir = data_dir / week
        week_dir.mkdir(parents=True)
        (week_dir / source).write_text(json.dumps({"week": week}) + "\n", encoding="utf-8")

    resolved = source_paths(monitoring_dir, source)

    assert resolved == [
        data_dir / "2026-W01" / source,
        data_dir / "2026-W02" / source,
        data_dir / "unknown-week" / source,
    ]


@pytest.mark.parametrize("source", _SOURCES)
def test_source_paths_prefers_real_shape_over_a_stray_scratch_file(tmp_path, source):
    monitoring_dir = tmp_path / "agent-monitoring"
    (monitoring_dir / source).parent.mkdir(parents=True, exist_ok=True)
    (monitoring_dir / source).write_text('{"legacy": true}\n', encoding="utf-8")
    week_dir = monitoring_dir / "data" / "2026-W01"
    week_dir.mkdir(parents=True)
    (week_dir / source).write_text('{"real": true}\n', encoding="utf-8")

    assert source_paths(monitoring_dir, source) == [week_dir / source]


def test_read_source_bytes_concatenates_in_sorted_path_order(tmp_path):
    monitoring_dir = tmp_path / "agent-monitoring"
    for week in ("2026-W02", "2026-W01", "unknown-week"):
        week_dir = monitoring_dir / "data" / week
        week_dir.mkdir(parents=True)
        (week_dir / "runs.jsonl").write_bytes(f'{{"week":"{week}"}}\n'.encode("utf-8"))

    result = read_source_bytes(monitoring_dir, "runs.jsonl")

    assert result == (
        b'{"week":"2026-W01"}\n' b'{"week":"2026-W02"}\n' b'{"week":"unknown-week"}\n'
    )


def test_hash_source_changes_with_any_source_file_and_is_stable_otherwise(tmp_path):
    monitoring_dir = tmp_path / "agent-monitoring"
    week_dir = monitoring_dir / "data" / "2026-W01"
    week_dir.mkdir(parents=True)
    (week_dir / "runs.jsonl").write_text('{"a": 1}\n', encoding="utf-8")

    unchanged = hash_source(monitoring_dir, "runs.jsonl")
    assert hash_source(monitoring_dir, "runs.jsonl") == unchanged

    (week_dir / "runs.jsonl").write_text('{"a": 2}\n', encoding="utf-8")
    assert hash_source(monitoring_dir, "runs.jsonl") != unchanged
