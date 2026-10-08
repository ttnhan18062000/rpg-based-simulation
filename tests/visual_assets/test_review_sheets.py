"""Owner review sheets: a deterministic folder of large labelled PNGs and a README for a draft set (`TCK-20261008-VISUAL-ASSETS-REVIEW-SHEET-FOLDER`)."""

from __future__ import annotations

import hashlib
import json
import shutil
import struct

import pytest

from tests.visual_assets import icon_owner_fixes_draft_set as fixes
from tests.visual_assets import icon_specs
from tests.visual_assets import review_sheets as rs
from tests.visual_assets.pilot_colour_vision import REPO
from visual_assets.store import config

SET = fixes.SET_ID


def png_size(data: bytes) -> tuple[int, int]:
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


def digest(folder) -> dict[str, str]:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.iterdir())}


@pytest.fixture(scope="module")
def folder(tmp_path_factory):
    out = tmp_path_factory.mktemp("review") / SET
    info = rs.generate(SET, out)
    return out, info


def test_one_command_writes_the_six_images_and_the_readme_and_only_those(folder):
    out, info = folder
    assert sorted(p.name for p in out.iterdir()) == sorted(rs.FILES)
    for name in rs.FILES[:-1]:
        w, h = png_size((out / name).read_bytes())
        assert w >= 1400 and h >= 250, name  # large canvases, legible at 100 percent
    assert set(info["files"]) == set(rs.FILES) and info["draft_set_hash"].startswith("sha256:")


def test_the_same_drafts_give_the_same_bytes(folder, tmp_path):
    out, _ = folder
    again = tmp_path / "again"
    rs.generate(SET, again)
    assert digest(again) == digest(out)


def test_only_the_four_proposed_drafts_are_shown_and_the_two_declined_ones_are_not_candidates(folder):
    out, info = folder
    assert sorted(info["tiles"]["01_overview"]) == sorted(fixes.PROPOSED)
    assert sorted(info["tiles"]["02_before_after"]) == sorted(fixes.PROPOSED)
    text = (out / "README.txt").read_text()
    assert "NOT PROPOSED" in text and all(k in text for k in fixes.NOT_PROPOSED)
    shown_section = text.split("THE DRAFTS SHOWN")[1].split("NOT PROPOSED")[0]
    assert not any(k in shown_section for k in fixes.NOT_PROPOSED)
    commands = text.split("YOUR COMMANDS")[1]
    assert not any(k in commands for k in fixes.NOT_PROPOSED)


def test_the_readme_holds_what_each_image_shows_the_recorded_results_the_findings_and_the_exact_owner_commands(folder):
    text = (folder[0] / "README.txt").read_text()
    for name in rs.FILES[:-1]:
        assert name in text
    assert "NOTHING IS ADOPTED" in text and "RECORDED RESULTS" in text and "PASS" in text and "FINDINGS FOR YOU" in text
    assert text.count(" review in-") == 4 and text.count(" adopt in-") == 4 and text.count("--parent r0001") == 4
    assert "<your licence decision>" in text and "adopt-set cannot make new revisions" in text
    for e in rs.load_set(SET)[0]:
        if e.key in fixes.PROPOSED:
            assert f"review {e.draft_id}" in text and f"--source-asset-id {e.key.replace('.', '_')} " in text  # the EXISTING source id, not the draft's


def test_a_planted_extra_draft_appears_in_the_overview_and_changes_the_image(tmp_path):
    root = tmp_path / "drafts"
    shutil.copytree(rs.keyset.DRAFTS / SET, root / SET)
    extra = next(p for p in (rs.keyset.DRAFTS / "icons-v2").iterdir() if p.is_dir() and json.loads((rs.keyset.DRAFTS / "icons-v2" / "draft_set.json").read_text())["entries"][0]["draft_id"] == p.name)
    entry = json.loads((rs.keyset.DRAFTS / "icons-v2" / "draft_set.json").read_text())["entries"][0]
    record = json.loads((root / SET / "draft_set.json").read_text())
    shutil.copytree(extra, root / SET / entry["draft_id"])
    record["entries"].append({**entry, "source_asset_id": entry["source_asset_id"] + "_planted"})
    (root / SET / "draft_set.json").write_text(json.dumps(record))
    base, planted = tmp_path / "base", tmp_path / "planted"
    rs.generate(SET, base, root=rs.keyset.DRAFTS)
    info = rs.generate(SET, planted, root=root)
    assert entry["visual_key"] in info["tiles"]["01_overview"]
    assert (planted / "01_overview.png").read_bytes() != (base / "01_overview.png").read_bytes()


