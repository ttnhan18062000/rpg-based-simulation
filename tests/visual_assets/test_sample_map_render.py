"""`tools/visual_assets_sample_map_render.py` (`TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-RENDER`): the port of the TS border rule is proven on the rule's own test vectors
(`frontend/src/visualAssets/__tests__/terrainBorders.test.ts`, `pickDetail.test.ts`), guarded against drift from the TS text, and, where node and esbuild are installed,
checked differentially against the real TS rule on random maps. The renderer is deterministic, marks its gaps and counts them."""

from __future__ import annotations

import json
import random
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from tools import visual_assets_sample_map_render as r

REPO = Path(__file__).resolve().parents[2]
TS_DIR = REPO / "frontend" / "src" / "visualAssets"
WATER, SHALLOW, DESERT, GRASS, FOREST, WALL = 2, 18, 7, 15, 6, 1
ALL = lambda _key: ["v1", "v2", "v3"]  # noqa: E731
NONE = lambda _key: []  # noqa: E731


def only(*kinds):
    keys = {r.MASK_KEYS[k] for k in kinds}
    return lambda key: ["v1"] if key in keys else []


def map_of(rows):
    return lambda x, y: rows[y][x] if 0 <= y < len(rows) and 0 <= x < len(rows[y]) else None


def summary(overlays):
    return [f"{o[0]}:{o[1]}:{o[2]}" for o in overlays]


# ---- the ported constants equal the TS text ----

def _ts(name: str) -> str:
    return (TS_DIR / name).read_text()


def test_the_ported_constants_equal_the_ts_source():
    borders = _ts("terrainBorders.ts")
    priority = re.search(r"TERRAIN_PRIORITY: readonly number\[\] = Object\.freeze\(\[(.*?)\]\)", borders, re.S).group(1)
    assert tuple(int(n) for n in re.findall(r"^\s*(\d+),", priority, re.M)) == r.TERRAIN_PRIORITY
    assert frozenset(int(n) for n in re.search(r"CRISP_TERRAINS: ReadonlySet<number> = new Set\(\[(.*?)\]\)", borders).group(1).split(",")) == r.CRISP_TERRAINS
    assert int(re.search(r"BORDER_DEPTH = (\d+)", borders).group(1)) == r.BORDER_DEPTH and int(re.search(r"TILE_PIXELS = (\d+)", borders).group(1)) == r.TILE
    assert dict(re.findall(r"^\s*(edge|outer_corner|inner_corner): '([a-z_.]+)',", borders, re.M)) == r.MASK_KEYS
    pick = _ts("pickDetail.ts")
    assert int(re.search(r"DETAIL_SEED = (\d+)", pick).group(1)) == r.DETAIL_SEED
    assert int(re.search(r"OFFSET_BASIS = (0x[0-9a-f]+)", pick).group(1), 16) == r.OFFSET_BASIS and int(re.search(r"PRIME = (0x[0-9a-f]+)", pick).group(1), 16) == r.PRIME
    drafts = _ts("terrainDrafts.ts")
    keys_block = drafts.split("TERRAIN_DRAFT_KEYS")[1].split("})")[0]
    assert {int(c): k for c, k in re.findall(r"(\d+): '(terrain\.[a-z_]+)'", keys_block)} == r.TERRAIN_DRAFT_KEYS
    colors_block = drafts.split("TILE_COLORS_COPY")[1].split("})")[0]
    assert {int(c): k for c, k in re.findall(r"(\d+): '(#[0-9a-f]{6})'", colors_block)} == r.TILE_COLORS


def test_the_priority_table_is_a_total_order_over_the_fringing_terrains():
    assert len(set(r.TERRAIN_PRIORITY)) == len(r.TERRAIN_PRIORITY)
    for code in r.TERRAIN_DRAFT_KEYS:
        assert (code in r.RANK) != (code in r.CRISP_TERRAINS)


# ---- pickDetail: the golden vectors of pickDetail.test.ts ----

