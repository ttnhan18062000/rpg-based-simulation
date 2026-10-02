"""Per-operation tests plus a full complex-asset build. Need real Aseprite + bwrap.

Run: .venv/bin/python -m pytest experiments/aseprite_mcp -q
"""

from __future__ import annotations

import shutil
import struct
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adapter  # noqa: E402

pytestmark = pytest.mark.skipif(
    not (Path(adapter.ASEPRITE).exists() and shutil.which("bwrap")),
    reason="requires aseprite and bwrap",
)

CLEAR = "#00000000"


@pytest.fixture(autouse=True)
def workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "WORKSPACE", tmp_path / "ws")
    return tmp_path / "ws"


def region(name, w, h, frame=1, revision=None):
    return adapter.inspect_sprite(
        name, revision, {"x": 0, "y": 0, "w": w, "h": h}, frame=frame
    )["region"]


def count(grid, value):
    return sum(row.count(value) for row in grid)


def png_size(png):
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", png[16:24])


def mk(name="s", w=8, h=8, bg=CLEAR):
    return adapter.new_sprite(name, w, h, bg)


# ------------------------------------------------------------------ drawing ops


def test_ellipse_filled_and_outline():
    mk("e", 10, 10)
    adapter.apply_ops("e", "r0001", [
        {"op": "ellipse", "x": 0, "y": 0, "width": 10, "height": 10, "color": "#ff0000"},
    ])
    adapter.apply_ops("e", "r0002", [
        {"op": "ellipse", "x": 0, "y": 0, "width": 10, "height": 10, "color": "#0000ff",
         "filled": False},
    ])
    g = region("e", 10, 10)
    assert g[0][0] == CLEAR and g[9][9] == CLEAR  # corners outside the ellipse
    assert g[5][5] == "#ff0000ff"  # interior keeps the fill
    assert g[5][0] == "#0000ffff" and g[0][5] == "#0000ffff"  # outline overwrote the rim
    # symmetric in both axes
    assert g == [row[::-1] for row in g] and g == g[::-1]


def test_flood_fill_stays_inside_boundary():
    mk("f", 8, 8)
    adapter.apply_ops("f", "r0001", [
        {"op": "rect", "x": 1, "y": 1, "width": 6, "height": 6, "color": "#000000", "filled": False},
        {"op": "flood_fill", "x": 3, "y": 3, "color": "#ffff00"},
    ])
    g = region("f", 8, 8)
    assert count(g, "#ffff00ff") == 16  # 4x4 interior
    assert g[0][0] == CLEAR  # outside untouched
    assert g[1][1] == "#000000ff"  # border untouched


def test_replace_color_outline_silhouette_flip_clear_grayscale():
    mk("o", 8, 8)
    adapter.apply_ops("o", "r0001", [
        {"op": "rect", "x": 2, "y": 2, "width": 3, "height": 3, "color": "#ff0000"},
        {"op": "replace_color", "from_color": "#ff0000", "to_color": "#00ff00"},
    ])
    g = region("o", 8, 8)
    assert count(g, "#00ff00ff") == 9 and count(g, "#ff0000ff") == 0

    adapter.apply_ops("o", "r0002", [{"op": "outline", "color": "#000000"}])
    g = region("o", 8, 8)
    assert count(g, "#000000ff") == 12  # 4-neighbour ring around a 3x3 block

    adapter.apply_ops("o", "r0003", [{"op": "grayscale"}])
    g = region("o", 8, 8)
    assert g[3][3] == "#969696ff"  # (299*0 + 587*255 + 114*0 + 500)//1000 = 150

    adapter.apply_ops("o", "r0004", [{"op": "silhouette", "color": "#123456"}])
    g = region("o", 8, 8)
    assert count(g, "#123456ff") == 21 and g[0][0] == CLEAR

    adapter.apply_ops("o", "r0005", [{"op": "flip", "axis": "h"}])
    g = region("o", 8, 8)
    assert g[3][2] == "#123456ff" and g[3][5] == "#123456ff"  # mirrored span 1..5 -> 2..6

    adapter.apply_ops("o", "r0006", [{"op": "clear"}])
    assert adapter.inspect_sprite("o")["nonempty_pixels"] == 0


