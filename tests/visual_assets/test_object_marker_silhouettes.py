"""The object-marker silhouettes (`TCK-20261013-VISUAL-ASSETS-OBJECT-MARKER-DRAFTS`): one slot per new key, well-formed rows, a deterministic review sheet."""

from __future__ import annotations

import yaml

from tools import visual_assets_object_marker_sheet as sheet
from visual_assets.review import icon_specs

NEW_KEYS = {
    "icon.building.healer_hut", "icon.building.town_hall", "icon.building.mine_entrance", "icon.building.watchtower", "icon.marker.nest",
    "icon.node.wood_node", "icon.node.herb_patch", "icon.node.berry_thicket", "icon.node.healing_flower_patch", "icon.node.cover_patch_high", "icon.node.cover_patch_medium",
    "icon.node.cover_patch_low", "icon.node.iron_vein", "icon.node.silver_vein", "icon.node.crystal_outcrop", "icon.node.frost_shard_cluster", "icon.node.spirit_wisp", "icon.node.moon_resin_tree",
}


def test_every_new_key_has_a_silhouette_slot_and_a_spec():
    slots = sheet.load()
    assert set(slots) == NEW_KEYS
    assert NEW_KEYS <= set(icon_specs.load())
    assert all(slot["size"] == icon_specs.load()[key].size for key, slot in slots.items())


def test_a_slot_with_two_options_is_a_building_the_owner_chooses_between():
    slots = sheet.load()
    assert {k for k, s in slots.items() if len(s["options"]) > 1} == {"icon.building.town_hall", "icon.building.mine_entrance"}


def test_the_sheets_are_byte_identical_on_two_runs(tmp_path):
    first = sheet.build(tmp_path / "a")
    second = sheet.build(tmp_path / "b")
    assert first == second == ["01_nodes_and_nest.png", "02_buildings.png"]
    for name in first:
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes()


def test_a_malformed_row_is_refused(tmp_path):
    data = yaml.safe_load(sheet.SILHOUETTES.read_text())
    key = "icon.node.wood_node"
    data["slots"][key]["options"]["A"][0] = "#" * 11
    path = tmp_path / "s.yaml"
    path.write_text(yaml.safe_dump(data))
    try:
        sheet.load(path)
    except ValueError as exc:
        assert key in str(exc)
    else:
        raise AssertionError("a short row was accepted")
