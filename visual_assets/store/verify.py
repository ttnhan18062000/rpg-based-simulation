"""`verify`: whole-store integrity in pure Python, so CI can run it without Aseprite.

It rebuilds the provenance chain (`audit_chain`), re-hashes every artifact PNG (file hash and a recomputed `pixels-v1` hash), checks every record against
its bytes and its name, follows every manifest entry to its artifact, and flags anything unexpected in the tracked tree. Every finding has a stable code.
`blocking=False` marks a finding that is visible history rather than a fault: an artifact whose source revision was later revoked (nothing is ever deleted,
so it stays; it only becomes a blocking finding if a release candidate still lists it).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from visual_assets.store import config, deletionlog, lock, pixels, records
from visual_assets.store.audit import audit_chain
from visual_assets.store.build.exportconfig import load_export_config
from visual_assets.store.catalog.registry import load_registry
from visual_assets.store.contracts import AdoptionRecord, ArtifactRecord, ReleaseCandidateManifest, SetAdoptionRecord, SourceRecord, parse_record, record_bound
from visual_assets.store.errors import BuildError, ContractError, PngDecodeError, RegistryError, StageError
from visual_assets.store.intake.validator import file_hash

_TOP = {"README.md", "STORE_FORMAT", "definitions", "sources", "provenance", "build-config", "generated", "manifests", "fixtures",
        ".quarantine", ".review", ".gitkeep"}
_INSIDE = {
    "definitions": {"visual_keys.yaml", ".gitkeep"},
    "build-config": {"export.toml", ".gitkeep"},
    "manifests": {"candidates", ".gitkeep"},
    "provenance": {"adoptions", "intake", "revocations", "set-adoptions", "licences", ".gitkeep"},
}
_ID = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}")
_PNG_NAME = re.compile(r"([0-9a-f]{64})\.png")
_RECORD_NAME = re.compile(r"([0-9a-f]{64})\.(r[0-9]{4})\.artifact\.json")
_FORBIDDEN_NAMES = ("active", "current", "latest")


@dataclass(frozen=True)
class Finding:
    code: str
    path: str
    detail: str
    blocking: bool = True


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return path.name


def verify(catalog_root: Path | str | None = None, *, allow_fixture_namespace: bool = False) -> list[Finding]:
    root = Path(catalog_root) if catalog_root is not None else config.CATALOG_ROOT
    out: list[Finding] = []
    _store_format(root, out)
    _registry(root, out, allow_fixture_namespace)
    _adoption_details(root, out, allow_fixture_namespace)
    _set_adoptions(root, out)
    out += [Finding(b.code, b.path, b.detail) for b in audit_chain(root).breaks]
    _tracked_tree(root, out)
    has_artifacts = _artifacts(root, out)
    _build_config(root, out, has_artifacts)
    _manifests(root, out)
    return out


def _store_format(root: Path, out: list[Finding]) -> None:
    path = root / "STORE_FORMAT"
    try:
        first = records.read_file(path, config.MAX_RECORD_BYTES).decode("utf-8").splitlines()[0]
    except (StageError, UnicodeDecodeError, IndexError):
        out.append(Finding("STORE_FORMAT_MISSING", "STORE_FORMAT", "STORE_FORMAT is missing or unreadable"))
        return
    if first.strip() != f"store_format_version: {config.STORE_FORMAT_VERSION}":
        out.append(Finding("STORE_FORMAT_UNSUPPORTED", "STORE_FORMAT", f"{first!r} is not store_format_version: {config.STORE_FORMAT_VERSION}"))


def _registry(root: Path, out: list[Finding], allow_fixture: bool) -> None:
    try:
        load_registry(root / "definitions" / "visual_keys.yaml", allow_fixture_namespace=allow_fixture)
    except RegistryError as exc:
        out.append(Finding("REGISTRY_INVALID", "definitions/visual_keys.yaml", str(exc)))


def _adoption_details(root: Path, out: list[Finding], allow_fixture: bool) -> None:
    """A live adoption's `detail_value` must be declared by its key (an undeclared one would make `assemble_release` refuse)."""
    try:
        keys = load_registry(root / "definitions" / "visual_keys.yaml", allow_fixture_namespace=allow_fixture).keys
    except RegistryError:
        return  # REGISTRY_INVALID already says so
    try:
        for sid in records.list_source_ids(root):
            eligible = [rev for rev in records.list_revisions(sid, root) if records.is_eligible(sid, rev, root)]
            if not eligible:
                continue
            adoption = records.load_adoption(records.load_source(sid, eligible[-1], root).adoption_id, root)
            definition = keys.get(adoption.visual_key)
            if adoption.detail_value is None or definition is None:
                continue
            if definition.detail is None or adoption.detail_value not in definition.detail.values:
                out.append(Finding("ADOPTION_UNKNOWN_DETAIL", f"sources/{sid}", f"{adoption.visual_key} does not declare the detail value {adoption.detail_value!r}"))
    except (StageError, ContractError):
        return  # the audit reports unreadable records


