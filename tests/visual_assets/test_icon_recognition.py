"""The deterministic parts of the blind recognition check: neutral images, hashes, candidate lists and scoring (`TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS`). The model's answers are evidence, not tested here."""

from __future__ import annotations

import json

from tests.visual_assets import icon_lookalikes as la
from tests.visual_assets import icon_recognition as rec
from tests.visual_assets import icon_specs as specs_mod
from visual_assets.store import pixels

SPECS = specs_mod.load()
SPRITES = la.all_icon_sprites()


def test_specs_are_complete_consistent_and_match_the_registry():
    assert specs_mod.problems(SPECS, specs_mod.registered_icon_keys()) == []
    assert len(SPECS) == 36


def test_images_are_neutral_shuffled_and_reproducible(tmp_path):
    keys = [k for k in SPRITES if k != rec.PLATE_KEY]
    a = rec.build_blind_set(tmp_path / "a", SPRITES, keys, seed=7)
    b = rec.build_blind_set(tmp_path / "b", SPRITES, keys, seed=7)
    c = rec.build_blind_set(tmp_path / "c", SPRITES, keys, seed=8)
    assert a == b and a["answer_key"] != c["answer_key"]
    names = sorted(p.name for p in (tmp_path / "a").iterdir())
    assert names == [f"icon-{n:02d}.png" for n in range(1, len(keys) + 1)]
    assert sorted(a["answer_key"].values()) == sorted(keys)
    assert [a["answer_key"][i] for i in sorted(a["answer_key"])] != sorted(keys)  # shuffled, not in key order


def test_a_rendering_is_a_valid_png_of_the_four_panels_and_a_location_glyph_sits_on_the_plate():
    glyph = rec.render("icon.marker.boss_arena", SPRITES)
    image = pixels.decode_png(glyph, max_dim=1024)
    n = 16 + 4  # native size plus padding on both sides
    assert (image.width, image.height) == (n * (1 + 1 + 4 + 4) + rec.GAP * 3, n * 4)
    plate_only = rec.render("icon.plate.location", SPRITES)
    assert glyph != plate_only
    swords = pixels.decode_png(rec.render("icon.item.weapon", SPRITES), max_dim=1024)
    assert swords.height == (24 + 4) * 4


def test_the_rendering_is_a_pure_function_of_the_sprites_and_a_glyph_differs_from_its_bare_plate():
    assert rec.render("icon.item.weapon", SPRITES) == rec.render("icon.item.weapon", SPRITES)
    assert rec.render("icon.marker.ruins", SPRITES) != rec.render("icon.marker.shrine", SPRITES)


def test_candidate_lists_hold_the_intended_name_once_the_distractors_and_none_last_and_are_seeded():
    spec = SPECS["icon.item.weapon"]
    options = rec.candidates(spec, seed=3)
    assert options.count(spec.subject) == 1 and options[-1] == rec.NONE_OF_THESE
    assert len(options) == 1 + len(spec.distractors) + 1
    assert options == rec.candidates(spec, seed=3) and options != rec.candidates(spec, seed=4)
    assert any("cleaver" in o for o in options)  # the misread that passed every gate is offered as a distractor


def test_free_text_scoring_counts_synonyms_and_flags_a_misread():
    sword = SPECS["icon.item.weapon"]
    assert rec.score_free("A steel Sword", sword)["flagged"] is False
    assert rec.score_free("a broadsword with a gold hilt", sword)["named"] is True
    miss = rec.score_free("a meat cleaver", sword)
    assert miss["flagged"] is True and "cleaver" in miss["confused_with"]
    assert rec.score_free("", sword)["flagged"] is True
    assert rec.score_free("a bell", SPECS["icon.marker.shrine"])["confused_with"] == ["bell"]


def test_synonyms_match_whole_words_so_a_crossbow_is_not_a_bow_and_a_swordfish_is_not_a_sword():
    ranger, sword = SPECS["icon.class.ranger"], SPECS["icon.item.weapon"]
    assert rec.score_free("a crossbow", ranger)["flagged"] is True
    assert rec.score_free("a wooden bow", ranger)["flagged"] is False and rec.score_free("two bows", ranger)["flagged"] is False
    assert rec.score_free("a longbow", ranger)["flagged"] is False  # listed in the spec: the spec decides what counts
    assert rec.score_free("a swordfish", sword)["flagged"] is True and rec.score_free("a steel sword", sword)["flagged"] is False


def test_the_distractor_check_uses_the_same_whole_word_rule_as_the_scoring():
    from tests.visual_assets import icon_specs as sm

    assert sm.has_word("a crossbow", "bow") is False and sm.has_word("a bow and arrow", "bow") is True
    assert "crossbow" in SPECS["icon.class.ranger"].distractors  # the actual misread is offered, and it is not a correct answer


def test_choice_scoring_requires_the_exact_intended_name():
    sword = SPECS["icon.item.weapon"]
    assert rec.score_choice(sword.subject, sword)["correct"] is True
    assert rec.score_choice("a cleaver", sword)["correct"] is False
    assert rec.score_choice(rec.NONE_OF_THESE, sword)["correct"] is False


def test_evaluate_lists_flags_and_misses_and_prompts_name_only_files(tmp_path):
    key_of = {"icon-01": "icon.item.weapon", "icon-02": "icon.marker.shrine"}
    out = rec.evaluate(key_of, {"icon-01": "a cleaver", "icon-02": "an obelisk"}, {"icon-01": "a cleaver", "icon-02": SPECS["icon.marker.shrine"].subject}, SPECS)
    assert out["flagged_free_text"] == ["icon.item.weapon"] and out["missed_in_choice"] == ["icon.item.weapon"]
    assert json.loads(rec.dumps(out)) == out
    prompt = rec.free_prompt(tmp_path, ["icon-02", "icon-01"])
    assert "icon-01.png" in prompt and "weapon" not in prompt and "sword" not in prompt
    cp = rec.choice_prompt(tmp_path, key_of, SPECS, seed=1)
    assert "icon-01.png" in cp and "icon.item" not in cp
