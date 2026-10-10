"""Draft sets: unadopted, tracked, never released. `draft keep` and `draft verify`.

A draft set is `visual_assets/drafts/<set_id>/draft_set.json` (a `DraftSet`) plus one folder per entry named by its intake id, holding the three staged files
and the intake result of a PASSED intake. It lives OUTSIDE the catalog: `build`, `release`, `runtime_export` and the catalog's `verify` never read it, and `gc`
never touches it. Keeping a draft records no approval, so an agent may run it (it is not an MCP tool); the one human decision is `adopt-set`.

`read_entry` is the single chain check both `draft verify` and `adopt-set` use, so a draft cannot pass one and fail the other:
source.aseprite bytes -> the staged-file hash inside intake_result.json; intake_result.json bytes -> `intake_hash`; preview.png pixels -> `pixel_hash`.
Every operation here takes an optional `root` (default `config.DRAFTS_ROOT`, read at call time). Writes are all-or-nothing (a staged `.tmp-*` directory renamed into place).
"""

from __future__ import annotations

import os
import re
import secrets
import shutil
from dataclasses import dataclass
from pathlib import Path

from visual_assets.store import config, pixels, records
from visual_assets.store.catalog.registry import Registry, load_registry
from visual_assets.store.contracts import DraftSet, IntakeResult, SetAdoptionRecord, canonical_json, parse_record, record_bound
from visual_assets.store.contracts.base import IntakeVerdict
from visual_assets.store.contracts.draft import DraftEntry, DroppedDraft
from visual_assets.store.errors import ContractError, DraftError, IdentityError, IntakeError, PngDecodeError, RegistryError, StageError
from visual_assets.store.identities import DraftSetId, SourceAssetId, SourceRevision, check
from visual_assets.store.intake import quarantine, service, validator

DRAFT_SET_FILE = "draft_set.json"
ENTRY_FILES = (quarantine.PACKAGE_FILE, quarantine.SOURCE_FILE, quarantine.PREVIEW_FILE, quarantine.RESULT_FILE)
_ID = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}")
_ENTRY_DIR = re.compile(r"in-[0-9a-f]{16}")


@dataclass(frozen=True)
class DraftFinding:
    code: str
    path: str
    detail: str


@dataclass(frozen=True)
class EntryFiles:
    package: bytes
    source: bytes
    preview: bytes
    result_bytes: bytes
    result: IntakeResult


def _root(root: Path | None) -> Path:
    return Path(root) if root is not None else config.DRAFTS_ROOT


def set_dir(set_id: str, root: Path | None = None) -> Path:
    return _root(root) / set_id


def list_set_ids(root: Path | None = None) -> list[str]:
    base = _root(root)
    if not base.is_dir() or base.is_symlink():
        return []
    return sorted(p.name for p in base.iterdir() if p.is_dir() and not p.is_symlink() and _ID.fullmatch(p.name))


def load_set(set_id: str, root: Path | None = None) -> tuple[DraftSet, bytes]:
    """The parsed DraftSet and its exact bytes. Raises `DraftError` when the set is missing or unreadable."""
    path = set_dir(set_id, root) / DRAFT_SET_FILE
    try:
        data = records.read_file(path, record_bound(DraftSet))
        record = parse_record(DraftSet, data)
    except StageError as exc:
        raise DraftError("unknown_set" if exc.code in {"missing_file", "not_found"} else "set_unreadable", f"draft set {set_id}: {exc.code}") from None
    except ContractError as exc:
        raise DraftError("set_invalid", f"draft set {set_id} does not parse ({exc.code})") from None
    if record.set_id != set_id:
        raise DraftError("set_id_mismatch", f"{path.parent.name}/{DRAFT_SET_FILE} names the set {record.set_id!r}")
    return record, data


