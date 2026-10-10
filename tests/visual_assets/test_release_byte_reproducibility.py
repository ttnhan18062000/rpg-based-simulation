"""Release bytes are reproducible (TCK-20261010-VISUAL-ASSETS-RELEASE-BYTE-REPRODUCIBILITY).

Artifact identity is the pixel hash and `png_hash` is informational, so nothing else compares file bytes. Two checks close that:

* LOCAL (`needs_aseprite`, ADR D10): rebuild every artifact of the current release candidate from its stored source in a temporary copy of the store and compare
  the PNG bytes and the pixel hash with the committed artifact. Verdict per entry: `IDENTICAL`; `BYTES_DIFFER_PIXELS_MATCH` (Aseprite version drift: the identity holds, the bytes
  moved; reported with the Aseprite version in a warning, never failed silently and never hidden); `PIXELS_DIFFER_OR_MISSING` (the rebuilt file named by the committed pixel hash does not exist) or `STORED_MISSING` (fail).
* CI: `export-runtime` of the committed candidate twice gives byte-identical directories, and no exported PNG carries a chunk outside the allowlist (no tIME, tEXt, iTXt, zTXt).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import warnings
from pathlib import Path

import pytest

from visual_assets.store import config, pixels, runtime_export
from visual_assets.store.build import exporter
from visual_assets.store.contracts import ReleaseCandidateManifest, parse_record

REAL_CATALOG = config.CATALOG_ROOT
CATALOG_ID, RELEASE_ID = "pilot", "rc-0008"  # the current release candidate (70 entries); a newer one moves this pin
# the chunks an exported PNG may carry: no timestamp, no text, no profile that would make two exports differ
CHUNK_ALLOWLIST = {b"IHDR", b"PLTE", b"tRNS", b"sRGB", b"gAMA", b"IDAT", b"IEND"}
STORE_PARTS = ("sources", "provenance", "definitions", "build-config", "STORE_FORMAT")


def chunk_types(png: bytes) -> list[bytes]:
    return [kind for kind, _ in pixels._chunks(png)]


def disallowed_chunks(png: bytes) -> list[bytes]:
    return [kind for kind in chunk_types(png) if kind not in CHUNK_ALLOWLIST]


def candidate() -> ReleaseCandidateManifest:
    return parse_record(ReleaseCandidateManifest, (REAL_CATALOG / "manifests" / "candidates" / CATALOG_ID / f"{RELEASE_ID}.json").read_bytes())


def tree_hash(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        digest.update(str(path.relative_to(directory)).encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


# ---- CI: export twice, chunk allowlist ----

@pytest.fixture(scope="module")
def exports(tmp_path_factory):
    base = tmp_path_factory.mktemp("export-twice")
    first, second = base / "one", base / "two"
    runtime_export.export_runtime(CATALOG_ID, RELEASE_ID, first)
    runtime_export.export_runtime(CATALOG_ID, RELEASE_ID, second)
    return first, second


def test_two_exports_of_the_committed_candidate_are_byte_identical(exports):
    first, second = exports
    names = sorted(p.name for p in first.iterdir())
    assert names == sorted(p.name for p in second.iterdir()) and len(names) == len(candidate().entries) + 1  # one PNG per entry (shared pixels share a file) plus the manifest
    assert tree_hash(first) == tree_hash(second)


def test_no_exported_png_carries_a_chunk_outside_the_allowlist(exports):
    pngs = sorted(exports[0].glob("*.png"))
    assert pngs
    assert {p.name: disallowed_chunks(p.read_bytes()) for p in pngs if disallowed_chunks(p.read_bytes())} == {}


def test_every_committed_artifact_png_passes_the_allowlist_too():
    pngs = sorted((REAL_CATALOG / "generated").glob("*/*.png"))
    assert pngs and all(not disallowed_chunks(p.read_bytes()) for p in pngs)


def with_chunk(png: bytes, kind: bytes, body: bytes = b"x") -> bytes:
    """`png` with one extra chunk inserted right before IEND (valid CRC)."""
    import struct
    import zlib

    chunk = struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    iend = png.rindex(b"\x00\x00\x00\x00IEND")
    return png[:iend] + chunk + png[iend:]


@pytest.mark.parametrize("kind", [b"tIME", b"tEXt", b"iTXt", b"zTXt"])
def test_the_allowlist_check_fails_on_a_planted_chunk(exports, kind):
    png = next(iter(sorted(exports[0].glob("*.png")))).read_bytes()
    assert disallowed_chunks(png) == []
    assert disallowed_chunks(with_chunk(png, kind)) == [kind]


def test_an_export_that_differs_by_one_byte_changes_the_tree_hash(exports, tmp_path):
    copy = tmp_path / "copy"
    shutil.copytree(exports[0], copy)
    target = next(iter(sorted(copy.glob("*.png"))))
    target.write_bytes(with_chunk(target.read_bytes(), b"tIME", b"\x07\xea\x0a\x0a\x00\x00\x00"))
    assert tree_hash(copy) != tree_hash(exports[0])


# ---- LOCAL: rebuild with the real Aseprite ----

def rebuild_verdicts(tmp: Path, monkeypatch, stored_root: Path = REAL_CATALOG) -> dict[str, str]:
    store = tmp / "catalog"
    store.mkdir()
    for part in STORE_PARTS:
        source = REAL_CATALOG / part
        shutil.copytree(source, store / part) if source.is_dir() else shutil.copy(source, store / part)
    monkeypatch.setattr(config, "CATALOG_ROOT", store)
    monkeypatch.setattr(config, "QUARANTINE_ROOT", store / ".quarantine")
    monkeypatch.setattr(config, "REVIEW_ROOT", store / ".review")
    exporter.build()  # every build-eligible source, the real Aseprite through the sandbox
    verdicts = {}
    for entry in candidate().entries:
        hexdigest = entry.pixel_hash[len(pixels.HASH_PREFIX):]
        stored = stored_root / "generated" / entry.artifact_id / f"{hexdigest}.png"
        rebuilt = store / "generated" / entry.artifact_id / f"{hexdigest}.png"  # the file name IS the pixel hash: it exists only when the pixels match
        if not rebuilt.is_file():
            verdicts[entry.visual_key + (f":{entry.detail}" if entry.detail else "")] = "PIXELS_DIFFER_OR_MISSING"
        else:
            name = entry.visual_key + (f":{entry.detail}" if entry.detail else "")
            if not stored.is_file():
                verdicts[name] = "STORED_MISSING"
            else:
                verdicts[name] = "IDENTICAL" if rebuilt.read_bytes() == stored.read_bytes() else "BYTES_DIFFER_PIXELS_MATCH"
    return verdicts


@pytest.mark.needs_aseprite
def test_the_current_release_candidate_rebuilds_from_its_stored_sources(tmp_path, monkeypatch):
    verdicts = rebuild_verdicts(tmp_path, monkeypatch)
    assert len(verdicts) == len(candidate().entries)
    bad = {k: v for k, v in verdicts.items() if v in ("PIXELS_DIFFER_OR_MISSING", "STORED_MISSING")}
    assert bad == {}, f"{len(bad)} entries do not rebuild to their committed pixels: {sorted(bad)}"
    drift = sorted(k for k, v in verdicts.items() if v == "BYTES_DIFFER_PIXELS_MATCH")
    if drift:
        version = subprocess.run([str(config_aseprite()), "--version"], capture_output=True, text=True, check=False).stdout.strip()
        warnings.warn(f"{len(drift)} of {len(verdicts)} entries rebuild to the same pixels but different PNG bytes under {version} (identity holds, bytes moved): {drift}")
    print(json.dumps({"release": f"{CATALOG_ID}/{RELEASE_ID}", "entries": len(verdicts), "identical": sum(v == 'IDENTICAL' for v in verdicts.values()), "bytes_differ_pixels_match": len(drift)}))


def config_aseprite() -> Path:
    from visual_assets.drawing import config as drawing_config

    return Path(drawing_config.ASEPRITE)


@pytest.mark.needs_aseprite
def test_the_rebuild_check_reports_a_byte_drift_and_a_pixel_change(tmp_path, monkeypatch):
    """The check is only worth having if it can fail: compare against a copy of the committed artifacts with one PNG re-encoded (same pixels, other bytes) and one missing."""
    stored = tmp_path / "stored"
    shutil.copytree(REAL_CATALOG / "generated", stored / "generated")
    entries = candidate().entries
    drifted, missing = entries[0], entries[1]
    path = stored / "generated" / drifted.artifact_id / f"{drifted.pixel_hash[len(pixels.HASH_PREFIX):]}.png"
    path.write_bytes(with_chunk(path.read_bytes(), b"tEXt", b"Software\0other"))  # same pixels, different file bytes
    (stored / "generated" / missing.artifact_id / f"{missing.pixel_hash[len(pixels.HASH_PREFIX):]}.png").unlink()
    (tmp_path / "work").mkdir()
    verdicts = rebuild_verdicts(tmp_path / "work", monkeypatch, stored_root=stored)
    key = lambda e: e.visual_key + (f":{e.detail}" if e.detail else "")  # noqa: E731
    assert verdicts[key(drifted)] == "BYTES_DIFFER_PIXELS_MATCH"
    assert verdicts[key(missing)] == "STORED_MISSING"
    assert sum(v == "IDENTICAL" for v in verdicts.values()) == len(entries) - 2
