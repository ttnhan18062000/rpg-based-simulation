"""The spec compliance table measures proportions from pixels: the committed redrawn icons meet their specs, and a planted copy of the sword that passed every earlier gate fails (`TCK-20261008-VISUAL-ASSETS-ICON-V2-RECOGNISABILITY-REDRAW`)."""

from __future__ import annotations

from visual_assets.review import icon_compliance as cp
from visual_assets.review import icon_lookalikes as la
from visual_assets.review import icon_sheet_rule as rule

INK = {"#": "#0e1018", "s": "#91a2ab", "g": "#e8c040", "b": "#5a2a1a"}


def sprite(rows: list[str]) -> rule.Sprite:
    return rule.from_rows(rows, INK)


def rows_of(rows: dict) -> dict[str, bool]:
    return {r.item: r.ok for r in next(iter(rows.values()))}


def make_sword(blade_len=12, blade_w=4, guard_w=12, guard_t=2, grip_w=2, grip_len=2, pommel=(4, 2), size=24) -> rule.Sprite:
    """A sword with the given proportions: content cells (two shades so the lint-free look is irrelevant), then a 1 px dark outline ring, centred on the canvas."""
    cells: dict[tuple[int, int], tuple[int, int, int]] = {}
    mid = (size - 1) / 2

    def row(y, width, colour):
        x0 = round(mid - (width - 1) / 2)
        for x in range(x0, x0 + width):
            cells[(x, y)] = colour

    y = 3
    row(y, 2, (0x91, 0xA2, 0xAB))
    for _ in range(blade_len - 1):
        y += 1
        row(y, blade_w, (0xC8, 0xD8, 0xE8))
    for _ in range(guard_t):
        y += 1
        row(y, guard_w, (0xE8, 0xC0, 0x40))
    for _ in range(grip_len):
        y += 1
        row(y, grip_w, (0x5A, 0x2A, 0x1A))
    for _ in range(pommel[1] if pommel else 0):
        y += 1
        row(y, pommel[0], (0xE8, 0xC0, 0x40))
    ring = {(x + dx, y2 + dy) for (x, y2) in cells for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))} - set(cells)
    rgba = [(0, 0, 0, 0)] * (size * size)
    for (x, y2), c in cells.items():
        rgba[y2 * size + x] = (*c, 255)
    for x, y2 in ring:
        rgba[y2 * size + x] = (0x0E, 0x10, 0x18, 255)
    return rule.Sprite(size, size, tuple(rgba))


def failed(rows: dict) -> set[str]:
    return {r.item for r in next(iter(rows.values())) if not r.ok}


def measure_sword(sprite: rule.Sprite) -> dict:
    return cp.measure({"icon.item.weapon": sprite}, ["icon.item.weapon"])


def test_the_committed_redrawn_icons_meet_every_spec_row():
    rows = cp.measure(la.all_icon_sprites())
    assert set(rows) == set(cp.CHECKS) and len(rows) == 6
    failing = [(k, r.item, r.measured) for k, rs in rows.items() for r in rs if not r.ok]
    assert failing == []


def test_a_sword_built_to_the_spec_passes_every_row():
    rows = measure_sword(make_sword())
    assert failed(rows) == set(), cp.markdown(rows)


def test_each_way_the_old_sword_was_wrong_fails_its_own_row():
    # the sword that was named "steel sword" and passed every gate: a short blade, a grip wider than the guard, no pommel
    assert "blade length" in failed(measure_sword(make_sword(blade_len=7)))
    assert "grip width" in failed(measure_sword(make_sword(grip_w=6, guard_w=9, blade_w=4)))
    assert "pommel" in failed(measure_sword(make_sword(pommel=None)))
    assert failed(measure_sword(make_sword(guard_w=6))) & {"crossguard width", "measurable"}  # a guard under 9 px cannot even be found as a guard: reported as not measurable
    assert "total height" in failed(measure_sword(make_sword(blade_len=14)))
    old_in_spirit = measure_sword(make_sword(blade_len=7, grip_w=6, guard_w=9, pommel=None))
    assert len(failed(old_in_spirit)) >= 3


