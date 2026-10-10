"""Cross-check the independent pure-Python validator against files written and read by real Aseprite.

The validator and the synthetic builder were written by the same hand, so on their own they could share a misreading
of the format. Here Aseprite itself is the oracle: it writes files the parser must read the same way, and it must be
able to open the files the builder writes. Skipped where Aseprite or bwrap is missing (CI).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.visual_assets.store import builders as b
from visual_assets.drawing import api
from visual_assets.drawing import config as drawing_config
from visual_assets.store.contracts.base import IntakeVerdict
from visual_assets.store.intake import aseprite, intake
from visual_assets.store.intake.validator import file_hash, validate

pytestmark = pytest.mark.needs_aseprite

COUNTS_LUA = """
local spr = app.open("{path}")
if not spr then print("NOT OPENED") return end
print(table.concat({{spr.width, spr.height, #spr.frames, #spr.layers, #spr.cels, #spr.tags, #spr.palettes[1],
                    spr.colorMode == ColorMode.RGB and 1 or 0}}, " "))
"""


@pytest.fixture(autouse=True)
def workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(drawing_config, "WORKSPACE", tmp_path / "ws")
    return tmp_path / "ws"


def aseprite_counts(path: Path, tmp_path: Path) -> tuple[int, ...]:
    script = tmp_path / "counts.lua"
    script.write_text(COUNTS_LUA.format(path=path))
    out = subprocess.run([drawing_config.ASEPRITE, "-b", "--script", str(script)], capture_output=True, text=True, timeout=30)
    assert "NOT OPENED" not in out.stdout, out.stderr
    return tuple(int(x) for x in out.stdout.split())


def facts_tuple(facts: aseprite.AsepriteFacts) -> tuple[int, ...]:
    return (facts.width, facts.height, facts.frames, facts.layers, facts.cels, facts.tags, facts.palette_size,
            1 if facts.color_depth == 32 else 0)


def revision_path(name: str, rev: str) -> Path:
    return drawing_config.WORKSPACE / "sprites" / name / f"{rev}.aseprite"


def build_rich_sprite() -> tuple[str, str]:
    api.new_sprite("hero", 20, 12, "#102030")
    rev = "r0001"
    steps = [
        [{"op": "add_layer", "name": "shade"}, {"op": "add_layer", "name": "hi"}],
        [{"op": "add_frame"}, {"op": "add_frame", "copy_from": 1}],
        [{"op": "add_tag", "name": "idle", "from_frame": 1, "to_frame": 2}, {"op": "add_tag", "name": "walk", "from_frame": 2, "to_frame": 3}],
        [{"op": "pixels", "pixels": [{"x": 1, "y": 1, "color": "#ff0000"}], "layer": "shade", "frame": 2}],
        [{"op": "set_palette", "colors": ["#000000", "#ffffff", "#ff0000", "#00ff00", "#0000ff"]}],
    ]
    for ops in steps:
        rev = api.apply_ops("hero", rev, ops)["revision"]
    return "hero", rev


def test_the_parser_reads_real_drawing_tool_revisions_exactly_as_aseprite_does(tmp_path):
    name, rev = build_rich_sprite()
    path = revision_path(name, rev)
    facts, problems = aseprite.read_facts(path.read_bytes())
    assert problems == []
    assert facts_tuple(facts) == aseprite_counts(path, tmp_path)
    info = api.inspect_sprite(name, rev)  # the drawing tools' own report agrees on everything they expose
    assert (facts.width, facts.height) == (info["width"], info["height"])
    assert facts.frames == len(info["frames"]) and facts.layers == len(info["layers"]) and facts.tags == len(info["tags"])
    assert facts.palette_size == info["palette_size"] == 5
    assert facts.cels >= facts.layers  # at least the base cels


def test_every_revision_of_a_growing_sprite_parses_like_aseprite(tmp_path):
    api.new_sprite("grow", 8, 8)
    rev = "r0001"
    for ops in ([{"op": "add_layer", "name": "a"}], [{"op": "add_frame"}], [{"op": "add_tag", "name": "t", "from_frame": 1, "to_frame": 2}],
                [{"op": "flip", "axis": "h"}], [{"op": "delete_layer", "layer": "a"}], [{"op": "delete_frame", "frame": 2}]):
        rev = api.apply_ops("grow", rev, ops)["revision"]
    for n in range(1, int(rev[1:]) + 1):
        path = revision_path("grow", f"r{n:04d}")
        facts, problems = aseprite.read_facts(path.read_bytes())
        if n == 1:
            # the untouched first revision still carries the default all-black palette: unverifiable, never guessed
            assert [c.value for c, _ in problems] == ["PALETTE_UNVERIFIABLE"] and facts.palette_size is None
            assert facts_tuple(facts)[:6] == aseprite_counts(path, tmp_path)[:6]  # everything else still agrees
            continue
        assert problems == [], n  # any edit re-saves a palette with real entries, which is exact
        assert facts_tuple(facts) == aseprite_counts(path, tmp_path), n


@pytest.mark.parametrize("kw", [dict(), dict(frames=3, layers=2), dict(tags=2, palette=6), dict(width=20, height=10, frames=2, layers=3, tags=2, palette=6)])
def test_real_aseprite_opens_the_synthetic_builder_files_with_the_same_facts(tmp_path, kw):
    data = b.aseprite(**kw)
    path = tmp_path / "synthetic.aseprite"
    path.write_bytes(data)
    facts, problems = aseprite.read_facts(data)
    assert problems == [] and facts_tuple(facts) == aseprite_counts(path, tmp_path)


def test_a_real_revision_with_its_real_preview_passes_intake_end_to_end(tmp_path, monkeypatch):
    from visual_assets.store import config

    name, rev = build_rich_sprite()
    source = revision_path(name, rev).read_bytes()
    preview = api.render_preview(name, rev, scale=8)
    package = b.package_bytes(source, preview, producer_class="CAP_A", adapter="aseprite-mcp 0.1.0", editor="Aseprite",
                              tool="Aseprite", tool_version="1.3.18.6", brief_id="UNAVAILABLE")
    assert validate(package, source, preview).findings == ()
    monkeypatch.setattr(config, "QUARANTINE_ROOT", tmp_path / "q")
    monkeypatch.setattr(config, "REVIEW_ROOT", tmp_path / "r")
    result = intake(b.write_dir(tmp_path / "pkg", package, source, preview), created_at="2026-01-01T00:00:00Z")
    assert result.verdict is IntakeVerdict.PASSED and result.staged_files[1].file_hash == file_hash(source)


def test_a_real_preview_is_a_whole_number_scale_of_the_real_source(tmp_path):
    name, rev = build_rich_sprite()
    source = revision_path(name, rev).read_bytes()
    for scale in (1, 2, 8, 16):
        preview = api.render_preview(name, rev, scale=scale)
        package = b.package_bytes(source, preview)
        assert validate(package, source, preview).findings == (), scale


ALL_BLACK = {"default_256", "default_resized_200", "resized_1", "resized_2", "resized_10_default_colors",
             "all_black_opaque_10", "custom_256_all_black"}  # every stored entry is opaque black

PALETTE_CASES = {
    "default_256": "",
    "default_resized_200": "s.palettes[1]:resize(200)",
    "resized_1": "s.palettes[1]:resize(1)",
    "resized_2": "s.palettes[1]:resize(2)",
    "resized_10_default_colors": "s.palettes[1]:resize(10)",
    "custom_10": "local p=s.palettes[1]; p:resize(10); for i=0,9 do p:setColor(i, Color{r=i*20,g=0,b=0,a=255}) end",
    "custom_10_with_alpha": "local p=s.palettes[1]; p:resize(10); for i=0,9 do p:setColor(i, Color{r=i*20,g=0,b=0,a=128}) end",
    "custom_256_random": "local p=s.palettes[1]; p:resize(256); for i=0,255 do p:setColor(i, Color{r=(i*7)%256,g=(i*13)%256,b=(i*29)%256,a=255}) end",
    "all_black_opaque_10": "local p=s.palettes[1]; p:resize(10); for i=0,9 do p:setColor(i, Color{r=0,g=0,b=0,a=255}) end",
    "all_same_red_10": "local p=s.palettes[1]; p:resize(10); for i=0,9 do p:setColor(i, Color{r=255,g=0,b=0,a=255}) end",
    "first_custom_rest_default_10": "local p=s.palettes[1]; p:resize(10); p:setColor(0, Color{r=9,g=9,b=9,a=255})",
    "last_custom_rest_default_10": "local p=s.palettes[1]; p:resize(10); p:setColor(9, Color{r=9,g=9,b=9,a=255})",
    "transparent_black_10": "local p=s.palettes[1]; p:resize(10); for i=0,9 do p:setColor(i, Color{r=0,g=0,b=0,a=0}) end",
    "custom_256_all_black": "local p=s.palettes[1]; p:resize(256); for i=0,255 do p:setColor(i, Color{r=0,g=0,b=0,a=255}) end",
}


def run_lua(tmp_path: Path, name: str, lines: list[str]) -> str:
    script = tmp_path / f"{name}.lua"
    script.write_text("\n".join(lines))
    out = subprocess.run([drawing_config.ASEPRITE, "-b", "--script", str(script)], capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    return out.stdout


def test_palette_size_matches_what_aseprite_reports_for_every_palette_it_writes(tmp_path):
    """Exact for every palette with a real colour; refused (None) for the all-black ones, never guessed."""
    script = ["local function rt(label, path, setup)", "  local s = Sprite(8, 8); setup(s); s:saveAs(path)",
              "  print(label, #app.open(path).palettes[1])", "end"]
    for label, body in PALETTE_CASES.items():
        script.append(f'rt("{label}", "{tmp_path / (label + ".aseprite")}", function(s) {body} end)')
    reported = {line.split()[0]: int(line.split()[1]) for line in run_lua(tmp_path, "palettes", script).splitlines() if line.strip()}
    assert set(reported) == set(PALETTE_CASES)
    for label in PALETTE_CASES:
        facts, problems = aseprite.read_facts((tmp_path / f"{label}.aseprite").read_bytes())
        if label in ALL_BLACK:
            assert facts.palette_size is None, label
            assert [c.value for c, _ in problems] == ["PALETTE_UNVERIFIABLE"], (label, problems)
        else:
            assert problems == [], (label, problems)
            assert facts.palette_size == reported[label], (label, facts.palette_size, reported[label])


def test_why_an_all_black_palette_is_unverifiable_its_loaded_size_follows_the_pixels(tmp_path):
    """Same stored palette, different image: Aseprite reports a different size. Intake does not decode pixels."""
    script = ["local function rt(label, setup)", "  local s = Sprite(8, 8); setup(s)",
              f'  local path = "{tmp_path}/" .. label .. ".aseprite"; s:saveAs(path)',
              "  print(label, #app.open(path).palettes[1])", "end",
              "local function px(s, x, y, r, g, b) s.cels[1].image:putPixel(x, y, app.pixelColor.rgba(r, g, b, 255)) end",
              'rt("blank", function(s) end)', 'rt("one_red", function(s) px(s, 1, 1, 255, 0, 0) end)',
              'rt("two", function(s) px(s, 1, 1, 255, 0, 0); px(s, 2, 2, 0, 255, 0) end)']
    reported = {line.split()[0]: int(line.split()[1]) for line in run_lua(tmp_path, "dep", script).splitlines() if line.strip()}
    assert reported == {"blank": 1, "one_red": 2, "two": 3}
    stored = {k: aseprite.read_facts((tmp_path / f"{k}.aseprite").read_bytes()) for k in reported}
    assert {facts.palette_size for facts, _ in stored.values()} == {None}  # identical stored palettes, unverifiable


def test_aseprite_reloads_the_synthetic_palette_shapes_like_the_parser_says(tmp_path):
    shapes = {
        "new_6": b.aseprite(palette=6),
        "new_named": b.aseprite(palette=6, palette_chunks=[b.palette_chunk(6, named=True)]),
        "new_transparent_single": b.aseprite(palette=1, palette_chunks=[b.palette_chunk(1, transparent=True)]),
        "old_9": b.aseprite(palette=9, palette_chunks=[b.old_palette_chunk([(0, 4), (2, 3)])]),
    }
    for label, data in shapes.items():
        path = tmp_path / f"{label}.aseprite"
        path.write_bytes(data)
        facts, problems = aseprite.read_facts(data)
        assert problems == [], label
        assert facts_tuple(facts) == aseprite_counts(path, tmp_path), label


def test_the_parser_reads_animation_metadata_exactly_as_aseprite_reads_it_back(tmp_path):
    """The builders and the parser share one reading of the frame header word and the tags chunk; real Aseprite is the oracle (`TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS`).
    Aseprite writes a 4-frame sprite with distinct durations and one tag per direction, then reloads it and prints what it holds; the parser must report the same, shifted to zero-based frames."""
    path = tmp_path / "anim.aseprite"
    script = [
        "local spr = Sprite(8, 8)", "spr:newFrame(); spr:newFrame(); spr:newFrame()",
        "local ms = {50, 100, 150, 200}", "for i = 1, 4 do spr.frames[i].duration = ms[i] / 1000 end",
        'local function tag(a, z, name, dir, n) local t = spr:newTag(a, z); t.name = name; t.aniDir = dir; t.repeats = n end',
        'tag(1, 2, "idle", AniDir.FORWARD, 0)', 'tag(1, 1, "back", AniDir.REVERSE, 2)', 'tag(2, 4, "walk", AniDir.PING_PONG, 3)', 'tag(3, 4, "swing", AniDir.PING_PONG_REVERSE, 7)',
        f'spr:saveAs("{path}")', f'local r = app.open("{path}")',
        'for i, f in ipairs(r.frames) do print("F", i, math.floor(f.duration * 1000 + 0.5)) end',
        'local function d(x) return x == AniDir.FORWARD and 0 or x == AniDir.REVERSE and 1 or x == AniDir.PING_PONG and 2 or 3 end',
        'for _, t in ipairs(r.tags) do print("T", t.name, t.fromFrame.frameNumber, t.toFrame.frameNumber, d(t.aniDir), t.repeats) end',
    ]
    lines = [line.split("\t") for line in run_lua(tmp_path, "anim", script).splitlines() if line.strip()]
    real_durations = tuple(int(x[2]) for x in lines if x[0] == "F")
    real_tags = [(x[1], int(x[2]) - 1, int(x[3]) - 1, int(x[4]), int(x[5])) for x in lines if x[0] == "T"]
    assert real_durations == (50, 100, 150, 200) and sorted(t[3] for t in real_tags) == [0, 1, 2, 3]
    facts, problems = aseprite.read_facts(path.read_bytes())
    assert not [p for p in problems if p[0].value.startswith(("ANIMATION_", "SOURCE_"))], problems
    assert facts.frame_durations_ms == real_durations
    assert sorted((t.name, t.from_frame, t.to_frame, t.direction, t.repeat) for t in facts.animation_tags) == sorted(real_tags)