GOLDEN = [
    ("terrain.forest", 0, 0, 1, 3, 2553659498, 2), ("terrain.forest", 1, 0, 1, 3, 1607584925, 2), ("terrain.forest", 0, 1, 1, 3, 733085261, 2),
    ("terrain.forest", 5, 7, 1, 3, 1330371028, 1), ("terrain.forest", -3, -9, 1, 3, 1245209784, 0), ("terrain.forest", 100000, 2000000, 1, 3, 1806053651, 2),
    ("terrain.forest", 7, 7, 1, 1, 2295137410, 0), ("terrain.forest", 7, 7, 1, 2, 2295137410, 0), ("terrain.forest", 7, 7, 2, 3, 2278359791, 2), ("ui.other", 7, 7, 1, 3, 4127443676, 2),
]


def test_the_golden_vectors_of_the_ts_pick_test_are_reproduced():
    assert [r.fnv1a32(""), r.fnv1a32("a"), r.fnv1a32("foobar"), r.fnv1a32("é")] == [0x811C9DC5, 0xE40C292C, 0xBF9CF968, 0x1E9DE8C1]
    for key, x, y, seed, n, digest, index in GOLDEN:
        assert r.fnv1a32(f"{key}|{x}|{y}|{seed}") == digest
        assert r.pick_detail(key, x, y, seed, [f"v{i}" for i in range(n)]) == f"v{index}"
    three = ["plain", "bush", "tree"]
    assert [r.pick_detail("terrain.forest", *p, r.DETAIL_SEED, three) for p in ((0, 0), (5, 7), (-3, -9))] == ["tree", "bush", "plain"]
    assert r.pick_detail("terrain.forest", 0, 0, r.DETAIL_SEED, ["tree", "bush", "plain"]) == "plain"  # a changed declaration reshuffles
    with pytest.raises(ValueError):
        r.pick_detail("k", 0, 0, 1, [])


# ---- borderOverlays: the vectors of terrainBorders.test.ts ----

def test_nothing_between_equal_codes_or_on_an_all_equal_map():
    assert r.border_overlays(map_of([[GRASS] * 3] * 3), 1, 1, ALL) == []


def test_the_higher_neighbour_fringes_onto_the_lower_cell_only():
    m = map_of([[WATER, DESERT]])
    assert summary(r.border_overlays(m, 0, 0, ALL)) == [f"{DESERT}:edge:90"]
    assert r.border_overlays(m, 1, 0, ALL) == []


def test_a_crisp_terrain_neither_gives_nor_takes():
    assert r.border_overlays(map_of([[WATER, WALL]]), 0, 0, ALL) == [] and r.border_overlays(map_of([[WATER, WALL]]), 1, 0, ALL) == []
    assert r.border_overlays(map_of([[WALL, FOREST]]), 0, 0, ALL) == []


def test_north_east_south_west_are_rotations_0_90_180_270():
    def grid(nx, ny):
        return map_of([[FOREST if (x, y) == (nx, ny) else SHALLOW for x in range(3)] for y in range(3)])

    assert [summary(r.border_overlays(grid(*p), 1, 1, ALL)) for p in ((1, 0), (2, 1), (1, 2), (0, 1))] == [[f"{FOREST}:edge:{d}"] for d in (0, 90, 180, 270)]


def test_four_matching_sides_become_two_inner_corners_not_four_edges():
    m = map_of([[WATER, FOREST, WATER], [FOREST, WATER, FOREST], [WATER, FOREST, WATER]])
    assert summary(r.border_overlays(m, 1, 1, ALL)) == [f"{FOREST}:inner_corner:0", f"{FOREST}:inner_corner:180"]


def test_an_outer_corner_for_a_higher_diagonal_whose_adjacent_sides_are_not_that_terrain():
    assert summary(r.border_overlays(map_of([[WATER, WATER, FOREST], [WATER] * 3, [WATER] * 3]), 1, 1, ALL)) == [f"{FOREST}:outer_corner:0"]
    assert summary(r.border_overlays(map_of([[WATER] * 3, [WATER] * 3, [FOREST, WATER, WATER]]), 1, 1, ALL)) == [f"{FOREST}:outer_corner:180"]
    assert summary(r.border_overlays(map_of([[WATER, WATER, FOREST], [WATER, WATER, FOREST], [WATER] * 3]), 1, 1, ALL)) == [f"{FOREST}:edge:90"]


