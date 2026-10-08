"""Every icon has a spec before it is drawn, the specs are consistent, and the style guide's table is the one generated from them (`TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS`)."""

from __future__ import annotations

import copy

import pytest
import yaml

from tests.visual_assets import icon_specs as specs
from tests.visual_assets.pilot_colour_vision import REPO

GUIDE = REPO / "docs" / "assets" / "icon_style_guide.md"


def test_there_is_one_complete_consistent_spec_for_every_registered_icon_key():
    loaded = specs.load()
    assert specs.problems(loaded, specs.registered_icon_keys()) == []
    assert len(loaded) == 36 and {s.status for s in loaded.values()} == {"v2", "adopted", "revision"}
    assert sum(1 for s in loaded.values() if s.status == "v2") == 19  # the 22 v2 icons minus the three that are now revisions (the ruins stay as adopted)
    assert sorted(k for k, s in loaded.items() if s.status == "revision") == sorted(["icon.rarity.common", "icon.status.frame_buff", "icon.class.rogue", "icon.item.tool"])  # the owner kept the adopted ruins and enemy camp


def test_the_style_guide_contains_the_generated_table_verbatim():
    assert specs.table(specs.load()) in GUIDE.read_text(), "regenerate: python -m tests.visual_assets.icon_specs --table"


def test_the_style_guide_states_the_process_rule_steps_in_order():
    text = GUIDE.read_text()
    marks = ["1. **Spec**", "2. **Reference study**", "3. **One-colour silhouette sheet**", "4. **Draw**", "5. **Spec compliance table**", "6. **Checks**", "7. **Owner gate**"]
    positions = [text.index(m) for m in marks]
    assert positions == sorted(positions)


def test_a_missing_key_a_missing_field_and_a_distractor_that_counts_as_correct_are_each_refused(tmp_path):
    raw = yaml.safe_load(specs.SPECS_FILE.read_text())
    loaded = specs.load()
    registered = specs.registered_icon_keys()
    assert specs.problems({k: v for k, v in loaded.items() if k != "icon.item.weapon"}, registered)
    broken = copy.deepcopy(raw)
    del broken["icons"]["icon.item.weapon"]["must_not_read_as"]
    path = tmp_path / "specs.yaml"
    path.write_text(yaml.safe_dump(broken))
    with pytest.raises(ValueError, match="must_not_read_as"):
        specs.load(path)
    clash = copy.deepcopy(raw)
    clash["icons"]["icon.item.weapon"]["distractors"].append("a long sword")
    path.write_text(yaml.safe_dump(clash))
    assert any("would count as a correct answer" in p for p in specs.problems(specs.load(path), registered))


def test_the_rogue_is_not_a_blade_any_more_and_the_enemy_camp_keeps_its_adopted_crossed_swords():
    loaded = specs.load()
    assert "upright" in loaded["icon.item.weapon"].orientation
    rogue = loaded["icon.class.rogue"]
    text = " ".join([rogue.subject, rogue.orientation, rogue.proportions, " ".join(rogue.parts)]).lower()
    assert "dagger" not in text and "sword" not in text and "blade" not in text
    camp = loaded["icon.marker.enemy_camp"]
    assert camp.status == "adopted" and "crossed swords" in camp.subject  # the owner kept the adopted drawing ("Keep current versions", 2026-10-08)