def test_pixels_with_alpha_roundtrip():
    mk("a", 4, 4)
    adapter.draw_pixels("a", "r0001", [{"x": 1, "y": 1, "color": "#aabbcc80"}])
    assert region("a", 4, 4)[1][1] == "#aabbcc80"


# ------------------------------------------------------------------ layers


def test_layers_target_hide_rename_and_preview():
    mk("l", 8, 8)
    out = adapter.apply_ops("l", "r0001", [
        {"op": "add_layer", "name": "gear"},
        {"op": "rect", "x": 0, "y": 0, "width": 4, "height": 4, "color": "#ff0000", "layer": "base"},
        {"op": "rect", "x": 4, "y": 4, "width": 4, "height": 4, "color": "#0000ff", "layer": "gear"},
    ])
    assert [l["name"] for l in out["layers"]] == ["base", "gear"]
    assert out["nonempty_pixels"] == 32
    assert out["layers"][0]["nonempty_by_frame"] == [16]
    assert out["layers"][1]["nonempty_by_frame"] == [16]

    out = adapter.apply_ops("l", "r0002", [
        {"op": "set_visible", "layer": "gear", "visible": False},
        {"op": "rename_layer", "layer": "base", "name": "body"},
    ])
    assert [l["name"] for l in out["layers"]] == ["body", "gear"]
    assert out["layers"][1]["visible"] is False
    assert out["nonempty_pixels"] == 16  # hidden layer is not in the flattened frame

    # layer-solo preview works; hidden layer still previewable on its own
    assert png_size(adapter.render_preview("l", scale=2, layer="body")) == (16, 16)


def test_layer_errors():
    mk("l", 4, 4)
    for ops, msg in [
        ([{"op": "pixels", "layer": "nope", "pixels": [{"x": 0, "y": 0, "color": "#fff000"}]}],
         "no such layer"),
        ([{"op": "add_layer", "name": "base"}], "layer exists"),
        ([{"op": "rename_layer", "layer": "base", "name": "base"}], None),  # same name is fine
    ]:
        if msg:
            with pytest.raises(adapter.AdapterError, match=msg):
                adapter.apply_ops("l", "r0001", ops)
        else:
            adapter.apply_ops("l", "r0001", ops)


def test_layer_limit():
    mk("l", 4, 4)
    ops = [{"op": "add_layer", "name": f"L{i}"} for i in range(16)]  # base + 16 = 17
    with pytest.raises(adapter.AdapterError, match="layer limit"):
        adapter.apply_ops("l", "r0001", ops)


# ------------------------------------------------------------------ frames, tags, palette


def test_frames_durations_tags_filmstrip():
    mk("m", 4, 4)
    out = adapter.apply_ops("m", "r0001", [
        {"op": "rect", "x": 0, "y": 0, "width": 2, "height": 2, "color": "#ff0000"},
        {"op": "add_frame", "copy_from": 1},
        {"op": "add_frame"},  # empty frame appended
        {"op": "pixels", "frame": 2, "pixels": [{"x": 3, "y": 3, "color": "#00ff00"}]},
        {"op": "set_duration", "frame": 1, "ms": 200},
        {"op": "set_duration", "frame": 2, "ms": 120},
        {"op": "add_tag", "name": "idle", "from_frame": 1, "to_frame": 2},
    ])
    assert [f["duration_ms"] for f in out["frames"]][:2] == [200, 120]
    assert [f["nonempty"] for f in out["frames"]] == [4, 5, 0]
    assert out["tags"] == [{"name": "idle", "from": 1, "to": 2}]
    checks = [f["checksum"] for f in out["frames"]]
    assert len(set(checks)) == 3  # per-frame checksums distinguish the frames

    assert png_size(adapter.render_preview("m", frame=2, scale=4)) == (16, 16)
    assert png_size(adapter.render_filmstrip("m", scale=2)) == (3 * 4 * 2, 8)
    assert region("m", 4, 4, frame=2)[3][3] == "#00ff00ff"
    assert region("m", 4, 4, frame=3)[3][3] == CLEAR


