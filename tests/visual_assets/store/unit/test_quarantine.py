"""Refusals happen before any byte is copied and leave no quarantine directory (symlink, extras, size, FIFO, links)."""

from __future__ import annotations

import os

import pytest

from tests.visual_assets.store import builders as b
from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.store import config
from visual_assets.store.errors import StageError
from visual_assets.store.intake import quarantine
from visual_assets.store.intake.service import intake

NOW = "2026-01-01T00:00:00Z"


@pytest.fixture
def package_dir(tmp_path):
    package, source, preview = b.good_files()
    return b.write_dir(tmp_path / "pkg", package, source, preview)


def refused(package_dir, code, roots, **kw):
    quarantine_root, review_root = roots
    before = snapshot(package_dir)
    with pytest.raises(StageError) as err:
        intake(package_dir, created_at=NOW)
    assert err.value.code == code, err.value
    assert not quarantine_root.exists() or list(quarantine_root.iterdir()) == [], "a quarantine directory was left behind"
    assert not review_root.exists()
    assert snapshot(package_dir) == before  # the producer's directory is never modified either


def test_a_clean_package_reads_back_exactly(package_dir):
    files = quarantine.read_directory(package_dir)
    assert files.package == (package_dir / "package.json").read_bytes()
    assert files.source == (package_dir / "source.aseprite").read_bytes()
    assert files.preview == (package_dir / "preview.png").read_bytes()


@pytest.mark.parametrize("name", quarantine.STAGED_NAMES)
def test_a_symlinked_file_is_refused(package_dir, roots, tmp_path, name):
    target = tmp_path / "elsewhere"
    target.write_bytes((package_dir / name).read_bytes())
    (package_dir / name).unlink()
    (package_dir / name).symlink_to(target)
    refused(package_dir, "symlink", roots)


def test_a_symlinked_package_directory_is_refused(package_dir, roots, tmp_path):
    link = tmp_path / "linked"
    link.symlink_to(package_dir, target_is_directory=True)
    quarantine_root, _ = roots
    with pytest.raises(StageError) as err:
        intake(link, created_at=NOW)
    assert err.value.code == "symlink"
    assert not quarantine_root.exists()


def test_a_symlinked_entry_pointing_at_a_directory_is_refused(package_dir, roots, tmp_path):
    (package_dir / "preview.png").unlink()
    (package_dir / "preview.png").symlink_to(tmp_path, target_is_directory=True)
    refused(package_dir, "symlink", roots)


def test_an_extra_file_is_refused(package_dir, roots):
    (package_dir / "notes.txt").write_text("hello")
    refused(package_dir, "extra_entry", roots)


def test_a_hidden_extra_file_is_refused(package_dir, roots):
    (package_dir / ".hidden").write_text("x")
    refused(package_dir, "extra_entry", roots)


def test_a_sub_directory_is_refused(package_dir, roots):
    (package_dir / "nested").mkdir()
    refused(package_dir, "sub_directory", roots)


@pytest.mark.parametrize("name,bound", [("package.json", "MAX_RECORD_BYTES"), ("source.aseprite", "MAX_SOURCE_BYTES"),
                                        ("preview.png", "MAX_PREVIEW_BYTES")])
def test_an_oversize_file_is_refused(package_dir, roots, monkeypatch, name, bound):
    size = (package_dir / name).stat().st_size
    monkeypatch.setattr(config, bound, size - 1)
    refused(package_dir, "oversize_file", roots)
    monkeypatch.setattr(config, bound, size)  # exactly at the bound is fine
    assert quarantine.read_directory(package_dir)


def test_a_fifo_is_refused_without_blocking(package_dir, roots):
    (package_dir / "preview.png").unlink()
    os.mkfifo(package_dir / "preview.png")
    refused(package_dir, "not_regular_file", roots)


def test_a_hard_linked_file_is_refused(package_dir, roots, tmp_path):
    os.link(package_dir / "source.aseprite", tmp_path / "second-name")
    refused(package_dir, "hard_link", roots)


@pytest.mark.parametrize("name", quarantine.STAGED_NAMES)
def test_a_missing_file_is_refused(package_dir, roots, name):
    (package_dir / name).unlink()
    refused(package_dir, "missing_file", roots)


def test_a_missing_or_non_directory_package_path_is_refused(tmp_path, roots):
    with pytest.raises(StageError) as err:
        intake(tmp_path / "nope", created_at=NOW)
    assert err.value.code == "not_found"
    plain = tmp_path / "plain"
    plain.write_text("x")
    with pytest.raises(StageError) as err:
        intake(plain, created_at=NOW)
    assert err.value.code == "not_a_directory"


def test_paths_inside_package_content_are_never_followed(package_dir, roots, tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("TOP SECRET")
    package, source, preview = b.good_files()
    hostile = b.package_bytes(source, preview, creator="../../secret.txt")
    (package_dir / "package.json").write_bytes(hostile)
    result = intake(package_dir, created_at=NOW)
    assert result.verdict.value == "PASSED"  # it is only text; nothing was opened because of it
    staged = roots[0] / result.intake_id
    assert sorted(p.name for p in staged.iterdir()) == ["intake_result.json", "package.json", "preview.png", "source.aseprite"]
    assert b"TOP SECRET" not in b"".join(p.read_bytes() for p in staged.iterdir())


def test_the_quarantine_root_must_not_be_a_symlink(package_dir, tmp_path, monkeypatch):
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    monkeypatch.setattr(config, "QUARANTINE_ROOT", link)
    monkeypatch.setattr(config, "REVIEW_ROOT", tmp_path / "review")
    with pytest.raises(StageError) as err:
        intake(package_dir, created_at=NOW)
    assert err.value.code == "root_symlink"
    assert list(real.iterdir()) == []


def test_staged_files_are_private_and_never_overwritten(package_dir, roots):
    result = intake(package_dir, created_at=NOW)
    staged = roots[0] / result.intake_id
    assert (staged.stat().st_mode & 0o777) == 0o700
    for path in staged.iterdir():
        assert (path.stat().st_mode & 0o777) == 0o600
    with pytest.raises(FileExistsError):
        quarantine.write_new(staged / "package.json", b"replacement")
    with pytest.raises(StageError) as err:  # publishing over an existing intake directory is refused, never replaced
        quarantine.stage_atomically(result.intake_id, {"package.json": b"replacement"})
    assert err.value.code == "exists"
    assert (staged / "package.json").read_bytes() == (package_dir / "package.json").read_bytes()
    assert [p.name for p in roots[0].iterdir()] == [result.intake_id]  # and no temporary directory is left


def test_a_special_file_is_never_even_opened(package_dir, roots, monkeypatch):
    """The lstat guard exists so a FIFO or device is not opened at all (the later fstat check is only a second line)."""
    (package_dir / "preview.png").unlink()
    os.mkfifo(package_dir / "preview.png")
    opened: list[str] = []
    real_open = os.open

    def spy(path, *args, **kwargs):
        opened.append(os.fspath(path))
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(quarantine.os, "open", spy)
    with pytest.raises(StageError) as err:
        quarantine.read_directory(package_dir)
    assert err.value.code == "not_regular_file"
    assert "preview.png" not in opened, opened
