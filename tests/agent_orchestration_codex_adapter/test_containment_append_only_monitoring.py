from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).parent.parent.parent
_MANIFEST_PATH = _REPO_ROOT / "tools" / "agent-monitoring" / "manifest.py"
_SPEC = importlib.util.spec_from_file_location("monitoring_manifest", _MANIFEST_PATH)
assert _SPEC and _SPEC.loader
_MANIFEST = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MANIFEST)


def _monitoring_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "agent-monitoring"
    directory.mkdir()
    for filename in ("runs.jsonl", "events.jsonl", "tools.jsonl"):
        (directory / filename).write_text("one\ntwo\n", encoding="utf-8")
    return directory


def test_assert_prefix_preserved_allows_appended_lines(tmp_path: Path):
    directory = _monitoring_dir(tmp_path)
    before = _MANIFEST.capture_lines(directory)
    (directory / "runs.jsonl").write_text("one\ntwo\nthree\n", encoding="utf-8")

    _MANIFEST.assert_prefix_preserved(before, _MANIFEST.capture_lines(directory))


def test_assert_prefix_preserved_rejects_rewritten_lines(tmp_path: Path):
    directory = _monitoring_dir(tmp_path)
    before = _MANIFEST.capture_lines(directory)
    (directory / "runs.jsonl").write_text("changed\ntwo\n", encoding="utf-8")

    with pytest.raises(AssertionError, match="rewritten/reordered/deleted"):
        _MANIFEST.assert_prefix_preserved(before, _MANIFEST.capture_lines(directory))


def test_assert_prefix_preserved_rejects_reordered_lines(tmp_path: Path):
    directory = _monitoring_dir(tmp_path)
    before = _MANIFEST.capture_lines(directory)
    (directory / "runs.jsonl").write_text("two\none\n", encoding="utf-8")

    with pytest.raises(AssertionError, match="rewritten/reordered/deleted"):
        _MANIFEST.assert_prefix_preserved(before, _MANIFEST.capture_lines(directory))


def test_capture_lines_reads_all_three_monitoring_files():
    captured = _MANIFEST.capture_lines(_REPO_ROOT / "agent-monitoring")

    assert set(captured) == {"runs.jsonl", "events.jsonl", "tools.jsonl"}
