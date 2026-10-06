"""The frontend's committed copy of the icon draft export equals a fresh `draft export` of `icons-key-v1`, modulo the manifest's `registry_hash` (pure Python, no Aseprite).

`draft_set_hash` is the file hash of `draft_set.json` alone (`draftexport.export_draft_preview`), which never holds the registry hash, so ignoring only `registry_hash` is consistent: a key
registration cannot break this guard (the tax `pilot/rc-0006` cost), while a changed PNG byte, set id, `draft_set_hash`, entry or detail still does. The recorded rule result is compared exactly.
Adopting `icons-key-v1` changes the export (the adopted slots it references), so the adoption ticket refreshes the copy.
"""

from __future__ import annotations

import json
import shutil

from tests.visual_assets import icon_draft_fixture as fx
from visual_assets.store.contracts import DraftPreviewManifest, parse_record

REGENERATE = "regenerate the committed copy: `python -m tests.visual_assets.icon_draft_fixture --write`"


def _fresh(tmp_path):
    out = tmp_path / "fresh"
    fx.export_fresh(out)
    return out


def test_the_committed_copy_equals_a_fresh_export_modulo_the_registry_hash(tmp_path):
    assert fx.differences(_fresh(tmp_path)) == [], REGENERATE


def test_the_manifest_is_a_draft_preview_manifest_with_the_14_icons_and_the_adopted_references():
    manifest = parse_record(DraftPreviewManifest, (fx.COMMITTED / fx.MANIFEST).read_bytes())
    assert manifest.set_id == "icons-key-v1" and manifest.draft_set_hash.startswith("sha256:")
    icons = [e for e in manifest.entries if e.visual_key.startswith("icon.")]
    assert len(icons) == 14 and all(not getattr(e, "adopted", False) for e in icons)
    adopted = [e for e in manifest.entries if getattr(e, "adopted", False)]
    assert len(adopted) == 34 and {e.visual_key.split(".")[0] for e in adopted} == {"terrain", "border"}


def test_the_recorded_rule_result_is_the_current_evaluation():
    assert (fx.COMMITTED / fx.RESULT).read_text() == fx.recorded_result_text()
    assert json.loads((fx.COMMITTED / fx.RESULT).read_text())["set_id"] == "icons-key-v1"


def test_a_flipped_png_byte_is_caught(tmp_path):
    copy = tmp_path / "copy"
    shutil.copytree(fx.COMMITTED, copy)
    png = next(p for p in sorted(copy.glob("*.png")))
    data = bytearray(png.read_bytes())
    data[-20] ^= 1
    png.write_bytes(bytes(data))
    problems = fx.differences(_fresh(tmp_path), copy)
    assert any(png.name in p for p in problems)


def test_a_changed_entry_is_caught(tmp_path):
    copy = tmp_path / "copy"
    shutil.copytree(fx.COMMITTED, copy)
    manifest = json.loads((copy / fx.MANIFEST).read_text())
    manifest["entries"][0]["draft_id"] = "in-0000000000000000"
    (copy / fx.MANIFEST).write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")))
    assert any(fx.MANIFEST in p for p in fx.differences(_fresh(tmp_path), copy))


def test_a_changed_registry_hash_alone_is_deliberately_not_caught(tmp_path):
    copy = tmp_path / "copy"
    shutil.copytree(fx.COMMITTED, copy)
    manifest = json.loads((copy / fx.MANIFEST).read_text())
    manifest["registry_hash"] = "sha256:" + "1" * 64
    (copy / fx.MANIFEST).write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")))
    assert fx.differences(_fresh(tmp_path), copy) == []


def test_a_missing_file_is_caught(tmp_path):
    copy = tmp_path / "copy"
    shutil.copytree(fx.COMMITTED, copy)
    next(copy.glob("*.png")).unlink()
    assert any("files differ" in p for p in fx.differences(_fresh(tmp_path), copy))