def test_each_measured_row_names_its_spec_and_its_measured_value_and_the_table_is_markdown():
    rows = cp.measure(la.all_icon_sprites())
    text = cp.markdown(rows)
    for key, rs in rows.items():
        assert f"**`{key}`**" in text and all(r.spec and r.measured for r in rs)
    assert text.count("| ok |") == sum(len(rs) for rs in rows.values())


def test_a_square_bead_and_an_eight_pixel_bead_fail_the_round_and_size_rows():
    def bead(rows):
        return rule.from_rows(rows, {"#": "#0e1018", "s": "#555b73"})

    square = bead(["######..", "#ssss#..", "#ssss#..", "#ssss#..", "#ssss#..", "######..", "........", "........"])
    big = bead(["..####..", ".#ssss#.", "#ssssss#", "#ssssss#", "#ssssss#", "#ssssss#", ".#ssss#.", "..####.."])
    sprites = la.all_icon_sprites()
    assert {"round, not square", "size"} <= {r.item for r in cp.measure({**sprites, "icon.rarity.common": square}, ["icon.rarity.common"])["icon.rarity.common"] if not r.ok}
    assert "size" in {r.item for r in cp.measure({**sprites, "icon.rarity.common": big}, ["icon.rarity.common"])["icon.rarity.common"] if not r.ok}


def staircase_wall(tops_by_column: list[int], size: int = 16) -> rule.Sprite:
    """A brick wall (courses of two rows, alternating light and dark) whose columns have the given top rows, with a 1 px dark outline."""
    cells = {}
    for i, top in enumerate(tops_by_column):
        for y in range(top, 11):
            cells[(3 + i, y)] = (0xC8, 0xD8, 0xE8) if ((y - 3) // 2) % 2 == 0 else (0x71, 0x7E, 0x8F)
    ring = {(x + dx, y + dy) for (x, y) in cells for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))} - set(cells)
    rgba = [(0, 0, 0, 0)] * (size * size)
    for (x, y), c in cells.items():
        rgba[y * size + x] = (*c, 255)
    for x, y in ring:
        rgba[y * size + x] = (0x0E, 0x10, 0x18, 255)
    return rule.Sprite(size, size, tuple(rgba))


def test_a_wall_that_slopes_one_way_like_the_boot_fails_the_u_shape_row_and_a_u_shaped_wall_passes_it():
    slope = cp.measure({"icon.marker.ruins": staircase_wall([3, 3, 3, 5, 5, 5, 7, 7, 9, 9])}, ["icon.marker.ruins"])["icon.marker.ruins"]
    assert "broken top edge: U-shaped, not a slope" in {r.item for r in slope if not r.ok}
    u_shape = cp.measure({"icon.marker.ruins": staircase_wall([4, 4, 4, 8, 8, 8, 8, 3, 3, 3])}, ["icon.marker.ruins"])["icon.marker.ruins"]
    assert "broken top edge: U-shaped, not a slope" not in {r.item for r in u_shape if not r.ok}


# ---- the owner-fix revisions (r0002): each spec row fails on its own planted defect (`TCK-20261008-VISUAL-ASSETS-ICON-OWNER-FIXES`) ----

from visual_assets.review import icon_owner_fixes_draft_set as of  # noqa: E402


def _edit(sprite: rule.Sprite, changes: dict[tuple[int, int], tuple[int, int, int, int]]) -> rule.Sprite:
    rgba = list(sprite.rgba)
    for (x, y), value in changes.items():
        rgba[y * sprite.width + x] = value
    return rule.Sprite(sprite.width, sprite.height, tuple(rgba))


def _r2(key: str, sprite: rule.Sprite) -> set[str]:
    sprites = of.proposed_sprites()
    sprites[key] = sprite
    return {r.item for r in cp.measure(sprites, [key], checks=cp.CHECKS_R2)[key] if not r.ok}


def test_the_six_drafts_as_drawn_meet_every_row_of_their_own_table():
    rows = cp.measure({**la.all_icon_sprites(), **of.fix_sprites()}, list(of.KEYS), checks=cp.CHECKS_R2)
    assert set(rows) == set(of.KEYS) and [(k, r.item) for k, rs in rows.items() for r in rs if not r.ok] == []