def test_a_folder_inside_a_repository_is_refused_and_the_default_is_outside_every_repo(tmp_path):
    with pytest.raises(ValueError, match="outside every repository"):
        rs.generate(SET, REPO / "visual_assets" / "review_try")
    assert REPO not in rs.DEFAULT_ROOT.parents and rs.DEFAULT_ROOT.name == "asset-review"
    assert config.CATALOG_ROOT not in rs.DEFAULT_ROOT.parents


def test_the_font_covers_every_character_the_labels_use():
    chars = set()
    for key in icon_specs.registered_icon_keys():
        chars |= set(key.upper())
    for text in ("ICONS-OWNER-FIXES-V1: OVERVIEW: EVERY PROPOSED DRAFT, TRUE SIZE AND ZOOMED, DARK AND LIGHT PANELS", "SHA256:0123456789ABCDEF...", "24X24 PX, ZOOM 6X", "PROTANOPIA (APPROXIMATION)", "<- ADOPTED R0001"):
        chars |= set(text)
    assert [c for c in sorted(chars) if c not in rs.FONT] == []
    assert all(len(rows) == 7 and all(len(r) == 5 for r in rows) for rows in rs.FONT.values())


def test_canvas_text_and_sprites_are_exact_whole_number_rectangles():
    a, b = rs.Canvas(60, 20), rs.Canvas(60, 20)
    assert a.text(2, 2, "ab 1", rs.INK, 2) == 4 * 6 * 2
    b.text(2, 2, "AB 1", rs.INK, 2)
    assert a.png() == b.png()  # lowercase is drawn as capitals
    assert any(rs.INK == tuple(a.rows[y][x * 3 : x * 3 + 3]) for y in range(20) for x in range(60))
    c = rs.Canvas(10, 10)
    c.rect(-5, -5, 8, 8, (1, 2, 3))  # clipped, never an error
    assert tuple(c.rows[0][0:3]) == (1, 2, 3) and tuple(c.rows[5][0:3]) == rs.PAGE


def test_the_vision_rows_are_real_colours_not_black_and_greyscale_has_equal_channels():
    for vision in ("protan", "deutan", "tritan"):
        out = rs.vision_mapper(vision)((128, 128, 128))
        assert max(out) > 60, vision  # the units bug: simulate works in 0..1
    assert rs.vision_mapper("protan")((72, 184, 88)) != (72, 184, 88)
    g = rs.vision_mapper("grey")((200, 100, 50))
    assert g[0] == g[1] == g[2] and rs.vision_mapper(None) is None


def test_other_draft_sets_generate_too_and_a_set_with_no_markers_says_so(tmp_path):
    info = rs.generate("icons-v2", tmp_path / "v2")
    assert len(info["tiles"]["01_overview"]) == 22
    assert png_size((tmp_path / "v2" / "05_map_markers.png").read_bytes())[1] > 600  # the location glyphs and the map scene
    text = (tmp_path / "v2" / "README.txt").read_text()
    assert text.count("ALREADY ADOPTED") == 22 and " adopt in-" not in text and "adopt-set icons-v2" not in text  # a set the owner already adopted gets no commands to run
    note = rs.generate(SET, tmp_path / "fx")
    assert png_size((tmp_path / "fx" / "05_map_markers.png").read_bytes())[1] < 400 and note["set_id"] == SET  # no location glyph: a note, not an empty map