def _set_adoptions(root: Path, out: list[Finding]) -> None:
    """Each reviewed-set adoption record parses, is named by its id, and every entry points at an adoption of the same intake, key and detail slot."""
    base = records.set_adoptions_dir(root)
    if not base.is_dir() or base.is_symlink():
        return
    for path in sorted(base.iterdir()):
        rel = _rel(root, path)
        try:
            record = parse_record(SetAdoptionRecord, records.read_file(path, record_bound(SetAdoptionRecord)))
        except (StageError, ContractError) as exc:
            out.append(Finding("SET_ADOPTION_UNREADABLE", rel, f"cannot be read ({exc.code})"))
            continue
        if path.name != f"{record.set_adoption_id}.json":
            out.append(Finding("SET_ADOPTION_MISMATCH", rel, "the file name is not the record's set adoption id"))
        for entry in record.entries:
            try:
                adoption = parse_record(AdoptionRecord, records.read_file(records.adoptions_dir(root) / f"{entry.adoption_id}.json", record_bound(AdoptionRecord)))
            except (StageError, ContractError):
                out.append(Finding("SET_ADOPTION_DANGLING", rel, f"{entry.visual_key} points at an adoption record that cannot be read"))
                continue
            if (adoption.intake_id, adoption.visual_key, adoption.detail_value) != (entry.intake_id, entry.visual_key, entry.detail):
                out.append(Finding("SET_ADOPTION_MISMATCH", rel, f"{entry.visual_key}: the adoption record names another intake, key or detail value"))


def _local_state(name: str) -> bool:
    """The gitignored local files of ADR D24 (the store lock, the gc deletion log and its archives); `audit_chain` checks the log."""
    return name in (lock.LOCK_NAME, deletionlog.LOG_NAME) or deletionlog.ARCHIVE.fullmatch(name) is not None


def _tracked_tree(root: Path, out: list[Finding]) -> None:
    if not root.is_dir():
        return
    for entry in sorted(root.iterdir()):
        if entry.name not in _TOP and not entry.name.startswith(".tmp-") and not _local_state(entry.name):
            out.append(Finding("UNEXPECTED_FILE", entry.name, "not part of the store layout"))
    for name, allowed in _INSIDE.items():
        base = root / name
        if base.is_dir() and not base.is_symlink():
            for entry in sorted(base.iterdir()):
                if entry.name not in allowed and not entry.name.startswith(".tmp-"):
                    out.append(Finding("UNEXPECTED_FILE", _rel(root, entry), f"not allowed inside {name}/"))


