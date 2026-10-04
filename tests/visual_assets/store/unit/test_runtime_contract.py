"""`RuntimeManifest`: the small shipped contract. It rejects what it must and carries nothing from the protected provenance."""

from __future__ import annotations

import json

import pytest

from tests.visual_assets.store.unit.conftest import FIXTURES
from visual_assets.store import config
from visual_assets.store.contracts import RuntimeManifest, canonical_json, parse_record
from visual_assets.store.errors import ContractError

GOOD = json.loads((FIXTURES / "runtime_manifest.json").read_text())
HEX_A, HEX_B = "a" * 64, "b" * 64


def entry(key: str, digest: str = HEX_A, **over) -> dict:
    return {"visual_key": key, "family": "sample", "pixel_hash": f"pixels-v1:{digest}", "file": f"{digest}.png", "width": 16, "height": 16, **over}


def code_of(data: dict) -> str:
    with pytest.raises(ContractError) as err:
        parse_record(RuntimeManifest, json.dumps(data).encode())
    return err.value.code


def with_entries(*entries: dict) -> dict:
    return {**GOOD, "entries": list(entries)}


def test_the_fixture_round_trips_to_canonical_bytes():
    raw = (FIXTURES / "runtime_manifest.json").read_bytes()
    assert canonical_json(parse_record(RuntimeManifest, raw)) == raw


def test_the_allowed_field_names_are_exactly_these_and_none_comes_from_provenance():
    assert set(RuntimeManifest.model_fields) == {
        "record_type", "schema_version", "catalog_id", "release_id", "candidate_manifest_hash", "registry_hash",
        "fallback_contract_version", "entries", "details",
    }
    assert set(RuntimeManifest.model_fields["entries"].annotation.__args__[0].model_fields) == {"visual_key", "family", "pixel_hash", "file", "width", "height", "detail"}


def test_unknown_fields_are_rejected_at_both_levels():
    assert code_of({**GOOD, "approver": "x"}) == "unknown_field"
    assert code_of(with_entries(entry("fixture.sample.a", source_path="/x"))) == "unknown_field"


@pytest.mark.parametrize("file", ["../" + HEX_A + ".png", "/" + HEX_A + ".png", HEX_A + ".PNG", HEX_A, "x" * 64 + ".png", HEX_A + ".png/"])
def test_a_file_that_is_not_exactly_a_hex_digest_png_is_rejected(file):
    assert code_of(with_entries(entry("fixture.sample.a", file=file))) == "invalid_record"


def test_a_file_that_is_not_derived_from_the_pixel_hash_is_rejected():
    assert code_of(with_entries(entry("fixture.sample.a", file=f"{HEX_B}.png"))) == "invalid_record"


def test_duplicate_or_unsorted_keys_are_rejected():
    assert code_of(with_entries(entry("fixture.sample.a"), entry("fixture.sample.a", HEX_B))) == "invalid_record"
    assert code_of(with_entries(entry("fixture.sample.b"), entry("fixture.sample.a", HEX_B))) == "invalid_record"


def test_oversize_dimensions_are_rejected():
    assert code_of(with_entries(entry("fixture.sample.a", width=config.MAX_DIM + 1))) == "invalid_record"
    assert code_of(with_entries(entry("fixture.sample.a", height=0))) == "invalid_record"


def test_an_unsupported_version_is_rejected():
    assert code_of({**GOOD, "schema_version": 2}) == "unsupported_schema_version"
    assert code_of({**GOOD, "fallback_contract_version": 2}) == "invalid_record"


def test_more_than_max_visual_keys_entries_are_rejected(monkeypatch):
    monkeypatch.setattr(config, "MAX_VISUAL_KEYS", 1)
    assert code_of(with_entries(entry("fixture.sample.a"), entry("fixture.sample.b", HEX_B))) == "invalid_record"