def read_entry(set_id: str, entry: DraftEntry, root: Path | None = None) -> EntryFiles:
    """Read one entry's four files and check the whole chain; raises `DraftError` with a stable code on the first break."""
    directory = set_dir(set_id, root) / entry.draft_id
    try:
        files = quarantine.read_directory(directory, extra_allowed=(quarantine.RESULT_FILE,))
        result_bytes = quarantine.read_one(directory, quarantine.RESULT_FILE)
    except StageError as exc:
        raise DraftError("entry_unreadable", f"{entry.draft_id}: its files cannot be read safely ({exc.code})") from None
    if validator.file_hash(result_bytes) != entry.intake_hash:
        raise DraftError("intake_hash_mismatch", f"{entry.draft_id}: intake_result.json differs from the hash the draft set holds")
    try:
        result = parse_record(IntakeResult, result_bytes)
    except ContractError as exc:
        raise DraftError("intake_result_invalid", f"{entry.draft_id}: intake_result.json does not parse ({exc.code})") from None
    if result.intake_id != entry.draft_id or result.verdict is not IntakeVerdict.PASSED:
        raise DraftError("intake_result_mismatch", f"{entry.draft_id}: its intake result is not a PASSED result for this intake")
    staged = {quarantine.PACKAGE_FILE: validator.file_hash(files.package), quarantine.SOURCE_FILE: validator.file_hash(files.source),
              quarantine.PREVIEW_FILE: validator.file_hash(files.preview)}
    if {f.name: f.file_hash for f in result.staged_files} != staged or staged[quarantine.PACKAGE_FILE] != result.package_hash:
        raise DraftError("staged_bytes_changed", f"{entry.draft_id}: a staged file differs from the hash its intake result recorded")
    try:
        if pixels.pixel_hash(files.preview, max_dim=config.MAX_PREVIEW_DIM) != entry.pixel_hash:
            raise DraftError("pixel_hash_mismatch", f"{entry.draft_id}: the preview's pixels differ from the draft set's pixel_hash")
    except PngDecodeError as exc:
        raise DraftError("preview_undecodable", f"{entry.draft_id}: the preview cannot be decoded ({exc.code})") from None
    return EntryFiles(files.package, files.source, files.preview, result_bytes, result)


def check_not_revoked(intake_id: str) -> None:
    """A draft whose intake was revoked, in the catalog (an intake-target revocation record) or locally in the quarantine, is never adoptable. Raises `DraftError`."""
    try:
        for revocation in records.all_revocations():
            target = revocation.target
            if getattr(target, "kind", "") == "intake" and target.intake_id == intake_id:  # type: ignore[union-attr]
                raise DraftError("intake_revoked", f"{intake_id} was revoked ({revocation.revocation_id})")
    except (StageError, ContractError) as exc:
        raise DraftError("catalog_unreadable", f"revocations could not be read ({getattr(exc, 'code', 'error')})") from None
    if records.intake_revoked_locally(intake_id):
        raise DraftError("intake_revoked", f"{intake_id} was revoked on this machine")


def _declared(registry: Registry, visual_key: str, detail: str | None) -> str | None:
    """The slot value, or raises `DraftError` when the key or value is not declared."""
    definition = registry.keys.get(visual_key)
    if definition is None:
        raise DraftError("unknown_visual_key", f"{visual_key} is not in the registry")
    if detail is not None:
        if definition.detail is None:
            raise DraftError("detail_not_declared", f"{visual_key} declares no detail axis, so it takes no detail value")
        if detail not in definition.detail.values:
            raise DraftError("unknown_detail_value", f"{detail!r} is not one of the declared detail values of {visual_key}: {', '.join(definition.detail.values)}")
    return definition.effective_detail(detail)


def default_source_asset_id(visual_key: str, detail: str | None) -> str:
    """The key with dots as underscores, plus `_<detail>` when a detail value is named (e.g. `terrain.forest` + `bush` -> `terrain_forest_bush`)."""
    return visual_key.replace(".", "_") + (f"_{detail}" if detail is not None else "")


def _write_new_dir(parent: Path, files: dict[str, bytes]) -> Path:
    staging = parent / f"{quarantine.TEMP_PREFIX}{secrets.token_hex(6)}"
    os.mkdir(staging, 0o755)
    try:
        for name, data in files.items():
            quarantine.write_new(staging / name, data)
            os.chmod(staging / name, 0o644)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return staging


def _check_revises(source_asset_id: str, parent_revision: str, catalog_sources: set[str], definition, detail: str | None) -> None:
    """`draft keep --revises`: the source asset exists, the named revision is its latest unrevoked one, and the draft is for the slot that revision was adopted for."""
    try:
        check(SourceRevision, parent_revision)
    except IdentityError:
        raise DraftError("invalid_parent", "a revision looks like r0001") from None
    if source_asset_id not in catalog_sources:
        raise DraftError("unknown_source_asset", f"{source_asset_id} is not a source asset in the catalog, so there is nothing to revise; drop --revises to draft a new one")
    try:
        revoked = records.revoked_revisions(source_asset_id)
        live = [r for r in records.list_revisions(source_asset_id) if r not in revoked]
        parent_slot = records.revision_slot(source_asset_id, parent_revision) if parent_revision in live else None
    except (StageError, ContractError) as exc:
        raise DraftError("catalog_unreadable", f"existing records could not be read ({getattr(exc, 'code', 'error')})") from None
    if not live or parent_revision != live[-1]:
        raise DraftError("parent_not_latest_unrevoked", f"{parent_revision} is not the latest unrevoked revision of {source_asset_id}" + (f" ({live[-1]})" if live else " (every revision is revoked)"))
    key, parent_detail = parent_slot  # type: ignore[misc]
    if key != definition.key or definition.effective_detail(parent_detail) != definition.effective_detail(detail):
        raise DraftError("revision_changes_slot", f"{source_asset_id} {parent_revision} was adopted for {key}{'' if parent_detail is None else ' [' + parent_detail + ']'}; a revision keeps its slot")


