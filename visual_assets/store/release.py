"""`assemble_release`: write an immutable release CANDIDATE manifest from the registry and the current artifacts.

There is no active pointer and no "latest" file (D6): a candidate is only a candidate. Eligibility is decided by `revoke.is_build_eligible` alone. A visual key
maps to its source asset through the adoption record of the asset's latest build-eligible revision; two assets claiming one SLOT is refused as ambiguous.
A slot is a visual key, plus a detail value when the key declares a detail axis (`detail` in the registry): one key then carries one artifact per
declared detail value, each adopted separately (`AdoptionRecord.detail_value`, `None` = the key's default value). Every artifact is at the single `x1` scale class.
A key that is not optional needs its default slot's artifact; its other detail values need none until someone adopts them, but an adopted (held) slot
without an artifact is refused (`key_without_artifact`: run `build`), never dropped.
"""

from __future__ import annotations

from pathlib import Path

from visual_assets.store import config, pixels, records
from visual_assets.store.catalog.registry import fallback_problems, load_registry
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


def _current_asset_for_each_slot(registry) -> dict[tuple[str, str | None], tuple[str, str]]:
    """(visual_key, detail value) -> (source_asset_id, latest build-eligible revision); an ambiguous slot, or a detail value the registry does not declare, raises.

    A key the registry does not know is ignored here, as before (the release loop only walks registry keys).
    """
    holders: dict[tuple[str, str | None], list[tuple[str, str]]] = {}
    for sid in records.list_source_ids():
        eligible = [rev for rev in records.list_revisions(sid) if is_build_eligible(sid, rev)]
        if eligible:
            adoption = records.load_adoption(records.load_source(sid, eligible[-1]).adoption_id)
            definition = registry.keys.get(adoption.visual_key)
            if definition is None:
                holders.setdefault((adoption.visual_key, None), []).append((sid, eligible[-1]))
                continue
            declared = () if definition.detail is None else definition.detail.values
            if adoption.detail_value is not None and adoption.detail_value not in declared:
                raise BuildError("undeclared_detail", f"{sid} was adopted as {adoption.visual_key} detail {adoption.detail_value!r}, which the registry does not declare")
            holders.setdefault((adoption.visual_key, definition.effective_detail(adoption.detail_value)), []).append((sid, eligible[-1]))
    for (key, detail), assets in holders.items():
        if len(assets) > 1:
            raise BuildError("ambiguous_key", f"{key if detail is None else f'{key} [{detail}]'} is held by {', '.join(a for a, _ in assets)}; revoke all but one")
    return {slot: assets[0] for slot, assets in holders.items()}


def _entry(what: str, key: str, detail: str | None, asset: tuple[str, str], *, optional: bool) -> ReleaseEntry | None:
    """The entry for one slot, or `None` when its asset has no artifact yet and the slot is optional."""
    sid, revision = asset
    found = records.load_artifact_for(sid, revision, SCALE_CLASS)
    if found is None:
        if optional:
            return None
        raise BuildError("key_without_artifact", f"{what} ({sid} {revision}) has no artifact; run build")
    artifact, _record_path = found
    if not is_build_eligible(artifact.source_asset_id, artifact.source_revision):
        raise BuildError("artifact_source_revoked", f"the artifact for {what} comes from a revoked source revision")
    digest = artifact.pixel_hash[len(pixels.HASH_PREFIX):]
    png_path = records.artifact_paths(artifact.artifact_id, digest, artifact.source_revision)[0]
    png = records.read_file(png_path, config.MAX_PNG_FILE_BYTES)
    if file_hash(png) != artifact.png_hash or pixels.pixel_hash(png, max_dim=config.MAX_DIM) != artifact.pixel_hash:
        raise BuildError("artifact_hash_mismatch", f"the artifact PNG for {what} no longer matches its record; run verify")
    return ReleaseEntry(visual_key=key, detail=detail, artifact_id=artifact.artifact_id, pixel_hash=artifact.pixel_hash)


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
        assets = _current_asset_for_each_slot(registry)
        entries: list[ReleaseEntry] = []
        for key in sorted(registry.keys):
            definition = registry.keys[key]
            slots = [None] if definition.detail is None else sorted(definition.detail.values)
            for detail in slots:
                is_default = definition.detail is None or detail == definition.detail.default
                required = is_default and not definition.optional  # only a default slot is ever required; the others fall back to it
                what = key if detail is None else f"{key} [{detail}]"
                if (key, detail) not in assets:
                    if not required:
                        continue
                    raise BuildError("key_without_artifact", f"the registry key {what} has no adopted, build-eligible source; mark it optional or adopt one")
                entry = _entry(what, key, detail, assets[(key, detail)], optional=definition.optional)  # a HELD slot with no artifact is a forgotten `build`, never silently dropped
                if entry is not None:
                    entries.append(entry)
        missing = fallback_problems(registry, {e.visual_key for e in entries})  # AM1-W06.3: what shows for every key this release leaves without an image
        if missing:
            raise BuildError("fallback_missing", f"{len(missing)} key(s) without an image have no alternative, first: {missing[0]}")
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