def test_two_adjacent_edges_of_the_same_higher_terrain_become_one_inner_corner_or_their_two_edges_without_the_mask():
    m = map_of([[WATER, FOREST, WATER], [WATER, WATER, FOREST], [WATER] * 3])
    assert summary(r.border_overlays(m, 1, 1, ALL)) == [f"{FOREST}:inner_corner:0"]
    assert summary(r.border_overlays(m, 1, 1, only("edge"))) == [f"{FOREST}:edge:0", f"{FOREST}:edge:90"]


def test_a_side_is_not_used_twice_when_three_sides_match():
    m = map_of([[WATER, FOREST, WATER], [WATER, WATER, FOREST], [WATER, FOREST, WATER]])
    assert summary(r.border_overlays(m, 1, 1, ALL)) == [f"{FOREST}:edge:180", f"{FOREST}:inner_corner:0"]


def test_lower_ranked_neighbours_are_drawn_first():
    m = map_of([[WATER, FOREST, WATER], [DESERT, WATER, GRASS], [WATER] * 3])
    order = [o[0] for o in r.border_overlays(m, 1, 1, ALL)]
    assert order == sorted(order, key=lambda c: r.RANK[c]) == [DESERT, GRASS, FOREST]


def test_nothing_off_the_map_for_an_unknown_code_or_without_a_mask():
    assert r.border_overlays(map_of([[WATER]]), 0, 0, ALL) == [] and r.border_overlays(map_of([[WATER]]), 5, 5, ALL) == []
    assert r.border_overlays(map_of([[999, FOREST]]), 0, 0, ALL) == []
    assert r.border_overlays(map_of([[WATER, DESERT]]), 0, 0, NONE) == []
    assert summary(r.border_overlays(map_of([[WATER, DESERT]]), 0, 0, only("outer_corner"))) == []


def test_deterministic_per_cell_and_only_declared_variants():
    m = map_of([[WATER, FOREST] * 3])
    first = [r.border_overlays(m, x, 0, ALL) for x in (0, 2, 4)]
    assert first == [r.border_overlays(m, x, 0, ALL) for x in (0, 2, 4)]
    assert all(o[4] in ("v1", "v2", "v3") for overlays in first for o in overlays)


# ---- rotate and composeCell: the pixel vectors of terrainBorders.test.ts ----

def px(fill):
    return b"".join(bytes(fill(x, y)) for y in range(r.TILE) for x in range(r.TILE))


def at(p, x, y):
    return list(p[(y * r.TILE + x) * 4:(y * r.TILE + x) * 4 + 4])


def solid(red, green, blue):
    return px(lambda *_: (red, green, blue, 255))


def test_rotate_turns_a_north_east_pixel_clockwise():
    marker = px(lambda x, y: (255, 0, 0, 255) if (x, y) == (15, 0) else (0, 0, 0, 0))
    assert at(r.rotate(marker, 90), 15, 15) == [255, 0, 0, 255] and at(r.rotate(marker, 180), 0, 15) == [255, 0, 0, 255]
    assert at(r.rotate(marker, 270), 0, 0) == [255, 0, 0, 255] and r.rotate(marker, 0) == marker


def test_compose_never_draws_beyond_4_px_whatever_the_mask_holds_in_any_rotation():
    base, tile, full = solid(10, 10, 10), solid(200, 200, 200), solid(0, 0, 0)
    for rotation in (0, 90, 180, 270):
        for kind in ("edge", "outer_corner", "inner_corner"):
            out = r.compose_cell(base, [(FOREST, kind, rotation, r.MASK_KEYS[kind], "v1")], lambda _c: tile, lambda *_: full)
            assert at(out, 7, 7) == [10, 10, 10, 255] and at(out, 8, 8) == [10, 10, 10, 255]
            for y in range(r.TILE):
                for x in range(r.TILE):
                    if at(out, x, y)[0] == 200:
                        assert min(x, y, r.TILE - 1 - x, r.TILE - 1 - y) < 4  # the approved cap, not the constant under test