def test_frame_errors_and_limit():
    mk("m", 4, 4)
    with pytest.raises(adapter.AdapterError, match="no such frame"):
        adapter.apply_ops("m", "r0001", [{"op": "clear", "frame": 2}])
    with pytest.raises(adapter.AdapterError, match="bad tag range"):
        adapter.apply_ops("m", "r0001", [{"op": "add_tag", "name": "x", "from_frame": 1, "to_frame": 3}])
    with pytest.raises(adapter.AdapterError, match="frame limit"):
        adapter.apply_ops("m", "r0001", [{"op": "add_frame"} for _ in range(16)])


def test_palette_set_and_read():
    mk("p", 4, 4)
    out = adapter.apply_ops("p", "r0001", [
        {"op": "set_palette", "colors": ["#000000", "#ff0000", "#00ff00ff", "#0000ff"]},
    ])
    assert out["palette_size"] == 4
    assert adapter.inspect_sprite("p")["palette"] == ["#000000ff", "#ff0000ff", "#00ff00ff", "#0000ffff"]


# ------------------------------------------------------------------ stamp / branch / atomicity


def test_stamp_composes_sprites_and_frames():
    mk("tile", 4, 4, "#ff0000")
    adapter.apply_ops("tile", "r0001", [
        {"op": "add_frame"},
        {"op": "rect", "x": 0, "y": 0, "width": 4, "height": 4, "color": "#0000ff", "frame": 2},
    ])
    mk("sheet", 16, 8)
    out = adapter.apply_ops("sheet", "r0001", [
        {"op": "stamp", "source": "tile", "x": 0, "y": 0},
        {"op": "stamp", "source": "tile", "source_frame": 2, "x": 8, "y": 4},
        {"op": "stamp", "source": "tile", "source_revision": "r0001", "x": 12, "y": 0},
    ])
    g = region("sheet", 16, 8)
    assert g[0][0] == "#ff0000ff" and g[4][8] == "#0000ffff" and g[0][12] == "#ff0000ff"
    assert out["nonempty_pixels"] == 48


def test_stamp_errors():
    mk("tile", 4, 4, "#ff0000")
    mk("sheet", 8, 8)
    with pytest.raises(adapter.AdapterError, match="does not fit"):
        adapter.apply_ops("sheet", "r0001", [{"op": "stamp", "source": "tile", "x": 6, "y": 0}])
    with pytest.raises(adapter.AdapterError, match="no such sprite"):
        adapter.apply_ops("sheet", "r0001", [{"op": "stamp", "source": "ghost", "x": 0, "y": 0}])
    with pytest.raises(adapter.AdapterError, match="no such revision"):
        adapter.apply_ops("sheet", "r0001", [
            {"op": "stamp", "source": "tile", "source_revision": "r0009", "x": 0, "y": 0}])
    with pytest.raises(adapter.AdapterError, match="no such source frame"):
        adapter.apply_ops("sheet", "r0001", [
            {"op": "stamp", "source": "tile", "source_frame": 3, "x": 0, "y": 0}])


def test_branch_keeps_geometry_and_is_independent():
    mk("hero", 8, 8)
    adapter.apply_ops("hero", "r0001", [
        {"op": "rect", "x": 1, "y": 1, "width": 5, "height": 5, "color": "#ff0000"}])
    b = adapter.branch_sprite("hero", "hero_gray", "r0002")
    assert b["revision"] == "r0001" and b["name"] == "hero_gray"
    assert b["frames"][0]["checksum"] == adapter.inspect_sprite("hero")["frames"][0]["checksum"]
    adapter.apply_ops("hero_gray", "r0001", [{"op": "grayscale"}])
    assert adapter.inspect_sprite("hero")["colors"] == ["#ff0000ff"]  # source untouched
    assert adapter.inspect_sprite("hero_gray")["colors"] == ["#4c4c4cff"]
    with pytest.raises(adapter.AdapterError, match="already exists"):
        adapter.branch_sprite("hero", "hero_gray")


