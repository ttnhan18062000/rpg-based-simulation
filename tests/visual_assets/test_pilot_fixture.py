"""The frontend's committed copy of the pilot terrain export (the forest's three slots, `pilot/rc-0004`) still equals what the store produces (pure Python, no Aseprite).

The only link between `visual_assets` and `frontend/` is this file-level copy (`TCK-20261004-VISUAL-ASSETS-M5-GAP-CLOSURE`): no import either way.

A fresh `export-runtime` of `pilot/rc-0004` is no longer possible: registering the 14 `icon.*` keys (D20, `TCK-20261006-VISUAL-ASSETS-ICON-KEY-FAMILIES`, user-approved on 2026-10-06) moved the
registry hash and the store refuses the old candidate (`registry_mismatch`, by design). `release` assembles every adopted slot, so no forest-only candidate on the new registry can exist either.
Two checks together replace the single fresh-export check:
1. the fixture's three entries and files equal the forest slots of a FRESH export of `pilot/rc-0006` (key, detail, file names, sizes, PNG bytes; the fixture holds exactly those three slots),
   and only `release_id`, `registry_hash` and the `candidate_manifest_hash` derived from them differ, which is what moved;
2. the fixture's manifest still equals `rc-0004`'s stored candidate (release id, registry hash, slots, pixel hashes, file names), so the "rc-0004: forest only" history the drill relies on is kept.
"""

from __future__ import annotations

import filecmp
import json
from pathlib import Path

from visual_assets.store.runtime_export import export_runtime

REPO = Path(__file__).resolve().parents[2]
COMMITTED = REPO / "frontend" / "src" / "visualAssets" / "__fixtures__" / "pilot"
CANDIDATES = REPO / "visual_assets" / "catalog" / "manifests" / "candidates" / "pilot"
REGENERATE = (
    "the pilot fixture is a frozen copy of rc-0004's export; its forest slots must equal those of a fresh `python -m visual_assets.store export-runtime --catalog-id pilot --release-id rc-0006 --out <dir>` "
    "(rc-0004 itself can no longer be exported)"
)
FOREST = "terrain.forest"


def _forest(manifest: dict) -> tuple[list[dict], list[dict]]:
    return [e for e in manifest["entries"] if e["visual_key"] == FOREST], [d for d in manifest["details"] if d["visual_key"] == FOREST]


def check_fixture_against_fresh_export(fresh: Path, committed: Path = COMMITTED) -> None:
    """Check 1, as a function so a mutant can be pointed at a corrupted copy."""
    fresh_manifest = json.loads((fresh / "runtime_manifest.json").read_text())
    fixture = json.loads((committed / "runtime_manifest.json").read_text())
    fresh_entries, fresh_details = _forest(fresh_manifest)
    assert len(fresh_entries) == 3, "a fresh export must hold the forest's three slots"
    assert fixture["entries"] == fresh_entries and fixture["details"] == fresh_details, f"the fixture's forest slots differ from a fresh export; {REGENERATE}"
    assert {k: v for k, v in fixture.items() if k not in ("entries", "details")} != {k: v for k, v in fresh_manifest.items() if k not in ("entries", "details")}
    changed = {k for k in fixture if k not in ("entries", "details") and fixture[k] != fresh_manifest.get(k)}
    assert changed == {"release_id", "registry_hash", "candidate_manifest_hash"}, f"only the release id, the registry hash and the manifest hash derived from them may differ, got {sorted(changed)}"
    assert sorted(p.name for p in committed.iterdir()) == sorted(["runtime_manifest.json", *(e["file"] for e in fixture["entries"])]), "the fixture holds exactly the three forest slots"
    for entry in fixture["entries"]:
        assert filecmp.cmp(fresh / entry["file"], committed / entry["file"], shallow=False), f"{entry['file']} differs from a fresh export; {REGENERATE}"


def test_the_committed_pilot_export_equals_the_forest_slots_of_a_fresh_export_of_the_release(tmp_path):
    fresh = tmp_path / "export"
    export_runtime("pilot", "rc-0006", fresh)
    check_fixture_against_fresh_export(fresh)


def test_the_committed_pilot_export_still_equals_the_stored_rc_0004_candidate():
    fixture = json.loads((COMMITTED / "runtime_manifest.json").read_text())
    stored = json.loads((CANDIDATES / "rc-0004.json").read_text())
    assert fixture["release_id"] == "rc-0004" and stored["release_id"] == "rc-0004" and fixture["registry_hash"] == stored["registry_hash"]
    assert fixture["catalog_id"] == stored["catalog_id"] == "pilot"
    assert len(stored["entries"]) == 3
    for entry, kept in zip(fixture["entries"], stored["entries"], strict=True):
        assert (entry["visual_key"], entry.get("detail")) == (kept["visual_key"], kept.get("detail"))
        assert entry["pixel_hash"] == kept["pixel_hash"] and entry["file"] == kept["pixel_hash"].removeprefix("pixels-v1:") + ".png"


def test_the_pilot_export_holds_the_three_declared_slots_of_terrain_forest():
    manifest = json.loads((COMMITTED / "runtime_manifest.json").read_text())
    assert [(e["visual_key"], e["detail"], e["family"], e["width"], e["height"]) for e in manifest["entries"]] == [
        ("terrain.forest", "bush", "terrain", 16, 16), ("terrain.forest", "plain", "terrain", 16, 16), ("terrain.forest", "tree", "terrain", 16, 16),
    ]
    # the declared order is what the client picks over (the approved 64 x 64 spread was computed for [plain, bush, tree])
    assert manifest["details"] == [{"visual_key": "terrain.forest", "values": ["plain", "bush", "tree"], "default": "plain"}]
    assert manifest["catalog_id"] == "pilot" and manifest["release_id"] == "rc-0004"


def test_rc_0003_lists_exactly_the_entries_of_rc_0002_so_only_the_registry_moved():
    """`pilot/rc-0003` was assembled only because registering the other 22 terrain keys changed the registry hash (`TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET`,
    planner decision A). Its entries must be the same slots, artifact ids and pixel hashes as rc-0002's, so "the release content is unchanged" is a checked fact."""
    base = REPO / "visual_assets" / "catalog" / "manifests" / "candidates" / "pilot"
    old, new = (json.loads((base / f"{rc}.json").read_text()) for rc in ("rc-0002", "rc-0003"))
    assert new["entries"] == old["entries"] and len(new["entries"]) == 3
    assert new["registry_hash"] != old["registry_hash"] and new["release_id"] == "rc-0003" and new["catalog_id"] == old["catalog_id"]


def test_rc_0004_lists_exactly_the_entries_of_rc_0003_so_only_the_registry_moved():
    """`pilot/rc-0004` was assembled only because registering the three `border.*` mask keys changed the registry hash (`TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-CONTRACT`, D19;
    the user approved assembling it on 2026-10-06). Same slots, artifact ids and pixel hashes as rc-0003's, so "the release content is unchanged" is a checked fact."""
    base = REPO / "visual_assets" / "catalog" / "manifests" / "candidates" / "pilot"
    old, new = (json.loads((base / f"{rc}.json").read_text()) for rc in ("rc-0003", "rc-0004"))
    assert new["entries"] == old["entries"] and len(new["entries"]) == 3
    assert new["registry_hash"] != old["registry_hash"] and new["release_id"] == "rc-0004" and new["catalog_id"] == old["catalog_id"]
