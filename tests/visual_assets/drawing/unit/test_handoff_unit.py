"""Handoff pieces that need no Aseprite (run in CI): verified revision reads and atomic publishing."""

from __future__ import annotations

import hashlib

import pytest

from visual_assets.drawing import api, config, handoff
from visual_assets.drawing.errors import AdapterError
from visual_assets.drawing.workspace import revisions


def fake_revision(name: str = "s", data: bytes = b"sprite-bytes") -> bytes:
    directory = config.WORKSPACE / "sprites" / name
    directory.mkdir(parents=True)
    (directory / "r0001.aseprite").write_bytes(data)
    (directory / "r0001.sha256").write_text(hashlib.sha256(data).hexdigest() + "\n")
    return data


def test_read_revision_returns_the_exact_verified_bytes():
    data = fake_revision()
    rev, got, digest = api.read_revision("s", "r0001")
    assert (rev, got, digest) == ("r0001", data, hashlib.sha256(data).hexdigest())


@pytest.mark.parametrize("revision,match", [(None, "revision is required"), ("latest", "revision must look like"),
                                            ("r0002", "no such revision")])
def test_read_revision_needs_an_explicit_existing_revision(revision, match):
    fake_revision()
    with pytest.raises(AdapterError, match=match):
        api.read_revision("s", revision)


def test_read_revision_rejects_a_bad_name_and_a_tampered_file():
    fake_revision()
    with pytest.raises(AdapterError, match="name must match"):
        api.read_revision("../evil", "r0001")
    (config.WORKSPACE / "sprites" / "s" / "r0001.aseprite").write_bytes(b"tampered")
    with pytest.raises(AdapterError, match="content-hash check"):
        api.read_revision("s", "r0001")


def test_read_revision_rechecks_the_bytes_it_actually_read(monkeypatch):
    """The file can change between the hash check and the read; the returned bytes must still match the digest."""
    fake_revision()
    real = revisions.resolve_revision

    def stale(name, revision):
        rev, path, _ = real(name, revision)
        return rev, path, hashlib.sha256(b"something else").hexdigest()  # as if the file were swapped after hashing

    monkeypatch.setattr(api.revisions, "resolve_revision", stale)
    with pytest.raises(AdapterError, match="changed while being read"):
        api.read_revision("s", "r0001")


def test_publish_leaves_no_temporary_directory_when_it_fails(tmp_path, monkeypatch):
    target = tmp_path / "handoffs" / "cand-0123456789abcdef"

    def boom(src, dst):
        raise OSError("cross-device")

    monkeypatch.setattr(handoff.os, "rename", boom)
    with pytest.raises(OSError):
        handoff._publish(target, {"package.json": b"{}", "source.aseprite": b"s", "preview.png": b"p"})
    assert list((tmp_path / "handoffs").iterdir()) == []


def test_publish_creates_the_directory_only_when_complete(tmp_path, monkeypatch):
    target = tmp_path / "handoffs" / "cand-0123456789abcdef"
    seen = []
    real = handoff.os.rename

    def spy(src, dst):
        seen.append((dst == target, sorted(p.name for p in src.iterdir())))
        real(src, dst)

    monkeypatch.setattr(handoff.os, "rename", spy)
    handoff._publish(target, {"package.json": b"{}", "source.aseprite": b"s", "preview.png": b"p"})
    assert seen == [(True, ["package.json", "preview.png", "source.aseprite"])]
    assert sorted(p.name for p in target.iterdir()) == ["package.json", "preview.png", "source.aseprite"]


# --------------------------------------------------------------------------- handoff_directory: found ONLY by its exact id


GOOD_ID = "cand-0123456789abcdef--0123456789ab"


def test_a_handoff_is_found_only_by_its_exact_id():
    directory = config.WORKSPACE / "handoffs" / GOOD_ID
    directory.mkdir(parents=True)
    assert handoff.handoff_directory(GOOD_ID) == directory


@pytest.mark.parametrize("bad", [
    "", " ", "..", "../x", "/etc/passwd", "cand-0123456789abcdef", "cand-0123456789abcdef--", GOOD_ID + "/..", GOOD_ID + "/", GOOD_ID + "\n",
    "x/" + GOOD_ID, "handoffs/" + GOOD_ID, GOOD_ID.upper(), GOOD_ID[:-1], GOOD_ID + "0", "cand-0123456789abcdeg--0123456789ab", None, 5, ["a"], b"x",
])
def test_anything_but_the_exact_shape_is_refused_before_touching_the_disk(bad):
    (config.WORKSPACE / "handoffs" / GOOD_ID).mkdir(parents=True)
    with pytest.raises(AdapterError, match="handoff id looks like"):
        handoff.handoff_directory(bad)


def test_an_unknown_or_symlinked_or_file_handoff_is_refused(tmp_path):
    (config.WORKSPACE / "handoffs").mkdir(parents=True)
    with pytest.raises(AdapterError, match="no such handoff"):
        handoff.handoff_directory(GOOD_ID)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (config.WORKSPACE / "handoffs" / GOOD_ID).symlink_to(elsewhere, target_is_directory=True)
    with pytest.raises(AdapterError, match="no such handoff"):
        handoff.handoff_directory(GOOD_ID)
    (config.WORKSPACE / "handoffs" / GOOD_ID).unlink()
    (config.WORKSPACE / "handoffs" / GOOD_ID).write_text("a file, not a directory")
    with pytest.raises(AdapterError, match="no such handoff"):
        handoff.handoff_directory(GOOD_ID)


def test_the_id_pattern_matches_what_build_handoff_returns():
    import re

    assert re.fullmatch(handoff.HANDOFF_ID, "cand-" + "a" * 16 + "--" + "b" * 12)
    assert not re.fullmatch(handoff.HANDOFF_ID, "cand-" + "a" * 16)
