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
    "AdoptionRecord": "adoption_record.json",
    "RevocationRecord": "revocation_record.json",
    "SourceRecord": "source_record.json",
    "ArtifactRecord": "artifact_record.json",
    "ReleaseCandidateManifest": "release_candidate_manifest.json",
    "VisualKeyRegistry": "visual_key_registry.json",
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