def test_failed_batch_publishes_nothing():
    mk("t", 8, 8)
    with pytest.raises(adapter.AdapterError, match=r"op 3 \(pixels\).*out of bounds"):
        adapter.apply_ops("t", "r0001", [
            {"op": "rect", "x": 0, "y": 0, "width": 2, "height": 2, "color": "#ff0000"},
            {"op": "add_layer", "name": "x"},
            {"op": "pixels", "pixels": [{"x": 99, "y": 0, "color": "#ffffff"}]},
        ])
    out = adapter.inspect_sprite("t")
    assert out["revision"] == "r0001" and out["nonempty_pixels"] == 0 and len(out["layers"]) == 1


# ------------------------------------------------------------------ validation


@pytest.mark.parametrize(
    "ops, msg",
    [
        ([], "ops must hold"),
        ("rect", "ops must hold"),
        ([{"op": "explode"}], "unknown op"),
        ([{"op": "rect", "x": 0, "y": 0, "width": 1, "height": 1, "color": "#fff000", "shell": "rm"}],
         "unexpected field"),
        ([{"op": "add_frame", "layer": "base"}], "does not take a layer"),
        ([{"op": "add_layer", "name": "x", "frame": 1}], "does not take a frame"),
        ([{"op": "flip", "axis": "d"}], "axis"),
        ([{"op": "set_duration", "ms": 100}], "needs a frame"),
        ([{"op": "set_duration", "frame": 1, "ms": 0}], "ms must be"),
        ([{"op": "add_layer", "name": "../x"}], "name must match"),
        ([{"op": "rect", "x": 0, "y": 0, "width": 1, "height": 1, "color": "red"}], "color must be"),
        ([{"op": "stamp", "source": "../x", "x": 0, "y": 0}], "name must match"),
        ([{"op": "set_palette", "colors": []}], "colors must hold"),
        ([{"op": "clear"}] * (adapter.MAX_OPS + 1), "ops must hold"),
        ([{"op": "pixels", "pixels": [{"x": 0, "y": 0, "color": "#fff000"}] * 4097}], "pixels must hold"),
        ([{"op": "pixels", "pixels": [{"x": 0, "y": 0, "color": "#fff000"}] * 4096}] * 3,
         "explicit pixels per batch"),
        ([{"op": "pixels", "pixels": [{"x": 0, "y": 0}]}], "color must be"),
        ([{"op": "pixels", "pixels": ["x"]}], "must be an object"),
        ([{"op": "delete_layer"}], "delete_layer needs a layer"),
        ([{"op": "delete_layer", "layer": "../x"}], "layer must match"),
        ([{"op": "delete_layer", "layer": "base", "frame": 1}], "does not take a frame"),
        ([{"op": "delete_layer", "layer": "base", "extra": 1}], "unexpected field"),
        ([{"op": "delete_frame"}], "delete_frame needs a frame"),
        ([{"op": "delete_frame", "frame": 0}], "frame must be an integer"),
        ([{"op": "delete_frame", "frame": 17}], "frame must be an integer"),
        ([{"op": "delete_frame", "frame": True}], "frame must be an integer"),
        ([{"op": "delete_frame", "frame": 1, "layer": "base"}], "does not take a layer"),
        ([{"op": "resize_canvas", "width": 8}], "height must be an integer"),
        ([{"op": "resize_canvas", "width": 0, "height": 8}], "width must be an integer"),
        ([{"op": "resize_canvas", "width": 8, "height": 129}], "height must be an integer"),
        ([{"op": "resize_canvas", "width": 129, "height": 8}], "width must be an integer"),
        ([{"op": "resize_canvas", "width": 8, "height": 0}], "height must be an integer"),
        ([{"op": "resize_canvas", "width": -1, "height": 8}], "width must be an integer"),
        ([{"op": "resize_canvas", "width": "8", "height": 8}], "width must be an integer"),
        ([{"op": "resize_canvas", "width": 8, "height": 8, "layer": "base"}], "does not take a layer"),
        ([{"op": "resize_canvas", "width": 8, "height": 8, "frame": 1}], "does not take a frame"),
        ([{"op": "resize_canvas", "width": 8, "height": 8, "anchor": "c"}], "unexpected field"),
    ],
)
def test_validation_rejects_before_running_aseprite(ops, msg, monkeypatch):
    mk("v", 4, 4)
    monkeypatch.setattr(adapter, "_bwrap", lambda *a, **k: pytest.fail("aseprite must not run"))
    with pytest.raises(adapter.AdapterError, match=msg):
        adapter.apply_ops("v", "r0001", ops)


