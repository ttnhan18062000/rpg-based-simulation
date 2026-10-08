"""The one-colour silhouette sheet: proposals are well-formed, the committed copy equals a fresh build, and the numbers are the rule's and the look-alike report's own (`TCK-20261008-VISUAL-ASSETS-ICON-OWNER-FIXES`)."""

from __future__ import annotations

import copy
import json

import pytest

from tests.visual_assets import icon_lookalikes as la
from tests.visual_assets import icon_sheet_rule as rule
from tests.visual_assets import icon_silhouette_sheet as ss
from tests.visual_assets import icon_specs

# the ruins arch and the tent camp were taken off the sheet when the owner kept the adopted versions ("Keep current versions", 2026-10-08)
SLOTS = ["icon.rarity.common", "icon.status.frame_buff", "icon.class.rogue", "icon.item.tool"]


def test_the_committed_sheet_equals_a_fresh_build():
    assert ss.COMMITTED.read_text() == ss.text(ss.build()), "regenerate: python -m tests.visual_assets.icon_silhouette_sheet --write"


def test_every_changed_slot_is_a_registered_icon_with_its_current_silhouette_and_at_least_one_option():
    sheet = ss.build()
    assert [s["key"] for s in sheet["slots"]] == SLOTS
    registered = set(icon_specs.registered_icon_keys())
    sprites = la.all_icon_sprites()
    for slot in sheet["slots"]:
        assert slot["key"] in registered and slot["options"]
        assert slot["current_rows"] == ss.rows_of(sprites[slot["key"]])  # the adopted r0001, from the kept drafts
        for opt in slot["options"]:
            assert opt["size"] == slot["size"] and len(opt["rows"]) == slot["size"]
            assert all(set(r) <= {"#", "."} for r in opt["rows"])  # one colour: a pixel or nothing
    assert [o["tag"] for o in next(s for s in sheet["slots"] if s["key"] == "icon.class.rogue")["options"]] == ["A", "B"]


def test_the_numbers_are_the_rules_own_measures():
    sheet = ss.build()
    sprites = la.all_icon_sprites()
    slot = next(s for s in sheet["slots"] if s["key"] == "icon.status.frame_buff")
    opt = slot["options"][0]
    mine = ss.sprite_of(opt["rows"])
    assert opt["i1_same_size_neighbours_xor_px"]["icon.status.frame_debuff"] == rule.shape_distance(mine, sprites["icon.status.frame_debuff"])
    near = opt["nearest_in_any_family_xor_px_of_576"][0]
    assert near["xor_px"] == la.distance(la.normalised(mine), la.normalised(sprites[near["key"]]))
    assert opt["nearest_in_any_family_xor_px_of_576"][0]["xor_px"] <= opt["nearest_in_any_family_xor_px_of_576"][1]["xor_px"]


def test_a_proposal_whose_rows_are_not_square_or_not_the_declared_size_is_refused(tmp_path):
    import yaml

    data = ss.load_proposals()
    bad = copy.deepcopy(data)
    bad["slots"]["icon.item.tool"]["options"]["A"]["rows"][3] = "#" * 5
    path = tmp_path / "p.yaml"
    path.write_text(yaml.safe_dump(bad))
    with pytest.raises(AssertionError):
        ss.load_proposals(path)
    wrong_size = copy.deepcopy(data)
    wrong_size["slots"]["icon.item.tool"]["options"]["A"]["size"] = 16
    path.write_text(yaml.safe_dump(wrong_size))
    with pytest.raises(AssertionError):
        ss.load_proposals(path)


def test_a_stale_committed_copy_is_detected():
    sheet = json.loads(ss.COMMITTED.read_text())
    sheet["slots"][0]["options"][0]["rows"][4] = "#" * 16
    assert ss.text(sheet) != ss.text(ss.build())