def keep(
    intake_id: str,
    *,
    set_id: str,
    visual_key: str,
    detail: str | None = None,
    source_asset_id: str | None = None,
    replace: bool = False,
    parent_revision: str | None = None,
    registry: Registry | None = None,
    root: Path | None = None,
) -> DraftEntry:
    """Keep a PASSED, unrevoked intake as a draft in `set_id` under `visual_key` (and `detail`). Raises `DraftError`; writes nothing on refusal.

    `parent_revision` (ADR D22, `draft keep --revises`): the draft is the NEXT revision of the existing source asset `source_asset_id`; that revision must be its latest unrevoked one and the
    draft must name the slot it was adopted for. Without it an existing source asset id is still refused."""
    try:
        check(DraftSetId, set_id)
    except IdentityError:
        raise DraftError("invalid_set_id", "a set id is lowercase letters, digits, - and _ (at most 64)") from None
    source_asset_id = source_asset_id if source_asset_id is not None else default_source_asset_id(visual_key, detail)
    try:
        check(SourceAssetId, source_asset_id)
    except IdentityError:
        raise DraftError("invalid_source_asset_id", f"{source_asset_id!r} is not a valid source asset id (give one with --source-asset-id)") from None
    try:
        result = service.show(intake_id)
    except IntakeError as exc:
        raise DraftError(exc.code, exc.message) from None
    if result.verdict is not IntakeVerdict.PASSED:
        raise DraftError("intake_not_passed", f"{intake_id} is {result.verdict.value}; only a PASSED intake can be kept")
    if records.intake_revoked_locally(intake_id):
        raise DraftError("intake_revoked", f"{intake_id} was revoked")
    try:
        known = registry if registry is not None else load_registry()
    except RegistryError as exc:
        raise DraftError("registry_unreadable", str(exc)) from None
    slot = _declared(known, visual_key, detail)

    directory = config.QUARANTINE_ROOT / intake_id
    try:
        files = quarantine.read_directory(directory, extra_allowed=quarantine.EXTRA_FILES)
        result_bytes = quarantine.read_one(directory, quarantine.RESULT_FILE)
    except StageError as exc:
        raise DraftError("staged_bytes_unreadable", f"the staged files of {intake_id} cannot be read safely ({exc.code})") from None
    staged = {quarantine.PACKAGE_FILE: validator.file_hash(files.package), quarantine.SOURCE_FILE: validator.file_hash(files.source),
              quarantine.PREVIEW_FILE: validator.file_hash(files.preview)}
    if {f.name: f.file_hash for f in result.staged_files} != staged:
        raise DraftError("staged_bytes_changed", f"the staged bytes of {intake_id} no longer match the recorded intake hashes")
    try:
        pixel_hash = pixels.pixel_hash(files.preview, max_dim=config.MAX_PREVIEW_DIM)
    except PngDecodeError as exc:
        raise DraftError("preview_undecodable", f"the preview cannot be decoded ({exc.code})") from None

    try:
        loaded = load_set(set_id, root)[0] if (set_dir(set_id, root) / DRAFT_SET_FILE).exists() else None
        existing = list(loaded.entries) if loaded is not None else []
        prior_dropped = loaded.dropped if loaded is not None else ()
        catalog_sources = set(records.list_source_ids())
    except (ContractError, StageError) as exc:
        raise DraftError("catalog_unreadable", f"existing records could not be read ({getattr(exc, 'code', 'error')})") from None
    definition = known.keys[visual_key]
    same_slot = [e for e in existing if e.visual_key == visual_key and definition.effective_detail(e.detail) == slot]
    if same_slot and not replace:
        raise DraftError("slot_taken_in_set", f"{set_id} already has a draft for this slot ({same_slot[0].draft_id}); pass --replace to replace it")
    kept = [e for e in existing if e not in same_slot]
    if any(e.draft_id == intake_id for e in kept):
        raise DraftError("draft_exists", f"{intake_id} is already kept in {set_id} under another slot")
    if parent_revision is not None:
        _check_revises(source_asset_id, parent_revision, catalog_sources, definition, detail)
    elif source_asset_id in catalog_sources:
        raise DraftError("source_asset_exists", f"{source_asset_id} is already a source asset in the catalog; give another with --source-asset-id, or --revises rNNNN to draft its next revision")
    if any(e.source_asset_id == source_asset_id for e in kept):
        raise DraftError("source_asset_in_set", f"{source_asset_id} is already used by another entry of {set_id}; give another with --source-asset-id")
    if len(kept) + 1 > config.MAX_DRAFT_SET_ENTRIES:
        raise DraftError("set_full", f"a draft set holds at most {config.MAX_DRAFT_SET_ENTRIES} entries")

    entry = DraftEntry(visual_key=visual_key, detail=detail, source_asset_id=source_asset_id, draft_id=intake_id, pixel_hash=pixel_hash,
                       intake_hash=validator.file_hash(result_bytes), parent_revision=parent_revision)
    entries = sorted([*kept, entry], key=lambda e: (e.visual_key, e.detail or ""))
    dropped = tuple(x for x in prior_dropped if x.draft_id != intake_id)  # keeping a dropped draft again takes it out of the drop list
    try:
        data = canonical_json(DraftSet(record_type="draft_set", schema_version=1, set_id=set_id, entries=tuple(entries), dropped=dropped))
    except (ContractError, ValueError) as exc:
        raise DraftError("set_invalid", f"the resulting draft set is not valid ({getattr(exc, 'code', 'error')})") from None

    base = _root(root)
    base.mkdir(parents=True, exist_ok=True)
    target = set_dir(set_id, root)
    target.mkdir(exist_ok=True)
    staging = _write_new_dir(base, {quarantine.PACKAGE_FILE: files.package, quarantine.SOURCE_FILE: files.source,
                                    quarantine.PREVIEW_FILE: files.preview, quarantine.RESULT_FILE: result_bytes})
    placed = target / intake_id
    temp_set = target / f"{quarantine.TEMP_PREFIX}set-{secrets.token_hex(4)}"
    try:
        os.rename(staging, placed)
    except OSError:
        shutil.rmtree(staging, ignore_errors=True)
        raise DraftError("draft_exists", f"{intake_id} is already kept in {set_id}") from None
    try:
        quarantine.write_new(temp_set, data)
        os.chmod(temp_set, 0o644)
        os.replace(temp_set, target / DRAFT_SET_FILE)
    except BaseException:
        temp_set.unlink(missing_ok=True)
        shutil.rmtree(placed, ignore_errors=True)
        raise
    for old in same_slot:  # replaced entries go only after the new set record is in place
        shutil.rmtree(target / old.draft_id, ignore_errors=True)
    return entry


