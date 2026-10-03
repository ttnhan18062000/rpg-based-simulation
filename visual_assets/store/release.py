"""`assemble_release`: write an immutable release CANDIDATE manifest from the registry and the current artifacts.

There is no active pointer and no "latest" file (D6): a candidate is only a candidate. Eligibility is decided by `revoke.is_build_eligible` alone. A visual key
maps to its source asset through the adoption record of the asset's latest build-eligible revision; two assets claiming one key is refused as ambiguous.
Stated limit: one visual key maps to one artifact (the single `x1` scale class); a key cannot carry two variants.
"""

from __future__ import annotations

from pathlib import Path

from visual_assets.store import config, pixels, records
from visual_assets.store.catalog.registry import load_registry
from visual_assets.store.catalogwrite import publish
from visual_assets.store.contracts import ReleaseCandidateManifest, canonical_json
from visual_assets.store.contracts.release import ReleaseEntry
from visual_assets.store.errors import BuildError, ContractError, IdentityError, RegistryError, StageError
from visual_assets.store.identities import CatalogId, ReleaseId, check, next_release_id, release_number
from visual_assets.store.intake.validator import file_hash
from visual_assets.store.revoke import is_build_eligible

SCALE_CLASS = "x1"


def _existing_release_ids(catalog_id: str) -> list[str]:
    base = records.manifests_dir() / catalog_id
    return sorted(p.stem for p in base.glob("rc-*.json")) if base.is_dir() else []


def _current_asset_for_each_key() -> dict[str, tuple[str, str]]:
    """visual_key -> (source_asset_id, latest build-eligible revision); an ambiguous key raises."""
    holders: dict[str, list[tuple[str, str]]] = {}
    for sid in records.list_source_ids():
        eligible = [rev for rev in records.list_revisions(sid) if is_build_eligible(sid, rev)]
        if eligible:
            adoption = records.load_adoption(records.load_source(sid, eligible[-1]).adoption_id)
            holders.setdefault(adoption.visual_key, []).append((sid, eligible[-1]))
    for key, assets in holders.items():
        if len(assets) > 1:
            raise BuildError("ambiguous_key", f"{key} is held by {', '.join(a for a, _ in assets)}; revoke all but one")
    return {key: assets[0] for key, assets in holders.items()}


def assemble_release(catalog_id: str, *, release_id: str | None = None, allow_fixture_namespace: bool = False) -> ReleaseCandidateManifest:
    """Write `manifests/candidates/<catalog_id>/<release_id>.json` or raise `BuildError`; nothing is written on failure."""
    try:
        check(CatalogId, catalog_id)
    except IdentityError:
        raise BuildError("invalid_catalog_id", "the catalog id is not valid") from None
    existing = _existing_release_ids(catalog_id)
    if release_id is None:
        try:
            release_id = next_release_id(existing)
        except IdentityError as exc:
            raise BuildError("release_ids_exhausted", str(exc)) from None
    try:
        check(ReleaseId, release_id)
    except IdentityError:
        raise BuildError("invalid_release_id", "a release id looks like rc-0001") from None
    if release_id in existing:
        raise BuildError("release_exists", f"{release_id} already exists; a candidate is never overwritten")
    if existing and release_number(release_id) <= max(release_number(r) for r in existing):
        raise BuildError("release_id_not_greater", f"{release_id} must be greater than every existing release id ({existing[-1]})")

    try:
        registry = load_registry(config.CATALOG_ROOT / "definitions" / "visual_keys.yaml", allow_fixture_namespace=allow_fixture_namespace)
        assets = _current_asset_for_each_key()
        entries: list[ReleaseEntry] = []
        for key in sorted(registry.keys):
            definition = registry.keys[key]
            if key not in assets:
                if definition.optional:
                    continue
                raise BuildError("key_without_artifact", f"the registry key {key} has no adopted, build-eligible source; mark it optional or adopt one")
            sid, revision = assets[key]
            found = records.load_artifact_for(sid, revision, SCALE_CLASS)
            if found is None:
                if definition.optional:
                    continue
                raise BuildError("key_without_artifact", f"{key} ({sid} {revision}) has no artifact; run build")
            artifact, record_path = found
            if not is_build_eligible(artifact.source_asset_id, artifact.source_revision):
                raise BuildError("artifact_source_revoked", f"the artifact for {key} comes from a revoked source revision")
            digest = artifact.pixel_hash[len(pixels.HASH_PREFIX):]
            png_path = records.artifact_paths(artifact.artifact_id, digest, artifact.source_revision)[0]
            png = records.read_file(png_path, config.MAX_DECODED_BYTES)
            if file_hash(png) != artifact.png_hash or pixels.pixel_hash(png, max_dim=config.MAX_DIM) != artifact.pixel_hash:
                raise BuildError("artifact_hash_mismatch", f"the artifact PNG for {key} no longer matches its record; run verify")
            entries.append(ReleaseEntry(visual_key=key, artifact_id=artifact.artifact_id, pixel_hash=artifact.pixel_hash))
        manifest = ReleaseCandidateManifest(
            record_type="release_candidate_manifest", schema_version=1, catalog_id=catalog_id, release_id=release_id,
            registry_hash=registry.file_hash, entries=tuple(entries), status="CANDIDATE",
        )
        data = canonical_json(manifest)
    except RegistryError as exc:
        raise BuildError("registry_invalid", str(exc)) from None
    except (StageError, ContractError, pixels.PngDecodeError) as exc:
        raise BuildError("catalog_unreadable", f"catalog records could not be read ({getattr(exc, 'code', 'error')})") from None

    publish([(records.manifests_dir() / catalog_id / f"{release_id}.json", data)])
    return manifest
