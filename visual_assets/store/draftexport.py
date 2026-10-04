"""`draft export`: write a draft preview manifest and its preview PNGs for one draft set, for the isolated preview page.

Read-only on the drafts and the catalog; the output goes to a NEW directory outside both (all-or-nothing: staged in a `.tmp-*` sibling, then renamed) and is deterministic.
The manifest is a record type of its own (`draft_preview_manifest`), never a `runtime_manifest`. It carries the set id and `draft_set_hash`, the file hash of the exact
`draft_set.json` bytes, which is the value `adopt-set` prints in its confirmation: a review record can name exactly the set that was reviewed and then adopted.
The set is verified first (the whole chain of every entry, declared keys and values, and no revoked intake) and any finding refuses the export. A live ADOPTED slot
the set does not hold is added as a labelled reference entry (`adopted: true`, from the catalog's artifact) so the map is complete; a draft for a slot always wins, and references exist only here, never in the DraftSet. Each entry's `preview.png` is copied
byte for byte, named by its pixel hash; the page draws it at 1/`scale` with smoothing off. No Aseprite is needed. Refusals have stable codes (`DraftError`).
"""

from __future__ import annotations

import os
import secrets
import shutil
from pathlib import Path

from visual_assets.store import config, drafts, pixels, records
from visual_assets.store.catalog.registry import Registry, load_registry
from visual_assets.store.contracts import CandidateHandoffPackage, DraftPreviewManifest, canonical_json, parse_record
from visual_assets.store.contracts.draft import DraftPreviewEntry
from visual_assets.store.contracts.runtime import RuntimeDetail
from visual_assets.store.errors import ContractError, DraftError, PngDecodeError, RegistryError, StageError
from visual_assets.store.intake import quarantine, validator

MANIFEST_NAME = "draft_preview_manifest.json"


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _check_out(out_dir: Path | str, drafts_root: Path) -> Path:
    out = Path(out_dir)
    if os.path.lexists(out):
        raise DraftError("out_exists", f"{out.name} already exists; an export never overwrites")
    parent = out.parent.resolve()
    if _inside(parent, config.CATALOG_ROOT.resolve()) or _inside(parent, drafts_root.resolve()):
        raise DraftError("out_inside_store", "the output must be outside the catalog and the drafts")
    if not parent.is_dir():
        raise DraftError("out_parent_missing", "the output's parent directory does not exist")
    return parent / out.name


def _adopted_references(known: Registry, record, files: dict[str, bytes]) -> list[DraftPreviewEntry]:
    """A reference entry for each live ADOPTED slot of a registered key that the set does not hold (a draft for the slot always wins), so the preview map is complete.

    Built from the catalog's 16 x 16 artifact (scale 1), never from a draft: nothing is copied into the drafts and `adopt-set` never sees it (it is not in the DraftSet).
    """
    held = {(e.visual_key, known.keys[e.visual_key].effective_detail(e.detail)) for e in record.entries if e.visual_key in known.keys}
    out: list[DraftPreviewEntry] = []
    try:
        for key, definition in sorted(known.keys.items()):
            for slot in ([None] if definition.detail is None else list(definition.detail.values)):
                if (key, slot) in held:
                    continue
                holders = records.slot_holders(definition, slot)
                if not holders:
                    continue
                sid = holders[0]
                revision = [r for r in records.list_revisions(sid) if records.is_eligible(sid, r)][-1]
                found = records.load_artifact_for(sid, revision, "x1")
                if found is None:
                    continue  # adopted but not built yet: nothing to show
                artifact, _ = found
                digest = artifact.pixel_hash[len(pixels.HASH_PREFIX):]
                png = records.read_file(records.artifact_paths(artifact.artifact_id, digest, artifact.source_revision)[0], config.MAX_PNG_FILE_BYTES)
                decoded = pixels.decode_png(png, max_dim=config.MAX_DIM)
                adoption = records.load_adoption(records.load_source(sid, revision).adoption_id)
                files[f"{digest}.png"] = png
                out.append(DraftPreviewEntry(
                    visual_key=key, family=definition.family, detail=slot, source_asset_id=sid, draft_id=adoption.intake_id, pixel_hash=artifact.pixel_hash,
                    file=f"{digest}.png", width=decoded.width, height=decoded.height, scale=1, adopted=True,
                ))
    except (ContractError, StageError, PngDecodeError) as exc:
        raise DraftError("catalog_unreadable", f"the adopted art could not be read ({getattr(exc, 'code', 'error')})") from None
    return out


