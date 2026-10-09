"""The one-colour silhouette sheet the owner approves BEFORE any full drawing (`TCK-20261008-VISUAL-ASSETS-ICON-OWNER-FIXES`, step 3 of the recognisability process).

`visual_assets/icons/silhouette_proposals.yaml` holds each proposed silhouette (outline included) as rows of `#`; this module puts every proposal beside the icon it would replace (the adopted revision r0001,
read from the kept drafts) and its neighbours, measures how far each option is from its same-size neighbours (the sheet rule's I1 measure, shape only) and from its nearest icon across all families (the
look-alike report's measure), and writes the committed copy the preview page shows: `frontend/src/visualAssets/__fixtures__/iconsilhouettes/silhouette_sheet.json`. Pure Python, read-only.

    python -m visual_assets.review.icon_silhouette_sheet --write     # refresh the committed copy
    python -m visual_assets.review.icon_silhouette_sheet --check     # exit 1 if it differs from a fresh build
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from visual_assets.review import icon_lookalikes as la
from visual_assets.review import icon_sheet_rule as rule
from visual_assets.review.pilot_colour_vision import REPO

PROPOSALS = REPO / "visual_assets" / "icons" / "silhouette_proposals.yaml"
COMMITTED = REPO / "frontend" / "src" / "visualAssets" / "__fixtures__" / "iconsilhouettes" / "silhouette_sheet.json"


def rows_of(sprite: rule.Sprite) -> list[str]:
    return ["".join("#" if sprite.rgba[y * sprite.width + x][3] else "." for x in range(sprite.width)) for y in range(sprite.height)]


def sprite_of(rows: list[str]) -> rule.Sprite:
    h, w = len(rows), len(rows[0])
    assert all(len(r) == w for r in rows), "rows must all be as wide as the first"
    return rule.Sprite(w, h, tuple((0x20, 0x20, 0x20, 255) if ch == "#" else (0, 0, 0, 0) for r in rows for ch in r))


def load_proposals(path: Path = PROPOSALS) -> dict:
    data = yaml.safe_load(path.read_text())
    for key, slot in data["slots"].items():
        for tag, opt in slot["options"].items():
            sprite_of(opt["rows"])  # validates the shape
            assert len(opt["rows"]) == opt["size"] and len(opt["rows"][0]) == opt["size"], f"{key} {tag}: rows are not size x size"
    return data


def build(proposals: dict | None = None, sprites: dict[str, rule.Sprite] | None = None) -> dict:
    proposals = proposals or load_proposals()
    sprites = sprites or la.all_icon_sprites()
    slots = []
    for key, slot in proposals["slots"].items():
        current = sprites[key]
        neighbours = [{"key": n, "size": sprites[n].width, "rows": rows_of(sprites[n])} for n in slot["neighbours"]]
        options = []
        for tag, opt in slot["options"].items():
            mine = sprite_of(opt["rows"])
            same = {n["key"]: rule.shape_distance(mine, sprites[n["key"]]) for n in neighbours if n["size"] == mine.width}
            shapes = {k: la.normalised(s) for k, s in sprites.items() if k != key}
            mine_norm = la.normalised(mine)
            nearest = sorted((la.distance(mine_norm, shp), k) for k, shp in shapes.items())[:2]
            options.append({
                "tag": tag, "label": opt["label"], "size": mine.width, "rows": opt["rows"],
                "i1_same_size_neighbours_xor_px": same,
                "i1_smallest_xor_px": min(same.values()) if same else None,
                "nearest_in_any_family_xor_px_of_576": [{"key": k, "xor_px": d} for d, k in nearest],
            })
        slots.append({"key": key, "size": current.width, "current_rows": rows_of(current), "neighbours": neighbours, "options": options})
    return {"record_type": "icon_silhouette_sheet", "decided": proposals["decided"], "slots": slots}


def text(sheet: dict) -> str:
    return json.dumps(sheet, indent=1, sort_keys=True) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    fresh = text(build())
    if args.write:
        COMMITTED.parent.mkdir(parents=True, exist_ok=True)
        COMMITTED.write_text(fresh)
        print(f"wrote {COMMITTED}")
    same = COMMITTED.exists() and COMMITTED.read_text() == fresh
    print("identical" if same else "differs from a fresh build")
    sys.exit(1 if args.check and not same else 0)
