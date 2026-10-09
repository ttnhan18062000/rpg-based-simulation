"""Every icon has a spec before it is drawn, the specs are consistent, and the style guide's table is the one generated from them (`TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS`)."""

from __future__ import annotations

import copy

import pytest
import yaml

from visual_assets.review import icon_specs as specs
from visual_assets.review.pilot_colour_vision import REPO

GUIDE = REPO / "docs" / "assets" / "icon_style_guide.md"


def test_there_is_one_complete_consistent_spec_for_every_registered_icon_key():
    loaded = specs.load()
    assert specs.problems(loaded, specs.registered_icon_keys()) == []
    assert len(loaded) == 36 and {s.status for s in loaded.values()} == {"v2", "adopted", "revision"}
    assert sum(1 for s in loaded.values() if s.status == "v2") == 17  # the 22 v2 icons minus the five that are now revisions (the ruins stay as adopted)
    assert sorted(k for k, s in loaded.items() if s.status == "revision") == sorted(["icon.rarity.common", "icon.status.frame_buff", "icon.class.rogue", "icon.item.tool", "icon.building.hero_house", "icon.status.frame_debuff", "icon.building.inn"])  # the owner kept the adopted ruins and enemy camp; theme fit added the house, the debuff frame and the inn


def test_the_style_guide_contains_the_generated_table_verbatim():
    assert specs.table(specs.load()) in GUIDE.read_text(), "regenerate: python -m visual_assets.review.icon_specs --table"


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


def test_every_spec_has_a_theme_and_modern_lookalikes_and_the_loader_refuses_a_spec_without_them(tmp_path):
    loaded = specs.load()
    assert all(s.theme and s.modern_lookalikes for s in loaded.values())
    assert all(s.theme.lower().startswith(specs.THEME_PREFIXES) for s in loaded.values())
    raw = yaml.safe_load(specs.SPECS_FILE.read_text())
    for field in ("theme", "modern_lookalikes_to_avoid"):
        broken = copy.deepcopy(raw)
        del broken["icons"]["icon.item.weapon"][field]
        path = tmp_path / "specs.yaml"
        path.write_text(yaml.safe_dump(broken))
        with pytest.raises(ValueError, match=field):
            specs.load(path)


def test_a_spec_that_describes_a_modern_object_or_an_unthemed_icon_is_refused_but_the_lookalike_fields_may_name_them(tmp_path):
    raw = yaml.safe_load(specs.SPECS_FILE.read_text())
    registered = specs.registered_icon_keys()
    toolbox = copy.deepcopy(raw)
    toolbox["icons"]["icon.item.tool"]["subject"] = "a toolbox"  # the owner rejected it as a modern suitcase
    path = tmp_path / "specs.yaml"
    path.write_text(yaml.safe_dump(toolbox))
    assert any("modern object" in p and "toolbox" in p for p in specs.problems(specs.load(path), registered))
    unthemed = copy.deepcopy(raw)
    unthemed["icons"]["icon.item.weapon"]["theme"] = "a shiny new object"
    path.write_text(yaml.safe_dump(unthemed))
    assert any("theme must start" in p for p in specs.problems(specs.load(path), registered))
    assert specs.problems(specs.load(), registered) == []  # the real specs name wrenches and suitcases only as lookalikes to avoid
    assert any("wrench" in " ".join(s.modern_lookalikes) for s in specs.load().values())


def test_the_style_guide_states_the_theme_and_the_adr_has_d21():
    guide = GUIDE.read_text()
    assert "## Theme (D21" in guide and "Medieval fantasy plus magic" in guide and "Nothing modern" in guide
    adr = (REPO / "docs" / "architecture" / "visual_asset_foundation_adr.md").read_text()
    assert "| D21 |" in adr and "Hammer and tongs" in adr and "Medieval fantasy + magic" in adr