def test_stamp_sources_limited():
    ops = [{"op": "stamp", "source": f"s{i}", "x": 0, "y": 0} for i in range(adapter.MAX_REFS + 1)]
    with pytest.raises(adapter.AdapterError, match="distinct stamp sources"):
        adapter.validate_ops(ops)


# ------------------------------------------------------------------ complex asset


def test_complex_asset_knight_for_art_experiments():
    """ART-W01/W03/W04/W06/W07-style pipeline on one 16x16 humanoid, three layers, 2-frame idle."""
    SKIN, ARMOR, DARK, METAL, PLUME = "#e8b890", "#6e7f99", "#2b2f3a", "#c9d1dc", "#c0392b"
    adapter.new_sprite("knight", 16, 16)
    r = adapter.apply_ops("knight", "r0001", [
        {"op": "add_layer", "name": "gear"},
        {"op": "add_layer", "name": "line"},
        # body (base layer): legs, torso, arms, head
        {"op": "rect", "x": 5, "y": 12, "width": 2, "height": 3, "color": ARMOR, "layer": "base"},
        {"op": "rect", "x": 9, "y": 12, "width": 2, "height": 3, "color": ARMOR, "layer": "base"},
        {"op": "rect", "x": 4, "y": 6, "width": 8, "height": 6, "color": ARMOR, "layer": "base"},
        {"op": "rect", "x": 3, "y": 7, "width": 1, "height": 4, "color": ARMOR, "layer": "base"},
        {"op": "rect", "x": 12, "y": 7, "width": 1, "height": 4, "color": ARMOR, "layer": "base"},
        {"op": "ellipse", "x": 5, "y": 1, "width": 6, "height": 6, "color": SKIN, "layer": "base"},
        {"op": "rect", "x": 6, "y": 8, "width": 4, "height": 1, "color": DARK, "layer": "base"},
        {"op": "pixels", "layer": "base", "pixels": [
            {"x": 6, "y": 3, "color": DARK}, {"x": 9, "y": 3, "color": DARK}]},
        # gear: helmet plume, sword, shield
        {"op": "rect", "x": 5, "y": 1, "width": 6, "height": 2, "color": METAL, "layer": "gear"},
        {"op": "line", "x0": 8, "y0": 0, "x1": 8, "y1": 1, "color": PLUME, "layer": "gear"},
        {"op": "line", "x0": 14, "y0": 3, "x1": 14, "y1": 11, "color": METAL, "layer": "gear"},
        {"op": "ellipse", "x": 1, "y": 7, "width": 4, "height": 5, "color": PLUME, "layer": "gear"},
        # outline layer built from a flattened-looking union: outline each pixel layer separately
        {"op": "outline", "color": "#000000", "layer": "base"},
    ])
    assert [l["name"] for l in r["layers"]] == ["base", "gear", "line"]
    base_only = r["layers"][0]["nonempty_by_frame"][0]
    assert base_only > 60 and r["layers"][1]["nonempty_by_frame"][0] > 25

    # idle: copy frame, bob the gear layer's shield 1px by redrawing it in frame 2
    r = adapter.apply_ops("knight", r["revision"], [
        {"op": "add_frame", "copy_from": 1},
        {"op": "clear", "layer": "gear", "frame": 2},
        {"op": "rect", "x": 5, "y": 2, "width": 6, "height": 2, "color": METAL, "layer": "gear", "frame": 2},
        {"op": "line", "x0": 14, "y0": 4, "x1": 14, "y1": 12, "color": METAL, "layer": "gear", "frame": 2},
        {"op": "set_duration", "frame": 1, "ms": 400},
        {"op": "set_duration", "frame": 2, "ms": 400},
        {"op": "add_tag", "name": "idle", "from_frame": 1, "to_frame": 2},
        {"op": "set_palette", "colors": [SKIN, ARMOR, DARK, METAL, PLUME, "#000000"]},
    ])
    f1, f2 = r["frames"]
    assert f1["checksum"] != f2["checksum"]  # motion is real
    assert r["tags"][0]["name"] == "idle" and r["palette_size"] == 6
    final = r["revision"]

    # W01 single-colour silhouette branch: same footprint on frame 1
    adapter.branch_sprite("knight", "knight_sil", final)
    sil = adapter.apply_ops("knight_sil", "r0001", [
        {"op": "silhouette", "color": "#101010", "layer": "base", "frame": 1},
        {"op": "silhouette", "color": "#101010", "layer": "gear", "frame": 1},
    ])
    assert sil["frames"][0]["nonempty"] == f1["nonempty"]
    assert set(adapter.inspect_sprite("knight_sil")["colors"]) >= {"#101010ff"}

    # W06 grayscale + colour-variant branches share identical geometry
    adapter.branch_sprite("knight", "knight_gray", final)
    gray = adapter.apply_ops("knight_gray", "r0001", [
        {"op": "grayscale", "layer": ly, "frame": f} for ly in ("base", "gear") for f in (1, 2)])
    assert [f["nonempty"] for f in gray["frames"]] == [f1["nonempty"], f2["nonempty"]]
    adapter.branch_sprite("knight", "knight_red", final)
    red = adapter.apply_ops("knight_red", "r0001", [
        {"op": "replace_color", "from_color": ARMOR, "to_color": "#a83232", "layer": "base", "frame": f}
        for f in (1, 2)])
    assert [f["nonempty"] for f in red["frames"]] == [f1["nonempty"], f2["nonempty"]]

    # W04/W05: comparison row — stamp the variants onto one native-scale sheet
    adapter.new_sprite("sheet", 64, 16)
    sheet = adapter.apply_ops("sheet", "r0001", [
        {"op": "stamp", "source": s, "x": 16 * i, "y": 0}
        for i, s in enumerate(["knight", "knight_sil", "knight_gray", "knight_red"])])
    assert sheet["nonempty_pixels"] > 3 * f1["nonempty"]

    # reviewer artefacts render at native and 8x
    assert png_size(adapter.render_preview("knight", scale=1)) == (16, 16)
    assert png_size(adapter.render_preview("knight", frame=2, scale=8)) == (128, 128)
    assert png_size(adapter.render_filmstrip("knight", scale=4)) == (128, 64)
    assert png_size(adapter.render_preview("sheet", scale=4)) == (256, 64)
    # every step left an immutable revision trail
    assert adapter.list_sprites()[0]["name"] in {"knight", "knight_gray", "knight_red", "knight_sil", "sheet"}
    assert dict((s["name"], s["revisions"]) for s in adapter.list_sprites())["knight"] == 3


