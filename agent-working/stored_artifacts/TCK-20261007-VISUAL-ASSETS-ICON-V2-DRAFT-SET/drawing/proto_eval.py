import json, sys
sys.path.insert(0, "/home/vboxuser/Work/rpg-aseprite-mcp")
from canvas import Canvas
import loc, pan, rar
from tests.visual_assets import icon_sheet_rule as r, icon_v2_groups as g, icon_v2_keys as v2, icon_draft_set as ds
from tests.visual_assets.pilot_colour_vision import VISIONS

def sprite(c: Canvas) -> r.Sprite:
    out = []
    for y in range(c.h):
        for x in range(c.w):
            col = c.px.get((x, y))
            out.append((int(col[1:3], 16), int(col[3:5], 16), int(col[5:7], 16), 255) if col else (0, 0, 0, 0))
    return r.Sprite(c.w, c.h, tuple(out))

def all_canvases(fills=rar.FILLS):
    d = {}
    for n, f in loc.ALL.items(): d[f"icon.marker.{n}"] = f()
    for n, f in pan.BUILD.items(): d[f"icon.building.{n}"] = f()
    for n, f in pan.CLASSES.items(): d[f"icon.class.{n}"] = f()
    for n, f in pan.ITEMS.items(): d[f"icon.item.{n}"] = f()
    for n, c in rar.all_badges(fills).items(): d[f"icon.rarity.{n}"] = c
    return d

def evaluate(canvases):
    icons = dict(ds.draft_sprites())          # the adopted key set (drafts kept as history)
    icons = {k: v for k, v in icons.items() if k != "icon.plate.location"}
    icons.update({k: sprite(c) for k, c in canvases.items()})
    rep = r.evaluate_sheet(icons, g.GROUPS, {}, {}, shape_only=g.SHAPE_ONLY)
    return rep

if __name__ == "__main__":
    cv = all_canvases()
    assert sorted(cv) == sorted(v2.KEYS), set(v2.KEYS) ^ set(cv)
    rep = evaluate(cv)
    print(rep["result"], "I1", rep["i1"], "I2", rep["i2"])
    for name, row in rep["groups"].items(): print(f"  {name:10} size {row['size']:2} pairs {row['pairs']:3} min shape {row['min_shape_px_across_classes']} value_checked {row['value_checked']} minL {row['min_dL_by_vision']}")
    print("I1 fails:", rep["failing"]["i1"])
    seen = set()
    for f in rep["failing"]["i2"]:
        k = (f["group"], f["a"], f["b"])
        if k not in seen: seen.add(k); print("I2 fail", k, f["vision"], f["dL"])
    for k, c in sorted(cv.items()):
        l = c.lint()
        if l["warn"]: print("LINT", k, l["warn"])