def test_a_changed_frame_pixel_or_an_outlined_chevron_fails_the_buff_rows():
    mine = of.fix_sprites()["icon.status.frame_buff"]
    assert "frame unchanged" in _r2("icon.status.frame_buff", _edit(mine, {(1, 7): (0, 0, 0, 0)}))
    assert "solid, not an outline" in _r2("icon.status.frame_buff", _edit(mine, {(7, 8): (0x4A, 0x60, 0x50, 255)}))  # a hole in the shaft


def test_the_adopted_slate_bead_fails_the_lighter_than_the_tier_badges_row():
    old = la.all_icon_sprites()["icon.rarity.common"]  # the 7 px slate bead of r0001: mean L* 40 against tier D's 29, a gap of 11
    failed_rows = _r2("icon.rarity.common", old)
    assert "lighter than the dark tier badges" in failed_rows and "silver fill" in failed_rows


def test_a_tent_that_reaches_the_canvas_edge_fails_the_live_area_row_which_the_first_drawing_did():
    mine = of.fix_sprites()["icon.marker.enemy_camp"]
    edge = _edit(mine, {(0, 0): (0x0E, 0x10, 0x18, 255)})
    assert "live area" in _r2("icon.marker.enemy_camp", edge)


def test_a_closed_dome_without_a_gap_fails_the_ruins_arch_rows():
    mine = of.fix_sprites()["icon.marker.ruins"]
    fill = {(x, y): (0x91, 0xA2, 0xAB, 255) for x in range(6, 10) for y in range(5, 11)}
    assert {"open gap", "rubble"} & _r2("icon.marker.ruins", _edit(mine, fill))


def test_a_hood_without_a_face_opening_fails_its_row_and_the_rejected_toolbox_is_not_hammer_and_tongs():
    toolbox = rule.from_rows(["#" * 18] * 16, {"#": "#d04030"})  # stands in for the rejected toolbox: a solid red slab
    slab = rule.Sprite(24, 24, tuple(p for y in range(24) for x in range(24) for p in [((0xD0, 0x40, 0x30, 255) if 3 <= x < 21 and 4 <= y < 20 else (0, 0, 0, 0))]))
    failed_rows = _r2("icon.item.tool", slab)
    assert {"wooden handle", "steel hammer head", "tong jaws", "rivet at the crossing"} <= failed_rows and toolbox is not None
    hood = of.fix_sprites()["icon.class.rogue"]
    no_face = _edit(hood, {(x, y): (0x3A, 0x30, 0x40, 255) for x in range(7, 17) for y in range(7, 18) if tuple(hood.rgba[y * 24 + x][:3]) == (0x25, 0x25, 0x30)})
    assert {"face opening", "measurable"} & _r2("icon.class.rogue", no_face)  # with no dark pixels at all the part cannot even be found: reported as not measurable


def test_a_cottage_with_modern_blue_glass_a_triangle_debuff_and_a_changed_tankard_outline_fail_their_rows():
    house = of.fix_sprites()["icon.building.hero_house"]
    blue = _edit(house, {(6, 15): (0x50, 0xA8, 0xE0, 255), (7, 15): (0x50, 0xA8, 0xE0, 255)})
    assert "no modern blue glass" in _r2("icon.building.hero_house", blue)
    old_house = la.all_icon_sprites()["icon.building.hero_house"]  # the adopted white-walled house with blue windows
    assert {"thatched roof", "timber frame", "no modern blue glass"} <= _r2("icon.building.hero_house", old_house)
    old_debuff = la.all_icon_sprites()["icon.status.frame_debuff"]  # the inverted red triangle that read as a road sign
    assert {"eight spikes", "not a triangle (not a road sign)", "symmetric"} & _r2("icon.status.frame_debuff", old_debuff)
    tankard = of.fix_sprites()["icon.building.inn"]
    assert "same outline" in _r2("icon.building.inn", _edit(tankard, {(2, 2): (0x0E, 0x10, 0x18, 255)}))
    assert "iron hoops" in _r2("icon.building.inn", la.all_icon_sprites()["icon.building.inn"])  # the adopted mug has none
