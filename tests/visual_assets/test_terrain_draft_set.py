"""The committed draft set `terrain-v1` (`TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET`): a draft for every Live Map terrain code except forest, which keeps its adopted slots.

Pure Python. Drafts are unadopted: this ticket adopts nothing, so the catalog's sources stay exactly the three forest tiles.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from visual_assets.store import config, drafts, records
from visual_assets.store.catalog.registry import load_registry

REPO = Path(__file__).resolve().parents[2]
SET = "terrain-v1"


def expected_keys() -> list[str]:
    """The page's explicit code-to-key table is the contract (`frontend/src/visualAssets/terrainDrafts.ts`): 23 keys, one per `TILE_NAMES` code."""
    table = (REPO / "frontend" / "src" / "visualAssets" / "terrainDrafts.ts").read_text()
    keys = re.findall(r"'(terrain\.[a-z_]+)'", table[table.index("TERRAIN_DRAFT_KEYS"):table.index("TERRAIN_CODES")])
    assert len(keys) == len(set(keys)) == 23
    return keys


def terrain_entries(record):
    """The set also holds the nine `border.*` mask drafts (`TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-MASKS`, D19); the terrain tiles are the entries of the `terrain.` family."""
    return [e for e in record.entries if e.visual_key.startswith("terrain.")]


def test_the_committed_set_has_a_draft_for_every_terrain_key_except_forest_and_verifies_clean():
    record, _ = drafts.load_set(SET)
    tiles = terrain_entries(record)
    assert [e.visual_key for e in tiles] == sorted(k for k in expected_keys() if k != "terrain.forest")
    assert len(tiles) == 22 and all(e.detail is None for e in tiles)
    assert len(record.entries) == 22 + 9 and sorted(e.visual_key for e in record.entries if e.visual_key.startswith("border.")) == sorted(
        f"border.{kind}" for kind in ("edge", "inner_corner", "outer_corner") for _ in range(3))
    assert drafts.verify_all() == []  # the whole chain of every entry, declared keys, no revoked intake, no stray files


def test_every_draft_is_an_8x_preview_of_a_16_pixel_tile_with_its_own_source_asset_id():
    record, _ = drafts.load_set(SET)
    assert len({e.source_asset_id for e in record.entries}) == len(record.entries) == 31
    for entry in record.entries:
        files = drafts.read_entry(SET, entry)
        package = json.loads(files.package)
        assert (package["width"], package["height"]) == (16, 16), entry.visual_key
        assert files.preview[:8] == b"\x89PNG\r\n\x1a\n" and entry.source_asset_id == entry.visual_key.replace(".", "_") + (f"_{entry.detail}" if entry.detail else "")


def test_the_drafts_are_unadopted_and_the_keys_are_registered_optional():
    assert records.list_source_ids() == ["terrain_forest", "terrain_forest_bush", "terrain_forest_tree"]  # nothing of the set is in the catalog
    registry = load_registry()
    record, _ = drafts.load_set(SET)
    assert all(registry.keys[e.visual_key].optional for e in record.entries)  # so no release needs them before adoption
    assert config.DRAFTS_ROOT.is_dir() and not str(config.DRAFTS_ROOT).startswith(str(config.CATALOG_ROOT))