def _set_adoptions_of(set_id: str) -> list[str]:
    """Ids of the set adoption records that name `set_id` (an adopted set is never altered)."""
    found: list[str] = []
    folder = records.set_adoptions_dir()
    if folder.is_dir():
        for path in sorted(folder.glob("sa-*.json")):
            record, _ = records.parse_file(SetAdoptionRecord, path)
            if record.set_id == set_id:  # type: ignore[union-attr]
                found.append(path.stem)
    return found


def drop(set_id: str, *, visual_key: str, detail: str | None = None, reason: str, registry: Registry | None = None, root: Path | None = None) -> DroppedDraft:
    """Remove the draft of one slot from `set_id` and record it in the set (`dropped`, ADR D22). Raises `DraftError`; writes nothing on refusal.

    It records no approval and has no MCP tool, like `keep`; it can only REDUCE what a human is later asked to adopt. The set file changes, so its hash changes: a review of the old hash no
    longer describes this set, and `adopt-set` shows the new hash. A set that has a set adoption record is never altered, and neither is an entry whose draft was adopted (per slot)."""
    try:
        check(DraftSetId, set_id)
    except IdentityError:
        raise DraftError("invalid_set_id", "a set id is lowercase letters, digits, - and _ (at most 64)") from None
    try:
        known = registry if registry is not None else load_registry()
    except RegistryError as exc:
        raise DraftError("registry_unreadable", str(exc)) from None
    slot = _declared(known, visual_key, detail)
    record, _ = load_set(set_id, root)
    definition = known.keys[visual_key]
    match = [e for e in record.entries if e.visual_key == visual_key and definition.effective_detail(e.detail) == slot]
    if not match:
        raise DraftError("unknown_slot", f"{set_id} has no draft for {visual_key}{'' if slot is None else ' [' + slot + ']'}")
    entry = match[0]
    try:
        adopted_as = _set_adoptions_of(set_id)
        adoption_of_entry = records.find_adoption_for_intake(entry.draft_id)
    except (ContractError, StageError) as exc:
        raise DraftError("catalog_unreadable", f"existing records could not be read ({getattr(exc, 'code', 'error')})") from None
    if adopted_as:
        raise DraftError("set_adopted", f"{set_id} was adopted ({adopted_as[0]}); an adopted set is never altered")
    if adoption_of_entry is not None:
        raise DraftError("entry_adopted", f"{entry.draft_id} was adopted as {adoption_of_entry.source_asset_id} {adoption_of_entry.source_revision}; an adopted draft is not dropped")
    if len(record.dropped) >= config.MAX_DROPPED_DRAFTS:
        raise DraftError("too_many_drops", f"{set_id} already records {config.MAX_DROPPED_DRAFTS} drops, the most a set holds")
    try:
        dropped = DroppedDraft(visual_key=entry.visual_key, detail=entry.detail, draft_id=entry.draft_id, reason=reason)
    except ValueError:
        raise DraftError("invalid_reason", "give a short plain-text reason (1 to 80 characters, no control characters, no leading or trailing space)") from None
    try:
        data = canonical_json(DraftSet(record_type="draft_set", schema_version=1, set_id=set_id, entries=tuple(e for e in record.entries if e is not entry), dropped=(*record.dropped, dropped)))
    except (ContractError, ValueError) as exc:
        raise DraftError("set_invalid", f"the resulting draft set is not valid ({getattr(exc, 'code', 'error')})") from None
    target = set_dir(set_id, root)
    temp_set = target / f"{quarantine.TEMP_PREFIX}set-{secrets.token_hex(4)}"
    try:
        quarantine.write_new(temp_set, data)
        os.chmod(temp_set, 0o644)
        os.replace(temp_set, target / DRAFT_SET_FILE)
    except BaseException:
        temp_set.unlink(missing_ok=True)
        raise
    shutil.rmtree(target / entry.draft_id, ignore_errors=True)  # the set record is in place first, so a failure here leaves a stray folder `verify` reports, never a half-dropped set
    return dropped