def _artifacts(root: Path, out: list[Finding]) -> bool:
    base = records.generated_dir(root)
    if not base.is_dir() or base.is_symlink():
        return False
    seen = False
    for directory in sorted(base.iterdir()):
        if directory.name == ".gitkeep" or directory.name.startswith(".tmp-"):
            continue
        if not directory.is_dir() or directory.is_symlink() or not _ID.fullmatch(directory.name):
            out.append(Finding("ORPHAN_FILE", _rel(root, directory), "not an artifact directory"))
            continue
        names = {p.name for p in directory.iterdir()}
        record_hexes = set()
        for name in sorted(names):
            if (m := _RECORD_NAME.fullmatch(name)):
                seen = True
                record_hexes.add(m.group(1))
                _check_record(root, directory, name, m.group(1), m.group(2), out)
            elif not _PNG_NAME.fullmatch(name):
                out.append(Finding("ORPHAN_FILE", _rel(root, directory / name), "unexpected file in generated/"))
        for name in sorted(names):
            if (m := _PNG_NAME.fullmatch(name)) and m.group(1) not in record_hexes:
                out.append(Finding("ORPHAN_FILE", _rel(root, directory / name), "an artifact PNG no artifact record refers to"))
    return seen


def _check_record(root: Path, directory: Path, name: str, digest: str, revision: str, out: list[Finding]) -> None:
    path = directory / name
    rel = _rel(root, path)
    try:
        data = records.read_file(path, record_bound(ArtifactRecord))
        record = parse_record(ArtifactRecord, data)
    except (StageError, ContractError) as exc:
        out.append(Finding("ARTIFACT_RECORD_UNREADABLE", rel, f"cannot be read ({exc.code})"))
        return
    if record.artifact_id != directory.name or record.source_revision != revision or record.pixel_hash != pixels.HASH_PREFIX + digest:
        out.append(Finding("ARTIFACT_NAME_MISMATCH", rel, "the file name does not match the record's artifact id, revision and pixel hash"))
    png_path = directory / f"{digest}.png"
    if not png_path.exists():
        out.append(Finding("ARTIFACT_PNG_MISSING", _rel(root, png_path), "the artifact record has no PNG"))
    else:
        try:
            png = records.read_file(png_path, config.MAX_PNG_FILE_BYTES)
            if file_hash(png) != record.png_hash:
                out.append(Finding("ARTIFACT_PNG_HASH_MISMATCH", _rel(root, png_path), "the PNG bytes differ from the recorded file hash"))
            actual = pixels.pixel_hash(png, max_dim=config.MAX_DIM * 16)
            if actual != record.pixel_hash:
                out.append(Finding("ARTIFACT_PIXEL_MISMATCH", _rel(root, png_path), "the decoded pixels do not hash to the recorded value (an edited or renamed PNG)"))
        except (StageError, PngDecodeError) as exc:
            out.append(Finding("ARTIFACT_PNG_UNREADABLE", _rel(root, png_path), f"cannot be decoded ({getattr(exc, 'code', 'error')})"))
    try:
        source = records.load_source(record.source_asset_id, record.source_revision, root)
        source_record_bytes = records.read_file(records.source_paths(record.source_asset_id, record.source_revision, root)[1], record_bound(SourceRecord))
    except (StageError, ContractError):
        out.append(Finding("ARTIFACT_SOURCE_MISSING", rel, f"its source revision {record.source_asset_id} {record.source_revision} cannot be read"))
        return
    if record.source_hash != source.source_hash or record.source_record_hash != file_hash(source_record_bytes):
        out.append(Finding("ARTIFACT_SOURCE_RECORD_MISMATCH", rel, "the artifact does not match the SourceRecord it says it was built from"))
    try:
        if record.source_revision in records.revoked_revisions(record.source_asset_id, root):
            out.append(Finding("ARTIFACT_SOURCE_REVOKED", rel, "built from a revoked source revision (history; harmless unless released)", blocking=False))
    except (StageError, ContractError):
        out.append(Finding("REVOCATION_UNREADABLE", "provenance/revocations", "revocations cannot be read, so revoked sources cannot be ruled out"))


