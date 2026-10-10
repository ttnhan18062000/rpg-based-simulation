"""`export_runtime`: write the client's runtime manifest and its PNGs for one release candidate (proposal 9.3, Profile A).

Read-only on the catalog; the output goes to a NEW directory outside it. No human gate (it publishes nothing a reviewer has not already adopted),
and no MCP tool: the drawing server may not import this module. The result is all-or-nothing (staged in a `.tmp-*` sibling, then renamed) and
deterministic: the same release gives byte-identical output (`runtime_manifest.json` is `canonical_json`, the PNGs are copied as stored and named
by their pixel hash). Refusals, each with a stable code and no output: `verify_failed`, `unknown_release`, `registry_mismatch`,
`artifact_mismatch`, `out_exists`, `out_inside_catalog`.
"""

from __future__ import annotations

import os
import secrets
import shutil
from pathlib import Path

from visual_assets.store import config, pixels, records, verify
from visual_assets.store.atlas import build_atlas
from visual_assets.store.catalog.registry import fallback_problems, load_registry
from visual_assets.store.contracts import ReleaseCandidateManifest, RuntimeManifest, canonical_json, parse_record, record_bound
from visual_assets.store.contracts.runtime import RuntimeDetail, RuntimeEntry
from visual_assets.store.errors import BuildError, ContractError, IdentityError, PngDecodeError, RegistryError, StageError
from visual_assets.store.identities import CatalogId, ReleaseId, check
from visual_assets.store.intake.validator import file_hash

MANIFEST_NAME = "runtime_manifest.json"
FALLBACK_CONTRACT_VERSION = 1


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _check_out(out_dir: Path | str) -> Path:
    out = Path(out_dir)
    if os.path.lexists(out):
        raise BuildError("out_exists", f"{out.name} already exists; an export never overwrites")
    parent = out.parent.resolve()
    if _inside(parent, config.CATALOG_ROOT.resolve()):
        raise BuildError("out_inside_catalog", "the output must be outside the catalog")
    if not parent.is_dir():
        raise BuildError("out_parent_missing", "the output's parent directory does not exist")
    return parent / out.name


def _write_new(path: Path, data: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def export_runtime(catalog_id: str, release_id: str, out_dir: Path | str, *, allow_fixture_namespace: bool = False, atlases: bool = False) -> RuntimeManifest:
    """Write `<out_dir>/runtime_manifest.json` and `<out_dir>/<hex>.png`, or raise `BuildError` leaving no output and the catalog unchanged.

    With `atlases=True` it also writes `atlas-<family>.png` and `atlas-<family>.json` per family (`store/atlas.py`); the per-file output and the manifest are byte-identical either way."""
    try:
        check(CatalogId, catalog_id)
    except IdentityError:
        raise BuildError("invalid_catalog_id", "the catalog id is not valid") from None
    try:
        check(ReleaseId, release_id)
    except IdentityError:
        raise BuildError("invalid_release_id", "a release id looks like rc-0001") from None
    out = _check_out(out_dir)

    blocking = [f for f in verify.verify(allow_fixture_namespace=allow_fixture_namespace) if f.blocking]
    if blocking:
        raise BuildError("verify_failed", f"{len(blocking)} blocking finding(s), first {blocking[0].code} at {blocking[0].path}")
    path = records.manifests_dir() / catalog_id / f"{release_id}.json"
    if not path.is_file() or path.is_symlink():
        raise BuildError("unknown_release", f"{catalog_id}/{release_id} is not a release candidate in this catalog")
    try:
        manifest_bytes = records.read_file(path, record_bound(ReleaseCandidateManifest))
        candidate = parse_record(ReleaseCandidateManifest, manifest_bytes)
        registry = load_registry(config.CATALOG_ROOT / "definitions" / "visual_keys.yaml", allow_fixture_namespace=allow_fixture_namespace)
        if registry.file_hash != candidate.registry_hash:
            raise BuildError("registry_mismatch", "the registry changed since this candidate was assembled; assemble a new one")
        entries: list[RuntimeEntry] = []
        files: dict[str, bytes] = {}
        images: dict[str, pixels.DecodedImage] = {}
        for entry in candidate.entries:
            digest = entry.pixel_hash[len(pixels.HASH_PREFIX):]
            png_path = records.generated_dir() / entry.artifact_id / f"{digest}.png"
            try:
                png = records.read_file(png_path, config.MAX_PNG_FILE_BYTES)
                decoded = pixels.decode_png(png, max_dim=config.MAX_DIM)
            except (StageError, PngDecodeError):
                raise BuildError("artifact_mismatch", f"the artifact PNG for {entry.visual_key} is missing or unreadable") from None
            if pixels.pixel_hash_of(decoded) != entry.pixel_hash:
                raise BuildError("artifact_mismatch", f"the artifact PNG for {entry.visual_key} does not match its pixel hash")
            files[f"{digest}.png"] = png
            images[entry.pixel_hash] = decoded
            entries.append(RuntimeEntry(visual_key=entry.visual_key, family=registry.keys[entry.visual_key].family, pixel_hash=entry.pixel_hash,
                                        file=f"{digest}.png", width=decoded.width, height=decoded.height, detail=entry.detail))
        missing = fallback_problems(registry, {e.visual_key for e in entries})  # AM1-W06.3 again at activation time: the client must be able to show something for every key it has no image for
        if missing:
            raise BuildError("fallback_missing", f"{len(missing)} key(s) without an image have no alternative, first: {missing[0]}")
        # the client picks over the DECLARED values, copied from the registry (the registry hash was just checked equal to the candidate's)
        details = tuple(
            RuntimeDetail(visual_key=key, values=tuple(registry.keys[key].detail.values), default=registry.keys[key].detail.default)
            for key in sorted({e.visual_key for e in entries}) if registry.keys[key].detail is not None
        )
        runtime = RuntimeManifest(
            record_type="runtime_manifest", schema_version=1, catalog_id=catalog_id, release_id=release_id,
            candidate_manifest_hash=file_hash(manifest_bytes), registry_hash=candidate.registry_hash,
            fallback_contract_version=FALLBACK_CONTRACT_VERSION, entries=tuple(sorted(entries, key=lambda e: (e.visual_key, e.detail or ""))),
            details=details,
        )
        data = canonical_json(runtime)
        if atlases:
            for family in sorted({e.family for e in runtime.entries}):
                sheet, sheet_json = build_atlas(family, [e for e in runtime.entries if e.family == family], images, catalog_id=catalog_id, release_id=release_id)
                files[f"atlas-{family}.png"] = sheet
                files[f"atlas-{family}.json"] = sheet_json
    except RegistryError as exc:
        raise BuildError("registry_invalid", str(exc)) from None
    except (StageError, ContractError) as exc:
        raise BuildError("catalog_unreadable", f"catalog records could not be read ({getattr(exc, 'code', 'error')})") from None

    staging = out.parent / f".tmp-{secrets.token_hex(6)}"
    os.mkdir(staging, 0o755)
    try:
        _write_new(staging / MANIFEST_NAME, data)
        for name, png in sorted(files.items()):
            _write_new(staging / name, png)
        try:
            # `out` was checked absent up front. If something appeared meanwhile: a file or a NON-empty directory makes rename fail and
            # nothing is replaced; on Linux an EMPTY directory is replaced, which loses nothing (a narrow race the pre-check makes unlikely).
            os.rename(staging, out)
        except OSError:
            raise BuildError("out_exists", f"{out.name} appeared while exporting; nothing was written") from None
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return runtime