def verify_set(set_id: str, *, registry: Registry | None = None, root: Path | None = None) -> list[DraftFinding]:
    """Every finding for one set (empty = clean): the chain of every entry, declared keys and values, no stray files."""
    out: list[DraftFinding] = []
    directory = set_dir(set_id, root)
    try:
        record, _ = load_set(set_id, root)
    except DraftError as exc:
        return [DraftFinding(exc.code, f"{set_id}/{DRAFT_SET_FILE}", exc.message)]
    try:
        known = registry if registry is not None else load_registry()
    except RegistryError as exc:
        known = None
        out.append(DraftFinding("registry_unreadable", set_id, str(exc)))
    expected = {DRAFT_SET_FILE, *(e.draft_id for e in record.entries)}
    for entry in sorted(directory.iterdir(), key=lambda p: p.name):
        if entry.name not in expected:
            out.append(DraftFinding("stray_file", f"{set_id}/{entry.name}", "not part of the draft set"))
    seen: dict[tuple[str, str | None], str] = {}
    for entry in record.entries:
        where = f"{set_id}/{entry.draft_id}"
        if known is not None:
            definition = known.keys.get(entry.visual_key)
            slot = (entry.visual_key, definition.effective_detail(entry.detail) if definition is not None else entry.detail)
            if slot in seen:
                out.append(DraftFinding("duplicate_slot", where, f"fills the same slot as {seen[slot]}"))
            seen.setdefault(slot, entry.draft_id)
            try:
                _declared(known, entry.visual_key, entry.detail)
            except DraftError as exc:
                out.append(DraftFinding(exc.code, where, exc.message))
        try:
            read_entry(set_id, entry, root)
            check_not_revoked(entry.draft_id)
        except DraftError as exc:
            out.append(DraftFinding(exc.code, where, exc.message))
    return out


def verify_all(*, registry: Registry | None = None, root: Path | None = None) -> list[DraftFinding]:
    out: list[DraftFinding] = []
    base = _root(root)
    if base.is_dir() and not base.is_symlink():
        for entry in sorted(base.iterdir(), key=lambda p: p.name):
            if not entry.is_dir() or entry.is_symlink() or not _ID.fullmatch(entry.name):
                if entry.name not in {".gitkeep", "README.md"}:
                    out.append(DraftFinding("stray_file", entry.name, "not a draft set directory"))
    for set_id in list_set_ids(root):
        out += verify_set(set_id, registry=registry, root=root)
    return out