# ------------------------------------------------------------------ delete_layer / delete_frame / resize_canvas


def test_delete_layer_removes_layer_and_its_pixels():
    mk("d", 4, 4)
    adapter.apply_ops("d", "r0001", [
        {"op": "add_layer", "name": "top"},
        {"op": "add_frame"},
        {"op": "rect", "x": 0, "y": 0, "width": 2, "height": 2, "color": "#ff0000", "layer": "base"},
        {"op": "rect", "x": 2, "y": 2, "width": 2, "height": 2, "color": "#0000ff", "layer": "top"},
        {"op": "rect", "x": 2, "y": 2, "width": 1, "height": 1, "color": "#0000ff", "layer": "top",
         "frame": 2},
    ])
    out = adapter.apply_ops("d", "r0002", [{"op": "delete_layer", "layer": "top"}])
    assert [l["name"] for l in out["layers"]] == ["base"]
    assert out["frames"][0]["nonempty"] == 4 and out["frames"][1]["nonempty"] == 0
    assert out["colors"] == ["#ff0000ff"]
    assert region("d", 4, 4)[3][3] == CLEAR
    assert [l["name"] for l in adapter.inspect_sprite("d", "r0002")["layers"]] == ["base", "top"]


def test_delete_layer_can_delete_the_bottom_layer_when_others_remain():
    mk("d", 4, 4)
    adapter.apply_ops("d", "r0001", [{"op": "add_layer", "name": "top"}])
    out = adapter.apply_ops("d", "r0002", [{"op": "delete_layer", "layer": "base"}])
    assert [l["name"] for l in out["layers"]] == ["top"]


