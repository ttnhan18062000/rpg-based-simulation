"""
Tests for tools/generate_artifact_pages.py
"""

import importlib.util
import sys
import time
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Load the module under test by path (no package install required)
# ---------------------------------------------------------------------------

_SCRIPT = Path(__file__).parent.parent.parent / "tools" / "generate_artifact_pages.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_artifact_pages", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gap = _load_module()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_dir(base: Path, name: str, files: list[str]) -> Path:
    d = base / name
    d.mkdir(parents=True, exist_ok=True)
    for f in files:
        (d / f).write_text(f"# {f}\n")
    return d


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_index_generated_for_dir_with_all_three_files(tmp_path, monkeypatch):
    """A directory with all three artifact files gets an index.md."""
    monkeypatch.setattr(gap, "STORED_ARTIFACTS", tmp_path)
    _make_dir(tmp_path, "TCK-TEST-001", ["investigation.md", "plan.md", "test_plan.md"])

    result = gap.run(dry_run=False)

    assert result == 0
    index = tmp_path / "TCK-TEST-001" / "index.md"
    assert index.exists()
    content = index.read_text()
    assert "TCK-TEST-001" in content
    assert "investigation.md" in content
    assert "plan.md" in content
    assert "test_plan.md" in content


def test_index_generated_for_dir_with_only_investigation(tmp_path, monkeypatch):
    """A directory with only investigation.md still gets an index.md."""
    monkeypatch.setattr(gap, "STORED_ARTIFACTS", tmp_path)
    _make_dir(tmp_path, "TCK-TEST-002", ["investigation.md"])

    gap.run(dry_run=False)

    index = tmp_path / "TCK-TEST-002" / "index.md"
    assert index.exists()
    content = index.read_text()
    assert "investigation.md" in content
    # plan.md and test_plan.md should NOT appear
    assert "plan.md" not in content
    assert "test_plan.md" not in content


def test_empty_dir_is_skipped(tmp_path, monkeypatch):
    """A directory with none of the three artifact files produces no index.md."""
    monkeypatch.setattr(gap, "STORED_ARTIFACTS", tmp_path)
    d = tmp_path / "TCK-TEST-003"
    d.mkdir()
    (d / "notes.txt").write_text("unrelated")

    gap.run(dry_run=False)

    assert not (d / "index.md").exists()


def test_idempotency(tmp_path, monkeypatch):
    """Running twice with unchanged sources produces identical output."""
    monkeypatch.setattr(gap, "STORED_ARTIFACTS", tmp_path)
    _make_dir(tmp_path, "TCK-TEST-004", ["plan.md", "test_plan.md"])

    gap.run(dry_run=False)
    index = tmp_path / "TCK-TEST-004" / "index.md"
    content_first = index.read_text()
    mtime_first = index.stat().st_mtime

    # Second run should skip (index is newer than source files)
    gap.run(dry_run=False)
    content_second = index.read_text()
    mtime_second = index.stat().st_mtime

    assert content_first == content_second
    assert mtime_first == mtime_second  # file not touched on second run


def test_frontmatter_in_generated_page(tmp_path, monkeypatch):
    """Generated index.md contains required frontmatter fields."""
    monkeypatch.setattr(gap, "STORED_ARTIFACTS", tmp_path)
    _make_dir(tmp_path, "TCK-TEST-005", ["investigation.md", "plan.md"])

    gap.run(dry_run=False)

    content = (tmp_path / "TCK-TEST-005" / "index.md").read_text()
    assert 'title: "TCK-TEST-005"' in content
    assert "artifact_type: index" in content
    assert "layer: misc" in content
    assert "tags: []" in content


def test_dry_run_does_not_write(tmp_path, monkeypatch):
    """--dry-run mode prints intent but does not create any files."""
    monkeypatch.setattr(gap, "STORED_ARTIFACTS", tmp_path)
    _make_dir(tmp_path, "TCK-TEST-006", ["investigation.md"])

    gap.run(dry_run=True)

    assert not (tmp_path / "TCK-TEST-006" / "index.md").exists()


def test_regenerates_when_source_newer_than_index(tmp_path, monkeypatch):
    """index.md is regenerated when a source artifact is newer than it."""
    monkeypatch.setattr(gap, "STORED_ARTIFACTS", tmp_path)
    d = _make_dir(tmp_path, "TCK-TEST-007", ["plan.md"])
    index = d / "index.md"

    # Write an old index
    index.write_text("stale content")
    old_mtime = time.time() - 10
    import os
    os.utime(index, (old_mtime, old_mtime))

    # Make plan.md newer
    plan = d / "plan.md"
    os.utime(plan, None)  # set to now

    gap.run(dry_run=False)

    new_content = index.read_text()
    assert "stale content" not in new_content
    assert "TCK-TEST-007" in new_content
