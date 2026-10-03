"""Package one exact drawing revision as a `CandidateHandoffPackage` for the store's intake.

Writes only inside the experiment workspace (`<workspace>/handoffs/<handoff_id>/`, where `handoff_id` is `<candidate_id>--<12 hex of sha256 of package.json>`): `package.json`, `source.aseprite`
(the revision's exact bytes) and `preview.png`. It never touches the asset store; getting the package into quarantine is a
separate, explicit `python -m visual_assets.store intake <dir>`. Provenance is filled from what the tools actually know
(adapter version, Aseprite version, Lua pin) and is an explicit `UNAVAILABLE`/`NOT_APPLICABLE` otherwise, never invented.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
from pathlib import Path

from visual_assets.drawing import __version__, api, config
from visual_assets.drawing.errors import AdapterError
from visual_assets.store.contracts import CandidateHandoffPackage, ContractError, canonical_json, parse_record
from visual_assets.store.contracts.handoff import HANDOFF_ASSERTION

PREVIEW_SCALE = 8
HANDOFF_ID = re.compile(r"cand-[0-9a-f]{16}--[0-9a-f]{12}")
FILES = ("package.json", "source.aseprite", "preview.png")


def _handoffs_root() -> Path:
    root = config.WORKSPACE / "handoffs"
    if root.is_symlink():
        raise AdapterError("the handoffs directory is a symlink; refusing to use it")
    return root


def handoff_directory(handoff_id: str) -> Path:
    """The workspace directory of a handoff previously written by `build_handoff`, found ONLY by its id.

    The id must have exactly the shape `build_handoff` returns (`cand-<16 hex>--<12 hex>`), so a path, `..`, a separator or a bare candidate id can never
    select a directory. The result is always `<workspace>/handoffs/<handoff_id>`.
    """
    if not isinstance(handoff_id, str) or not HANDOFF_ID.fullmatch(handoff_id):
        raise AdapterError("a handoff id looks like cand-<16 hex>--<12 hex>: the handoff_id export_handoff returned (a candidate id alone is not enough)")
    directory = _handoffs_root() / handoff_id
    if directory.is_symlink() or not directory.is_dir():
        raise AdapterError(f"no such handoff: {handoff_id}")
    return directory


def _file_hash(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _publish(directory: Path, files: dict[str, bytes]) -> None:
    """Write `files` into a temporary sibling and rename it into place; an existing identical directory is left alone."""
    root = directory.parent
    root.mkdir(parents=True, exist_ok=True)
    temp = root / f".tmp-{directory.name}-{secrets.token_hex(4)}"
    os.mkdir(temp, 0o700)
    try:
        for name, data in files.items():
            with open(temp / name, "xb") as handle:
                handle.write(data)
        os.rename(temp, directory)
    except BaseException:
        shutil.rmtree(temp, ignore_errors=True)
        raise


def _same_files(directory: Path, files: dict[str, bytes]) -> bool:
    if directory.is_symlink() or not directory.is_dir():
        return False
    present = sorted(p.name for p in directory.iterdir())
    if present != sorted(files):
        return False
    return all((directory / n).is_file() and not (directory / n).is_symlink() and (directory / n).read_bytes() == d
               for n, d in files.items())


def build_handoff(
    name: str,
    revision: str,
    *,
    licence_state: str,
    licence_evidence_ref: str,
    brief_id: str,
    review_evidence_ref: str,
    limitations: list[str] | None = None,
) -> dict:
    """Package `name`@`revision`. Rebuilding the same revision with the same inputs is idempotent."""
    rev, source, _ = api.read_revision(name, revision)  # validates the name and verifies the revision hash
    info = api.inspect_sprite(name, rev)
    preview = api.render_preview(name, rev, scale=PREVIEW_SCALE)
    candidate_id = "cand-" + hashlib.sha256(source).hexdigest()[:16]
    number = int(rev[1:])
    data = {
        "record_type": "candidate_handoff_package",
        "schema_version": 1,
        "candidate_id": candidate_id,
        "source_file_name": "source.aseprite",
        "preview_file_name": "preview.png",
        "source_hash": _file_hash(source),
        "source_revision": rev,
        "expected_parent": "NOT_APPLICABLE" if number == 1 else f"r{number - 1:04d}",
        "producer_class": "CAP_A",
        "creator": "UNAVAILABLE",
        "editor": "Aseprite",
        "adapter": f"visual_assets.drawing {__version__} (lua pin {config.LUA_SHA256[:12]})",
        "tool": "Aseprite",
        "tool_version": info["aseprite_version"],
        "source_format": "ASEPRITE",
        "width": info["width"],
        "height": info["height"],
        "frame_count": len(info["frames"]),
        "layer_count": len(info["layers"]),
        "cel_count": info["cels"],
        "tag_count": len(info["tags"]),
        "palette_size": info["palette_size"],
        "preview_hash": _file_hash(preview),
        "brief_id": brief_id,
        "human_review_ref": review_evidence_ref,
        "licence_state": licence_state,
        "licence_evidence_ref": licence_evidence_ref,
        "producer_state": "ACTIVE",
        "producer_validation": "NOT_RUN",
        "declared_limitations": list(limitations or []),
        "assertion": HANDOFF_ASSERTION,
    }
    try:
        package = canonical_json(parse_record(CandidateHandoffPackage, json.dumps(data).encode()))
    except ContractError as exc:
        raise AdapterError(f"handoff rejected ({exc.code}): {exc.message}") from None

    files = {"package.json": package, "source.aseprite": source, "preview.png": preview}
    # H1 (asset-planner): candidate_id identifies the source bytes; the directory also identifies the exact package.json, so a
    # corrected brief or licence statement for the same revision is a new, separate, immutable handoff instead of a permanent refusal.
    handoff_id = f"{candidate_id}--{hashlib.sha256(package).hexdigest()[:12]}"
    directory = _handoffs_root() / handoff_id
    if directory.exists() or directory.is_symlink():
        if not _same_files(directory, files):
            raise AdapterError(f"handoff {handoff_id} already exists with different files (an id collision); nothing was written")
    else:
        try:
            _publish(directory, files)
        except OSError:
            if not _same_files(directory, files):  # a concurrent identical build is fine; anything else is an error
                raise AdapterError("could not write the handoff (storage error); nothing was saved") from None
    return {
        "handoff_id": handoff_id,
        "candidate_id": candidate_id,
        "revision": rev,
        "directory": str(directory),
        "files": list(FILES),
        "source_hash": data["source_hash"],
        "preview_hash": data["preview_hash"],
        "next": "a human or agent may run `python -m visual_assets.store intake <directory>`; this does not adopt anything",
    }