def test_last_layer_cannot_be_deleted():
    mk("d", 4, 4)
    with pytest.raises(adapter.AdapterError, match=r"op 1 \(delete_layer\).*cannot delete the last layer"):
        adapter.apply_ops("d", "r0001", [{"op": "delete_layer", "layer": "base"}])
    out = adapter.inspect_sprite("d")
    assert out["revision"] == "r0001" and [l["name"] for l in out["layers"]] == ["base"]
    # also when an earlier op in the same batch leaves exactly one layer
    with pytest.raises(adapter.AdapterError, match="cannot delete the last layer"):
        adapter.apply_ops("d", "r0001", [
            {"op": "add_layer", "name": "x"},
            {"op": "delete_layer", "layer": "x"},
            {"op": "delete_layer", "layer": "base"},
        ])
    assert adapter.inspect_sprite("d")["revision"] == "r0001"
    with pytest.raises(adapter.AdapterError, match="no such layer: ghost"):
        adapter.apply_ops("d", "r0001", [{"op": "add_layer", "name": "x"},
                                         {"op": "delete_layer", "layer": "ghost"}])


def test_delete_frame_renumbers_and_keeps_durations():
    mk("f", 4, 4)
    adapter.apply_ops("f", "r0001", [
        {"op": "add_frame"}, {"op": "add_frame"},
        {"op": "pixels", "frame": 1, "pixels": [{"x": 0, "y": 0, "color": "#ff0000"}]},
        {"op": "pixels", "frame": 2, "pixels": [{"x": 1, "y": 0, "color": "#00ff00"},
                                                {"x": 2, "y": 0, "color": "#00ff00"}]},
        {"op": "pixels", "frame": 3, "pixels": [{"x": 3, "y": 0, "color": "#0000ff"}]},
        {"op": "set_duration", "frame": 1, "ms": 100},
        {"op": "set_duration", "frame": 2, "ms": 200},
        {"op": "set_duration", "frame": 3, "ms": 300},
    ])
    out = adapter.apply_ops("f", "r0002", [{"op": "delete_frame", "frame": 2}])
    assert [(f["index"], f["duration_ms"], f["nonempty"]) for f in out["frames"]] == [
        (1, 100, 1), (2, 300, 1)]
    assert region("f", 4, 4, frame=2)[0][3] == "#0000ffff"
    assert len(adapter.inspect_sprite("f", "r0002")["frames"]) == 3  # old revision untouched


def test_delete_frame_adjusts_tags_natively():
    mk("f", 4, 4)
    adapter.apply_ops("f", "r0001", [
        {"op": "add_frame"}, {"op": "add_frame"},
        {"op": "add_tag", "name": "span", "from_frame": 1, "to_frame": 2},
        {"op": "add_tag", "name": "only3", "from_frame": 3, "to_frame": 3},
    ])
    out = adapter.apply_ops("f", "r0002", [{"op": "delete_frame", "frame": 2}])
    tags = {t["name"]: (t["from"], t["to"]) for t in out["tags"]}
    assert tags == {"span": (1, 1), "only3": (2, 2)}  # Aseprite shrinks/shifts; not hand-rolled
    out = adapter.apply_ops("f", "r0003", [{"op": "delete_frame", "frame": 2}])
    assert [t["name"] for t in out["tags"]] == ["span"]  # a tag wholly inside the frame is removed


def test_last_frame_cannot_be_deleted_and_bad_frame_is_rejected():
    mk("f", 4, 4)
    with pytest.raises(adapter.AdapterError, match=r"op 1 \(delete_frame\).*cannot delete the last frame"):
        adapter.apply_ops("f", "r0001", [{"op": "delete_frame", "frame": 1}])
    out = adapter.inspect_sprite("f")
    assert out["revision"] == "r0001" and len(out["frames"]) == 1
    adapter.apply_ops("f", "r0001", [{"op": "add_frame"}])
    with pytest.raises(adapter.AdapterError, match="no such frame: 3"):
        adapter.apply_ops("f", "r0002", [{"op": "delete_frame", "frame": 3}])
    assert adapter.inspect_sprite("f")["revision"] == "r0002"