def test_compose_shows_the_neighbour_tile_pixels_where_the_rotated_mask_is_opaque_and_the_base_elsewhere():
    base = solid(10, 10, 10)
    tile = px(lambda x, y: (x * 10, y * 10, 5, 255))
    mask = px(lambda x, y: (0, 0, 0, 255) if y < 2 and x % 2 == 0 else (0, 0, 0, 0))
    north = r.compose_cell(base, [(FOREST, "edge", 0, "border.edge", "v1")], lambda _c: tile, lambda *_: mask)
    assert at(north, 4, 1) == [40, 10, 5, 255] and at(north, 5, 1) == [10, 10, 10, 255] and at(north, 4, 2) == [10, 10, 10, 255]
    east = r.compose_cell(base, [(FOREST, "edge", 90, "border.edge", "v1")], lambda _c: tile, lambda *_: mask)
    assert at(east, 14, 4) == [140, 40, 5, 255] and at(east, 14, 5) == [10, 10, 10, 255]


def test_compose_skips_an_overlay_without_tile_or_mask_and_leaves_its_inputs_alone():
    base = solid(10, 10, 10)
    copy = bytes(base)
    assert r.compose_cell(base, [(FOREST, "edge", 0, "border.edge", "v1")], lambda _c: None, lambda *_: solid(0, 0, 0)) == base == copy


# ---- differential: the real TS rule on random maps (needs node and esbuild; the vitest suite of the TS is its own gate) ----

ESBUILD = REPO / "frontend" / "node_modules" / ".bin" / "esbuild"
NODE = shutil.which("node")


@pytest.mark.skipif(NODE is None or not ESBUILD.is_file(), reason="needs node and the frontend's esbuild")
def test_the_port_equals_the_real_ts_rule_on_random_maps(tmp_path):
    bundle = tmp_path / "rule.cjs"
    subprocess.run([str(ESBUILD), str(TS_DIR / "terrainBorders.ts"), "--bundle", "--format=cjs", "--platform=node", f"--outfile={bundle}", "--log-level=error"], check=True, cwd=REPO)
    rng = random.Random(20261011)
    codes = [*r.TERRAIN_PRIORITY, *sorted(r.CRISP_TERRAINS)]
    cases = []
    for _ in range(6):
        w, h = rng.randint(3, 9), rng.randint(3, 9)
        palette = rng.sample(codes, rng.randint(2, 5))
        cases.append([[rng.choice(palette) for _ in range(w)] for _ in range(h)])
    script = tmp_path / "run.cjs"
    script.write_text(
        "const m=require('./rule.cjs');const cases=JSON.parse(require('fs').readFileSync(process.argv[2],'utf8'));const masks={variants:()=>['v1','v2','v3']};"
        "console.log(JSON.stringify(cases.map(g=>{const out=[];for(let y=0;y<g.length;y++)for(let x=0;x<g[0].length;x++)"
        "out.push(m.borderOverlays((a,b)=>g[b]?.[a],x,y,masks).map(o=>[o.neighbour,o.kind,o.rotation,o.maskKey,o.detail]));return out})))"
    )
    (tmp_path / "cases.json").write_text(json.dumps(cases))
    ts = json.loads(subprocess.run([NODE, str(script), str(tmp_path / "cases.json")], check=True, capture_output=True, text=True, cwd=tmp_path).stdout)
    for grid, expected in zip(cases, ts):
        got = [[list(o) for o in r.border_overlays(map_of(grid), x, y, ALL)] for y in range(len(grid)) for x in range(len(grid[0]))]
        assert got == expected
    assert sum(len(cell) for case in ts for cell in case) > 20  # the random maps really exercise fringes


# ---- the renderer ----

