"""The invariant behind the size bounds: every record a writer can produce under the contract bounds is readable by every reader.

For each record type this builds the maximum legal instance (every list full, longest strings, 4-byte UTF-8 characters), serializes
it with the writer (`canonical_json`), writes it to a file, reads it back with the per-type bound (`record_bound`) and parses it with
the real read path. Also: the worst legal PNG is readable at every PNG read site, and `MAX_DECODED_BYTES` is used only for decoded size.
No Aseprite needed.
"""

from __future__ import annotations

import ast
import json
import os
import struct
import zlib
from pathlib import Path

import pytest
import yaml

from tests.visual_assets.store.builders import png_chunk
from tests.visual_assets.store.unit.conftest import FIXTURES, RECORD_FILES
from visual_assets.store import config, pixels, records
from visual_assets.store.catalog.registry import load_registry
from visual_assets.store.contracts import RECORD_TYPES, DraftPreviewManifest, ReleaseCandidateManifest, RuntimeManifest, VisualKeyRegistry, canonical_json, parse_record, record_bound
from visual_assets.store.contracts.definitions import MAX_DETAIL_VALUES
from visual_assets.store.contracts.handoff import MAX_LIMITATIONS
from visual_assets.store.contracts.intake import MAX_FINDINGS, IntakeFindingCode

FOUR_BYTE = "\U0001d4b3"  # 4 bytes in UTF-8 and accepted as plain text
STORE = Path(__file__).resolve().parents[4] / "visual_assets" / "store"


def _fixture(cls) -> dict:
    return json.loads((FIXTURES / RECORD_FILES[cls.__name__]).read_text())


def _valid(cls, data: dict) -> bool:
    try:
        cls.model_validate_json(json.dumps(data))
    except ValueError:
        return False
    return True


def _widen(cls, data: dict, node=None, path=()) -> None:
    """Replace every free-text leaf with the longest filler the contract still accepts (4-byte characters first, then ASCII)."""
    node = data if node is None else node
    items = node.items() if isinstance(node, dict) else enumerate(node)
    for key, value in list(items):
        if isinstance(value, (dict, list)):
            _widen(cls, data, value, (*path, key))
        elif isinstance(value, str):
            for filler in (FOUR_BYTE, "x"):
                for width in (256, 128, 96, 64, 32):
                    node[key] = filler * width
                    if _valid(cls, data):
                        break
                else:
                    continue
                break
            else:
                node[key] = value


def _maximal_intake_result(cls) -> dict:
    data = _fixture(cls)
    data["verdict"], data["staged_files"] = "QUARANTINED", data["staged_files"][:1]
    code = max((c.value for c in IntakeFindingCode), key=len)
    data["findings"] = [{"code": code, "detail": FOUR_BYTE * 256} for _ in range(MAX_FINDINGS)]
    _widen(cls, data)
    return data


def _maximal_package(cls) -> dict:
    data = _fixture(cls)
    data["declared_limitations"] = [FOUR_BYTE * 256] * MAX_LIMITATIONS
    _widen(cls, data)
    return data


def _wide_key(i: int) -> str:
    return f"a{i:05d}" + "x" * 26 + ".b" + "y" * 31 + ".c" + "z" * 29


def _wide_slots() -> list[tuple[str, str]]:
    """MAX_VISUAL_KEYS slots, every one carrying a maximum-length detail value: MAX_DETAIL_KEYS keys x MAX_DETAIL_VALUES values.

    That is the widest legal slot set: a slot without a detail value is narrower, and a key needs no more than MAX_DETAIL_VALUES values to
    have its entries distinguished, so fewer keys would not fit MAX_VISUAL_KEYS slots.
    """
    assert config.MAX_DETAIL_KEYS * MAX_DETAIL_VALUES == config.MAX_VISUAL_KEYS
    return [(_wide_key(k), f"{v:02d}" + "d" * 30) for k in range(config.MAX_DETAIL_KEYS) for v in range(MAX_DETAIL_VALUES)]


def _maximal_manifest(cls) -> dict:
    data = _fixture(cls)
    data["entries"] = [
        {"visual_key": key, "detail": detail, "artifact_id": "x" * 62 + f"{i % 100:02d}", "pixel_hash": "pixels-v1:" + f"{i:064x}"}
        for i, (key, detail) in enumerate(_wide_slots())
    ]
    return data


