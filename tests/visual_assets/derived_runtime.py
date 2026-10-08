"""The runtime manifest of a stored release candidate, DERIVED from the candidate and its artifacts, without `export_runtime`.

The frontend's committed fixtures (`__fixtures__/pilot`, `terrainset`) must equal what the store produces for the slots they claim. They used to prove that with a fresh `export_runtime` of the
current candidate, but the store refuses a candidate whose registry hash is not the live registry's (`registry_mismatch`), so registering a key broke the guards and forced a new candidate each time
(rc-0006, rc-0007; `TCK-20261008-VISUAL-ASSETS-FIXTURE-GUARD-DECOUPLING`). `derive` computes the same manifest bytes and files from the stored candidate, so a registry-only change no longer breaks a
fixture guard, while every substantive fact stays asserted: the slots, the details, the PNG bytes, the hashes.

It mirrors `visual_assets.store.runtime_export.export_runtime` minus the registry-hash refusal and the output writing; `test_derived_runtime.py` proves, on the hermetic catalog, that its output equals
`export_runtime`'s byte for byte (the drift guard), and the store's own `registry_mismatch` refusal stays the only comparison of a candidate with the live registry
(`tests/visual_assets/store/unit/test_runtime_export.py`).

Every artifact PNG is decoded here and must hash to the pixel hash the candidate records for that entry; `store verify` guarantees the same transitively (`verify._check_entry` requires the
artifact record for the digest and `verify` hashes each tracked artifact PNG against its record), so this is a direct, cheap restatement rather than new trust.
"""

from __future__ import annotations

from pathlib import Path

from visual_assets.store import config, pixels, records
from visual_assets.store.catalog.registry import load_registry
from visual_assets.store.contracts import ReleaseCandidateManifest, RuntimeManifest, canonical_json, parse_record, record_bound
from visual_assets.store.contracts.runtime import RuntimeDetail, RuntimeEntry
from visual_assets.store.intake.validator import file_hash
from visual_assets.store.runtime_export import FALLBACK_CONTRACT_VERSION, MANIFEST_NAME


def derive(catalog_id: str, release_id: str, *, allow_fixture_namespace: bool = False) -> tuple[bytes, dict[str, bytes]]:
    """(`runtime_manifest.json` bytes, {file name: PNG bytes}) for a stored candidate, read from the CURRENT store roots. Raises `AssertionError` when an artifact PNG does not hash to its recorded pixel hash."""
    manifest_bytes = records.read_file(records.manifests_dir() / catalog_id / f"{release_id}.json", record_bound(ReleaseCandidateManifest))
    candidate = parse_record(ReleaseCandidateManifest, manifest_bytes)
    registry = load_registry(config.CATALOG_ROOT / "definitions" / "visual_keys.yaml", allow_fixture_namespace=allow_fixture_namespace)
    entries: list[RuntimeEntry] = []
    files: dict[str, bytes] = {}
    for entry in candidate.entries:
        digest = entry.pixel_hash[len(pixels.HASH_PREFIX):]
        png = records.read_file(records.generated_dir() / entry.artifact_id / f"{digest}.png", config.MAX_PNG_FILE_BYTES)
        decoded = pixels.decode_png(png, max_dim=config.MAX_DIM)
        assert pixels.pixel_hash_of(decoded) == entry.pixel_hash, f"the artifact PNG of {entry.visual_key} does not decode to the pixel hash the candidate records"
        files[f"{digest}.png"] = png
        entries.append(RuntimeEntry(visual_key=entry.visual_key, family=registry.keys[entry.visual_key].family, pixel_hash=entry.pixel_hash,
                                    file=f"{digest}.png", width=decoded.width, height=decoded.height, detail=entry.detail))
    details = tuple(RuntimeDetail(visual_key=key, values=tuple(registry.keys[key].detail.values), default=registry.keys[key].detail.default)
                    for key in sorted({e.visual_key for e in entries}) if registry.keys[key].detail is not None)
    runtime = RuntimeManifest(record_type="runtime_manifest", schema_version=1, catalog_id=catalog_id, release_id=release_id, candidate_manifest_hash=file_hash(manifest_bytes),
                              registry_hash=candidate.registry_hash, fallback_contract_version=FALLBACK_CONTRACT_VERSION,
                              entries=tuple(sorted(entries, key=lambda e: (e.visual_key, e.detail or ""))), details=details)
    return canonical_json(runtime), files


def write(out: Path, catalog_id: str, release_id: str, **kwargs) -> None:
    """`derive` into a new directory laid out like an export (for a mutant to point a guard at)."""
    data, files = derive(catalog_id, release_id, **kwargs)
    out.mkdir()
    (out / MANIFEST_NAME).write_bytes(data)
    for name, png in files.items():
        (out / name).write_bytes(png)