def test_resize_canvas_crop_keeps_top_left_pixels_on_every_layer_and_frame():
    mk("c", 6, 6)
    adapter.apply_ops("c", "r0001", [
        {"op": "add_layer", "name": "top"}, {"op": "add_frame"},
        {"op": "pixels", "layer": "base", "frame": 1, "pixels": [
            {"x": 0, "y": 0, "color": "#ff0000"}, {"x": 5, "y": 5, "color": "#ff0000"}]},
        {"op": "pixels", "layer": "top", "frame": 2, "pixels": [
            {"x": 2, "y": 1, "color": "#0000ff"}, {"x": 4, "y": 4, "color": "#0000ff"}]},
    ])
    out = adapter.apply_ops("c", "r0002", [{"op": "resize_canvas", "width": 3, "height": 3}])
    assert (out["width"], out["height"]) == (3, 3)
    # the (5,5)/(4,4) pixels were cropped away, and per-layer counts must not include them
    by = {l["name"]: l["nonempty_by_frame"] for l in out["layers"]}
    assert by == {"base": [1, 0], "top": [0, 1]}
    assert region("c", 3, 3, frame=1)[0][0] == "#ff0000ff"
    assert region("c", 3, 3, frame=2)[1][2] == "#0000ffff"
    assert [f["nonempty"] for f in out["frames"]] == [1, 1]
    assert png_size(adapter.render_preview("c", scale=2)) == (6, 6)
    assert adapter.inspect_sprite("c", "r0002")["width"] == 6  # old revision untouched


def test_resize_canvas_pad_keeps_positions_and_new_area_is_transparent():
    mk("p", 3, 3)
    adapter.apply_ops("p", "r0001", [
        {"op": "rect", "x": 0, "y": 0, "width": 3, "height": 3, "color": "#ff0000"},
        {"op": "add_layer", "name": "top"},
        {"op": "pixels", "layer": "top", "pixels": [{"x": 2, "y": 2, "color": "#0000ff"}]},
    ])
    out = adapter.apply_ops("p", "r0002", [{"op": "resize_canvas", "width": 5, "height": 4}])
    assert (out["width"], out["height"]) == (5, 4)
    assert out["nonempty_pixels"] == 9  # only the original 3x3 is opaque
    g = region("p", 5, 4)
    assert g[0][0] == "#ff0000ff" and g[2][2] == "#0000ffff"  # same coordinates as before
    assert g[0][3] == CLEAR and g[3][0] == CLEAR and g[3][4] == CLEAR
    by = {l["name"]: l["nonempty_by_frame"] for l in out["layers"]}
    assert by == {"base": [9], "top": [1]}
    # drawing into the newly added area works on a normalised cel on every layer
    out = adapter.apply_ops("p", "r0003", [
        {"op": "pixels", "layer": "base", "pixels": [{"x": 4, "y": 3, "color": "#00ff00"}]},
        {"op": "pixels", "layer": "top", "pixels": [{"x": 3, "y": 0, "color": "#00ff00"}]},
    ])
    assert region("p", 5, 4)[3][4] == "#00ff00ff" and region("p", 5, 4)[0][3] == "#00ff00ff"


def test_resize_canvas_noop_same_size_and_one_pixel():
    mk("n", 4, 4)
    adapter.apply_ops("n", "r0001", [{"op": "rect", "x": 0, "y": 0, "width": 4, "height": 4,
                                      "color": "#ff0000"}])
    same = adapter.apply_ops("n", "r0002", [{"op": "resize_canvas", "width": 4, "height": 4}])
    assert same["frames"][0]["checksum"] == adapter.inspect_sprite("n", "r0002")["frames"][0]["checksum"]
    tiny = adapter.apply_ops("n", "r0003", [{"op": "resize_canvas", "width": 1, "height": 1}])
    assert (tiny["width"], tiny["height"]) == (1, 1) and tiny["nonempty_pixels"] == 1
    big = adapter.apply_ops("n", "r0004", [
        {"op": "resize_canvas", "width": adapter.MAX_DIM, "height": adapter.MAX_DIM}])
    assert (big["width"], big["height"]) == (adapter.MAX_DIM, adapter.MAX_DIM)
    assert big["nonempty_pixels"] == 1