def _maximal_runtime(cls) -> dict:
    """MAX_VISUAL_KEYS slots of maximum-length keys, families and detail values, 128 px images, plus the full `details` block: the widest legal runtime manifest."""
    data = _fixture(cls)
    slots = _wide_slots()
    data["entries"] = [
        {"visual_key": key, "family": "f" * 32, "pixel_hash": "pixels-v1:" + f"{i:064x}", "file": f"{i:064x}.png",
         "width": config.MAX_DIM, "height": config.MAX_DIM, "detail": detail}
        for i, (key, detail) in enumerate(slots)
    ]
    data["details"] = [
        {"visual_key": _wide_key(k), "values": [d for key, d in slots if key == _wide_key(k)], "default": f"00{'d' * 30}"}
        for k in range(config.MAX_DETAIL_KEYS)
    ]
    return data


def _maximal_draft_set(cls) -> dict:
    """MAX_DRAFT_SET_ENTRIES entries of maximum-length keys, detail values and source asset ids (the widest legal DraftSet)."""
    data = _fixture(cls)
    data["set_id"] = "s" * 64
    data["entries"] = [
        {"visual_key": _wide_key(i), "detail": f"{i % 100:02d}" + "d" * 30, "source_asset_id": "s" * 60 + f"{i:04d}", "draft_id": f"in-{i:016x}",
         "pixel_hash": "pixels-v1:" + f"{i:064x}", "intake_hash": "sha256:" + f"{i + 1:064x}"}
        for i in range(config.MAX_DRAFT_SET_ENTRIES)
    ]
    return data


def _maximal_set_adoption(cls) -> dict:
    """MAX_DRAFT_SET_ENTRIES entries and the longest 4-byte text in every free field: the widest legal SetAdoptionRecord."""
    data = _fixture(cls)
    data["set_id"] = "s" * 64
    data["review_evidence_ref"], data["approver_name"], data["approver_role"] = FOUR_BYTE * 256, FOUR_BYTE * 128, FOUR_BYTE * 128
    data["entries"] = [
        {"visual_key": _wide_key(i), "detail": f"{i % 100:02d}" + "d" * 30, "adoption_id": f"ad-{i:016x}", "intake_id": f"in-{i:016x}"}
        for i in range(config.MAX_DRAFT_SET_ENTRIES)
    ]
    return data


def _maximal_draft_preview(cls) -> dict:
    """MAX_DRAFT_SET_ENTRIES entries (MAX_DETAIL_KEYS keys x 4 detail values, each maximum-length, at the largest preview size) plus the full `details` block."""
    data = _fixture(cls)
    data["set_id"] = "s" * 64
    per_key = config.MAX_DRAFT_SET_ENTRIES // config.MAX_DETAIL_KEYS
    values = [f"{v:02d}" + "d" * 30 for v in range(per_key)]
    slots = [(_wide_key(k), v) for k in range(config.MAX_DETAIL_KEYS) for v in values]
    data["entries"] = [
        {"visual_key": key, "family": "f" * 32, "detail": value, "source_asset_id": "s" * 60 + f"{i:04d}", "draft_id": f"in-{i:016x}",
         "pixel_hash": "pixels-v1:" + f"{i:064x}", "file": f"{i:064x}.png", "width": config.MAX_PREVIEW_DIM, "height": config.MAX_PREVIEW_DIM, "scale": 16}
        for i, (key, value) in enumerate(slots)
    ]
    data["details"] = [{"visual_key": _wide_key(k), "values": values, "default": values[0]} for k in range(config.MAX_DETAIL_KEYS)]
    return data


def _maximal_registry(cls) -> dict:
    """MAX_VISUAL_KEYS keys of the realistic shape (2 axes x 4 values) and MAX_ALIASES aliases: the count bound is for this shape;
    wider keys are bounded by MAX_REGISTRY_BYTES first (the registry is a hand-edited file), see docs/assets/budgets.md."""
    data = _fixture(cls)
    data["keys"] = [
        {"key": f"ui.family{i % 40}.entry{i}", "family": f"family{i % 40}", "description": "A realistic one-line description of what this visual key is for",
         "variant_axes": [{"name": f"axis{a}", "values": [f"value{v}" for v in range(4)]} for a in range(2)], "optional": False}
        for i in range(config.MAX_VISUAL_KEYS)
    ]
    for definition in data["keys"][: config.MAX_DETAIL_KEYS]:
        definition["detail"] = {"values": [f"{'d' * 30}{v:02d}" for v in range(MAX_DETAIL_VALUES)], "default": f"{'d' * 30}00"}
    data["aliases"] = [{"alias": f"ui.old{i}.entry{i}", "target": f"ui.family{i % 40}.entry{i}"} for i in range(config.MAX_ALIASES)]
    return data


