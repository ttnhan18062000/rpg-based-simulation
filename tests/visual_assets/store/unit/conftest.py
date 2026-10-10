"""Shared helpers: committed synthetic fixtures (`visual_assets/catalog/fixtures/contracts/`)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from visual_assets.store.contracts import RECORD_TYPES

FIXTURES = Path(__file__).resolve().parents[4] / "visual_assets" / "catalog" / "fixtures" / "contracts"

RECORD_FILES = {
    "CandidateHandoffPackage": "candidate_handoff_package.json",
    "IntakeResult": "intake_result.json",
    "ReviewRenderCheck": "review_render_check.json",
    "AdoptionRecord": "adoption_record.json",
    "RevocationRecord": "revocation_record.json",
    "SourceRecord": "source_record.json",
    "ArtifactRecord": "artifact_record.json",
    "ReleaseCandidateManifest": "release_candidate_manifest.json",
    "VisualKeyRegistry": "visual_key_registry.json",
    "RuntimeManifest": "runtime_manifest.json",
    "DraftSet": "draft_set.json",
    "SetAdoptionRecord": "set_adoption_record.json",
    "DraftPreviewManifest": "draft_preview_manifest.json",
}


def fixture_bytes(cls) -> bytes:
    return (FIXTURES / RECORD_FILES[cls.__name__]).read_bytes()


def fixture_dict(cls) -> dict:
    return json.loads(fixture_bytes(cls))


def dump(data: dict) -> bytes:
    return json.dumps(data).encode()


@pytest.fixture(params=RECORD_TYPES, ids=lambda c: c.__name__)
def record_cls(request):
    return request.param


@pytest.fixture
def roots(tmp_path, monkeypatch):
    """Patch the store's writable roots into tmp_path (`config.NAME` is read at call time)."""
    from visual_assets.store import config

    quarantine, review = tmp_path / "quarantine", tmp_path / "review"
    monkeypatch.setattr(config, "QUARANTINE_ROOT", quarantine)
    monkeypatch.setattr(config, "REVIEW_ROOT", review)
    return quarantine, review


def snapshot(root) -> dict[str, tuple]:
    """Relative path -> (kind, size, sha256) for everything under `root` (symlinks not followed)."""
    import hashlib
    import os
    import stat as st
    from pathlib import Path

    out: dict[str, tuple] = {}
    root = Path(root)
    if not root.exists():
        return out
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for name in dirnames + filenames:
            if name == ".store.lock" or name.startswith(".deletions"):
                continue  # ADR D24: the advisory lock file and the local gc deletion log are gitignored local files, not tracked store state
            path = Path(dirpath) / name
            mode = path.lstat().st_mode
            rel = str(path.relative_to(root))
            if st.S_ISREG(mode):
                out[rel] = ("file", path.lstat().st_size, hashlib.sha256(path.read_bytes()).hexdigest())
            elif st.S_ISLNK(mode):
                out[rel] = ("link", os.readlink(path))
            else:
                out[rel] = ("dir" if st.S_ISDIR(mode) else "special",)
    return out


@pytest.fixture
def env(tmp_path, monkeypatch):
    """An isolated catalog root plus quarantine and review roots; `config.NAME` is read at call time everywhere."""
    from types import SimpleNamespace

    from visual_assets.store import config

    catalog = tmp_path / "catalog"
    catalog.mkdir()
    quarantine, review = tmp_path / "quarantine", tmp_path / "review"
    monkeypatch.setattr(config, "CATALOG_ROOT", catalog)
    monkeypatch.setattr(config, "QUARANTINE_ROOT", quarantine)
    monkeypatch.setattr(config, "REVIEW_ROOT", review)
    return SimpleNamespace(catalog=catalog, quarantine=quarantine, review=review, tmp=tmp_path)