def _build_config(root: Path, out: list[Finding], has_artifacts: bool) -> None:
    path = root / "build-config" / "export.toml"
    if not path.exists():
        if has_artifacts:
            out.append(Finding("BUILD_CONFIG_MISSING", "build-config/export.toml", "artifacts exist but the pinned export rules are missing"))
        return
    try:
        load_export_config(path)
    except BuildError as exc:
        out.append(Finding("BUILD_CONFIG_INVALID", "build-config/export.toml", exc.message))


def _manifests(root: Path, out: list[Finding]) -> None:
    base = records.manifests_dir(root)
    if not base.is_dir() or base.is_symlink():
        return
    try:
        registry_keys = dict(load_registry(root / "definitions" / "visual_keys.yaml", allow_fixture_namespace=True).keys)
    except RegistryError:
        registry_keys = {}
    for catalog in sorted(base.iterdir()):
        if catalog.name in (".gitkeep",) or catalog.name.startswith(".tmp-"):
            continue
        if not catalog.is_dir() or catalog.is_symlink() or not _ID.fullmatch(catalog.name):
            out.append(Finding("ORPHAN_FILE", _rel(root, catalog), "not a catalog directory"))
            continue
        for path in sorted(catalog.iterdir()):
            rel = _rel(root, path)
            if any(word in path.name.lower() for word in _FORBIDDEN_NAMES):
                out.append(Finding("UNEXPECTED_FILE", rel, "a release candidate directory never names an active, current or latest release"))
                continue
            try:
                manifest = parse_record(ReleaseCandidateManifest, records.read_file(path, record_bound(ReleaseCandidateManifest)))
            except (StageError, ContractError) as exc:
                out.append(Finding("MANIFEST_UNREADABLE", rel, f"cannot be read ({exc.code})"))
                continue
            if manifest.catalog_id != catalog.name or manifest.release_id != path.stem:
                out.append(Finding("MANIFEST_MISMATCH", rel, "the file or directory name is not the manifest's catalog and release id"))
            for entry in manifest.entries:
                _check_entry(root, rel, entry, registry_keys, out)


def _check_entry(root: Path, rel: str, entry, registry_keys: dict, out: list[Finding]) -> None:
    digest = entry.pixel_hash[len(pixels.HASH_PREFIX):]
    directory = records.generated_dir(root) / entry.artifact_id
    candidates = sorted(directory.glob(f"{digest}.r????.artifact.json")) if directory.is_dir() else []
    if not candidates or not (directory / f"{digest}.png").exists():
        out.append(Finding("MANIFEST_DANGLING", rel, f"{entry.visual_key} points at an artifact that does not exist"))
        return
    if registry_keys and entry.visual_key not in registry_keys:
        out.append(Finding("MANIFEST_UNKNOWN_KEY", rel, f"{entry.visual_key} is not in the registry"))
    elif entry.detail is not None and registry_keys:
        # An entry WITHOUT a detail value is tolerated for a key that now declares an axis: the candidate predates the declaration.
        declared = registry_keys[entry.visual_key].detail
        if declared is None or entry.detail not in declared.values:
            out.append(Finding("MANIFEST_UNKNOWN_DETAIL", rel, f"{entry.visual_key} does not declare the detail value {entry.detail!r}"))
    for candidate in candidates:
        try:
            record = parse_record(ArtifactRecord, records.read_file(candidate, record_bound(ArtifactRecord)))
            if record.source_revision in records.revoked_revisions(record.source_asset_id, root):
                out.append(Finding("MANIFEST_ENTRY_SOURCE_REVOKED", rel, f"{entry.visual_key} lists an artifact built from a revoked source revision"))
        except (StageError, ContractError):
            out.append(Finding("MANIFEST_DANGLING", rel, f"the artifact record for {entry.visual_key} cannot be read"))
