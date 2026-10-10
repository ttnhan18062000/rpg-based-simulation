"""How a committed draft-preview fixture is checked against the store (`TCK-20261009-VISUAL-ASSETS-ICON-RELEASE-CANDIDATE`, planner ruling 2026-10-09).

A draft set the owner has already decided is a CLOSED gate (`adopted_facts.CLOSED_DRAFT_SETS`): its committed fixture is the evidence of what the owner saw. A fresh export also lists a reference for every
adopted slot the set does not hold, and that list grows whenever art is built after the gate (the 36 icons, `pilot/rc-0008`). So a closed set is checked against the gate's own record, not the moving store:

1. the DRAFT entries (not `adopted`) equal the fresh export's draft entries exactly, and every draft PNG is byte-equal to the fresh one;
2. every adopted-REFERENCE entry is byte-equal to the catalog artifact it names (the catalog is append-only, so this stays strict);
3. nothing else: no stray entry, no duplicate slot, no file no entry names;
4. the committed `draft_preview_manifest.json` still hashes to the pin in `CLOSED_DRAFT_SETS` (checks 1-3 prove the record is still TRUE of the store; this proves the record itself was not rewritten, which `icon_draft_fixture --write` would do and 1-3 alone would accept).

It does NOT ask for the references a fresh export would add for art built after the gate. A set that is not pinned (an OPEN draft set) keeps the full fresh-export equality of `icon_draft_fixture.differences`.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tests.visual_assets import adopted_facts as af
from visual_assets.review import icon_draft_fixture as fx
from visual_assets.store import config, records
from visual_assets.store.contracts import ContractError
from visual_assets.store.errors import StageError


def _manifest(directory: Path) -> dict:
    return json.loads((directory / fx.MANIFEST).read_text())


def _reference_problems(entry: dict, committed: Path) -> list[str]:
    name = f"{entry['visual_key']}/{entry.get('detail')}"
    digest = entry["pixel_hash"].split(":", 1)[1]
    sid = entry["source_asset_id"]
    try:
        found = [
            records.load_artifact_for(sid, revision, "x1")
            for revision in records.list_revisions(sid)
            if records.load_source(sid, revision).adoption_id and records.load_adoption(records.load_source(sid, revision).adoption_id).intake_id == entry["draft_id"]
        ]
    except (ContractError, StageError) as exc:  # the store's own errors (an unreadable or missing record) are a failed reference; any other exception is a bug in this checker and must crash the test
        return [f"{fx.MANIFEST}: reference {name} names no readable catalog source {sid} ({type(exc).__name__})"]
    found = [f for f in found if f is not None and f[0].pixel_hash == entry["pixel_hash"]]
    if len(found) != 1:
        return [f"{fx.MANIFEST}: reference {name} names no catalog artifact of {sid} with pixel_hash {entry['pixel_hash']} at the revision adopted from {entry['draft_id']}"]
    artifact, _ = found[0]
    problems = []
    png = records.read_file(records.artifact_paths(artifact.artifact_id, digest, artifact.source_revision)[0], config.MAX_PNG_FILE_BYTES)
    if entry["file"] != digest + ".png" or not (committed / entry["file"]).is_file() or (committed / entry["file"]).read_bytes() != png:
        problems.append(f"{fx.MANIFEST}: reference {name}: {entry['file']} is not byte-equal to the catalog artifact {artifact.artifact_id}")
    if (entry["width"], entry["height"], entry["scale"]) != (artifact.width, artifact.height, 1):
        problems.append(f"{fx.MANIFEST}: reference {name}: size differs from the catalog artifact")
    return problems


def closed_differences(fresh: Path, committed: Path, result_text=fx.recorded_result_text, *, pinned_manifest_sha256: str) -> list[str]:
    problems: list[str] = []
    actual = "sha256:" + hashlib.sha256((committed / fx.MANIFEST).read_bytes()).hexdigest()
    if actual != pinned_manifest_sha256:
        problems.append(f"{fx.MANIFEST}: the committed gate evidence was rewritten (sha256 {actual} is not the pinned {pinned_manifest_sha256})")
    fm, cm = _manifest(fresh), _manifest(committed)
    rest = lambda m: {k: v for k, v in m.items() if k not in ("entries", "registry_hash")}  # noqa: E731 - the registry hash is ignored as in `icon_draft_fixture`
    if rest(fm) != rest(cm):
        problems.append(f"{fx.MANIFEST}: set id, draft_set_hash or details differ")
    fresh_drafts = [e for e in fm["entries"] if not e.get("adopted")]
    committed_drafts = [e for e in cm["entries"] if not e.get("adopted")]
    references = [e for e in cm["entries"] if e.get("adopted")]
    if fresh_drafts != committed_drafts:
        problems.append(f"{fx.MANIFEST}: draft entries differ from a fresh export")
    for entry in committed_drafts:
        mine, theirs = committed / entry["file"], fresh / entry["file"]
        if not mine.is_file() or not theirs.is_file() or mine.read_bytes() != theirs.read_bytes():
            problems.append(f"draft PNG {entry['file']} differs from a fresh export")
    for entry in references:
        problems += _reference_problems(entry, committed)
    slots = [(e["visual_key"], e.get("detail")) for e in cm["entries"]]
    if len(set(slots)) != len(slots):
        problems.append(f"{fx.MANIFEST}: a slot is listed twice")
    named = {e["file"] for e in cm["entries"]}
    have = {p.name for p in committed.iterdir() if p.name not in (fx.MANIFEST, fx.RESULT)}
    if named != have:
        problems.append(f"files differ from the entries' files: only in entries {sorted(named - have)}, only on disk {sorted(have - named)}")
    if (committed / fx.RESULT).read_text() != result_text():
        problems.append(f"{fx.RESULT} differs from a fresh evaluation of the rule")
    return problems


def differences(set_id: str, fresh: Path, committed: Path, result_text=fx.recorded_result_text, closed=af.CLOSED_DRAFT_SETS) -> list[str]:
    """The closed-set check for a pinned set, else the full fresh-export equality."""
    if set_id in closed:
        return closed_differences(fresh, committed, result_text, pinned_manifest_sha256=closed[set_id]["fixture_manifest_sha256"])
    return fx.differences(fresh, committed, result_text)