class FakeRelease:
    """A stand-in for the runtime export: a few keys with 16 x 16 solid art, optional detail axes, no art for anything else."""

    release_id = "rc-test"

    def __init__(self, art: dict[tuple, bytes], axes=None, masks=True):
        self.art, self.axes, self._masks = art, axes or {}, masks

    def image(self, key, detail):
        rgba = self.art.get((key, detail))
        return (16, 16, rgba) if rgba else None

    def tile(self, key, x, y):
        axis = self.axes.get(key)
        if axis is None:
            img = self.image(key, None)
            return (img[2], None) if img else (None, None)
        picked = r.pick_detail(key, x, y, r.DETAIL_SEED, axis["values"])
        for detail in (picked, axis["default"]):
            img = self.image(key, detail)
            if img:
                return img[2], detail
        return None, picked

    def variants(self, mask_key):
        return [v for v in ("v1", "v2", "v3") if self._masks and (mask_key, v) in self.art]

    def mask(self, mask_key, detail):
        return self.art.get((mask_key, detail))


def small_data(rows, terrain_rows, **kinds):
    names = sorted({n for row in rows for n in row})
    flat = [names.index(n) for row in rows for n in row]
    from tools import visual_assets_sample_map as sm

    return {
        "world_id": "t", "role": "", "width": len(rows[0]), "height": len(rows), "terrain_names": names, "terrain_rle": sm.rle(flat), "terrain": terrain_rows,
        "buildings": kinds.get("buildings", []), "places": kinds.get("places", []), "resource_nodes": kinds.get("resource_nodes", []),
        "kinds": {"building": kinds.get("building", []), "place": kinds.get("place", []), "resource_node": kinds.get("resource_node", []), "entity": []},
        "proposed_aliases": {"label": sm.ALIAS_LABEL},
    }


def trow(name, count, key, alias=None):
    row = {"name": name, "count": count, "key": key, "near": []}
    if alias:
        row["proposed_alias"] = alias
    return row


def test_the_views_differ_only_by_the_labelled_alias_and_each_gap_is_marked_and_counted():
    art = {("terrain.forest", None): solid(0, 90, 0), ("terrain.grassland", None): solid(90, 140, 40)}
    data = small_data([["forest", "PLAIN"], ["PLAIN", "forest"]], [trow("PLAIN", 2, None, "terrain.grassland"), trow("forest", 2, "terrain.forest")])
    exact, e_stats = r.draw_world(data, FakeRelease(art), "exact")
    alias, a_stats = r.draw_world(data, FakeRelease(art), "alias")
    assert e_stats["terrain_no_key"] == {"PLAIN": 2} and e_stats["terrain_cells_in_gap"] == 2 and a_stats["terrain_cells_in_gap"] == 0
    assert bytes(exact[0][16 * 4:16 * 4 + 4]) == bytes(r.no_key_hatch()[:4]) and bytes(alias[0][16 * 4:16 * 4 + 4]) == bytes((90, 140, 40, 255))
    assert a_stats["terrain_drawn"] == {"terrain.forest": 2, "terrain.grassland": 2}


def test_a_key_without_art_is_the_flat_fill_with_a_diagonal_and_is_counted_per_key():
    data = small_data([["swamp"]], [trow("swamp", 1, "terrain.swamp")])
    canvas, stats = r.draw_world(data, FakeRelease({}), "exact")
    assert stats["terrain_key_without_art"] == {"terrain.swamp": 1} and stats["terrain_drawn"] == {}
    assert bytes(canvas[0][0:4]) == bytes((0x2A, 0x2A, 0x3A, 255)) and bytes(canvas[15][0:4]) == bytes((round(0x2A + (255 - 0x2A) * 0.35), round(0x2A + (255 - 0x2A) * 0.35), round(0x3A + (255 - 0x3A) * 0.35), 255))


def test_the_detail_pick_falls_back_to_the_default_value_when_the_picked_value_has_no_art():
    axes = {"terrain.forest": {"values": ["plain", "bush", "tree"], "default": "plain"}}
    art = {("terrain.forest", "plain"): solid(1, 2, 3)}
    release = FakeRelease(art, axes)
    for x in range(8):
        tile, detail = release.tile("terrain.forest", x, 0)
        assert tile == solid(1, 2, 3) and detail == "plain"