MAXIMAL = {"IntakeResult": _maximal_intake_result, "CandidateHandoffPackage": _maximal_package, "ReleaseCandidateManifest": _maximal_manifest, "RuntimeManifest": _maximal_runtime, "VisualKeyRegistry": _maximal_registry,
           "DraftSet": _maximal_draft_set, "SetAdoptionRecord": _maximal_set_adoption, "DraftPreviewManifest": _maximal_draft_preview}


def maximal_instance(cls):
    data = MAXIMAL[cls.__name__](cls) if cls.__name__ in MAXIMAL else (lambda d: (_widen(cls, d), d)[1])(_fixture(cls))
    return parse_record_unbounded(cls, data)


def parse_record_unbounded(cls, data: dict):
    return cls.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("cls", RECORD_TYPES, ids=lambda c: c.__name__)
def test_the_maximum_legal_record_is_written_and_read_back(cls, tmp_path):
    record = maximal_instance(cls)
    data = canonical_json(record)  # the writer's own bound
    assert len(data) <= record_bound(cls)
    path = tmp_path / "record.json"
    path.write_bytes(data)
    assert parse_record(cls, records.read_file(path, record_bound(cls))) == record


def test_every_record_type_has_a_bound_and_the_big_ones_have_their_own():
    assert record_bound(ReleaseCandidateManifest) == record_bound(RuntimeManifest) == record_bound(DraftPreviewManifest) == config.MAX_MANIFEST_BYTES
    assert record_bound(VisualKeyRegistry) == config.MAX_REGISTRY_BYTES
    assert all(record_bound(cls) == config.MAX_RECORD_BYTES for cls in RECORD_TYPES if cls not in (ReleaseCandidateManifest, RuntimeManifest, DraftPreviewManifest, VisualKeyRegistry))


def test_the_maximal_registry_loads_through_the_real_read_path(tmp_path):
    """The model allows variant axes (the bound tests above use them) but the loader refuses them (D17, AM1-W03.1), so the real read path is measured with the realistic registry a loader accepts:
    no axes, and every key with a class, a structured fallback and (for icons) a label (`AM1-W02.7`)."""
    data = _maximal_registry(VisualKeyRegistry)
    data.pop("record_type"), data.pop("schema_version")
    for definition in data["keys"]:
        definition["variant_axes"] = []
        definition.update({"safety_class": "identifying", "fallback": {"kind": "glyph_and_text", "glyph": "Lucide Hammer icon (#f59e0b)", "text": "the building name as text"}})
    path = tmp_path / "visual_keys.yaml"
    path.write_text(yaml.safe_dump({"record_type": "visual_key_registry", "schema_version": 1, **data}))
    assert path.stat().st_size <= config.MAX_REGISTRY_BYTES
    registry = load_registry(path, allow_fixture_namespace=True)
    assert len(registry._keys) == config.MAX_VISUAL_KEYS and len(registry._aliases) == config.MAX_ALIASES


def _worst_png(level: int) -> bytes:
    dim = config.MAX_PREVIEW_DIM
    samples = os.urandom(dim * dim * 4)
    raw = b"".join(b"\x00" + samples[y * dim * 4 : (y + 1) * dim * 4] for y in range(dim))
    ihdr = struct.pack(">IIBBBBB", dim, dim, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr) + png_chunk(b"IDAT", zlib.compress(raw, level)) + png_chunk(b"IEND", b"")


@pytest.mark.parametrize("level", [0, 9])
def test_the_worst_legal_png_is_readable_and_decodable(level, tmp_path):
    png = _worst_png(level)  # a 1024 px RGBA square of random noise: it barely compresses, so the file is about the decoded size
    assert len(png) <= config.MAX_PNG_FILE_BYTES
    path = tmp_path / "worst.png"
    path.write_bytes(png)
    assert records.read_file(path, config.MAX_PNG_FILE_BYTES) == png
    assert pixels.decode_png(png, max_dim=config.MAX_PREVIEW_DIM).width == config.MAX_PREVIEW_DIM


def _attribute_uses(attr: str) -> dict[str, int]:
    uses = {}
    for path in sorted(STORE.rglob("*.py")):
        if path.name == "config.py":
            continue
        count = sum(1 for node in ast.walk(ast.parse(path.read_text())) if isinstance(node, ast.Attribute) and node.attr == attr)
        if count:
            uses[str(path.relative_to(STORE))] = count
    return uses


def test_the_decoded_size_bound_is_used_only_for_decoded_size():
    assert set(_attribute_uses("MAX_DECODED_BYTES")) == {"pixels.py"}


def test_every_png_file_read_site_uses_the_file_size_bound():
    assert set(_attribute_uses("MAX_PNG_FILE_BYTES")) == {"adoption.py", "build/exporter.py", "intake/service.py", "release.py", "runtime_export.py", "verify.py", "draftexport.py"}