def export_draft_preview(
    set_id: str, out_dir: Path | str, *, registry: Registry | None = None, root: Path | None = None
) -> DraftPreviewManifest:
    """Write `<out_dir>/draft_preview_manifest.json` and `<out_dir>/<hex>.png`, or raise `DraftError` leaving no output."""
    drafts_root = Path(root) if root is not None else config.DRAFTS_ROOT
    out = _check_out(out_dir, drafts_root)
    try:
        known = registry if registry is not None else load_registry()
    except RegistryError as exc:
        raise DraftError("registry_unreadable", str(exc)) from None
    record, set_bytes = drafts.load_set(set_id, root)
    findings = drafts.verify_set(set_id, registry=known, root=root)
    if findings:
        raise DraftError("draft_set_invalid", f"{len(findings)} problem(s) in the draft set, first {findings[0].code}: {findings[0].detail}")

    entries: list[DraftPreviewEntry] = []
    files: dict[str, bytes] = {}
    for entry in record.entries:
        data = drafts.read_entry(set_id, entry, root)
        try:
            package = parse_record(CandidateHandoffPackage, data.package)
            decoded = pixels.decode_png(data.preview, max_dim=config.MAX_PREVIEW_DIM)
        except (ContractError, PngDecodeError) as exc:
            raise DraftError("entry_unreadable", f"{entry.draft_id}: {getattr(exc, 'code', 'error')}") from None
        if package.width < 1 or decoded.width % package.width or decoded.height % package.height or decoded.width // package.width != decoded.height // package.height:
            raise DraftError("scale_unsupported", f"{entry.draft_id}: the preview is not a whole-number scale of the {package.width} x {package.height} tile")
        name = entry.pixel_hash.split(":", 1)[1] + ".png"
        files[name] = data.preview
        entries.append(DraftPreviewEntry(
            visual_key=entry.visual_key, family=known.keys[entry.visual_key].family, detail=entry.detail, source_asset_id=entry.source_asset_id,
            draft_id=entry.draft_id, pixel_hash=entry.pixel_hash, file=name, width=decoded.width, height=decoded.height, scale=decoded.width // package.width,
        ))
    entries += _adopted_references(known, record, files)
    entries.sort(key=lambda e: (e.visual_key, e.detail or ""))
    details = tuple(
        RuntimeDetail(visual_key=key, values=tuple(known.keys[key].detail.values), default=known.keys[key].detail.default)
        for key in sorted({e.visual_key for e in entries}) if known.keys[key].detail is not None
    )
    try:
        manifest = DraftPreviewManifest(
            record_type="draft_preview_manifest", schema_version=1, set_id=set_id, draft_set_hash=validator.file_hash(set_bytes),
            registry_hash=known.file_hash, entries=tuple(entries), details=details,
        )
        manifest_bytes = canonical_json(manifest)
    except (ContractError, ValueError) as exc:
        raise DraftError("manifest_invalid", f"the preview manifest is not valid ({getattr(exc, 'code', 'error')})") from None

    staging = out.parent / f"{quarantine.TEMP_PREFIX}{secrets.token_hex(6)}"
    os.mkdir(staging, 0o755)
    try:
        for name, blob in {MANIFEST_NAME: manifest_bytes, **dict(sorted(files.items()))}.items():
            quarantine.write_new(staging / name, blob)
            os.chmod(staging / name, 0o644)
        try:
            os.rename(staging, out)
        except OSError:
            raise DraftError("out_exists", f"{out.name} appeared while exporting; nothing was written") from None
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return manifest