def test_objects_with_art_are_drawn_and_objects_without_are_a_counted_checkered_marker():
    art = {("terrain.forest", None): solid(0, 90, 0), ("icon.building.inn", None): solid(200, 0, 0)}
    data = small_data(
        [["forest", "forest"]], [trow("forest", 2, "terrain.forest")],
        buildings=[{"id": "1", "kind": "inn", "x": 0.0, "y": 0}, {"id": "2", "kind": "shop", "x": 1, "y": 0}],
        building=[{"name": "inn", "count": 1, "key": "icon.building.inn", "near": []}, {"name": "shop", "count": 1, "key": None, "near": [], "proposed_alias": "icon.building.store"}],
    )
    canvas, stats = r.draw_world(data, FakeRelease(art), "exact")
    assert stats["objects_drawn"] == {"building:inn": 1} and stats["objects_gap"] == {"building:shop": 1}
    assert bytes(canvas[8][8 * 4:8 * 4 + 4]) == bytes((200, 0, 0, 255)) and bytes(canvas[3][(16 + 3) * 4:(16 + 3) * 4 + 4]) == bytes((255, 0, 255, 255))
    _, alias_stats = r.draw_world(data, FakeRelease(art), "alias")
    assert alias_stats["objects_gap"] == {"building:shop": 1}  # the alias key has no art in this release: still a counted gap


def test_borders_are_composed_only_where_a_ranked_terrain_meets_a_higher_one():
    art = {
        ("terrain.water", None): solid(0, 0, 200), ("terrain.forest", None): solid(0, 200, 0),
        ("border.edge", "v1"): px(lambda x, y: (0, 0, 0, 255) if y < 2 else (0, 0, 0, 0)),
    }
    data = small_data([["water", "forest"]], [trow("water", 1, "terrain.water"), trow("forest", 1, "terrain.forest")])
    canvas, stats = r.draw_world(data, FakeRelease(art), "exact")
    assert stats["bordered_cells"] == 1 and stats["border_pieces"] == 1  # water takes forest's fringe on its east side
    assert bytes(canvas[4][14 * 4:14 * 4 + 4]) == bytes((0, 200, 0, 255)) and bytes(canvas[4][0:4]) == bytes((0, 0, 200, 255))


def test_the_encoder_and_the_upscale_are_deterministic_and_decodable():
    from visual_assets.store import pixels

    rows = [bytearray(bytes((x * 60, y * 90, 7, 255)) for x in range(3)) if False else bytearray(b"".join(bytes((x * 60, y * 90, 7, 255)) for x in range(3))) for y in range(2)]
    png = r.encode_png(3, 2, rows)
    assert png == r.encode_png(3, 2, rows)
    img = pixels.decode_png(png)
    assert (img.width, img.height) == (3, 2) and img.rgba[0:4] == bytes((0, 0, 7, 255))
    doubled = r.upscale2(bytes(rows[0]))
    assert len(doubled) == 24 and bytes(doubled[0:8]) == bytes(rows[0][0:4]) * 2


def _chunk_offsets(png: bytes):
    import struct

    i = 8
    while i < len(png):
        yield i
        i += 12 + struct.unpack(">I", png[i:i + 4])[0]


@pytest.fixture(scope="module")
def rendered_twice(tmp_path_factory):
    from tools import visual_assets_sample_map as sm

    export = tmp_path_factory.mktemp("export") / "runtime"
    from visual_assets.store import runtime_export

    runtime_export.export_runtime("pilot", r.RELEASE_ID, export)
    release = r.Release(export)
    data = sm.build_data("dungeon_crawl")
    first = tmp_path_factory.mktemp("render-a")
    second = tmp_path_factory.mktemp("render-b")
    stats = r.render_world(data, release, first)
    r.render_world(data, release, second)
    return data, stats, first, second


def test_two_renders_of_a_real_world_are_byte_identical(rendered_twice):
    _, _, first, second = rendered_twice
    for name in ("exact_x1.png", "exact_x2.png", "alias_x1.png", "alias_x2.png", "render_stats.json"):
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_the_real_render_counts_its_gaps_against_the_data_and_every_png_decodes(rendered_twice):
    data, stats, first, _ = rendered_twice
    by_name = {row["name"]: row["count"] for row in data["terrain"]}
    exact, alias = stats["views"]["exact"], stats["views"]["alias"]
    # the exact view resolves terrain names through the registry aliases (`plain` -> grassland, `ruin` -> ruins; the base fill is the catalog id `plain` since D72, divergence 2.124), so the terrain gap is empty in both views
    assert exact["terrain_no_key"] == {} and exact["terrain_cells_in_gap"] == 0 and alias["terrain_cells_in_gap"] == 0
    assert exact["terrain_drawn"] == alias["terrain_drawn"] and alias["terrain_drawn"]["terrain.grassland"] == by_name["plain"] and alias["terrain_drawn"]["terrain.ruins"] == by_name["ruin"]
    assert exact["objects_gap"] == {"place:RUIN": 1} and alias["objects_gap"] == {} and alias["objects_drawn"] == {"place:RUIN": 1}
    for view in (exact, alias):
        assert view["cells"] == data["width"] * data["height"]
        for name, info in view["files"].items():
            png = (first / name).read_bytes()
            assert len(png) == info["bytes"] and len(png) < 1_000_000
    # the store's decoder refuses images over `MAX_DECODED_BYTES` (a bound, not changed here), so the sheet is checked through its header and its inflated size
    import struct
    import zlib

    png = (first / "exact_x1.png").read_bytes()
    width, height = struct.unpack(">II", png[16:24])
    assert (width, height) == (data["width"] * 16, data["height"] * 16)
    idat = b"".join(png[i + 8:i + 8 + struct.unpack(">I", png[i:i + 4])[0]] for i in _chunk_offsets(png) if png[i + 4:i + 8] == b"IDAT")
    assert len(zlib.decompress(idat)) == (width * 4 + 1) * height


def test_the_page_names_the_view_of_every_number_and_labels_the_aliases(rendered_twice, tmp_path):
    data, stats, _, _ = rendered_twice
    page = r.write_page([stats], {data["world_id"]: data}, tmp_path).read_text()
    assert "Exact view (primary evidence)" in page and "unconfirmed: asset-planner proposal for rpg-planner (#519)" in page
    assert "never intaken, adopted or put in a release candidate" in page and "scaled to one 16 x 16 cell" in page


# ---- the committed evidence (docs/assets/sample_map/) ----

def test_the_committed_evidence_is_small_and_is_exactly_what_the_tool_produces(tmp_path):
    from tools import visual_assets_sample_map as sm
    from visual_assets.store import runtime_export

    export = tmp_path / "runtime"
    runtime_export.export_runtime("pilot", r.RELEASE_ID, export)
    produced = r.evidence_files({w: sm.build_data(w) for w in sm.WORLDS}, r.Release(export))
    committed = {p.name: p.read_bytes() for p in sorted(r.EVIDENCE_DIR.glob("*.png"))}
    assert committed == produced  # regenerate with `python -m tools.visual_assets_sample_map evidence`
    assert sum(len(b) for b in committed.values()) <= r.EVIDENCE_CAP_BYTES == 256 * 1024
    assert sorted(committed) == sorted(f"{name}_{view}_x1.png" for name in r.EVIDENCE_CROPS for view in ("exact", "alias"))
    docs_bytes = sum(p.stat().st_size for p in r.EVIDENCE_DIR.iterdir() if p.is_file())
    assert docs_bytes <= r.EVIDENCE_CAP_BYTES  # the whole folder, README and gap report included


def test_the_evidence_writer_refuses_a_total_over_the_cap(tmp_path, monkeypatch):
    monkeypatch.setattr(r, "EVIDENCE_CAP_BYTES", 10)
    monkeypatch.setattr(r, "evidence_files", lambda datas, release: {"a_exact_x1.png": b"x" * 11})
    with pytest.raises(SystemExit):
        r.write_evidence({}, object(), tmp_path)
    assert list(tmp_path.iterdir()) == []
